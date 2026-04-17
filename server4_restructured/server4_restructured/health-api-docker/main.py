from fastapi import FastAPI
import requests
from datetime import datetime, timezone
import asyncio
import threading

app = FastAPI()

PROMETHEUS_URL = "http://obs-prometheus:9090"

# =========================
# State Management
# =========================
SCAN_INTERVAL_SECONDS = 15
SERVICE_STATE = {}
STATE_LOCK = threading.Lock()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def update_service_state(service, status, reason):
    now = now_iso()

    with STATE_LOCK:
        old = SERVICE_STATE.get(service)

        if old is None:
            SERVICE_STATE[service] = {
                "service": service,
                "purpose": SERVICE_PURPOSE.get(service, "Unknown"),
                "status": status,
                "reason": reason,
                "last_scan": now,
                "last_updated": now,
            }
            return

        prev_status = old["status"]

        # always update scan time
        old["last_scan"] = now
        old["reason"] = reason

        # update status and last_updated only if status changes
        if prev_status != status:
            old["status"] = status
            old["last_updated"] = now


# =========================
# Service Purpose Mapping
# =========================
SERVICE_PURPOSE = {
    "airflow": "Workflow orchestration",
    "keycloak": "Authentication & SSO",
    "spark": "Distributed processing engine",
    "prometheus": "Metrics collection",
    "grafana": "Monitoring dashboards",
    "minio": "Object storage (S3-compatible)",
    "kafka": "Event streaming backbone",
    "mlflow": "ML lifecycle management",
    "feast": "Feature store",
    "openmetadata": "Metadata management",
    "openlineage": "Data lineage tracking",
    "fastapi": "Backend API service",
}


# =========================
# Prometheus Helpers
# =========================
def prom_query(query):
    try:
        res = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": query},
            timeout=3
        )
        res.raise_for_status()
        data = res.json()
        return data.get("data", {}).get("result", [])
    except Exception:
        return []


def prom_job_any_up(job):
    try:
        result = prom_query(f'up{{job="{job}"}}')
        for r in result:
            if float(r["value"][1]) == 1:
                return True
        return False
    except Exception:
        return False


def http_check(url):
    try:
        res = requests.get(url, timeout=3)
        return res.status_code
    except Exception as e:
        return str(e)


# =========================
# Health Scan Logic
# =========================
def run_all_checks():
    # Airflow
    airflow_up = prom_job_any_up("airflow")
    update_service_state(
        "airflow",
        "Healthy" if airflow_up else "Unhealthy",
        "up=1" if airflow_up else "up=0",
    )

    # Keycloak
    keycloak_up = prom_job_any_up("keycloak")
    update_service_state(
        "keycloak",
        "Healthy" if keycloak_up else "Unhealthy",
        "up=1" if keycloak_up else "up=0",
    )

    # Spark
    update_service_state(
        "spark",
        "Not Configured",
        "not_configured",
    )

    # Prometheus
    code = http_check("http://obs-prometheus:9090/-/healthy")
    update_service_state(
        "prometheus",
        "Healthy" if code == 200 else "Unhealthy",
        str(code),
    )

    # Grafana
    code = http_check("http://obs-grafana:3000/api/health")
    update_service_state(
        "grafana",
        "Healthy" if code == 200 else "Unhealthy",
        str(code),
    )

    # MinIO
    update_service_state(
        "minio",
        "Not Configured",
        "not_configured",
    )

    # Kafka
    update_service_state(
        "kafka",
        "Not Configured",
        "not_configured",
    )

    # MLflow
    # corrected from :5000 to :5002
    # treat 401/403 as reachable service
    code = http_check("http://10.155.38.139:5002")
    update_service_state(
        "mlflow",
        "Healthy" if code in [200, 401, 403] else "Unhealthy",
        str(code),
    )

    # Feast
    # use health endpoint
    # treat 401/403 as reachable service
    code = http_check("http://10.155.38.139:6566/health")
    update_service_state(
        "feast",
        "Healthy" if code in [200, 401, 403] else "Unhealthy",
        str(code),
    )

    # OpenMetadata
    code = http_check("http://10.155.38.139:8585/api/v1/system/version")
    update_service_state(
        "openmetadata",
        "Healthy" if code == 200 else "Unhealthy",
        str(code),
    )

    # OpenLineage / Marquez admin health endpoint
    code = http_check("http://10.155.38.139:5001/healthcheck")
    update_service_state(
        "openlineage",
        "Healthy" if code == 200 else "Unhealthy",
        str(code),
    )

    # FastAPI
    # use dedicated health endpoint instead of /docs
    code = http_check("http://10.155.38.139:8000/health")
    update_service_state(
        "fastapi",
        "Healthy" if code == 200 else "Unhealthy",
        str(code),
    )


# =========================
# Background Loop
# =========================
async def health_loop():
    while True:
        try:
            run_all_checks()
        except Exception as e:
            print("Health loop error:", e)
        await asyncio.sleep(SCAN_INTERVAL_SECONDS)


@app.on_event("startup")
async def startup():
    run_all_checks()
    asyncio.create_task(health_loop())


# =========================
# API
# =========================
@app.get("/api/health")
def health():
    with STATE_LOCK:
        services = list(SERVICE_STATE.values())

    return {
        "time": now_iso(),
        "services": services,
    }
