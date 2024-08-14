from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from models.film import Film, FilmDetailed
from services.film import (FilmService, MultipleFilmsService,
                               get_film_service, get_multiple_films_service)

# Объект router, в котором регистрируем обработчики
router = APIRouter()

# FastAPI в качестве моделей использует библиотеку pydantic
# https://pydantic-docs.helpmanual.io
# У неё есть встроенные механизмы валидации, сериализации и десериализации
# Также она основана на дата-классах

# С помощью декоратора регистрируем обработчик film_details
# На обработку запросов по адресу <some_prefix>/some_id
# Позже подключим роутер к корневому роутеру
# И адрес запроса будет выглядеть так — /api/v1/films/some_id
# В сигнатуре функции указываем тип данных, получаемый из адреса запроса (film_id: str)
# И указываем тип возвращаемого объекта — Film


# 1. Главная страница. На ней выводятся популярные фильмы. Пока у вас есть только один признак,
# который можно использовать в качестве критерия популярности - imdb_rating
#   GET /api/v1/films?sort=-imdb_rating&page_size=50&page_number=1

# 2. Жанр и популярные фильмы в нём. Это просто фильтрация.
# GET /api/v1/films?genre=<uuid:UUID>&sort=-imdb_rating&page_size=50&page_number=1

# 5. Похожие фильмы. Похожесть можно оценить с помощью ElasticSearch, но цель модуля не в этом.
# Сделаем просто: покажем фильмы того же жанра.
# /api/v1/films?...

# в основном эндпойнте с использованием параметра similar


@router.get(
    "/",
    summary="Популярные фильмы",
    description="Популярное кино в своем жанре с сортировкой результата, указать количество и номер страницы",
)
async def get_popular_films(
    similar: Optional[str] = Query(
        None, description="Get films of same genre as similar"
    ),
    genre: Optional[str] = Query(None, description="Get films of given genres"),
    sort: str = Query("-imdb_rating", description="Sort by field"),
    page_size: int = Query(50, description="Number of items per page", ge=1),
    page_number: int = Query(1, description="Page number", ge=1),
    film_service: MultipleFilmsService = Depends(get_multiple_films_service),
):
    valid_sort_fields = ("imdb_rating", "-imdb_rating")
    if sort not in valid_sort_fields:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Invalid value for "sort" parameter',
        )

    desc = sort[0] == "-"

    return await film_service.get_multiple_films(
        similar=similar,
        genre=genre,
        desc_order=desc,
        page_size=page_size,
        page_number=page_number,
    )


# 3. Поиск по фильмам (2.1. из т.з.)
# GET /api/v1/films/search?query=star&page_number=1&page_size=50


@router.get(
    "/search",
    response_model=list[Film],
    summary="Поиск фильма по наименованию",
    description="Запрос должен содержать наименование фильма, количество фильмов на странице и номер страницы",
)
async def fulltext_search_filmworks(
    query: str = Query("Star", description="Film title or part of film title"),
    page_size: int = Query(50, description="Number of items per page", ge=1),
    page_number: int = Query(1, description="Page number", ge=1),
    pop_film_service: MultipleFilmsService = Depends(get_multiple_films_service),
) -> list[Film]:

    return await pop_film_service.search_films(
        query,
        page_number,
        page_size,
    )


# 4. Полная информация по фильму (т.з. 3.1.)


# Внедряем FilmService с помощью Depends(get_film_service)
@router.get(
    "/{film_id}",
    response_model=FilmDetailed,
    summary="Запрос фильма по id",
    description="Полная информация о фильме: id, наименование, рейтинг, жанр, описание, режиссер, актёры, авторы",
)
async def film_details(
    film_uuid: str,
    film_service: FilmService = Depends(get_film_service),
) -> FilmDetailed:
    film = await film_service.get_by_uuid(film_uuid)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")
    return film
