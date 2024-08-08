FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

ARG HOME_DIR=/app

WORKDIR $HOME_DIR
COPY ./src ./src
EXPOSE 8000

COPY requirements.txt requirements.txt

RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt --no-cache-dir