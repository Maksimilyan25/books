from sqlalchemy import (
    String, Uuid, Enum, DECIMAL, Integer, ForeignKey, TIMESTAMP, func
)
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4
import enum

from app.database.db import Base


class Role(enum.Enum):
    AUTHOR = 'author'
    EDITOR = 'editor'
    ILLUSTRATOR = 'illustrator'


class SortField(enum.Enum):
    TITLE = 'title'
    RATING = 'rating'
    PUBLISHED_YEAR = 'published_year'


class SortOrder(enum.Enum):
    ASC = 'asc'
    DESC = 'desc'


class TimestampMixin:
    created_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )
    updated_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )


class Book(Base, TimestampMixin):
    __tablename__ = 'books'

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String, nullable=False)
    rating: Mapped[DECIMAL] = mapped_column(DECIMAL(3, 1), nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    published_year: Mapped[int] = mapped_column(Integer, nullable=True)


class Contributor(Base, TimestampMixin):
    __tablename__ = 'contributors'

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    full_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)


class BookContributor(Base, TimestampMixin):
    __tablename__ = 'books_contributors'

    book_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey('books.id', ondelete='CASCADE'), primary_key=True
    )
    contributor_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey('contributors.id', ondelete='CASCADE'),
        primary_key=True
    )
    role: Mapped[Role] = mapped_column(Enum(Role), primary_key=True)


class BookGenre(Base, TimestampMixin):
    __tablename__ = 'books_genres'

    book_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey('books.id', ondelete='CASCADE'), primary_key=True
    )
    genre_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey('genres.id', ondelete='CASCADE'), primary_key=True
    )
