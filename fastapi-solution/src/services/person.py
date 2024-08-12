import json
from functools import lru_cache
from typing import List, Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis
from pydantic import TypeAdapter

from db.elastic import get_elastic
from db.redis import get_redis, generate_cache_key
from models.person import Person, PersonQuery

PERSON_ADAPTER = TypeAdapter(list[Person])


class PersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

<<<<<<< HEAD
    async def get_by_id(self, person_id: str) -> Optional[Person]:
=======
    async def get_by_uuid(self, person_id: str) -> Optional[Person]:
        cache_key = f"person:{person_id}"
        cached_person = await self.redis.get(cache_key)
        if cached_person:
            return Person.parse_raw(cached_person)
>>>>>>> origin/develop

        params_to_key = {
            "id": person_id,
        }

        cache_key = generate_cache_key("person", params_to_key)

        person = await self.redis.get(cache_key)
        if not person:
            person = await self.get_person_from_elastic(person_id)
            if not person:
                return None
            await self.redis.set(cache_key, person.model_dump_json(), ex=300)
        return person

    async def get_person_from_elastic(self, person_id: str) -> Optional[Person]:
        try:
            doc = await self.elastic.get(index='persons', id=person_id)
        except NotFoundError:
            return None

        return Person(**doc['_source'])


    async def search(self, search_person: PersonQuery) -> List[Person]:
        params_to_key = {
            'query': search_person.query,
            'page_size': str(search_person.page_size),
            'page_number': str(search_person.page_number),
        }

        cache_key = generate_cache_key("person", params_to_key)
        persons = await self._person_search_from_cache(cache_key)

        if not persons:
            body={
                    'query': {
                        'multi_match': {
                            'query': f'{search_person.query}',
                            'fuzziness': 'auto',
                        },
                    },
                }
            result = await self.elastic.search(index="persons", body=body)
            persons = [Person(**hit["_source"]) for hit in result["hits"]["hits"]]
            await self.redis.set(cache_key, PERSON_ADAPTER.dump_json(persons),
            ex=300)
            if not persons:
                return []
        return persons


    async def _person_search_from_cache(self, cache_key: str) -> list[Person] | None:
        cache_person_data = await self.redis.get(cache_key)
        if not cache_person_data:
            return None
        return PERSON_ADAPTER.validate_json(cache_person_data)


    async def get_persons(self) -> Optional[list[Person]]:
        persons = await self._all_persons_from_elastic()
        if not persons:
            return None
        return persons


    async def _all_persons_from_elastic(self) -> Optional[list[Person]]:
        query = {
            'query': {
                'match_all': {},
            },
            'from': 0,
            'size': 10000,
        }

        try:
            response = await self.elastic.search(index='persons', body=query)
        except NotFoundError:
            return None
        hits = response.get('hits', {}).get('hits', [])
        persons = [Person(**hit['_source']) for hit in hits]
        return persons














@lru_cache()
def get_person_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)
