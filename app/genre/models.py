from sqlalchemy import (
    String, Uuid, TIMESTAMP, func
)
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID, uuid4

from app.database.db import Base


class TimestampMixin:
    created_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )
    updated_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )


class Genre(Base, TimestampMixin):
    __tablename__ = 'genres'

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
