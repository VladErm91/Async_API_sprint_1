from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    postgres_dsn: str = Field(..., env="POSTGRES_DSN")
    redis_dsn: str = Field(..., env="REDIS_DSN")
    elasticsearch_dsn: str = Field(..., env="ELASTICSEARCH_DSN")
    elasticsearch_index: str = Field("movies")
    batch_size: int = Field(100, env="BATCH_SIZE")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    etl_interval_minutes: int = Field(5, env="ETL_INTERVAL_MINUTES")
    backoff_max_time: int = Field(60, env="BACKOFF_MAX_TIME")

    class Config:
        env_file = ".env"


settings = Settings()
