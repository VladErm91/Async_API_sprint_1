from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class Participant(BaseModel):
    """Модель данных участников фильма"""

    uuid: UUID
    full_name: str


class FilmGenre(BaseModel):
    """Модель данных жанра фильма"""

    uuid: UUID
    name: str


class Film(BaseModel):
    """Минимальная модель данных кинопроизведения """

    uuid: UUID
    title: str
    imdb_rating: float


class FilmDetailed(Film):
    """Подробная модель данных о кинопроизведении."""

    genre: Optional[list[str]]
    description: Optional[str]
    director: Optional[list[str]]
    actors_names: Optional[list[str]]
    writers_names: Optional[list[str]]
    actors: Optional[list[Participant]]
    writers: Optional[list[Participant]]