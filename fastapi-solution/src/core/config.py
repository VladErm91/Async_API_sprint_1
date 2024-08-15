import os
from logging import config as logging_config

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.logger import LOGGING

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    project_name: str = "movies"

    # Настройки Redis
    redis_host: str = Field("127.0.0.1", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")

    # Настройки Elastic
    elastic_host: str = Field("127.0.0.1", alias="ELASTIC_HOST")
    elastic_port: int = Field(9200, alias="ELASTIC_PORT")
    elastic_schema: str = "http://"
    cache_time_life: int = 60 * 60


# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

settings = Settings()
