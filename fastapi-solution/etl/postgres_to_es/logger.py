import logging

from config import settings


def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    file_handler = logging.FileHandler("etl.log")
    file_handler.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s %(message)s")
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()
