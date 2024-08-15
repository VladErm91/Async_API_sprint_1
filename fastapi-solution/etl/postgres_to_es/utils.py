from datetime import datetime
from typing import Optional

from config import settings
from redis import Redis

redis_client = Redis.from_url(settings.redis_dsn)


def get_last_processed_id() -> Optional[str]:
    """Retrieve the last processed movie ID from Redis."""
    last_id = redis_client.get("last_processed_id")
    return last_id.decode("utf-8") if last_id else None


def set_last_processed_id(movie_id: str):
    """Store the last processed movie ID in Redis."""
    redis_client.set("last_processed_id", str(movie_id))


def get_last_modified_movies() -> datetime:
    """Retrieve the last modified timestamp of movies from Redis."""
    last_modified = redis_client.get("last_modified_movies")
    return (
        datetime.fromisoformat(last_modified.decode("utf-8"))
        if last_modified
        else datetime.min
    )


def set_last_modified_movies(last_modified: datetime):
    """Store the last modified timestamp of movies in Redis."""
    redis_client.set("last_modified_movies", last_modified.isoformat())


def get_last_modified_genres() -> datetime:
    """Retrieve the last modified timestamp of genres from Redis."""
    last_modified = redis_client.get("last_modified_genres")
    return (
        datetime.fromisoformat(last_modified.decode("utf-8"))
        if last_modified
        else datetime.min
    )


def set_last_modified_genres(last_modified: datetime):
    """Store the last modified timestamp of genres in Redis."""
    redis_client.set("last_modified_genres", last_modified.isoformat())


def get_last_modified_persons() -> datetime:
    """Retrieve the last modified timestamp of persons from Redis."""
    last_modified = redis_client.get("last_modified_persons")
    return (
        datetime.fromisoformat(last_modified.decode("utf-8"))
        if last_modified
        else datetime.min
    )


def set_last_modified_persons(last_modified: datetime):
    """Store the last modified timestamp of persons in Redis."""
    redis_client.set("last_modified_persons", last_modified.isoformat())
