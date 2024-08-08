from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from src.models.genre import Genre
from src.services.genre import GenreService, get_genre_service

router = APIRouter()


@router.get("/{genre_id}", response_model=Genre)
async def genre_details(
    genre_id: str, genre_service: GenreService = Depends(get_genre_service)
) -> Genre:
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="genre not found")
    return genre


@router.get("/", response_model=List[Genre])
async def search_genres(
    query: str,
    sort: str = None,
    genre_service: GenreService = Depends(get_genre_service),
) -> List[Genre]:
    genres = await genre_service.search(query, sort)
    return genres
