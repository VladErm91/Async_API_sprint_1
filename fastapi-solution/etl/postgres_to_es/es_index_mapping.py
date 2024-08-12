from config import settings
from elasticsearch import Elasticsearch

# Создаем клиент Elasticsearch с указанием настроек и параметров транспорта
es = Elasticsearch(settings.elasticsearch_dsn)

index_body = {
    "settings": {
        "refresh_interval": "1s",
        "analysis": {
            "filter": {
                "english_stop": {"type": "stop", "stopwords": "_english_"},
                "english_stemmer": {"type": "stemmer", "language": "english"},
                "english_possessive_stemmer": {
                    "type": "stemmer",
                    "language": "possessive_english",
                },
                "russian_stop": {"type": "stop", "stopwords": "_russian_"},
                "russian_stemmer": {"type": "stemmer", "language": "russian"},
            },
            "analyzer": {
                "ru_en": {
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "english_stop",
                        "english_stemmer",
                        "english_possessive_stemmer",
                        "russian_stop",
                        "russian_stemmer",
                    ],
                }
            },
        },
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "uuid": {"type": "keyword"},
            "imdb_rating": {"type": "float"},
            "genre": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "uuid": {"type": "keyword"},
                    "name": {"type": "keyword"},
                },
            },
            "title": {
                "type": "text",
                "analyzer": "ru_en",
                "fields": {"raw": {"type": "keyword"}},
            },
            "description": {"type": "text", "analyzer": "ru_en"},
            "directors_names": {"type": "text", "analyzer": "ru_en"},
            "actors_names": {"type": "text", "analyzer": "ru_en"},
            "writers_names": {"type": "text", "analyzer": "ru_en"},
            "directors": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "uuid": {"type": "keyword"},
                    "full_name": {"type": "text", "analyzer": "ru_en"},
                },
            },
            "actors": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "uuid": {"type": "keyword"},
                    "full_name": {"type": "text", "analyzer": "ru_en"},
                },
            },
            "writers": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "uuid": {"type": "keyword"},
                    "full_name": {"type": "text", "analyzer": "ru_en"},
                },
            },
        },
    },
}

index_body_genres = {
    "settings": {
        "refresh_interval": "1s",
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "uuid": {
                "type": "keyword",
                "dynamic": "strict",
            },
            "name": {
                "type": "text",
                "dynamic": "strict",
                "analyzer": "standard",
                "fields": {"raw": {"type": "keyword"}},
            },
        },
    },
}

index_body_persons = {
    "settings": {
        "refresh_interval": "1s",
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "uuid": {
                "type": "keyword",
                "dynamic": "strict",
            },
            "full_name": {
                "type": "text",
                "dynamic": "strict",
                "analyzer": "standard",
                "fields": {"raw": {"type": "keyword"}},
            },
            "modified": {
                "modified": {"type": "date"},
            },
        },
    },
}
es.options(ignore_status=[400]).indices.create(index="movies", body=index_body)
es.options(ignore_status=[400]).indices.create(index="genres", body=index_body_genres)
es.options(ignore_status=[400]).indices.create(index="persons", body=index_body_persons)
