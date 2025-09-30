from uuid import UUID

from fastapi import APIRouter, Query
from fastapi import HTTPException, status

from app.database.db import SessionDep
from app.genre.schemas import (
    GenresListResponse, GenreResponse, GenreCreate, GenreUpdate
)
from app.genre.service import GenreService

router = APIRouter(prefix='/genres', tags=['Жанры'])


@router.get(
    '/',
    summary='Получить список жанров',
    response_model=GenresListResponse
)
async def get_genres(
    session: SessionDep,
    page: int = Query(
        ge=1, default=1, description='Номер страницы (начиная с 1)'
    ),
    page_size: int = Query(
        ge=1, le=100, default=10, description='Размер страницы (от 1 до 100)'
    ),
    q: str = Query(
        default=None, description='Поиск по подстроке в названии'
    ),
):
    """
    Получить список жанров с фильтрацией и пагинацией.

    Args:
        session: Сессия базы данных
        page: Номер страницы (начиная с 1)
        page_size: Размер страницы (от 1 до 100)
        q: Поиск по подстроке в названии

    Returns:
        GenresListResponse: Список жанров с метаинформацией
    """
    service = GenreService(session)
    return await service.get_genres_list(
        page=page,
        page_size=page_size,
        q=q,
    )


@router.get(
    '/{genre_id}',
    summary='Получить жанр по ID',
    response_model=GenreResponse
)
async def get_genre(genre_id: UUID, session: SessionDep):
    """
    Получить жанр по ID.

    Args:
        genre_id: ID жанра
        session: Сессия базы данных

    Returns:
        GenreResponse: Данные жанра
    """
    service = GenreService(session)
    genre = await service.get_genre_by_id(genre_id)
    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Жанр не найден"
        )
    return genre


@router.post(
    '/',
    summary='Создание жанра',
    response_model=GenreResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_genre(genre_data: GenreCreate, session: SessionDep):
    """
    Создать новый жанр.

    Args:
        genre_data: Данные для создания жанра
        session: Сессия базы данных

    Returns:
        GenreResponse: Созданный жанр
    """
    service = GenreService(session)
    try:
        return await service.create_genre(genre_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch(
    '/{genre_id}',
    summary='Обновление жанра по ID',
    response_model=GenreResponse)
async def update_genre(
    genre_id: UUID, genre_data: GenreUpdate, session: SessionDep
):
    """
    Обновить существующий жанр.

    Args:
        genre_id: ID жанра
        genre_data: Данные для обновления
        session: Сессия базы данных

    Returns:
        GenreResponse: Обновленный жанр
    """
    service = GenreService(session)
    try:
        genre = await service.update_genre(genre_id, genre_data)
        if not genre:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Жанр не найден"
            )
        return genre
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    '/{genre_id}',
    summary='Удаление жанра по ID',
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_genre(genre_id: UUID, session: SessionDep):
    """
    Удалить жанр.

    Args:
        genre_id: ID жанра
        session: Сессия базы данных
    """
    service = GenreService(session)
    deleted = await service.delete_genre(genre_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Жанр не найден"
        )
