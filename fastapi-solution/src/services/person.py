import json
from functools import lru_cache
from typing import List, Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.redis import get_redis
from models.person import Person


class PersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, person_id: str) -> Optional[Person]:
        cache_key = f"person:{person_id}"
        cached_person = await self.redis.get(cache_key)
        if cached_person:
            return Person.parse_raw(cached_person)

        try:
            doc = await self.elastic.get(index="persons", id=person_id)
        except NotFoundError:
            return None
        person = Person(**doc["_source"])
        await self.redis.set(cache_key, person.json(), ex=300)  # Кеш на 5 минут
        return person

    async def search(self, query: str, sort: Optional[str] = None) -> List[Person]:
        cache_key = f"persons:search:{query}:{sort}"
        cached_persons = await self.redis.get(cache_key)
        if cached_persons:
            return [Person.parse_raw(person) for person in json.loads(cached_persons)]

        body = {"query": {"multi_match": {"query": query, "fields": ["name"]}}}
        if sort:
            body["sort"] = {sort: {"order": "asc"}}

        result = await self.elastic.search(index="persons", body=body)
        persons = [Person(**hit["_source"]) for hit in result["hits"]["hits"]]
        await self.redis.set(
            cache_key, json.dumps([person.json() for person in persons]), ex=300
        )  # Кеш на 5 минут
        return persons


@lru_cache()
def get_person_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)
