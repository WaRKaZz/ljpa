FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update

WORKDIR /code
COPY src/ /code/src/
COPY requirements.txt /code/

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

RUN mkdir /code/screenshots

EXPOSE 8080 5900

CMD ["sh", "-c", \
    "PYTHONPATH=/code/src/ljpa python /code/src/ljpa/db/database_setup.py && \
     python /code/src/ljpa/main.py"]
