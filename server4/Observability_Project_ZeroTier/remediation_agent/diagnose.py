import re
from typing import Any, Dict


def _lc(value: Any) -> str:
    return str(value or "").lower()


def match_issue_type(logs_text: str, health_status: str) -> str:
    text = _lc(logs_text)
    status = _lc(health_status)

    if "connection refused" in text:
        return "dependency_timeout"
    if "timed out" in text or "timeout" in text:
        return "dependency_timeout"
    if "oomkilled" in text or "killed process" in text or "out of memory" in text:
        return "crash_loop"
    if "crashloopbackoff" in text or "back-off restarting" in text:
        return "crash_loop"
    if "inactive (dead)" in text or "failed state" in text:
        return "down"
    if status == "unhealthy":
        return "unhealthy"
    return "unhealthy"


def build_reason_summary(service: str, issue_type: str, logs_text: str, health_status: str) -> str:
    text = _lc(logs_text)
    if issue_type == "dependency_timeout":
        if "connection refused" in text:
            return f"{service} appears unhealthy because recent logs contain connection refused errors."
        return f"{service} appears unhealthy because recent logs show timeout or dependency reachability failures."
    if issue_type == "crash_loop":
        return f"{service} appears unhealthy because logs suggest repeated crashes or memory pressure."
    if issue_type == "down":
        return f"{service} appears unhealthy because runtime state suggests the service is down or inactive."
    return f"{service} is unhealthy based on health status '{health_status}' and recent operational signals."


def confidence_for(issue_type: str, logs_text: str, health_status: str) -> str:
    text = _lc(logs_text)
    if issue_type == "dependency_timeout" and ("connection refused" in text or "timeout" in text):
        return "high"
    if issue_type == "crash_loop" and ("oomkilled" in text or "crash" in text):
        return "high"
    if _lc(health_status) == "unhealthy":
        return "medium"
    return "low"


def diagnose_service(service: str, health_status: str, logs_text: str, catalog_entry: Dict[str, Any]) -> Dict[str, Any]:
    issue_type = match_issue_type(logs_text, health_status)
    reason_summary = build_reason_summary(service, issue_type, logs_text, health_status)
    confidence = confidence_for(issue_type, logs_text, health_status)

    evidence = {
        "source": "detector",
        "health_status": health_status,
        "service_name": catalog_entry.get("service_name", service),
        "container_name": catalog_entry.get("container_name", service),
        "compose_service": catalog_entry.get("compose_service", service),
        "log_selector": catalog_entry.get("log_selector", service),
        "logs_excerpt": (logs_text or "")[-3000:],
    }

    return {
        "suspected_issue": issue_type.replace("_", " "),
        "issue_type": issue_type,
        "reason_summary": reason_summary,
        "confidence": confidence,
        "evidence": evidence,
    }
