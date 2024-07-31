import logging
from functools import wraps
from time import sleep

logging.basicConfig(filename="logger.log", level=logging.INFO)
log = logging.getLogger()


class FunctionError(Exception):
    pass


def backoff(
    exceptions,
    start_sleep_time: float = 0.1,
    factor: int = 2,
    border_sleep_time: int = 10,
    max_attempts: int = 5,
):
    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            sleep_time = start_sleep_time
            count = 0
            attempts = 0
            while True and attempts <= max_attempts:
                attempts = +1
                try:
                    return func(*args, **kwargs)
                except exceptions as error:
                    count += 1
                    log.info(
                        f"Возникла ошибка {error} при выполнении"
                        f" функции {func.__name__}"
                    )
                    if sleep_time >= border_sleep_time:
                        sleep_time = border_sleep_time
                    else:
                        sleep_time = min(
                            sleep_time * (factor**count), border_sleep_time
                        )
                    sleep(sleep_time)

        return inner

    return func_wrapper
