FROM python:3.10

WORKDIR /etl
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="/etl"


COPY requirements.txt requirements.txt

RUN python -m pip install --upgrade pip \
     && pip install -r requirements.txt --no-cache-dir

COPY . .

CMD ["sh", "-c", "python ./es_index_mapping.py && python ./etl.py"]

