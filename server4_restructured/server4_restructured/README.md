# Server4 — Observability Project (Restructured)

> ZeroTier IP: `10.155.38.64`  |  Network: `10.155.38.0/24`

Each service in its own `<service>-docker/` folder — same pattern as server2.

> **Note on naming:** `kafka-control-api-docker` is a FastAPI wrapper that controls the Kafka broker
> (which runs natively on `10.155.38.64:9092`). It is NOT Kafka itself.
> Server2 (`10.155.38.155`) owns Postgres · MinIO · Vault · Hive Metastore — no duplication here.

## Structure

```
server4/
├── prometheus-docker/           Metrics collection
│   ├── .env
│   ├── docker-compose.yml
│   └── prometheus.yml
│
├── grafana-docker/              Dashboards & alerting
│   ├── .env
│   ├── docker-compose.yml
│   └── provisioning/datasources/    loki.yml · prometheus.yml
│
├── loki-docker/                 Log aggregation
│   ├── .env
│   ├── docker-compose.yml
│   └── loki-local-config.yaml
│
├── alloy-docker/                Grafana Alloy telemetry pipeline
│   ├── .env
│   ├── docker-compose.yml
│   └── config.alloy
│
├── health-api-docker/           Health API + internal Postgres sidecar
│   ├── .env
│   ├── docker-compose.yml       ← runs obs-postgres + health-api together
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
│
├── kafka-control-api-docker/    FastAPI wrapper for the Kafka broker
│   ├── .env
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── main.py
│   └── kafka_admin.py
│
├── obs-ai-docker/               Log AI assistant + event collector
│   ├── .env
│   ├── docker-compose.yml
│   ├── event_collector.py
│   └── app/                     obs-log-ai-api
│       ├── app.py · Dockerfile · requirements.txt
│
├── remediation-docker/          Auto-remediation agent
│   ├── .env
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── remediation_agent/
│       ├── api.py · detector.py · diagnose.py
│       ├── runbooks.yaml · service_catalog.yaml
│
├── streamlit-docker/            Observability Console UI
│   ├── .env
│   ├── app.py
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── ui/
│       ├── config.py · state.py · runtime.py · router.py
│       ├── pages/common · kafka · observability · remediation
│       ├── services/
│       └── components/
│
├── SERVICE_URLS.md
└── README.md
```

## Prerequisites

```bash
docker network create observability-stack_default
```

## Startup Order

```bash
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
