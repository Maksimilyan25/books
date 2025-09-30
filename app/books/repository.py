from typing import List, Optional, Tuple
from uuid import UUID
from decimal import Decimal

from sqlalchemy import select, func, and_, delete

from app.database.db import SessionDep
from app.books.models import (
    Book,
    BookGenre,
    Contributor,
    BookContributor,
    SortField,
    SortOrder,
    Role,
)
from app.genre.models import Genre


class BookRepository:
    def __init__(self, session: SessionDep):
        self.session = session

    async def get_books_list(
        self,
        page: int = 1,
        page_size: int = 10,
        sort: str = "title",
        order: str = "asc",
        q: Optional[str] = None,
        genre_id: Optional[UUID] = None,
        published_year: Optional[int] = None,
        rating_min: Optional[Decimal] = None,
        rating_max: Optional[Decimal] = None,
    ) -> Tuple[List[Book], int]:
        query = select(Book)
        conditions = []

        if q:
            conditions.append(Book.title.ilike(f"%{q}%"))

        if genre_id:
            query = query.join(BookGenre, Book.id == BookGenre.book_id).join(
                Genre, BookGenre.genre_id == Genre.id
            )
            conditions.append(Genre.id == genre_id)

        if published_year:
            conditions.append(Book.published_year == published_year)

        if rating_min is not None:
            conditions.append(Book.rating >= rating_min)

        if rating_max is not None:
            conditions.append(Book.rating <= rating_max)

        if conditions:
            query = query.where(and_(*conditions))

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)

        try:
            sort_enum = SortField(sort)
        except ValueError:
            sort_enum = SortField.TITLE

        try:
            order_enum = SortOrder(order)
        except ValueError:
            order_enum = SortOrder.ASC

        if sort_enum == SortField.TITLE:
            sort_column = Book.title
        elif sort_enum == SortField.RATING:
            sort_column = Book.rating
        elif sort_enum == SortField.PUBLISHED_YEAR:
            sort_column = Book.published_year
        else:
            sort_column = Book.title

        if order_enum == SortOrder.DESC:
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        books = result.scalars().all()

        return list(books), total or 0

    async def get_book_by_id(self, book_id: UUID) -> Optional[Book]:
        query = select(Book).where(Book.id == book_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_book_genres(self, book_id: UUID) -> List[Genre]:
        query = select(Genre).join(BookGenre).where(
            BookGenre.book_id == book_id
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_book_contributors(
        self, book_id: UUID
    ) -> List[Tuple[Contributor, Role]]:
        query = (
            select(Contributor, BookContributor.role)
            .join(
                BookContributor,
                Contributor.id == BookContributor.contributor_id
            )
            .where(BookContributor.book_id == book_id)
        )
        result = await self.session.execute(query)
        return list(result.all())

    async def create_book(self, book_data: dict) -> Book:
        book = Book(**book_data)
        self.session.add(book)
        await self.session.flush()
        await self.session.refresh(book)
        return book

    async def update_book(
        self, book_id: UUID, book_data: dict
    ) -> Optional[Book]:
        query = select(Book).where(Book.id == book_id)
        result = await self.session.execute(query)
        book = result.scalar_one_or_none()
        if not book:
            return None

        for key, value in book_data.items():
            if hasattr(book, key) and value is not None:
                setattr(book, key, value)

        await self.session.flush()
        await self.session.refresh(book)
        return book

    async def delete_book(self, book_id: UUID) -> bool:
        query = select(Book).where(Book.id == book_id)
        result = await self.session.execute(query)
        book = result.scalar_one_or_none()

        if not book:
            return False

        await self.session.delete(book)
        await self.session.flush()
        return True

    async def update_book_genres(
        self, book_id: UUID, genre_ids: List[UUID]
    ) -> None:
        # Проверяем существование всех жанров перед добавлением
        if genre_ids:
            # Получаем все существующие ID жанров
            existing_genres_query = select(Genre.id).where(
                Genre.id.in_(genre_ids)
            )
            result = await self.session.execute(existing_genres_query)
            existing_genre_ids = {row[0] for row in result.all()}

            # Находим отсутствующие жанры
            missing_genre_ids = set(genre_ids) - existing_genre_ids
            if missing_genre_ids:
                raise ValueError(
                    f"Жанры с указанными ID не существуют: {missing_genre_ids}"
                )

        await self.session.execute(
            delete(BookGenre).where(BookGenre.book_id == book_id)
        )
        for genre_id in genre_ids:
            book_genre = BookGenre(book_id=book_id, genre_id=genre_id)
            self.session.add(book_genre)

        await self.session.flush()

    async def update_book_contributors(
        self, book_id: UUID, contributors_data: List[dict]
    ) -> None:
        await self.session.execute(
            delete(BookContributor).where(BookContributor.book_id == book_id)
        )
        for contributor_data in contributors_data:
            book_contributor = BookContributor(
                book_id=book_id,
                contributor_id=contributor_data["contributor_id"],
                role=contributor_data["role"],
            )
            self.session.add(book_contributor)

        await self.session.flush()
