from typing import List, Optional

from pydantic import BaseModel


class Film(BaseModel):
    id: str
    imdb_rating: Optional[float]
    genres: List[str]
    title: str
    description: Optional[str]
    directors_names: List[str]
    actors_names: List[str]
    writers_names: List[str]
