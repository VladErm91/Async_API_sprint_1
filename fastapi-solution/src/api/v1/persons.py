from http import HTTPStatus
from typing import List, Optional

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path
import logging

from pydantic import BaseModel

from models.person import  PersonFilm, FilmRating
from services.person import PersonService, get_person_service
from services.film import FilmService, get_film_service



router = APIRouter()

class PortfolioFilm(BaseModel):
    uuid: UUID
    roles: list[str]


@router.get('/search', response_model=list[PersonFilm])
async def persons_search(
    query: str = Query("", description="Поиск"),
    page_size: int = Query(default=50,  description="Размер страницы", gt=0, lt=100),
    page_number: int = Query(default=1, description="Номер страницы", gt=0, lt=1000),
    person_service: PersonService = Depends(get_person_service),
) -> List[PersonFilm]:
    persons = await person_service.search(
        search_str=query,
        page_size=page_size,
        page_number=page_number,)
    if not persons:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Никто не найден")
    return persons


@router.get('/{person_id}', response_model=PersonFilm | None,)
async def person_details(
    person_id: str, person_service: PersonService = Depends(get_person_service)
) -> PersonFilm:
    person = await person_service.get_by_uuid(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Никто не найден")
    return person


@router.get(
    '/{person_id}/film/',
    response_model=list[FilmRating])
async def person_films(
    person_id: str,
    person_service: PersonService = Depends(get_person_service)
) -> list[FilmRating]:
    list_films = await person_service.get_film_detail_on_person(person_id)
    if not list_films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Фильмы не найдены')
    return list_films
