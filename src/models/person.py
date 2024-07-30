from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class Filmography(BaseModel):
    """Модель фильмографии персоны."""

    uuid: UUID
    title: str
    imdb_rating: float


class PersonFilm(BaseModel):
    """Модель данных фильма в портфолио персоны."""

    uuid: UUID
    roles: list[str]


class Person(BaseModel):
    """Модель данных персоны."""

    uuid: UUID
    full_name: str
    films: Optional[list[PersonFilm]]
