from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.film import FilmService, get_film_service

router = APIRouter()


class Film(BaseModel):
    id: str
    title: str


# Внедряем FilmService с помощью Depends(get_film_service)
@router.get("/{film_id}", response_model=Film)
async def film_details(
    film_id: str, film_service: FilmService = Depends(get_film_service)
) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Film not found")
    return Film(id=film.id, title=film.title)


@router.get("/", response_model=List[Film])
async def search_films(
    query: Optional[str] = None,
    genre: Optional[str] = Query(None, alias="genre"),
    sort: Optional[str] = Query(None, alias="sort"),
    film_service: FilmService = Depends(get_film_service),
) -> List[Film]:
    films = await film_service.search(query=query, genre=genre, sort=sort)
    return films
