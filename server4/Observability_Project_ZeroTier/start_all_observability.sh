#!/usr/bin/env bash
set -e

cd ~/observability-stack
docker compose -f docker-compose-observability.yml up -d --build

cd ~/obs-ai
if [ "${ENABLE_OLLAMA:-1}" = "1" ]; then
  docker compose --profile ollama up -d --build
else
  docker compose up -d --build
fi

cd ~/kafka-control-api
docker compose -f docker-compose.streamlit.yml up -d --build

docker compose ls
docker ps
