from typing import Optional
from uuid import UUID

from app.database.db import SessionDep
from app.genre.repository import GenreRepository
from app.genre.schemas import (
    GenreResponse, GenresListResponse, GenreCreate, GenreUpdate
)


class GenreService:
    """
    Сервис для работы с жанрами.

    Предоставляет бизнес-логику для операций с жанрами,
    включая получение списков жанров с фильтрацией и пагинацией.
    """

    def __init__(self, session: SessionDep):
        """
        Инициализация сервиса.

        Args:
            session: Сессия базы данных
        """
        self.repository = GenreRepository(session)
        self.session = session

    async def get_genres_list(
        self,
        page: int = 1,
        page_size: int = 10,
        q: Optional[str] = None,
    ) -> GenresListResponse:
        """
        Получить список жанров с фильтрацией и пагинацией.

        Args:
            page: Номер страницы (начиная с 1)
            page_size: Размер страницы (от 1 до 100)
            q: Поиск по подстроке в названии

        Returns:
            GenresListResponse: Список жанров с метаинформацией
        """
        # Валидация параметров
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 10

        genres, total = await self.repository.get_genres_list(
            page=page,
            page_size=page_size,
            q=q,
        )

        # Преобразуем модели в схемы ответа
        genre_responses = [
            GenreResponse(id=genre.id, name=genre.name) for genre in genres
        ]

        return GenresListResponse(
            items=genre_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_genre_by_id(self, genre_id: UUID) -> Optional[GenreResponse]:
        """
        Получить жанр по ID.

        Args:
            genre_id: ID жанра

        Returns:
            Optional[GenreResponse]: Данные жанра или None, если не найден
        """
        genre = await self.repository.get_genre_by_id(genre_id)
        if not genre:
            return None

        return GenreResponse(id=genre.id, name=genre.name)

    async def create_genre(self, genre_data: GenreCreate) -> GenreResponse:
        """
        Создать новый жанр.

        Args:
            genre_data: Данные для создания жанра

        Returns:
            GenreResponse: Созданный жанр

        Raises:
            ValueError: Если жанр с таким названием уже существует
        """
        # Проверяем, существует ли жанр с таким названием
        existing_genre = await self.repository.get_genre_by_name(
            genre_data.name
        )
        if existing_genre:
            raise ValueError(
                f"Жанр с названием '{genre_data.name}' уже существует"
            )

        genre_dict = genre_data.model_dump()
        genre = await self.repository.create_genre(genre_dict)
        await self.session.commit()

        return GenreResponse(id=genre.id, name=genre.name)

    async def update_genre(
        self, genre_id: UUID, genre_data: GenreUpdate
    ) -> Optional[GenreResponse]:
        """
        Обновить существующий жанр.

        Args:
            genre_id: ID жанра
            genre_data: Данные для обновления

        Returns:
            Optional[GenreResponse]: Обновленный жанр или None, если не найден

        Raises:
            ValueError: Если жанр с таким названием уже существует
        """
        # Если обновляется название, проверяем, не занято ли оно
        if genre_data.name:
            existing_genre = await self.repository.get_genre_by_name(
                genre_data.name
            )
            if existing_genre and existing_genre.id != genre_id:
                raise ValueError(
                    f"Жанр с названием '{genre_data.name}' уже существует"
                )

        update_dict = genre_data.model_dump(exclude_unset=True)
        if not update_dict:
            return await self.get_genre_by_id(genre_id)

        genre = await self.repository.update_genre(genre_id, update_dict)
        if not genre:
            return None
        await self.session.commit()

        return GenreResponse(id=genre.id, name=genre.name)

    async def delete_genre(self, genre_id: UUID) -> bool:
        """
        Удалить жанр.

        Args:
            genre_id: ID жанра

        Returns:
            bool: True если жанр был удален, False если не найден
        """
        deleted = await self.repository.delete_genre(genre_id)
        if deleted:
            await self.session.commit()
        return deleted
