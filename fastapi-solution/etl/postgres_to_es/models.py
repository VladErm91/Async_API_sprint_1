from typing import Dict, List, Optional

from pydantic import BaseModel


class Movie(BaseModel):
    id: str
    imdb_rating: Optional[float]
    genres: List[str]
    title: str
    description: str
    directors_names: List[str]
    actors_names: List[str]
    writers_names: List[str]
    directors: List[Dict]
    actors: List[Dict]
    writers: List[Dict]


class Genre(BaseModel):
    id: str
    name: str
