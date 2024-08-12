from http import HTTPStatus
from typing import List, Optional

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
import logging

from pydantic import BaseModel

from models.person import PersonQuery, ListFilm
from services.person import PersonService, get_person_service
from services.film import FilmService, get_film_service

router = APIRouter()


class PortfolioFilm(BaseModel):
    uuid: UUID
    roles: list[str]

class Person(BaseModel):
    id: UUID
    full_name: str
    films: list[PortfolioFilm]


@router.get('/{person_id}', response_model=Person)
async def person_details(
    person_id: str, person_service: PersonService = Depends(get_person_service)
) -> Person:
<<<<<<< HEAD

    person = await person_service.get_by_id(person_id)
=======
    person = await person_service.get_by_uuid(person_id)
>>>>>>> origin/develop
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="person not found")
    return person





@router.get('/search', response_model=List[Person] | None)
async def search_persons(
    query_params: PersonQuery = Depends(),
    sort: Optional[str] = None,
    person_service: PersonService = Depends(get_person_service),
) -> List[Person]:
    persons = await person_service.search(query_params)
    return persons


@router.get(
    '/{person_id}/film/',
    response_model=list[ListFilm])


async def person_films(
    person_id: str,
    person_service: PersonService = Depends(get_person_service),
    film_service: FilmService = Depends(get_film_service),
) -> list[ListFilm]:

    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    films = []
    for film in person.films:
        film_info = await film_service.get_by_uuid(str(film.uuid))
        if film_info:
            films.append(
                ListFilm(
                    uuid=film.uuid,
                    title=film_info.title,
                    imdb_rating=film_info.imdb_rating,
                ),
            )
        else:
            msg = 'В БД отсутствют фильмы с указаным uuid'
            logging.error(msg)

    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Фильмы не найдены')

    return films



@router.get(
    '/',
    response_model=list[Person],
)

async def all_persons(
    person_service: PersonService = Depends(get_person_service),
) -> list[Person]:

    persons = await person_service.get_persons()
    if not persons:
        # Если не найден, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='no genres in database')
    logging.debug('Объект для выдачи list[Persons]:\n{0}'.format(persons))
    return persons
