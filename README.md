# База данных книг

API для управления библиотекой книг с использованием FastAPI, SQLAlchemy и PostgreSQL.

## Функциональность

- Управление книгами (CRUD операции)
- Управление жанрами (CRUD операции)
- Связь книг с жанрами и участниками (авторы, редакторы, иллюстраторы)
- Пагинация, фильтрация и сортировка результатов

## Технологический стек

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Database**: PostgreSQL
- **Migrations**: Alembic
- **Testing**: Pytest
- **Containerization**: Docker, Docker Compose

## Тестирование

Для запуска тестов выполните команду:

```bash
# Локально
pytest app/tests/

# С помощью Docker
docker-compose exec app pytest app/tests/
```

## Запуск проекта

### Локальный запуск

1. Клонируйте репозиторий:
   ```bash
   git clone <repository-url>
   cd <имя_проекта>
   ```

2. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Для Linux/Mac
   # или
   venv\Scripts\activate  # Для Windows
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Создайте файл `.env` на основе `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Настройте переменные окружения в файле `.env`:
   ```env
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=password
   POSTGRES_DB=books_db
   DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/books_db
   ```

6. Запустите базу данных PostgreSQL (например, с помощью Docker):
   ```bash
   docker run --name books-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=password -e POSTGRES_DB=books_db -p 5432:5432 -d postgres:15
   ```

7. Примените миграции базы данных:
   ```bash
   alembic upgrade head
   ```

8. Запустите приложение:
   ```bash
   uvicorn app.main:app --reload
   ```


### Запуск с помощью Docker Compose

1. Клонируйте репозиторий:
   ```bash
   git clone <repository-url>
   cd <имя_проекта>
   ```

2. Создайте файл `.env` на основе `.env.example` (если он еще не создан):
   ```bash
   cp .env.example .env
   ```
   
   **Важно:** Убедитесь, что файл `.env` существует в корневой директории проекта перед запуском Docker Compose.
   
3. Если вы столкнулись с ошибками импорта модулей, пересоберите контейнеры:
   ```bash
   docker-compose down
   docker-compose up --build
   ```

3. Запустите проект с помощью Docker Compose:
   ```bash
   docker-compose up --build
   ```

4. Примените миграции базы данных в отдельном терминале:
   ```bash
   docker-compose exec app alembic upgrade head
   ```

## API документация

После запуска проекта API документация будет доступна по адресу:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Примеры запросов

### Жанры

#### Создание жанра
```bash
curl -X POST "http://localhost:8000/api/v1/genres/" \
-H "Content-Type: application/json" \
-d '{"name": "Фантастика"}'
```

#### Получение списка жанров
```bash
curl -X GET "http://localhost:8000/api/v1/genres/"
```

#### Получение жанра по ID
```bash
curl -X GET "http://localhost:8000/api/v1/genres/{genre_id}"
```

#### Обновление жанра
```bash
curl -X PATCH "http://localhost:8000/api/v1/genres/{genre_id}" \
-H "Content-Type: application/json" \
-d '{"name": "Научная фантастика"}'
```

#### Удаление жанра
```bash
curl -X DELETE "http://localhost:8000/api/v1/genres/{genre_id}"
```

### Книги

#### Создание книги
```bash
curl -X POST "http://localhost:8000/api/v1/books/" \
-H "Content-Type: application/json" \
-d '{
  "title": "Дюна",
  "rating": 9.5,
  "description": "Культовый роман Фрэнка Герберта",
  "published_year": 1965,
  "genre_ids": ["{genre_id}"],
  "contributors": [
    {
      "contributor_id": "{contributor_id}",
      "role": "author"
    }
  ]
}'
```

#### Получение списка книг с фильтрацией и пагинацией
```bash
curl -X GET "http://localhost:8000/api/v1/books/?page=1&page_size=10&sort=title&order=asc&q=дюна"
```

#### Получение книги по ID
```bash
curl -X GET "http://localhost:8000/api/v1/books/{book_id}"
```

#### Обновление книги
```bash
curl -X PATCH "http://localhost:8000/api/v1/books/{book_id}" \
-H "Content-Type: application/json" \
-d '{"rating": 9.8}'
```

#### Удаление книги
```bash
curl -X DELETE "http://localhost:8000/api/v1/books/{book_id}"
```

## Структура проекта

```
abs/
├── app/
│   ├── backend/
│   │   ├── books/          # Модуль работы с книгами
│   │   ├── genre/          # Модуль работы с жанрами
│   │   ├── database/       # Настройки базы данных
│   │   ├── tests/          # Тесты
│   │   └── main.py         # Точка входа в приложение
│   ├── migrations/         # Миграции базы данных
│   └── requirements.txt    # Зависимости проекта
├── alembic.ini             # Конфигурация Alembic
├── docker-compose.yml      # Конфигурация Docker Compose
├── Dockerfile             # Конфигурация Docker для бэкенда
├── .env.example           # Пример файла с переменными окружения
└── README.md              # Документация проекта
