from pydantic import BaseSettings, Field


class DBSettigs(BaseSettings):
    dbname: str = Field("db", env="POSTGRES_DB")
    user: str = Field("postgres", env="POSTGRES_USER")
    password: str = Field("pwtest", env="POSTGRES_PASSWORD")
    host: str = Field("127.0.0.1", env="DB_HOST")
    port: str = Field(5432, env="DB_PORT")

    class Config:
        env_file = "./.env"
        env_file_encoding = "utf-8"


class BaseConfig(BaseSettings):
    es_host: str = Field("http://127.0.0.1:9200", env="ES_HOST")
    batch_size: int = Field(100, env="BATCH_SIZE")
    sleep_time: float = Field(10.0, env="SLEEP_TIME")
    pg_dsl: DBSettigs = DBSettigs()

    class Config:
        env_file = "./.env"
        env_file_encoding = "utf-8"
