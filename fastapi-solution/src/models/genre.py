from typing import List

from pydantic import BaseModel


class Genre(BaseModel):
    """Схема данных по жанрам."""

    uuid: str
    name: str


class GenrePaginationResponse(BaseModel):
    """Схема данных по жанрам с пагинацией."""

    items: List[Genre]
    total: int
    page: int
    page_size: int
