import json
import os
import re
import sqlite3
import subprocess
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("REMEDIATION_DB", BASE_DIR / "data" / "remediation.db"))
RUNBOOK_PATH = Path(os.getenv("REMEDIATION_RUNBOOKS", BASE_DIR / "remediation_agent" / "runbooks.yaml"))
SHARED_TOKEN = os.getenv("REMEDIATION_SHARED_TOKEN", "")

SAFE_VALUE = re.compile(r"^[A-Za-z0-9._:/?&=%+@-]+$")

app = FastAPI(title="Remediation Agent", version="0.1.0")


def build_status_command(service: str, runtime: str) -> str:
    runtime = (runtime or "").strip().lower()
    if runtime == "systemd":
        return f"systemctl status {service} --no-pager || true"
    if runtime == "docker":
        return f"docker ps -a --filter name={service}"
    if runtime in {"docker-compose", "compose"}:
        return f"docker compose ps {service}"
    if runtime == "kubernetes":
        return f"kubectl get pods -A | grep {service} || true"
    return f"echo Unsupported runtime: {runtime}"

def build_logs_command(service: str, runtime: str) -> str:
    runtime = (runtime or "").strip().lower()
    if runtime == "systemd":
        return f"journalctl -u {service} -n 120 --no-pager || true"
    if runtime == "docker":
        return f"docker logs --tail 120 {service} || true"
    if runtime in {"docker-compose", "compose"}:
        return f"docker compose logs --tail 120 {service} || true"
    if runtime == "kubernetes":
        return f"kubectl logs deployment/{service} --tail=120 || true"
    return f"echo Unsupported runtime: {runtime}"

def build_restart_command(service: str, runtime: str) -> str:
    runtime = (runtime or "").strip().lower()
    if runtime == "systemd":
        return f"systemctl restart {service}"
    if runtime == "docker":
        return f"docker restart {service}"
    if runtime in {"docker-compose", "compose"}:
        return f"docker compose restart {service}"
    if runtime == "kubernetes":
        return f"kubectl rollout restart deployment/{service}"
    return f"echo Unsupported runtime: {runtime}"

def build_validation_command(service: str, runtime: str) -> str:
    runtime = (runtime or "").strip().lower()
    if runtime == "systemd":
        return f"systemctl is-active {service}"
    if runtime == "docker":
        return "docker inspect -f '{{.State.Running}}' " + service
    if runtime in {"docker-compose", "compose"}:
        return f"docker compose ps {service}"
    if runtime == "kubernetes":
        return f"kubectl rollout status deployment/{service} --timeout=60s"
    return f"echo Unsupported runtime: {runtime}"



class ProposeIn(BaseModel):
    service: str
    runtime: str
    issue_type: str = "unhealthy"
    node: str = "local"
    evidence: Dict[str, Any] = Field(default_factory=dict)


class ApproveIn(BaseModel):
    approved_by: str = "admin"
    dry_run: bool = False


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                service TEXT NOT NULL,
                node TEXT NOT NULL,
                runtime TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                title TEXT NOT NULL,
                risk TEXT NOT NULL,
                status TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                remedy_json TEXT NOT NULL,
                execution_json TEXT,
                approved_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def require_token(x_remediation_token: str = Header(default="")) -> None:
    if not SHARED_TOKEN:
        raise HTTPException(status_code=500, detail="REMEDIATION_SHARED_TOKEN is not set")
    if x_remediation_token != SHARED_TOKEN:
        raise HTTPException(status_code=401, detail="invalid token")


def load_runbooks() -> List[Dict[str, Any]]:
    if not RUNBOOK_PATH.exists():
        raise HTTPException(status_code=500, detail=f"runbooks file missing: {RUNBOOK_PATH}")
    data = yaml.safe_load(RUNBOOK_PATH.read_text()) or {}
    return data.get("runbooks", [])


def choose_runbook(runtime: str, issue_type: str) -> Dict[str, Any]:
    runbooks = load_runbooks()
    exact = [r for r in runbooks if r.get("runtime") == runtime and issue_type in r.get("issues", [])]
    if exact:
        return exact[0]
    fallback = [r for r in runbooks if r.get("runtime") == runtime]
    if fallback:
        return fallback[0]
    raise HTTPException(status_code=400, detail=f"no runbook for runtime={runtime}")


def sanitize_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    if value == "":
        return value
    if not SAFE_VALUE.fullmatch(value):
        raise HTTPException(status_code=400, detail=f"unsafe parameter value: {value}")
    return value


def make_params(payload: ProposeIn) -> Dict[str, Any]:
    evidence = payload.evidence or {}
    params = {
        "service_name": sanitize_value(str(evidence.get("service_name", payload.service))),
        "container_name": sanitize_value(str(evidence.get("container_name", payload.service))),
        "compose_service": sanitize_value(str(evidence.get("compose_service", payload.service))),
        "node": sanitize_value(str(payload.node)),
        "service": sanitize_value(str(payload.service)),
        "runtime": sanitize_value(str(payload.runtime)),
        "issue_type": sanitize_value(str(payload.issue_type)),
    }
    return params


def deep_render(obj: Any, params: Dict[str, Any]) -> Any:
    if isinstance(obj, str):
        return obj.format(**params)
    if isinstance(obj, list):
        return [deep_render(x, params) for x in obj]
    if isinstance(obj, dict):
        return {k: deep_render(v, params) for k, v in obj.items()}
    return obj



# ===== AUTO SPARK PLAYBOOK =====

def spark_commands(service="spark", runtime="docker"):
    if runtime == "docker":
        return {
            "status": f"docker ps -a --filter name={service}",
            "logs": f"docker logs --tail 200 {service} || true",
            "restart": f"docker restart {service}",
            "validate": f"docker inspect -f '{{{{.State.Running}}}}' {service}",
        }
    return {
        "status": f"systemctl status {service} --no-pager || true",
        "logs": f"journalctl -u {service} -n 200 --no-pager || true",
        "restart": f"systemctl restart {service}",
        "validate": f"systemctl is-active {service}",
    }

def collect_spark_evidence(service="spark", runtime="docker"):
    cmds = spark_commands(service, runtime)
    return [
        {"name": "status", **run_command(cmds["status"], 20)},
        {"name": "logs", **run_command(cmds["logs"], 20)},
    ]

def classify_spark_issue(evidence):
    text = str(evidence).lower()
    if "exited" in text or "not running" in text:
        return "service_down"
    if "connection refused" in text or "timeout" in text:
        return "dependency_failure"
    if "out of memory" in text:
        return "resource_failure"
    return "unknown"

def build_spark_remedy(service="spark", runtime="docker", issue="unknown"):
    cmds = spark_commands(service, runtime)
    if issue == "service_down":
        return {
            "steps": [
                {"name": "Restart Spark", "command": cmds["restart"], "timeout": 30},
                {"name": "Validate", "command": cmds["validate"], "timeout": 20},
            ]
        }
    return {
        "steps": [
            {"name": "Manual review", "command": "echo Needs manual investigation", "timeout": 5}
        ]
    }

# ===== END SPARK PLAYBOOK =====

def run_command(command: str, timeout: int) -> Dict[str, Any]:
    try:
        cp = subprocess.run(
            command,
            shell=True,
            executable="/bin/bash",
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return {
            "command": command,
            "timeout": timeout,
            "returncode": cp.returncode,
            "stdout": cp.stdout[-12000:],
            "stderr": cp.stderr[-12000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "timeout": timeout,
            "returncode": 124,
            "stdout": (exc.stdout or "")[-12000:] if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "")[-12000:] if isinstance(exc.stderr, str) else "",
            "error": "timeout",
        }


def validate_result(step_def: Dict[str, Any], result: Dict[str, Any]) -> bool:
    if result.get("returncode", 1) != 0:
        return False
    expect_contains = step_def.get("expect_contains")
    if expect_contains is not None:
        haystack = (result.get("stdout", "") + "\n" + result.get("stderr", "")).strip()
        return expect_contains in haystack
    return True


def save_incident(record: Dict[str, Any]) -> None:
    with db() as conn:
        conn.execute(
            """
            INSERT INTO incidents (
                id, service, node, runtime, issue_type, title, risk, status,
                evidence_json, remedy_json, execution_json, approved_by,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["service"],
                record["node"],
                record["runtime"],
                record["issue_type"],
                record["title"],
                record["risk"],
                record["status"],
                json.dumps(record["evidence"], ensure_ascii=False),
                json.dumps(record["remedy"], ensure_ascii=False),
                json.dumps(record.get("execution"), ensure_ascii=False) if record.get("execution") is not None else None,
                record.get("approved_by"),
                record["created_at"],
                record["updated_at"],
            ),
        )
        conn.commit()


def update_incident(incident_id: str, status: str, execution: Dict[str, Any], approved_by: str | None) -> Dict[str, Any]:
    now = utcnow()
    with db() as conn:
        conn.execute(
            """
            UPDATE incidents
            SET status = ?, execution_json = ?, approved_by = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, json.dumps(execution, ensure_ascii=False), approved_by, now, incident_id),
        )
        conn.commit()
    return get_incident(incident_id)


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "service": row["service"],
        "node": row["node"],
        "runtime": row["runtime"],
        "issue_type": row["issue_type"],
        "title": row["title"],
        "risk": row["risk"],
        "status": row["status"],
        "evidence": json.loads(row["evidence_json"]),
        "remedy": json.loads(row["remedy_json"]),
        "execution": json.loads(row["execution_json"]) if row["execution_json"] else None,
        "approved_by": row["approved_by"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def get_incident(incident_id: str) -> Dict[str, Any]:
    with db() as conn:
        row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="incident not found")
        return row_to_dict(row)


def list_incidents(limit: int = 50) -> List[Dict[str, Any]]:
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM incidents ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [row_to_dict(r) for r in rows]


def execute_plan(remedy: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    steps_out: List[Dict[str, Any]] = []
    validations_out: List[Dict[str, Any]] = []
    success = True

    for step in remedy.get("steps", []):
        if dry_run:
            steps_out.append(
                {
                    "name": step.get("name"),
                    "command": step.get("command"),
                    "timeout": step.get("timeout", 30),
                    "skipped": True,
                }
            )
            continue
        result = run_command(step["command"], int(step.get("timeout", 30)))
        result["name"] = step.get("name")
        steps_out.append(result)

    for step in remedy.get("validation", []):
        if dry_run:
            validations_out.append(
                {
                    "name": step.get("name"),
                    "command": step.get("command"),
                    "timeout": step.get("timeout", 30),
                    "expect_contains": step.get("expect_contains"),
                    "skipped": True,
                    "ok": None,
                }
            )
            continue
        result = run_command(step["command"], int(step.get("timeout", 30)))
        result["name"] = step.get("name")
        result["expect_contains"] = step.get("expect_contains")
        result["ok"] = validate_result(step, result)
        validations_out.append(result)
        success = success and bool(result["ok"])

    if dry_run:
        success = False

    return {
        "dry_run": dry_run,
        "steps": steps_out,
        "validation": validations_out,
        "success": success,
    }


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/healthz")
def healthz() -> Dict[str, Any]:
    return {"ok": True, "db": str(DB_PATH), "runbooks": str(RUNBOOK_PATH)}


@app.get("/incidents", dependencies=[Depends(require_token)])
def incidents() -> List[Dict[str, Any]]:
    return list_incidents()


@app.get("/incidents/{incident_id}", dependencies=[Depends(require_token)])
def incident_by_id(incident_id: str) -> Dict[str, Any]:
    return get_incident(incident_id)


@app.post("/incidents/propose", dependencies=[Depends(require_token)])
def propose(payload: ProposeIn) -> Dict[str, Any]:
    runbook = choose_runbook(payload.runtime, payload.issue_type)
    params = make_params(payload)
    rendered = deep_render(deepcopy(runbook), params)

    incident = {
        "id": str(uuid.uuid4()),
        "service": payload.service,
        "node": payload.node,
        "runtime": payload.runtime,
        "issue_type": payload.issue_type,
        "title": rendered.get("title", runbook["id"]),
        "risk": rendered.get("risk", "low"),
        "status": "awaiting_approval",
        "evidence": payload.evidence,
        "remedy": rendered,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    save_incident(incident)
    return {
        "incident_id": incident["id"],
        "status": incident["status"],
        "title": incident["title"],
        "risk": incident["risk"],
        "steps": rendered.get("steps", []),
        "validation": rendered.get("validation", []),
    }


@app.post("/incidents/{incident_id}/approve", dependencies=[Depends(require_token)])
def approve(incident_id: str, payload: ApproveIn) -> Dict[str, Any]:
    incident = get_incident(incident_id)
    if incident["status"] not in {"awaiting_approval", "failed", "dry_run_ready"}:
        raise HTTPException(status_code=400, detail=f"incident status does not allow execution: {incident['status']}")

    execution = execute_plan(incident["remedy"], payload.dry_run)
    status = "dry_run_ready" if payload.dry_run else ("resolved" if execution["success"] else "failed")
    return update_incident(incident_id, status, execution, payload.approved_by)
