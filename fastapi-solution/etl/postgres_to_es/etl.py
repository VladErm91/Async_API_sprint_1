from datetime import datetime

import backoff
from apscheduler.schedulers.blocking import BlockingScheduler
from config import settings
from database import (
    extract_genres,
    extract_movies,
    extract_persons,
    get_movies_by_genre,
    get_movies_by_person,
)
from es_load import (
    load_genres_to_elasticsearch,
    load_movies_to_elasticsearch,
    load_persons_to_elasticsearch,
)
from logger import logger
from sqlalchemy.exc import OperationalError
from transform import transform_genre, transform_movie, transform_person
from utils import (
    get_last_modified_genres,
    get_last_modified_movies,
    get_last_modified_persons,
    get_last_processed_id,
    set_last_modified_genres,
    set_last_modified_movies,
    set_last_modified_persons,
    set_last_processed_id,
)


@backoff.on_exception(
    backoff.expo,
    (OperationalError, ConnectionError),
    max_time=settings.backoff_max_time,
)
def etl_process():
    """Main ETL process."""
    last_id = get_last_processed_id()
    last_modified_movies = get_last_modified_movies()
    last_modified_genres = get_last_modified_genres()
    last_modified_persons = get_last_modified_persons()

    logger.info(
        f"Starting ETL process with batch size {settings.batch_size}, last processed ID {last_id}, "
        f"and last modified movies timestamp {last_modified_movies}..."
    )
    try:
        movie_rows = extract_movies(settings.batch_size, last_id)
        updated_genres = extract_genres(last_modified_genres)
        updated_persons = extract_persons(last_modified_persons)

        if not movie_rows and not updated_genres and not updated_persons:
            logger.info("No data to process.")
            return

        # Transform movies
        movies = [transform_movie(movie_row) for movie_row in movie_rows]

        if movie_rows:
            last_processed_id = movies[-1]["uuid"]
            set_last_processed_id(last_processed_id)
            # Update last modified timestamps
            latest_timestamp_movies = max(
                [
                    datetime.fromisoformat(movie["modified"].isoformat())
                    for movie in movie_rows
                ]
            )
            set_last_modified_movies(latest_timestamp_movies)

        if updated_genres:
            # Transform genres
            genres = [transform_genre(genre_row) for genre_row in updated_genres]
            # Load genres to Elasticsearch
            load_genres_to_elasticsearch(genres)
            # Update last modified timestamp for genres
            latest_timestamp_genres = max(genre["modified"] for genre in updated_genres)
            set_last_modified_genres(latest_timestamp_genres)
            # Get and transform movies by updated genres
            genre_ids = [genre["id"] for genre in updated_genres]
            genre_movie_rows = get_movies_by_genre(genre_ids)
            genre_movies = [
                transform_movie(movie_row) for movie_row in genre_movie_rows
            ]
            movies.extend(genre_movies)

        if updated_persons:
            # Transform persons
            persons = [transform_person(person_row) for person_row in updated_persons]
            # Load persons to Elasticsearch
            load_persons_to_elasticsearch(persons)
            # Update last modified timestamp for persons
            latest_timestamp_persons = max(
                [person["modified"] for person in updated_persons]
            )
            set_last_modified_persons(latest_timestamp_persons)

            person_ids = [person["id"] for person in updated_persons]
            person_movie_rows = get_movies_by_person(person_ids)
            person_movies = [
                transform_movie(movie_row) for movie_row in person_movie_rows
            ]
            movies.extend(person_movies)

        # Load movies to Elasticsearch
        load_movies_to_elasticsearch(movies)

    except Exception as e:
        logger.error(f"ETL process failed: {e}")
        raise


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(etl_process, "interval", minutes=settings.etl_interval_minutes)
    try:
        logger.info("Starting scheduler...")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
