import time
from datetime import datetime

from elasticsearch.exceptions import ConnectionError
from psycopg2 import OperationalError

from es_funcs import ESLoader, ESTransformer
from modules.state import JsonFileStorage, State
from modules.utils import backoff, log
from pg_loader import PGLoader
from settings import BaseConfig


@backoff((ConnectionError, OperationalError))
def etl_load(
    extractor: PGLoader,
    loader: ESLoader,
    transformer: ESTransformer,
    state: State,
) -> None:
    """запуск скрипта извлечения, обработки и загрузки данных"""

    start_timestamp = datetime.now()
    modified = state.get_state("modified")
    log.info(f"Последнее изменение {modified}")
    params = modified or datetime.min

    for extracted_part in extractor.extract(params):
        data = transformer.transform(extracted_part)
        loader.load(data)
        state.set_state("modified", str(start_timestamp))


if __name__ == "__main__":
    """запуск ETL"""

    configs = BaseConfig()
    state = State(JsonFileStorage(file_path="data.json"))

    extractor = PGLoader(
        postgres_dsl=configs.pg_dsl.dict(),
        batch_size=configs.batch_size,
        storage_state=state,
    )
    transformer = ESTransformer()
    loader = ESLoader(configs.es_host)

    while True:
        etl_load(extractor, loader, transformer, state)
        log.info(f"Sleep {configs.sleep_time}")
        time.sleep(configs.sleep_time)
