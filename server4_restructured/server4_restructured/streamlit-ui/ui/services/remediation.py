import requests
from ui.config import REMEDIATION_API_URL, REMEDIATION_SHARED_TOKEN


def _h():
    return {"Authorization": f"Bearer {REMEDIATION_SHARED_TOKEN}"}


def list_incidents() -> list:
    try:
        r = requests.get(f"{REMEDIATION_API_URL}/incidents", headers=_h(), timeout=8)
        return r.json() if r.ok else []
    except Exception:
        return []


def create_incident(service: str, issue: str, severity: str, description: str) -> dict:
    try:
        r = requests.post(
            f"{REMEDIATION_API_URL}/incidents",
            json={"service": service, "issue": issue, "severity": severity, "description": description},
            headers=_h(), timeout=10,
        )
        return {"ok": r.ok, "body": r.json() if r.ok else r.text}
    except Exception as e:
        return {"ok": False, "body": str(e)}


def list_pending() -> list:
    try:
        r = requests.get(f"{REMEDIATION_API_URL}/pending", headers=_h(), timeout=8)
        return r.json() if r.ok else []
    except Exception:
        return []


def approve_action(action_id: str) -> dict:
    try:
        r = requests.post(f"{REMEDIATION_API_URL}/approve/{action_id}", headers=_h(), timeout=10)
        return {"ok": r.ok, "body": r.text}
    except Exception as e:
        return {"ok": False, "body": str(e)}


def reject_action(action_id: str) -> dict:
    try:
        r = requests.post(f"{REMEDIATION_API_URL}/reject/{action_id}", headers=_h(), timeout=10)
        return {"ok": r.ok, "body": r.text}
    except Exception as e:
        return {"ok": False, "body": str(e)}


def trigger_remediation(service: str) -> dict:
    try:
        r = requests.post(
            f"{REMEDIATION_API_URL}/trigger",
            json={"service": service}, headers=_h(), timeout=15,
        )
        return {"ok": r.ok, "body": r.json() if r.ok else r.text}
    except Exception as e:
        return {"ok": False, "body": str(e)}
