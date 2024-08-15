from typing import List

from config import settings
from elasticsearch import Elasticsearch, helpers
from logger import logger

# Elasticsearch client
es = Elasticsearch(settings.elasticsearch_dsn)


def transform_person_data(person):
    return {"uuid": str(person["id"]), "full_name": person["name"]}


def load_movies_to_elasticsearch(movies: List[dict]):
    """Load movies to Elasticsearch."""
    if not movies:
        logger.info("No movies to index.")
        return

    actions = []
    for movie in movies:
        movie_copy = movie.copy()

        # Преобразуем структуру directors, actors и writers
        if "directors" in movie_copy:
            movie_copy["directors"] = [
                transform_person_data(director) for director in movie_copy["directors"]
            ]
        if "actors" in movie_copy:
            movie_copy["actors"] = [
                transform_person_data(actor) for actor in movie_copy["actors"]
            ]
        if "writers" in movie_copy:
            movie_copy["writers"] = [
                transform_person_data(writer) for writer in movie_copy["writers"]
            ]

        actions.append(
            {
                "_index": settings.elasticsearch_index,
                "_id": movie["uuid"],
                "_source": movie_copy,
            }
        )
    try:
        logger.info(
            f"Indexing actions: {actions}"
        )  # Логирование данных перед отправкой
        success, failed = helpers.bulk(es, actions, stats_only=True)
        logger.info(f"Successfully indexed {success} movies.")
        if failed:
            logger.error(f"{failed} movies failed to index.")
    except helpers.BulkIndexError as e:
        for error in e.errors:
            logger.error(f"Failed to index document: {error}")
        raise
    except Exception as e:
        logger.error(f"Failed to index movies in Elasticsearch: {e}")
        raise


def load_genres_to_elasticsearch(genres):
    es_client = Elasticsearch(settings.elasticsearch_dsn)
    for genre in genres:
        try:
            es_client.index(index="genres", id=genre["uuid"], document=genre)
            logger.info(f"Genre {genre['uuid']} indexed successfully")
        except Exception as e:
            logger.error(f"Failed to index genre {genre['uuid']}: {e}")


def load_persons_to_elasticsearch(persons):
    es_client = Elasticsearch(settings.elasticsearch_dsn)
    for person in persons:
        try:
            es_client.index(index="persons", id=person["uuid"], document=person)
            logger.info(f"Person {person['uuid']} indexed successfully")
        except Exception as e:
            logger.error(f"Failed to index person {person['uuid']}: {e}")
