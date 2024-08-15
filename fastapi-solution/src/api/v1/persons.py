from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from models.person import FilmRating, PersonFilm
from services.person import PersonService, get_person_service

router = APIRouter()


@router.get(
    "/search", response_model=list[PersonFilm], summary="Поиск персоны по имени"
)
async def persons_search(
    query: str = Query("", description="Get Persons by names"),
    page_size: int = Query(
        default=10, description="Number of items per page", gt=0, lt=100
    ),
    page_number: int = Query(default=1, description="Page number", gt=0, lt=1000),
    person_service: PersonService = Depends(get_person_service),
) -> List[PersonFilm]:
    persons = await person_service.search(
        search_str=query,
        page_size=page_size,
        page_number=page_number,
    )
    if not persons:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Person not found")
    return persons


@router.get(
    "/{person_id}", response_model=PersonFilm | None, summary="Запрос персоны по id"
)
async def person_details(
    person_id: str, person_service: PersonService = Depends(get_person_service)
) -> PersonFilm:
    person = await person_service.get_by_uuid(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Person not found")
    return person


@router.get(
    "/{person_id}/film/",
    response_model=list[FilmRating],
    summary="Запрос фильмов в котором принимала участие персона по id",
)
async def person_films(
    person_id: str, person_service: PersonService = Depends(get_person_service)
) -> list[FilmRating]:
    list_films = await person_service.get_film_detail_on_person(person_id)
    if not list_films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Films not found")
    return list_films
