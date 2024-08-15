import json
from functools import lru_cache
from typing import List, Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis
from pydantic import TypeAdapter

from db.elastic import get_elastic
from db.redis import get_redis, generate_cache_key
from models.person import PersonWithFilms, PersonRoleInFilms, FilmRating, PersonFilm, PortfolioFilm

PERSONFILM_ADAPTER = TypeAdapter(PersonFilm)
LISTPERSONFILM_ADAPTER = TypeAdapter(list[PersonFilm])
FILMRATING_ADAPTER = TypeAdapter(list[FilmRating])


class PersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic


    async def get_by_uuid(self, person_id: str) ->PersonFilm:
        params_to_key = {
            'query': 'get_by_uuid',
            'person_id': str(person_id)
        }
        cache_key = generate_cache_key("person", params_to_key)
        person = await self.redis.get(cache_key)
        if person:
          return  PERSONFILM_ADAPTER.validate_json(person)
        person = await self.get_person_from_elastic(person_id)
        if not person:
            return None
        await self.redis.set(cache_key, PERSONFILM_ADAPTER.dump_json(person), ex=300)
        return person

    async def get_person_from_elastic(self, person_id: str) -> PersonWithFilms | None:
        person_name = await self._get_person_name_from_elastic(person_id=person_id)
        if not person_name:
            return
        films = await self._get_uuid_roles_in_films(person_id=person_id)
        return PersonFilm(uuid=person_id, full_name=person_name, films=films)

    async def _get_uuid_roles_in_films(self, person_id: str) -> list[PersonRoleInFilms]:
        films_doc = await self.elastic.search(
            index="movies",
            body={
                "query": {
                    "bool": {
                        "should": [
                            {
                                "nested": {
                                    "path": "directors",
                                    "query": {"bool": {"should": {"term": {"directors.uuid": person_id}}}},
                                }
                            },
                            {
                                "nested": {
                                    "path": "writers",
                                    "query": {"bool": {"should": {"term": {"writers.uuid": person_id}}}},
                                }
                            },
                            {
                                "nested": {
                                    "path": "actors",
                                    "query": {"bool": {"should": {"term": {"actors.uuid": person_id}}}},
                                }
                            },
                        ]
                    }
                }
            },
            size=999,
        )

        hits_list = films_doc.body.get("hits", {}).get("hits", [])
        films = []
        for hit in hits_list:
            source = hit["_source"]
            uuid = source["uuid"]
            roles = []
            for actor_in_film in source["actors"]:
                if actor_in_film["uuid"] == person_id:
                    roles.append("actors")

            for writer_in_film in source["writers"]:
                if writer_in_film["uuid"] == person_id:
                    roles.append("writer")

            for director_in_film in source["directors"]:
                if director_in_film["uuid"] == person_id:
                    roles.append("director")
            films.append(PortfolioFilm(uuid=uuid, roles=roles))
        return films


    async def search(
            self, search_str: str, page_size: int = 50, page_number: int = 1) -> List[PersonFilm]:
        params_to_key = {
            'query': str(search_str),
            'page_size': str(page_size),
            'page_number': str(page_number),
        }
        cache_key = generate_cache_key("person", params_to_key)
        persons = await self.redis.get(cache_key)
        if persons:
          return  LISTPERSONFILM_ADAPTER.validate_json(persons)
        persons = await self._get_films_by_person_full_name_from_elastic(
            search_str=search_str,
            page_size=page_size,
            page_number=page_number,
            )
        await self.redis.set(cache_key, LISTPERSONFILM_ADAPTER.dump_json(persons), ex=300)
        if not persons:
            return []
        return persons

    async def _get_films_by_person_full_name_from_elastic(
        self, search_str: str, page_size: int = 50, page_number: int = 1
    ) -> List[PersonFilm] | None:

        search_results = await self.elastic.search(
            index='persons',
            body={
                "query": {"match": {"full_name": search_str}},
                "from": (page_number - 1) * page_size,
                "size": page_size,
            },
        )
        persons_hit_list = search_results.body.get("hits", {}).get("hits", [])
        total = search_results.body.get("hits", {})["total"]["value"]
        films_by_person = []
        for person_hit in persons_hit_list:
            person_uuid = person_hit["_source"]["uuid"]
            full_name = person_hit["_source"]["full_name"]
            films = await self._get_uuid_roles_in_films(person_id=person_uuid)
            films_by_person.append(PersonFilm(uuid=person_uuid, full_name=full_name, films=films))
        if not films_by_person:
            return
        return films_by_person

    async def get_film_detail_on_person(self, person_id: str) -> list[FilmRating]:
        params_to_key = {
            'query': 'get_film_detail_on_person',
            "person_id": str(person_id),
        }
        cache_key = generate_cache_key("person", params_to_key)
        films_rated = await self.redis.get(cache_key)
        if films_rated:
            return  FILMRATING_ADAPTER.validate_json(films_rated)
        films_rated = await self._get_film_details_by_person_id(person_id=person_id)
        await self.redis.set(cache_key, FILMRATING_ADAPTER.dump_json(films_rated), ex=300)
        if not films_rated:
                return []
        return films_rated

    async def _get_film_details_by_person_id(self, person_id: str) -> list[FilmRating]:
        films_doc = await self.elastic.search(
            index="movies",
            body={
                "query": {
                    "bool": {
                        "should": [
                            {
                                "nested": {
                                    "path": "directors",
                                    "query": {"bool": {"should": {"term": {"directors.uuid": person_id}}}},
                                }
                            },
                            {
                                "nested": {
                                    "path": "writers",
                                    "query": {"bool": {"should": {"term": {"writers.uuid": person_id}}}},
                                }
                            },
                            {
                                "nested": {
                                    "path": "actors",
                                    "query": {"bool": {"should": {"term": {"actors.uuid": person_id}}}},
                                }
                            },
                        ]
                    }
                }
            },
            size=999,
        )
        hits_list = films_doc.body.get("hits", {}).get("hits", [])
        films = []
        for hit in hits_list:
            source = hit["_source"]
            films.append(
                FilmRating(
                    uuid=source["uuid"],
                    title=source["title"],
                    imdb_rating=source["imdb_rating"],
                    )
                )
        return films

    async def _get_person_name_from_elastic(self, person_id: str) -> str | None:
        try:
            person_doc = await self.elastic.get(index="persons", id=person_id)
        except NotFoundError:
            return None

        return person_doc.body["_source"]["full_name"]


@lru_cache()
def get_person_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)
