from datetime import datetime
from typing import Dict, List, Optional

import backoff
from config import settings
from logger import logger
from sqlalchemy import MetaData, Table, create_engine, select
from sqlalchemy.exc import DataError, OperationalError
from sqlalchemy.orm import sessionmaker

metadata = MetaData(schema="content")


@backoff.on_exception(
    backoff.expo, OperationalError, max_time=settings.backoff_max_time
)
def get_session():
    logger.info("Creating session...")
    engine = create_engine(settings.postgres_dsn)
    Session = sessionmaker(bind=engine)
    return Session()


session = get_session()


@backoff.on_exception(
    backoff.expo, OperationalError, max_time=settings.backoff_max_time
)
def reflect_metadata(engine):
    logger.info("Reflecting metadata...")
    metadata.reflect(bind=engine)


reflect_metadata(session.bind)

film_work = Table("film_work", metadata, autoload_with=session.bind)
person = Table("person", metadata, autoload_with=session.bind)
person_film_work = Table("person_film_work", metadata, autoload_with=session.bind)
genre = Table("genre", metadata, autoload_with=session.bind)
genre_film_work = Table("genre_film_work", metadata, autoload_with=session.bind)


@backoff.on_exception(
    backoff.expo,
    (OperationalError, ConnectionError),
    max_time=settings.backoff_max_time,
)
def extract_movies(batch_size: int, last_id: Optional[str]) -> List[Dict]:
    """Extract movies from the database in batches."""
    query = select(
        film_work.c.id,
        film_work.c.rating,
        film_work.c.title,
        film_work.c.description,
        film_work.c.modified,
    )
    if last_id:
        query = query.where(film_work.c.id > last_id)
    query = query.order_by(film_work.c.id).limit(batch_size)
    try:
        result = session.execute(query)
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result]
    except DataError as e:
        logger.error(f"DataError: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []


@backoff.on_exception(
    backoff.expo, OperationalError, max_time=settings.backoff_max_time
)
def extract_genres(last_modified_genres: datetime) -> List[Dict]:
    """Extract updated genres from the database."""
    query = select(genre.c.id, genre.c.name, genre.c.modified).where(
        genre.c.modified > last_modified_genres
    )
    try:
        result = session.execute(query)
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result]
    except DataError as e:
        logger.error(f"DataError: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []


@backoff.on_exception(
    backoff.expo, OperationalError, max_time=settings.backoff_max_time
)
def extract_persons(last_modified_persons: datetime) -> List[Dict]:
    """Extract updated persons from the database."""
    query = select(person.c.id, person.c.full_name, person.c.modified).where(
        person.c.modified > last_modified_persons
    )
    try:
        result = session.execute(query)
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result]
    except DataError as e:
        logger.error(f"DataError: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []


def get_genres(movie_id: str) -> List[Dict[str, str]]:
    """Retrieve genres for a given movie."""
    if not movie_id:
        logger.error("Invalid movie ID: None")
        return []
    query = (
        select(genre.c.name, genre.c.id)
        .select_from(
            genre.join(genre_film_work, genre.c.id == genre_film_work.c.genre_id)
        )
        .where(genre_film_work.c.film_work_id == movie_id)
    )
    try:
        result = session.execute(query)
        return [{"name": row[0], "uuid": str(row[1])} for row in result]
    except DataError as e:
        logger.error(f"DataError for movie ID {movie_id}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error for movie ID {movie_id}: {e}")
        return []


def get_names(movie_id: str, role: str) -> List[str]:
    """Retrieve names of persons with a given role for a specific movie."""
    if not movie_id or not role:
        logger.error("Invalid movie ID or role: movie_id=%s, role=%s", movie_id, role)
        return []

    query = (
        select((person.c.full_name))
        .select_from(person.join(person_film_work))
        .where(person_film_work.c.film_work_id == movie_id)
        .where(person_film_work.c.role == role)
    )
    try:
        result = session.execute(query)
        return [row[0] for row in result]
    except DataError as e:
        logger.error(f"DataError for movie ID {movie_id}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error for movie ID {movie_id}: {e}")
        return []


def get_persons(movie_id: str, role: str) -> List[Dict]:
    """Retrieve persons with a given role for a specific movie."""
    query = (
        select(person.c.id, person.c.full_name)
        .select_from(person.join(person_film_work))
        .where(person_film_work.c.film_work_id == movie_id)
        .where(person_film_work.c.role == role)
    )

    try:
        result = session.execute(query).fetchall()
        return [{"id": row[0], "name": row[1]} for row in result]
    except DataError as e:
        logger.error(f"DataError for movie ID {movie_id}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error for movie ID {movie_id}: {e}")
        return []


def get_movies_by_genre(genre_ids: List[str]) -> List[Dict]:
    """Retrieve all movies associated with a list of genre IDs."""
    if not genre_ids:
        return []
    query = (
        select(
            film_work.c.id,
            film_work.c.rating,
            film_work.c.title,
            film_work.c.description,
            film_work.c.modified,
        )
        .select_from(film_work.join(genre_film_work))
        .where(genre_film_work.c.genre_id.in_(genre_ids))
    )
    try:
        result = session.execute(query)
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result]
    except DataError as e:
        logger.error(f"DataError: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []


def get_movies_by_person(person_ids: List[str]) -> List[Dict]:
    """Retrieve all movies associated with a list of person IDs."""
    if not person_ids:
        return []
    query = (
        select(
            film_work.c.id,
            film_work.c.rating,
            film_work.c.title,
            film_work.c.description,
            film_work.c.modified,
        )
        .select_from(film_work.join(person_film_work))
        .where(person_film_work.c.person_id.in_(person_ids))
    )
    try:
        result = session.execute(query)
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result]
    except DataError as e:
        logger.error(f"DataError: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []
