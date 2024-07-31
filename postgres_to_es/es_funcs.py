import json
from contextlib import contextmanager

from elasticsearch import ConnectionError, Elasticsearch, helpers

from modules.models import ESMovies
from modules.queries import mappings, settings
from modules.utils import FunctionError, backoff, log


@contextmanager
def es_conn(dsn: str):
    es_connection = Elasticsearch(dsn)
    try:
        yield es_connection
    finally:
        es_connection.close()


class ESLoader:
    """Загрузка данных в Elasticsearch"""

    def __init__(self, host) -> None:
        self.host = host
        self.create_index("movies")

    @backoff((ConnectionError))
    def create_index(self, index_name: str) -> None:
        with es_conn(self.host) as es:
            if not es.ping():
                raise ConnectionError

            if not es.indices.exists(index="movies"):
                es.indices.create(
                    index=index_name, settings=settings, mappings=mappings
                )
                log.info(
                    f"Создан индекс {index_name} с:"
                    f"{json.dumps(settings, indent=2)} и {json.dumps(mappings, indent=2)} "
                )

    @backoff((FunctionError))
    def load(self, data: list[ESMovies]) -> None:
        actions = [
            {"_index": "movies", "_id": row.id, "_source": row.json()} for row in data
        ]
        with es_conn(self.host) as es:
            helpers.bulk(es, actions, stats_only=True)
            log.info(f"Загружено {len(data)} строк")


class ESTransformer:
    """Преобразование данных полученых из Postgres"""

    def set_person_names(row: dict, role: str) -> list[str]:
        names = []
        for person in row["persons"]:
            if person["person_role"] == role:
                names.append(person["person_name"])
        return names

    def set_person_details(row: dict, role: str) -> list[dict]:
        person_details = []
        for person in row["persons"]:
            if person["person_role"] == role:
                person_details.append(person)
        return person_details

    def set_genres(row: list) -> list[str]:
        genres = []
        for genre in row:
            genres.append(genre["genre_name"])
        return genres

    def transform(self, batch: list[dict]) -> list[ESMovies]:

        es_output = []
        for row in batch:
            transformed_row = ESMovies(
                id=row["id"],
                imdb_rating=row["rating"],
                genre=ESTransformer.set_genres(row["genres"]),
                genres=row["genres"],
                title=row["title"],
                description=row["description"],
                director_names=ESTransformer.set_person_names(row, "director"),
                actors_names=ESTransformer.set_person_names(row, "actor"),
                writers_names=ESTransformer.set_person_names(row, "writer"),
                directors=ESTransformer.set_person_details(row, "director"),
                actors=ESTransformer.set_person_details(row, "actor"),
                writers=ESTransformer.set_person_details(row, "writer"),
                modified=row["modified"],
            )
            es_output.append(transformed_row)

        return es_output
