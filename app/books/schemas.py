from typing import Optional, List
from pydantic import BaseModel, Field
from decimal import Decimal
from uuid import UUID
from app.books.models import Role
from app.genre.schemas import GenreResponse


class ContributorResponse(BaseModel):
    id: UUID
    full_name: str


class BookContributorResponse(BaseModel):
    contributor: ContributorResponse
    role: Role


class BookResponse(BaseModel):
    id: UUID
    title: str
    rating: Optional[Decimal] = None
    description: Optional[str] = None
    published_year: Optional[int] = None
    genres: List[GenreResponse] = []
    contributors: List[BookContributorResponse] = []


class BooksListResponse(BaseModel):
    items: List[BookResponse]
    total: int
    page: int
    page_size: int


class BooksQueryParams(BaseModel):
    page: int = Field(
        ge=1, default=1, description='Номер страницы (начиная с 1)'
    )
    page_size: int = Field(
        ge=1, le=100, default=10, description='Размер страницы (от 1 до 100)'
    )
    sort: str = Field(
        default='title',
        description='Поле для сортировки: title|rating|published_year'
    )
    order: str = Field(
        default='asc', pattern='^(asc|desc)$',
        description='Порядок сортировки: asc|desc'
    )
    q: Optional[str] = Field(
        default=None, description='Поиск по подстроке в названии'
    )
    genre_id: Optional[UUID] = Field(
        default=None, description='Фильтр по жанру'
    )
    published_year: Optional[int] = Field(
        default=None, description='Фильтр по году публикации'
    )
    rating_min: Optional[Decimal] = Field(
        default=None, ge=0, le=99.9, description='Минимальный рейтинг'
    )
    rating_max: Optional[Decimal] = Field(
        default=None, ge=0, le=99.9, description='Максимальный рейтинг'
    )


class ContributorCreate(BaseModel):
    contributor_id: UUID
    role: Role


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    rating: Optional[Decimal] = Field(None, ge=0, le=99.9)
    description: Optional[str] = Field(None, max_length=1000)
    published_year: Optional[int] = Field(None, ge=1800, le=2100)
    genre_ids: List[UUID] = []
    contributors: List[ContributorCreate] = []


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    rating: Optional[Decimal] = Field(None, ge=0, le=99.9)
    description: Optional[str] = Field(None, max_length=1000)
    published_year: Optional[int] = Field(None, ge=1800, le=2100)
    genre_ids: Optional[List[UUID]] = None
    contributors: Optional[List[ContributorCreate]] = None
