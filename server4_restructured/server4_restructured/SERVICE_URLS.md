# Server4 — Service URLs

> ZeroTier IP: `10.155.38.64`  |  ZeroTier Network: `10.155.38.0/24`

| Service                  | URL                                      | Purpose                              |
|--------------------------|------------------------------------------|--------------------------------------|
| **Grafana**              | http://10.155.38.64:3000                 | Dashboards & alerting (admin/admin)  |
| **Prometheus**           | http://10.155.38.64:9090                 | Metrics & query UI                   |
| **Loki**                 | http://10.155.38.64:3100                 | Log aggregation API                  |
| **Alloy UI**             | http://10.155.38.64:12345                | Telemetry pipeline UI                |
| **Health API**           | http://10.155.38.64:8005/api/health      | Service health status                |
| **Streamlit UI**         | http://10.155.38.64:8501                 | Observability Console                |
| **Kafka Control API**    | http://10.155.38.64:8601                 | FastAPI wrapper for Kafka broker     |
| **OBS AI API**           | http://10.155.38.64:8088                 | Log AI assistant                     |
| **Remediation API**      | http://10.155.38.64:8808                 | Auto-remediation agent               |
| **Ollama** (opt)         | http://10.155.38.64:11434                | Local LLM (enable: --profile ollama) |

> **Kafka broker** runs directly on `10.155.38.64:9092` — not containerized in this project.
> **Server2** (`10.155.38.155`) hosts: Postgres · MinIO · Vault · Hive Metastore.

---

## Startup Order

```bash
# Create shared network once
docker network create observability-stack_default

cd prometheus-docker         && docker compose up -d && cd ..
cd loki-docker               && docker compose up -d && cd ..
cd grafana-docker            && docker compose up -d && cd ..
cd alloy-docker              && docker compose up -d && cd ..
cd health-api-docker         && docker compose up -d && cd ..
cd kafka-control-api-docker  && docker compose up -d && cd ..
cd obs-ai-docker             && docker compose up -d && cd ..
cd remediation-docker        && docker compose up -d && cd ..
cd streamlit-docker          && docker compose up -d && cd ..
```

## Verify

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```
