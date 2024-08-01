import json
from functools import lru_cache
from typing import List, Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.redis import get_redis
from models.genre import Genre


class GenreService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, genre_id: str) -> Optional[Genre]:
        cache_key = f"genre:{genre_id}"
        cached_genre = await self.redis.get(cache_key)
        if cached_genre:
            return Genre.parse_raw(cached_genre)

        try:
            doc = await self.elastic.get(index="genres", id=genre_id)
        except NotFoundError:
            return None
        genre = Genre(**doc["_source"])
        await self.redis.set(cache_key, genre.json(), ex=300)  # Кеш на 5 минут
        return genre

    async def search(self, query: str, sort: Optional[str] = None) -> List[Genre]:
        cache_key = f"genres:search:{query}:{sort}"
        cached_genres = await self.redis.get(cache_key)
        if cached_genres:
            return [Genre.parse_raw(genre) for genre in json.loads(cached_genres)]

        body = {"query": {"multi_match": {"query": query, "fields": ["name"]}}}
        if sort:
            body["sort"] = {sort: {"order": "asc"}}

        result = await self.elastic.search(index="genres", body=body)
        genres = [Genre(**hit["_source"]) for hit in result["hits"]["hits"]]
        await self.redis.set(
            cache_key, json.dumps([genre.json() for genre in genres]), ex=300
        )  # Кеш на 5 минут
        return genres


@lru_cache()
def get_genre_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(redis, elastic)
