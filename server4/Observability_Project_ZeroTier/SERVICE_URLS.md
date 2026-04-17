# Observability Stack — Service URLs

> ZeroTier IP: `10.155.38.64`  |  ZeroTier Network: `10.155.38.0/24`

## Access URLs (for anyone on the ZeroTier network)

| Service | URL | Purpose |
|---|---|---|
| **Grafana** | http://10.155.38.64:3000 | Dashboards & alerting (admin/admin) |
| **Prometheus** | http://10.155.38.64:9090 | Metrics & query UI |
| **Loki** | http://10.155.38.64:3100 | Log aggregation API |
| **Streamlit UI** | http://10.155.38.64:8501 | Kafka Control & observability UI |
| **Health API** | http://10.155.38.64:8005/api/health | Service health status |
| **OBS AI API** | http://10.155.38.64:8088 | Log AI assistant API |
| **Kafka API** | http://10.155.38.64:8601 | Kafka topic control API |
| **Remediation API** | http://10.155.38.64:8808 | Auto-remediation API |
| **Alloy UI** | http://10.155.38.64:12345 | Grafana Alloy pipeline UI |

---

## Startup Order

Run these in order from WSL or Git Bash:

```bash
# 1. Start core observability stack (Grafana, Prometheus, Loki, Health API, Postgres)
cd ~/observability-stack
docker compose -f docker-compose-observability.yml up -d --build

# 2. Start OBS AI + event collector (joins observability-stack_default network)
cd ~/obs-ai
docker compose up -d --build
# To include Ollama LLM locally:
# docker compose --profile ollama up -d --build

# 3. Start Kafka API + Streamlit UI
cd ~/kafka-control-api
docker compose -f docker-compose.streamlit.yml up -d --build

# 4. Start Remediation API (runs as a host process, not Docker)
cd ~/  (your project root)
bash bin/remediation-api.sh &

# 5. (Optional) Start Remediation Detector
bash bin/remediation-detector.sh &
```

## Verify all containers running
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

## Docker Network
All containers share the `observability-stack_default` network.
Containers can reach each other by container name (e.g. `obs-loki`, `obs-prometheus`).

