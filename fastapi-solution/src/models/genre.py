from pydantic import BaseModel
from typing import List


class Genre(BaseModel):
    uuid: str
    name: str


class GenrePaginationResponse(BaseModel):
    items: List[Genre]
    total: int
    page: int
    page_size: int
