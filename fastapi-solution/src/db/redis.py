import logging
from typing import Optional

from redis.asyncio import Redis

redis: Optional[Redis] = None


# Функция понадобится при внедрении зависимостей
async def get_redis() -> Redis:
    """Геттер, который возвращает объект- соединение с БД Redis.

    Returns:
        Активное существующее соединение с БД Redis
    """
    return redis


def generate_cache_key(
    index: str,
    params_to_key: dict,
) -> str:
    """Генерирует ключ по полученным параметрам.

    Ключ для кэша задается в формате индекс::параметр::значение::параметр::значение и т.д.
    Функция сортирует параметры запроса

    Args:
        index: Имя индекса Elasticsearch
        params_to_key: Словарь с параметрами и значениями для кэша

    Returns:
        Имя кэша для Redis
    """
    if not params_to_key:
        logging.error('Невозможно сгенерировать кэш-ключ: не переданы параметры')
        raise TypeError('Missing parameters to generate cache-key')

    sorted_keys = sorted(params_to_key.keys())
    volumes = ['{0}::{1}'.format(key, str(params_to_key[key])) for key in sorted_keys]
    cache_key = '{0}::{1}'.format(index, '::'.join(volumes))

    # logging.info('Кэш-ключ: {0}'.format(cache_key))
    return cache_key
