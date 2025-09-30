from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_

from app.database.db import SessionDep
from app.genre.models import Genre


class GenreRepository:
    def __init__(self, session: SessionDep):
        self.session = session

    async def get_genres_list(
        self,
        page: int = 1,
        page_size: int = 10,
        q: Optional[str] = None,
    ) -> Tuple[List[Genre], int]:
        # Создаем базовый запрос для подсчета
        count_query = select(func.count(Genre.id))
        conditions = []

        if q:
            conditions.append(Genre.name.ilike(f"%{q}%"))

        if conditions:
            count_query = count_query.where(and_(*conditions))

        total = await self.session.scalar(count_query)

        # Создаем запрос для получения данных с теми же условиями
        query = select(Genre)
        if conditions:
            query = query.where(and_(*conditions))

        offset = (page - 1) * page_size
        query = query.order_by(Genre.name.asc()).offset(offset).limit(
            page_size
        )

        result = await self.session.execute(query)
        genres = result.scalars().all()

        return list(genres), total or 0

    async def get_genre_by_id(self, genre_id: UUID) -> Optional[Genre]:
        query = select(Genre).where(Genre.id == genre_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_genre_by_name(self, name: str) -> Optional[Genre]:
        query = select(Genre).where(Genre.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_genre(self, genre_data: dict) -> Genre:
        genre = Genre(**genre_data)
        self.session.add(genre)
        await self.session.flush()
        await self.session.refresh(genre)
        return genre

    async def update_genre(
        self, genre_id: UUID, genre_data: dict
    ) -> Optional[Genre]:
        query = select(Genre).where(Genre.id == genre_id)
        result = await self.session.execute(query)
        genre = result.scalar_one_or_none()
        if not genre:
            return None

        for key, value in genre_data.items():
            if hasattr(genre, key) and value is not None:
                setattr(genre, key, value)

        await self.session.flush()
        await self.session.refresh(genre)
        return genre

    async def delete_genre(self, genre_id: UUID) -> bool:
        query = select(Genre).where(Genre.id == genre_id)
        result = await self.session.execute(query)
        genre = result.scalar_one_or_none()

        if not genre:
            return False

        await self.session.delete(genre)
        await self.session.flush()
        return True
