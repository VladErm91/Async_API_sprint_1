from typing import List

from config import settings
from elasticsearch import Elasticsearch, helpers
from logger import logger

# Elasticsearch client
es = Elasticsearch(settings.elasticsearch_dsn)


def load_movies_to_elasticsearch(movies: List[dict]):
    """Load movies to Elasticsearch."""
    if not movies:
        logger.info("No movies to index.")
        return

    actions = [
        {
            "_index": settings.elasticsearch_index,
            "_id": movie["id"],
            "_source": movie,
        }
        for movie in movies
    ]

    try:
        helpers.bulk(es, actions)
        logger.info(f"Successfully indexed {len(movies)} movies.")
    except helpers.BulkIndexError as e:
        logger.error(f"Failed to bulk index movies in Elasticsearch: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to index movies in Elasticsearch: {e}")
        raise


def load_genres_to_elasticsearch(genres):
    for genre in genres:
        es_client = Elasticsearch(settings.elasticsearch_dsn)
        for genre in genres:
            try:
                es_client.index(index="genres", id=genre["id"], document=genre)
                logger.info(f"Genre {genre['id']} indexed successfully")
            except Exception as e:
                logger.error(f"Failed to index genre {genre['id']}: {e}")


def load_persons_to_elasticsearch(persons):
    es_client = Elasticsearch(settings.elasticsearch_dsn)
    for person in persons:
        try:
            es_client.index(index="persons", id=person["id"], document=person)
            logger.info(f"Person {person['id']} indexed successfully")
        except Exception as e:
            logger.error(f"Failed to index person {person['id']}: {e}")
