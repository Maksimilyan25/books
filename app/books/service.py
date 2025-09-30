from typing import Optional
from uuid import UUID
from decimal import Decimal

from fastapi import HTTPException, status

from app.database.db import SessionDep
from app.books.repository import BookRepository
from app.books.schemas import (
    BookResponse, BooksListResponse, BookCreate, BookUpdate,
    ContributorResponse, BookContributorResponse
)
from app.genre.schemas import GenreResponse
from app.books.models import SortField, SortOrder


class BookService:
    """
    Сервис для работы с книгами.

    Предоставляет бизнес-логику для операций с книгами,
    включая получение списков книг с фильтрацией, сортировкой и пагинацией.
    """

    def __init__(self, session: SessionDep):
        """
        Инициализация сервиса.

        Args:
            session: Сессия базы данных
        """
        self.repository = BookRepository(session)
        self.session = session

    async def get_books_list(
        self,
        page: int = 1,
        page_size: int = 10,
        sort: str = 'title',
        order: str = 'asc',
        q: Optional[str] = None,
        genre_id: Optional[UUID] = None,
        published_year: Optional[int] = None,
        rating_min: Optional[Decimal] = None,
        rating_max: Optional[Decimal] = None,
    ) -> BooksListResponse:
        """
        Получить список книг с фильтрацией, сортировкой и пагинацией.

        Args:
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
        # Валидация параметров
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 10

        # Преобразуем строки в Enum
        try:
            sort_enum = SortField(sort)
        except ValueError:
            sort_enum = SortField.TITLE

        try:
            order_enum = SortOrder(order)
        except ValueError:
            order_enum = SortOrder.ASC

        sort = sort_enum.value
        order = order_enum.value

        books, total = await self.repository.get_books_list(
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

        # Преобразуем модели в схемы ответа с полной информацией
        book_responses = []
        for book in books:
            # Получаем жанры книги
            genres = await self.repository.get_book_genres(book.id)
            genre_responses = [
                GenreResponse(id=genre.id, name=genre.name) for genre in genres
            ]

            # Получаем участников книги
            contributors_data = await self.repository.get_book_contributors(
                book.id
            )
            contributor_responses = [
                BookContributorResponse(
                    contributor=ContributorResponse(
                        id=contributor.id, full_name=contributor.full_name
                    ),
                    role=role
                )
                for contributor, role in contributors_data
            ]

            book_responses.append(BookResponse(
                id=book.id,
                title=book.title,
                rating=book.rating,
                description=book.description,
                published_year=book.published_year,
                genres=genre_responses,
                contributors=contributor_responses
            ))

        return BooksListResponse(
            items=book_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_book_by_id(self, book_id: UUID) -> Optional[BookResponse]:
        """
        Получить книгу по ID с информацией о жанрах и участниках.

        Args:
            book_id: ID книги

        Returns:
            Optional[BookResponse]: Данные книги или None, если не найдена
        """
        book = await self.repository.get_book_by_id(book_id)
        if not book:
            return None

        # Получаем жанры книги
        genres = await self.repository.get_book_genres(book_id)
        genre_responses = [
            GenreResponse(id=genre.id, name=genre.name) for genre in genres
        ]

        # Получаем участников книги
        contributors_data = await self.repository.get_book_contributors(
            book_id
        )
        contributor_responses = [
            BookContributorResponse(
                contributor=ContributorResponse(
                    id=contributor.id, full_name=contributor.full_name
                ),
                role=role
            )
            for contributor, role in contributors_data
        ]

        return BookResponse(
            id=book.id,
            title=book.title,
            rating=book.rating,
            description=book.description,
            published_year=book.published_year,
            genres=genre_responses,
            contributors=contributor_responses
        )

    async def create_book(self, book_data: BookCreate) -> BookResponse:
        """
        Создать новую книгу.

        Args:
            book_data: Данные для создания книги

        Returns:
            BookResponse: Созданная книга
        """
        book_dict = book_data.model_dump(exclude={"genre_ids", "contributors"})
        book = await self.repository.create_book(book_dict)

        if book_data.genre_ids:
            try:
                await self.repository.update_book_genres(
                    book.id, book_data.genre_ids
                )
            except ValueError as e:
                # Если жанры не существуют, удаляем созданную книгу
                await self.repository.delete_book(book.id)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        if book_data.contributors:
            contributors_data = [
                {"contributor_id": c.contributor_id, "role": c.role}
                for c in book_data.contributors
            ]
            await self.repository.update_book_contributors(
                book.id, contributors_data
            )

        await self.session.commit()

        return await self.get_book_by_id(book.id)

    async def update_book(
        self, book_id: UUID, book_data: BookUpdate
    ) -> Optional[BookResponse]:
        """
        Обновить существующую книгу.

        Args:
            book_id: ID книги
            book_data: Данные для обновления

        Returns:
            Optional[BookResponse]: Обновленная книга или None, если не найдена
        """
        update_dict = book_data.model_dump(
            exclude_unset=True, exclude={"genre_ids", "contributors"}
        )
        if update_dict:
            book = await self.repository.update_book(book_id, update_dict)
            if not book:
                return None

        if book_data.genre_ids is not None:
            try:
                await self.repository.update_book_genres(
                    book_id, book_data.genre_ids
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        if book_data.contributors is not None:
            contributors_data = [
                {"contributor_id": c.contributor_id, "role": c.role}
                for c in book_data.contributors
            ]
            await self.repository.update_book_contributors(
                book_id, contributors_data
            )

        await self.session.commit()

        return await self.get_book_by_id(book_id)

    async def delete_book(self, book_id: UUID) -> bool:
        """
        Удалить книгу.

        Args:
            book_id: ID книги

        Returns:
            bool: True если книга была удалена, False если не найдена
        """
        deleted = await self.repository.delete_book(book_id)
        if deleted:
            await self.session.commit()
        return deleted
