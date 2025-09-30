# Используем официальный образ Python в качестве базового
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создаем структуру директорий для приложения
RUN mkdir -p /app/app

# Копируем код приложения в директорию app
COPY . /app/app/

# Копируем alembic.ini в корень контейнера
COPY ./alembic.ini /app/alembic.ini

# Копируем .env файл в корень контейнера
COPY ../.env /app/.env

# Копируем директорию с миграциями
COPY ../app/migrations /app/migrations

# Открываем порт для FastAPI
EXPOSE 8000

# Команда для запуска приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]