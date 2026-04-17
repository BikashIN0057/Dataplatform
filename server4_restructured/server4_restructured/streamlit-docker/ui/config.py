import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

SERVER4_IP = "10.155.38.64"

# Grafana
GRAFANA_BASE_URL          = os.getenv("GRAFANA_BASE_URL",          f"http://{SERVER4_IP}:3000")
GRAFANA_KAFKA_DASH_URL    = os.getenv("GRAFANA_KAFKA_DASH_URL",    f"http://{SERVER4_IP}:3000/d/5nhADrDWk/kafka-monitoring")
GRAFANA_MINIO_DASH_URL    = os.getenv("GRAFANA_MINIO_DASH_URL",    f"http://{SERVER4_IP}:3000/d/TgmJnqnnk/minio-dashboard")
GRAFANA_PROMETHEUS_DASH   = os.getenv("GRAFANA_PROMETHEUS_DASH_URL", f"http://{SERVER4_IP}:3000/d/ad4pdfz/prometheus-2-0-overview")
GRAFANA_GRAFANA_DASH      = os.getenv("GRAFANA_GRAFANA_DASH_URL",  f"http://{SERVER4_IP}:3000/d/isFoa0z7k/grafana-metrics")
GRAFANA_AIRFLOW_DASH      = os.getenv("GRAFANA_AIRFLOW_DASH_URL",  f"http://{SERVER4_IP}:3000/d/airflow/ckuens-airflow")
GRAFANA_SPARK_DASH        = os.getenv("GRAFANA_SPARK_DASH_URL",    f"http://{SERVER4_IP}:3000/d/spark/ckuens-spark")
GRAFANA_TRINO_DASH        = os.getenv("GRAFANA_TRINO_DASH_URL",    f"http://{SERVER4_IP}:3000/d/trino/ckuens-trino")
GRAFANA_VAULT_DASH        = os.getenv("GRAFANA_VAULT_DASH_URL",    f"http://{SERVER4_IP}:3000/d/vault/ckuens-vault")
GRAFANA_KEYCLOAK_DASH     = os.getenv("GRAFANA_KEYCLOAK_DASH_URL", f"http://{SERVER4_IP}:3000/d/keycloak/ckuens-keycloak")

# Core services
PROMETHEUS_BASE_URL  = os.getenv("PROMETHEUS_BASE_URL", f"http://{SERVER4_IP}:9090")
LOKI_BASE_URL        = os.getenv("LOKI_BASE_URL",       f"http://{SERVER4_IP}:3100")
HEALTH_API_URL       = os.getenv("HEALTH_API_URL",      f"http://{SERVER4_IP}:8005/api/health")
ALLOY_UI_URL         = os.getenv("ALLOY_UI_URL",        f"http://{SERVER4_IP}:12345")

# Kafka API
KAFKA_API_BASE_URL   = os.getenv("KAFKA_API_BASE_URL",  f"http://{SERVER4_IP}:8601")

# OBS AI
OBS_AI_API_URL       = os.getenv("OBS_AI_API_URL",      f"http://{SERVER4_IP}:8088")

# Remediation
REMEDIATION_API_URL      = os.getenv("REMEDIATION_API_URL",      f"http://{SERVER4_IP}:8808")
REMEDIATION_SHARED_TOKEN = os.getenv("REMEDIATION_SHARED_TOKEN", "")

GRAFANA_DASHBOARDS = {
    "grafana":    GRAFANA_GRAFANA_DASH,
    "prometheus": GRAFANA_PROMETHEUS_DASH,
    "kafka":      GRAFANA_KAFKA_DASH_URL,
    "minio":      GRAFANA_MINIO_DASH_URL,
}

ALL_SERVICES = {
    "grafana":     "Dashboards & alerting",
    "prometheus":  "Metrics collection",
    "loki":        "Log aggregation",
    "alloy":       "Telemetry pipeline",
    "kafka":       "Kafka control API",
    "obs-ai":      "Log AI assistant",
    "remediation": "Auto-remediation agent",
    "health-api":  "Service health checks",
}
