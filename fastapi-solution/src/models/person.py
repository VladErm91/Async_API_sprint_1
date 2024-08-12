from pydantic import BaseModel
from typing import Optional
from uuid import UUID



class ListFilm(BaseModel):
    uuid: str
    title: str
    imdb_rating: float


class PortfolioFilm(BaseModel):
    uuid: str
    roles: list[str]


class Person(BaseModel):
    uuid: UUID
    full_name: str
    films: Optional[list[PortfolioFilm]]


class PersonQuery(BaseModel):
    query: str
    page_number: int = 1
    page_size: int = 30

