#!/usr/bin/env bash
set -e

cd ~/kafka-control-api
docker compose -f docker-compose.streamlit.yml down

cd ~/obs-ai
docker compose down

cd ~/observability-stack
docker compose -f docker-compose-observability.yml down
