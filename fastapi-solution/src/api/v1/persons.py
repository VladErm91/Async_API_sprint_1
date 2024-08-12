from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from src.models.person import Person
from src.services.person import PersonService, get_person_service

router = APIRouter()


@router.get("/{person_id}", response_model=Person)
async def person_details(
    person_id: str, person_service: PersonService = Depends(get_person_service)
) -> Person:
    person = await person_service.get_by_uuid(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="person not found")
    return person


@router.get("/", response_model=List[Person])
async def search_persons(
    query: str,
    sort: Optional[str] = None,
    person_service: PersonService = Depends(get_person_service),
) -> List[Person]:
    persons = await person_service.search(query, sort)
    return persons
