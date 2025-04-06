FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install Chrome and VNC dependencies
# Update package lists
RUN apt-get update

WORKDIR /code
COPY . /code/

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

RUN mkdir /code/screenshots

EXPOSE 8080 5900

CMD ["sh", "-c", \
    "python database_setup.py && python main.py"]