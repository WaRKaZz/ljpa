#!/bin/bash

docker compose down && \
docker system prune -a -f && \
docker compose build && \
docker compose pull && \
docker compose up -d && \
docker compose logs -f