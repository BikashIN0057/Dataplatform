#!/bin/bash
set -e

cd ~/observability-stack
docker compose -f docker-compose-observability.yml up -d

cd ~/obs-ai
if [ "${ENABLE_OLLAMA:-1}" = "1" ]; then
  docker compose --profile ollama up -d
else
  docker compose up -d
fi

cd ~/kafka-control-api
docker compose -f docker-compose.streamlit.yml up -d

docker ps
