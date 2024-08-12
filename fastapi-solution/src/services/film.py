import logging
from functools import lru_cache
from http import HTTPStatus
from pprint import pformat
from typing import Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends, HTTPException
from pydantic import TypeAdapter
from redis.asyncio import Redis

from core import config
from db.elastic import get_elastic
from db.redis import generate_cache_key, get_redis
from models.film import Film, FilmDetailed
from models.genre import Genre

FILM_ADAPTER = TypeAdapter(list[Film])

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class FilmService:
    """Сервис для получения детальной информации по фильму из ES."""

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        """Инициализация сервиса.

        Parameters:
            redis: экземпляр redis'а
            elastic: экземпляр elastic'а
        """
        self.redis = redis
        self.elastic = elastic

    # 1.1. получение фильма по id
    # get_by_uuid возвращает объект фильма. Он опционален, так как фильм может отсутствовать в базе
    async def get_by_uuid(self, film_uuid: str) -> Optional[FilmDetailed]:
        """Получить детальную информацию о фильме по его id.

        Parameters:
            film_uuid: uuid фильма

        Returns:
            детальная информация о фильме
        """
        # Получаем данные из кеша
        film = await self._get_film_from_cache(film_uuid)
        if not film:
            # Если фильма нет в кеше, то ищем его в Elasticsearch
            film = await self._get_film_from_elastic(film_uuid)
            if not film:
                # Если он отсутствует в Elasticsearch, значит, фильма вообще нет в базе
                return None
            # Сохраняем фильм в кеш
            await self._put_film_to_cache(film)

        return film

    # 2.1. получение фильма из ES по id
    async def _get_film_from_elastic(self, film_id: str) -> Optional[FilmDetailed]:
        try:
            doc = await self.elastic.get(index="movies", id=film_id)
        except NotFoundError:
            return None
        source = doc["_source"]
        logger.debug(pformat(doc["_source"]))
        genres = source.get("genre", [])
        genre_objs = [Genre(**genre) for genre in genres]
        film_data = {
            "uuid": source.get("uuid"),
            "title": source.get("title"),
            "description": source.get("description"),
            "imdb_rating": source.get("imdb_rating"),
            "genre": genre_objs,
            "directors": source.get("directors", []),
            "actors": source.get("actors", []),
            "writers": source.get("writers", []),
        }
        return FilmDetailed(**film_data)

    # 3.1. получение фильма из кэша по id
    async def _get_film_from_cache(self, film_uuid: str) -> Optional[FilmDetailed]:
        params_to_key = {
            "uuid": film_uuid,
        }
        cache_key = generate_cache_key("movies", params_to_key)

        film_data = await self.redis.get(cache_key)
        if not film_data:
            return None

        logging.info("Взято из кэша по ключу: {0}".format(cache_key))
        # pydantic предоставляет удобное API для создания объекта моделей из json
        return FilmDetailed.model_validate_json(film_data)  # возвращаем

    # десериализованный объект Film

    # 4.1. сохранение фильма в кэш по id:
    async def _put_film_to_cache(self, film: Film):
        # Сохраняем данные о фильме, используя команду set
        # Выставляем время жизни кеша — CACHE_TIME_LIFE
        # https://redis.io/commands/set/
        # pydantic позволяет сериализовать модель в json

        # подготовка к генерации ключа
        params_to_key = {
            "uuid": film.uuid,
        }
        cache_key = generate_cache_key("movies", params_to_key)

        await self.redis.set(
            cache_key,
            film.model_dump_json(),
            config.CACHE_TIME_LIFE,
        )


class MultipleFilmsService:
    """Сервис для получения информации о нескольких фильмов из elastic."""

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        """
        Инициализация сервиса.

        Parameters:
            redis: экземпляр redis'а
            elastic: экземпляр elastic'а
        """
        self.redis = redis
        self.elastic = elastic

    async def get_by_uuid(self, uuid: str):
        response = await self.elastic.get(index="movies", id=uuid)
        if not response["found"]:
            return None
        return response["_source"]

    # 1.2. получение страницы списка фильмов отсортированных по популярности
    async def get_multiple_films(
        self,
        desc_order: bool,
        page_size: int,
        page_number: int,
        genre: Optional[str] = None,
        similar: Optional[str] = None,
    ) -> Optional[list[Film]]:
        """Получение нескольких фильмов из elastic.

        Parameters:
            desc_order: порядок сортировки (True: убывающий, False: возрастающий)
            page_size: количество объектов на странице выдачи
            page_number: номер страницы выдачи
            genre: id жанра, по которому нужно фильтровать фильмы
            similar: id фильма, по чьим жанрам нужно фильтровать фильмы

        Returns:
            список фильмов (краткий вариант объекта)
        """
        # ключ для кэша задается в формате ключ::значение::ключ::значение и т.д.
        params_to_key = {
            "desc": str(int(desc_order)),
            "page_size": str(page_size),
            "page_number": str(page_number),
            "genre": genre,
            "similar": similar,
        }
        # создаём ключ для кэша
        cache_key = generate_cache_key("movies", params_to_key)

        # запрашиваем инфо в кэше по ключу
        films_page = await self._get_multiple_films_from_cache(cache_key)
        if not films_page:
            # если в кэше нет значения по этому ключу, делаем запрос в ES
            films_page = await self._get_multiple_films_from_elastic(
                desc_order=desc_order,
                page_size=page_size,
                page_number=page_number,
                genre=genre,
                similar=similar,
            )
            # Кэшируем результат (пустой результат тоже)
            await self._put_multiple_films_to_cache(
                cache_key=cache_key,
                films=films_page,
            )

            if not films_page:
                return None

        return films_page

    async def search_films(
        self,
        query: str,
        page_number: int,
        page_size: int,
    ) -> list[Film]:
        """Полнотекстовый поиск фильмов.

        Parameters:
            query: строка запроса - предполагаемый вариант (или часть) названия фильма
            page_number: номер страницы выдачи
            page_size: размер страницы выдачи

        Returns:
            список фильмов
        """
        # ключ для кэша задается в формате ключ::значение::ключ::значение и т.д.
        params_to_key = {
            "query": query,
            "page_size": str(page_size),
            "page_number": str(page_number),
        }

        # создаём ключ для кэша
        cache_key = generate_cache_key("movies", params_to_key)

        # запрашиваем инфо в кэше
        films_page = await self._get_multiple_films_from_cache(cache_key)
        if not films_page:
            films_page = await self._fulltext_search_films_in_elastic(
                query=query,
                page_number=page_number,
                page_size=page_size,
            )

        # Сохраняем поиск по фильму в кеш (даже если поиск не дал результата)
        await self._put_multiple_films_to_cache(cache_key, films_page)

        return films_page

    # 2.2. получение из es страницы списка фильмов отсортированных по популярности
    # async def _get_multiple_films_from_elastic(
    #     self,
    #     desc_order: bool,
    #     page_size: int,
    #     page_number: int,
    #     genre: Optional[str] = None,
    #     similar: Optional[str] = None,
    # ):
    #     if desc_order:
    #         order_name = 'desc'
    #         order_mode = 'max'
    #     else:
    #         order_name = 'asc'
    #         order_mode = 'min'

    #     search_body = {
    #         'size': page_size,
    #         'from': (page_number - 1) * page_size,
    #         'sort': [
    #             {'imdb_rating': {'order': order_name, 'mode': order_mode}},
    #         ],
    #     }

    #     # Фильтр по жанру
    #     if genre is not None:
    #         search_body['query'] = {
    #             'bool': {
    #                 'filter': [
    #                     {'term': {'genre.uuid': genre}},
    #                 ],
    #             },
    #         }
    #         logger.debug("genre is not None", genre, search_body)

    #     # Фильтр по жанрам похожего фильма
    #     if similar is not None:
    #         similar_search_body = {
    #             'query': {
    #                 'bool': {
    #                     'filter': [
    #                         {'term': {'id': genre}},
    #                     ],
    #                 },
    #             },
    #         }
    #         similar_response = await self.elastic.search(index='movies', body=similar_search_body)
    #         similar_films = []
    #         for similar_hit in similar_response['hits']['hits']:
    #             similar_films.append(FilmDetailed(**similar_hit['_source']))
    #         genre_names = [similar_film.genre for similar_film in similar_films]

    #         if genre_names:
    #             genre_names = genre_names[0]
    #         logger.debug('genres: %s' % (', '.join(genre_names)))
    #         search_body['query'] = {
    #             'bool': {
    #                 'filter': [
    #                     {'terms': {'genre': genre_names}},
    #                 ],
    #             },
    #         }

    #     response = await self.elastic.search(index='movies', body=search_body)

    #     multiple_films = []
    #     for film_hit in response['hits']['hits']:
    #         multiple_films.append(Film(**film_hit['_source']))

    #     return multiple_films
    async def _get_multiple_films_from_elastic(
        self,
        similar: Optional[str] = None,
        genre: Optional[str] = None,
        desc_order: bool = True,
        page_size: int = 50,
        page_number: int = 1,
    ):
        query = {
            "size": page_size,
            "from": (page_number - 1) * page_size,
            "sort": [{"imdb_rating": {"order": "desc" if desc_order else "asc"}}],
            "query": {"bool": {"must": [], "filter": []}},
        }

        if similar:
            logging.info("similar: %s", similar)

            similar_film = await self.get_by_uuid(similar)
            logging.info("similar film retrieved: %s", similar_film)
            if similar_film and similar_film.get("genre"):
                first_genre_uuid = similar_film["genre"][0]["uuid"]
                logging.info("first_genre_uuid: %s", first_genre_uuid)
                query["query"]["bool"]["filter"].append(
                    {
                        "nested": {
                            "path": "genre",
                            "query": {"term": {"genre.uuid": first_genre_uuid}},
                        }
                    }
                )
                logging.info("query: %s", query)
            else:
                logging.warning("No genre found for film with id: %s", similar)

        if genre:
            query["query"]["bool"]["filter"].append(
                {"nested": {"path": "genre", "query": {"term": {"genre.uuid": genre}}}}
            )
            logging.info("genre: %s", genre)
        logging.info(f"Query to Elasticsearch: {pformat(query)}")
        try:
            similar_response = await self.elastic.search(index="movies", body=query)
            logging.debug(f"Response from Elasticsearch: {pformat(similar_response)}")
        except Exception as e:
            logging.error(f"Error while querying Elasticsearch: {str(e)}")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e)
            )

        if not similar_response["hits"]["hits"]:
            return []

        films_page = [
            Film(**hit["_source"]) for hit in similar_response["hits"]["hits"]
        ]
        return films_page

    # 2.3 Полнотекстовый поиск по фильмам:
    async def _fulltext_search_films_in_elastic(
        self,
        query: str,
        page_number: int,
        page_size: int,
    ):
        search_results = await self.elastic.search(
            index="movies",
            body={
                "query": {"match": {"title": query}},
                "from": (page_number - 1) * page_size,
                "size": page_size,
            },
        )
        logging.debug(search_results)
        return [Film(**hit["_source"]) for hit in search_results["hits"]["hits"]]

    # 3.2. получение страницы списка фильмов отсортированных по популярности из кэша
    async def _get_multiple_films_from_cache(self, cache_key: str):
        films_data = await self.redis.get(cache_key)
        if not films_data:
            logging.info("Не найдено в кэш")
            return None

        logging.info("Взято из кэша по ключу: {0}".format(cache_key))
        return FILM_ADAPTER.validate_json(films_data)

    # 4.2. сохранение страницы фильмов (отсортированных по популярности) в кэш:
    async def _put_multiple_films_to_cache(self, cache_key: str, films):
        await self.redis.set(
            cache_key,
            FILM_ADAPTER.dump_json(films),
            config.CACHE_TIME_LIFE,
        )


# get_film_service — это провайдер FilmService.
# С помощью Depends он сообщает, что ему необходимы Redis и Elasticsearch
# Для их получения вы ранее создали функции-провайдеры в модуле db
# Используем lru_cache-декоратор, чтобы создать объект сервиса в едином экземпляре (синглтона)
@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    """Провайдер сервиса для получения детальной информации о фильме.

    Parameters:
        redis: экземпляр redis
        elastic: экземпляр elastic

    Returns:
        сервис для получения информации о фильме
    """
    return FilmService(redis, elastic)


@lru_cache()
def get_multiple_films_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> MultipleFilmsService:
    """Провайдер сервиса для получения детальной информации о нескольких фильмах.

    Parameters:
        redis: экземпляр redis
        elastic: экземпляр elastic

    Returns:
        сервис для получения информации о нескольких фильмах
    """
    return MultipleFilmsService(redis, elastic)
