from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Query
from fastapi import HTTPException, status

from app.database.db import SessionDep
from app.books.schemas import (
    BooksListResponse, BookResponse, BookCreate, BookUpdate
)
from app.books.service import BookService

router = APIRouter(prefix='/books', tags=['Книги'])


@router.get('/', summary='Список книг', response_model=BooksListResponse)
async def get_books(
    session: SessionDep,
    page: int = Query(
        ge=1, default=1, description='Номер страницы (начиная с 1)'
    ),
    page_size: int = Query(
        ge=1, le=100, default=10, description='Размер страницы (от 1 до 100)'
    ),
    sort: str = Query(
        default='title',
        description='Поле для сортировки: title|rating|published_year'
    ),
    order: str = Query(
        default='asc', pattern='^(asc|desc)$',
        description='Порядок сортировки: asc|desc'
    ),
    q: str = Query(
        default=None, description='Поиск по подстроке в названии'
    ),
    genre_id: UUID = Query(
        default=None, description='Фильтр по жанру'
    ),
    published_year: int = Query(
        default=None, description='Фильтр по году публикации'
    ),
    rating_min: Decimal = Query(
        default=None, ge=0, le=99.9, description='Минимальный рейтинг'
    ),
    rating_max: Decimal = Query(
        default=None, ge=0, le=99.9, description='Максимальный рейтинг'
    ),
):
    """
    Получить список книг с фильтрацией, сортировкой и пагинацией.

    Args:
        session: Сессия базы данных
        page: Номер страницы (начиная с 1)
        page_size: Размер страницы (от 1 до 100)
        sort: Поле для сортировки (title|rating|published_year)
        order: Порядок сортировки (asc|desc)
        q: Поиск по подстроке в названии
        genre_id: Фильтр по жанру
        published_year: Фильтр по году публикации
        rating_min: Минимальный рейтинг
        rating_max: Максимальный рейтинг

    Returns:
        BooksListResponse: Список книг с метаинформацией
    """
    service = BookService(session)
    return await service.get_books_list(
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
        q=q,
        genre_id=genre_id,
        published_year=published_year,
        rating_min=rating_min,
        rating_max=rating_max,
    )


@router.get(
    '/{book_id}',
    summary='Получение книги по ID',
    response_model=BookResponse
)
async def get_book(book_id: UUID, session: SessionDep):
    """
    Получить книгу по ID с информацией о жанрах и участниках.

    Args:
        book_id: ID книги
        session: Сессия базы данных

    Returns:
        BookResponse: Данные книги с жанрами и участниками
    """
    service = BookService(session)
    book = await service.get_book_by_id(book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена"
        )
    return book


@router.post(
    '/',
    summary='Создание книги',
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_book(book_data: BookCreate, session: SessionDep):
    """
    Создать новую книгу.

    Args:
        book_data: Данные для создания книги
        session: Сессия базы данных

    Returns:
        BookResponse: Созданная книга
    """
    service = BookService(session)
    return await service.create_book(book_data)


@router.patch(
    '/{book_id}',
    summary='Обновление информации о книге по ID',
    response_model=BookResponse)
async def update_book(
    book_id: UUID, book_data: BookUpdate, session: SessionDep
):
    """
    Обновить существующую книгу.

    Args:
        book_id: ID книги
        book_data: Данные для обновления
        session: Сессия базы данных

    Returns:
        BookResponse: Обновленная книга
    """
    service = BookService(session)
    book = await service.update_book(book_id, book_data)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена"
        )
    return book


@router.delete(
    '/{book_id}',
    summary='Удалить книгу по ID',
    status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: UUID, session: SessionDep):
    """
    Удалить книгу.

    Args:
        book_id: ID книги
        session: Сессия базы данных
    """
    service = BookService(session)
    deleted = await service.delete_book(book_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена"
        )
