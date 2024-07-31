from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Genre(BaseModel):
    id: str = Field(alias="genre_id")
    name: str = Field(alias="genre_name")


class Person(BaseModel):
    id: str = Field(alias="person_id")
    name: str = Field(alias="person_name")


class ESMovies(BaseModel):
    id: str
    imdb_rating: Optional[float]
    genres: list[Genre]
    genre: list[str]
    title: str
    description: str | None
    director_names: list[str] | None
    actors_names: list[str] | None
    writers_names: list[str] | None
    directors: list[Person] | None
    actors: list[Person] | None
    writers: list[Person] | None
    modified: datetime
