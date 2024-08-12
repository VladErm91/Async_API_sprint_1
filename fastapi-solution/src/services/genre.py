import json
from functools import lru_cache
from typing import List, Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends, HTTPException
from redis.asyncio import Redis

from src.db.elastic import get_elastic
from src.db.redis import get_redis
from src.models.genre import Genre


class GenreService:
    """Сервис для получения информации о жанре/жанрах из ES."""

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_uuid(self, genre_id: str) -> Optional[Genre]:
        cache_key = f"genre:{genre_id}"

        cached_genre = await self.redis.get(cache_key)
        if cached_genre:
            return Genre(**json.loads(cached_genre))

        try:
            doc = await self.elastic.get(index="genres", id=genre_id)
        except NotFoundError:
            return None
        genre = Genre(**doc["_source"])
        await self.redis.set(
            cache_key, genre.model_dump_json(), ex=300
        )  # Кеш на 5 минут
        return genre

    async def search(
        self,
        query: Optional[str] = None,
        sort: Optional[str] = None,
        order: str = "asc",
        page: int = 1,
        page_size: int = 10,
    ) -> (List[Genre], int):
        cache_key = f"genres:search:{query}:{sort}:{order}:{page}:{page_size}"
        cached_genres = await self.redis.get(cache_key)
        if cached_genres:
            data = json.loads(cached_genres)
            return [Genre.model_validate_json(genre) for genre in data["items"]], data[
                "total"
            ]

        body = {}
        if query:
            body["query"] = {
                "bool": {
                    "should": [
                        {"prefix": {"name": query.lower()}},
                        {"wildcard": {"name": f"{query.lower()}*"}},
                    ]
                }
            }
        else:
            body["query"] = {"match_all": {}}

        if sort:
            body["sort"] = [
                {sort: {"order": order}}
            ]  # Используем переменные sort и order корректно

        body["from"] = (page - 1) * page_size
        body["size"] = page_size

        result = await self.elastic.search(index="genres", body=body)
        genres = [Genre(**hit["_source"]) for hit in result["hits"]["hits"]]
        total = result["hits"]["total"]["value"]

        if (page - 1) * page_size >= total:
            raise HTTPException(status_code=404, detail="Page not found")

        await self.redis.set(
            cache_key,
            json.dumps({"items": [genre.json() for genre in genres], "total": total}),
            ex=300,
        )  # Кеш на 5 минут
        return genres, total


@lru_cache()
def get_genre_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(redis, elastic)
