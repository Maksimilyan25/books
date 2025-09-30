import os
import sys
import json
import csv
import logging
from typing import List, Dict, Any
from uuid import UUID
from pathlib import Path

import pydantic
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

# Проверяем, запущен ли скрипт в Docker-контейнере
IN_DOCKER = os.environ.get('RUNNING_IN_DOCKER', 'false').lower() == 'true'

if IN_DOCKER:
    # Если запущено в Docker, используем абсолютные пути
    sys.path.append('/app')
else:
    # Если запущено локально, добавляем корневую директорию проекта
    # Это позволяет импортировать модуль 'app' из любой поддиректории
    project_root = str(Path(__file__).parent.parent)
    sys.path.append(project_root)

# flake8: noqa: E402
from database.db import Base, engine, async_session
from genre.models import Genre

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("import_genres.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()


class GenreImportModel(BaseModel):
    """Модель для валидации данных жанра при импорте."""
    id: UUID = Field(..., description="ID жанра")
    name: str = Field(
        ..., min_length=1, max_length=100, description="Название жанра"
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        return v.strip()


async def create_tables():
    """Создание таблиц в базе данных, если они не существуют."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Таблицы успешно созданы")


async def read_csv_file(file_path: str) -> List[Dict[str, Any]]:
    """Чтение данных из CSV файла."""
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            data = [row for row in reader]
            logger.info(
                f"Прочитано {len(data)} записей из CSV файла: {file_path}"
            )
            return data
    except Exception as e:
        logger.error(f"Ошибка при чтении CSV файла {file_path}: {str(e)}")
        raise


async def read_json_file(file_path: str) -> List[Dict[str, Any]]:
    """Чтение данных из JSON файла."""
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            data = json.load(file)
            logger.info(
                f"Прочитано {len(data)} записей из JSON файла: {file_path}"
            )
            return data
    except Exception as e:
        logger.error(f"Ошибка при чтении JSON файла {file_path}: {str(e)}")
        raise


def validate_genres_data(
    genres_data: List[Dict[str, Any]]
) -> List[GenreImportModel]:
    """Валидация данных жанров с использованием Pydantic."""
    validated_genres = []
    errors = []

    for idx, genre_data in enumerate(genres_data, 1):
        try:
            validated_genre = GenreImportModel(**genre_data)
            validated_genres.append(validated_genre)
        except pydantic.ValidationError as e:
            error_msg = f"Ошибка валидации записи #{idx}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)

    if errors:
        logger.warning(
            f"Найдено {len(errors)} ошибок валидации из "
            f"{len(genres_data)} записей"
        )

    return validated_genres


async def import_genres_batch(
    genres_batch: List[GenreImportModel]
) -> Dict[str, int]:
    """Импорт батча жанров в базу данных с поддержкой upsert."""
    result = {"created": 0, "updated": 0, "errors": 0}
    
    async with async_session() as session:
        try:
            async with session.begin():
                for genre_data in genres_batch:
                    try:
                        existing_genre = await session.get(
                            Genre, genre_data.id
                        )
                        
                        if existing_genre:
                            existing_genre.name = genre_data.name
                            result["updated"] += 1
                            logger.debug(
                                f"Обновлен жанр: {genre_data.id} - "
                                f"{genre_data.name}"
                            )
                        else:
                            from sqlalchemy import select
                            query = select(Genre).where(
                                Genre.name == genre_data.name
                            )
                            existing_by_name = (
                                await session.execute(query)
                            ).scalar_one_or_none()
                            
                            if existing_by_name:
                                existing_by_name.id = genre_data.id
                                existing_by_name.name = genre_data.name
                                result["updated"] += 1
                                logger.debug(
                                    f"Обновлен жанр по названию: "
                                    f"{genre_data.id} - "
                                    f"{genre_data.name}"
                                )
                            else:
                                new_genre = Genre(
                                    id=genre_data.id, name=genre_data.name
                                )
                                session.add(new_genre)
                                result["created"] += 1
                                logger.debug(
                                    f"Создан новый жанр: {genre_data.id} - "
                                    f"{genre_data.name}"
                                )
                    
                    except Exception as e:
                        result["errors"] += 1
                        logger.error(
                            f"Ошибка при импорте жанра {genre_data.id}: "
                            f"{str(e)}"
                        )
            
            await session.commit()
            logger.info(
                f"Батч успешно обработан: создано {result['created']}, "
                f"обновлено {result['updated']}, ошибок {result['errors']}"
            )
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при обработке батча: {str(e)}")
            result["errors"] += len(genres_batch)
    
    return result


async def import_genres(
    file_path: str, batch_size: int = 100
) -> Dict[str, int]:
    """Основная функция импорта жанров."""
    total_result = {"created": 0, "updated": 0, "errors": 0}
    
    try:
        if file_path.endswith('.csv'):
            genres_data = await read_csv_file(file_path)
        elif file_path.endswith('.json'):
            genres_data = await read_json_file(file_path)
        else:
            raise ValueError(
                "Неподдерживаемый формат файла. Используйте CSV или JSON."
            )
        
        validated_genres = validate_genres_data(genres_data)
        
        if not validated_genres:
            logger.warning("Нет валидных данных для импорта")
            return total_result
        
        for i in range(0, len(validated_genres), batch_size):
            batch = validated_genres[i:i + batch_size]
            batch_result = await import_genres_batch(batch)
            
            total_result["created"] += batch_result["created"]
            total_result["updated"] += batch_result["updated"]
            total_result["errors"] += batch_result["errors"]
            
            logger.info(
                f"Обработано {min(i + batch_size, len(validated_genres))} "
                f"из {len(validated_genres)} записей"
            )
        
        logger.info(
            f"Импорт завершен: создано {total_result['created']}, "
            f"обновлено {total_result['updated']}, "
            f"ошибок {total_result['errors']}"
        )
        
    except Exception as e:
        logger.error(f"Критическая ошибка при импорте: {str(e)}")
        total_result["errors"] += (
            len(genres_data) if 'genres_data' in locals() else 0
        )
    
    return total_result


async def main():
    """Основная функция скрипта."""
    if len(sys.argv) < 2:
        logger.error("Укажите путь к файлу с данными жанров")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        logger.error(f"Файл не найден: {file_path}")
        sys.exit(1)
    
    batch_size = int(os.getenv("BATCH_SIZE", "100"))
    logger.info(f"Размер батча: {batch_size}")
    
    await create_tables()
    
    result = await import_genres(file_path, batch_size)
    
    logger.info("=== Итоговая статистика ===")
    logger.info(f"Создано: {result['created']}")
    logger.info(f"Обновлено: {result['updated']}")
    logger.info(f"Ошибок: {result['errors']}")


if __name__ == "__main__":
    import asyncio
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Импорт прерван пользователем")
    except Exception as e:
        logger.error(f"Необработанная ошибка: {str(e)}")
        sys.exit(1)