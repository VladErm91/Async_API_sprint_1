from typing import Dict, List, Optional

from pydantic import BaseModel


class Genre(BaseModel):
    uuid: str
    name: str


class Movie(BaseModel):
    uuid: str
    imdb_rating: Optional[float]
    genre: List[Genre]
    title: str
    description: str
    directors_names: List[str]
    actors_names: List[str]
    writers_names: List[str]
    directors: List[Dict]
    actors: List[Dict]
    writers: List[Dict]
