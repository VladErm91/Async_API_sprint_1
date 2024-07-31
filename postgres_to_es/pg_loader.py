from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

import psycopg2
from psycopg2.extras import RealDictCursor

from modules.queries import pg_query
from modules.utils import log


@contextmanager
def postgres_conn(dsl: dict):
    connection = psycopg2.connect(**dsl, cursor_factory=RealDictCursor)
    connection.set_session(autocommit=True)
    try:
        yield connection
    finally:
        connection.close()


class PGLoader:
    """Получение данных из Postgres"""

    def __init__(self, postgres_dsl, batch_size: int, storage_state) -> None:
        self.batch_size = batch_size
        self.state = storage_state
        self.dsl = postgres_dsl

    def extract(self, modified: datetime) -> Iterator:
        with postgres_conn(self.dsl) as pg_conn, pg_conn.cursor() as cursor:
            select_query = cursor.mogrify(pg_query, (modified,) * 3)
            cursor.execute(select_query)

            while True:
                rows = cursor.fetchmany(self.batch_size)
                if not rows:
                    log.info("Изменений не обнаружено")
                    break
                log.info(f"Извлечено {len(rows)} записей")
                yield rows
