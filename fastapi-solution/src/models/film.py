"""Модуль, где определена модель кинопроизведения."""
from typing import Optional, List

from pydantic import BaseModel


class Person(BaseModel):
    """Модель данных персоны, участвующей в создании фильма."""

    uuid: str
    full_name: str


class FilmGenre(BaseModel):
    """Модель данных жанра, к которому относится фильм."""

    uuid: str
    name: str


class Film(BaseModel):
    """Модель данных кинопроизведения (минимальная - для главной страницы)."""

    uuid: str
    title: str
    imdb_rating: float


class FilmDetailed(Film):
    """Схема данных подробностей о кинопроизведении."""

    genre: Optional[List[FilmGenre]]
    description: Optional[str] = None
    directors_names: Optional[List[str]] = None
    actors_names: Optional[List[str]] = None
    writers_names: Optional[List[str]] = None
    directors: Optional[List[Person]] = None
    actors: Optional[List[Person]] = None
    writers: Optional[List[Person]] = None
