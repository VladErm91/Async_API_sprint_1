from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from models.genre import Genre, GenrePaginationResponse
from services.genre import GenreService, get_genre_service

router = APIRouter()


@router.get("/{genre_id}", response_model=Genre)
async def genre_details(
    genre_id: str, genre_service: GenreService = Depends(get_genre_service)
) -> Genre:
    genre = await genre_service.get_by_uuid(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="genre not found")
    return genre


@router.get("", response_model=GenrePaginationResponse)
async def search_genres(
    query: str = "",
    sort: Optional[str] = None,
    order: Optional[str] = Query(None, regex="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    genre_service: GenreService = Depends(get_genre_service),
) -> GenrePaginationResponse:
    genres, total = await genre_service.search(query, sort, order, page, page_size)

    max_pages = (total + page_size - 1) // page_size
    if page > max_pages:
        raise HTTPException(status_code=404, detail="Page not found")

    return GenrePaginationResponse(
        items=genres, total=total, page=page, page_size=page_size
    )
