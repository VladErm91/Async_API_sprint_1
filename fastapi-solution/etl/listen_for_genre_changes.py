import asyncio
import logging

import asyncpg
from postgres_to_es.config import settings

from etl.postgres_to_es.etl import etl_process

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def listen_for_genre_changes():
    conn = await asyncpg.connect(settings.postgres_dsn)
    await conn.add_listener("genre_changes", genre_change_handler)


async def genre_change_handler(connection, pid, channel, payload):
    logger.info(f"Received notification: {payload}")
    etl_process()


if __name__ == "__main__":
    asyncio.run(listen_for_genre_changes())
