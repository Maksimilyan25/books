from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


class GenreResponse(BaseModel):
    id: UUID
    name: str


class GenreCreate(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="Название жанра"
    )


class GenreUpdate(BaseModel):
    name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Название жанра"
    )


class GenresListResponse(BaseModel):
    items: List[GenreResponse]
    total: int
    page: int
    page_size: int


class GenresQueryParams(BaseModel):
    page: int = Field(
        ge=1, default=1, description='Номер страницы (начиная с 1)'
    )
    page_size: int = Field(
        ge=1, le=100, default=10, description='Размер страницы (от 1 до 100)'
    )
    q: Optional[str] = Field(
        default=None, description='Поиск по подстроке в названии'
    )
