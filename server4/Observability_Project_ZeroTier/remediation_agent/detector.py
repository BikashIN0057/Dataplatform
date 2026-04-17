import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests
import yaml
from dotenv import load_dotenv

from remediation_agent.diagnose import diagnose_service

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env.remediation")

REMEDIATION_API_URL = os.getenv("REMEDIATION_API_URL", "http://127.0.0.1:8808")
REMEDIATION_SHARED_TOKEN = os.getenv("REMEDIATION_SHARED_TOKEN", "")
REMEDIATION_SERVICE_CATALOG = os.getenv("REMEDIATION_SERVICE_CATALOG", str(BASE_DIR / "remediation_agent" / "service_catalog.yaml"))
HEALTH_API_URL = os.getenv("HEALTH_API_URL", "http://10.155.38.64:8005/api/health")
LOKI_BASE_URL = os.getenv("LOKI_BASE_URL", "http://10.155.38.64:3100")
DETECTOR_INTERVAL_SECONDS = int(os.getenv("DETECTOR_INTERVAL_SECONDS", "30"))
DETECT_STATUSES = {x.strip() for x in os.getenv("DETECT_STATUSES", "Unhealthy").split(",") if x.strip()}


def load_catalog() -> Dict[str, Any]:
    path = Path(REMEDIATION_SERVICE_CATALOG)
    if not path.exists():
        return {}
    return (yaml.safe_load(path.read_text()) or {}).get("services", {})


def api(method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
    headers = {"X-Remediation-Token": REMEDIATION_SHARED_TOKEN}
    url = f"{REMEDIATION_API_URL}{path}"
    if payload is None:
        r = requests.request(method, url, headers=headers, timeout=120)
    else:
        r = requests.request(method, url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()


def fetch_health_snapshot() -> Dict[str, Any]:
    r = requests.get(HEALTH_API_URL, timeout=20)
    r.raise_for_status()
    return r.json()


def fetch_recent_logs(log_selector: str) -> str:
    try:
        params = {
            "query": f'{{service_name="{log_selector}"}}',
            "limit": 25,
        }
        r = requests.get(f"{LOKI_BASE_URL}/loki/api/v1/query", params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        result = data.get("data", {}).get("result", [])
        lines = []
        for stream in result:
            for ts, line in stream.get("values", []):
                lines.append(line)
        return "\n".join(lines[-25:])
    except Exception:
        return ""


def already_open(service: str) -> bool:
    try:
        incidents = api("GET", "/incidents/open")
        return any(x.get("service") == service for x in incidents)
    except Exception:
        return False


def process_service(service: str, status: str, catalog_entry: Dict[str, Any]) -> None:
    if already_open(service):
        return

    logs_text = fetch_recent_logs(catalog_entry.get("log_selector", service))
    diagnosis = diagnose_service(service, status, logs_text, catalog_entry)

    api(
        "POST",
        "/incidents/propose",
        {
            "service": service,
            "runtime": catalog_entry.get("runtime", "systemd"),
            "issue_type": diagnosis["issue_type"],
            "node": catalog_entry.get("node", "local"),
            "evidence": diagnosis["evidence"],
            "suspected_issue": diagnosis["suspected_issue"],
            "reason_summary": diagnosis["reason_summary"],
            "confidence": diagnosis["confidence"],
            "source": "detector",
            "auto_created": True,
        },
    )


def main_loop() -> None:
    if not REMEDIATION_SHARED_TOKEN:
        raise RuntimeError("REMEDIATION_SHARED_TOKEN is not set")
    catalog = load_catalog()

    while True:
        try:
            health = fetch_health_snapshot()
            for service, status in health.items():
                if str(status) not in DETECT_STATUSES:
                    continue
                entry = catalog.get(service.lower()) or catalog.get(service) or {"runtime": "systemd", "node": "local"}
                process_service(service, str(status), entry)
        except Exception as exc:
            print(f"[detector] error: {exc}", flush=True)
        time.sleep(DETECTOR_INTERVAL_SECONDS)


if __name__ == "__main__":
    main_loop()
