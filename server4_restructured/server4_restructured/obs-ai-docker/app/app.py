import gzip
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

LOKI_URL = os.getenv("LOKI_URL", "http://obs-loki:3100")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://obs-ollama:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ARCHIVE_DIR = os.getenv("ARCHIVE_DIR", "/data/archive")
DATA_DIR = os.getenv("DATA_DIR", "/data")
LOKI_RETENTION_PERIOD = os.getenv("LOKI_RETENTION_PERIOD", "168h")
LOKI_TENANT_ID = os.getenv("LOKI_TENANT_ID", "fake")

ARCHIVE_DIR_PATH = Path(ARCHIVE_DIR)
DATA_DIR_PATH = Path(DATA_DIR)
MANIFEST_PATH = DATA_DIR_PATH / "archive_manifest.jsonl"
EVENTS_PATH = DATA_DIR_PATH / "service_events.jsonl"
INCIDENTS_PATH = DATA_DIR_PATH / "incidents.jsonl"

app = FastAPI(title="obs-log-ai-api")

RUNBOOKS = {
    "connection refused": "Check whether the target service is listening on the configured host and port. Validate firewall, DNS, route, and container state.",
    "permission denied": "Check file ownership, mounted volume permissions, service user permissions, and security policy.",
    "disk full": "Check disk usage and inode usage. Remove old files and verify Loki retention and archive jobs.",
    "no space left on device": "Free disk space, check inode exhaustion, and verify Loki retention and archive jobs.",
    "tls handshake failed": "Check certificate validity, CA chain, hostname mismatch, and time sync.",
    "context deadline exceeded": "Check downstream latency, network reachability, timeout values, and dependency health.",
    "too many open files": "Increase file descriptor limits and inspect connection or file descriptor leaks.",
    "too far behind": "Loki is rejecting old log entries. Restart the shipper or drop stale backlog so only fresh logs are sent.",
}

class SummaryReq(BaseModel):
    query: str
    start: str
    end: str
    limit: int = Field(default=200, ge=1, le=5000)
    provider: Optional[str] = None
    model: Optional[str] = None

class ArchiveReq(BaseModel):
    query: str
    start: str
    end: str
    limit: int = Field(default=1000, ge=1, le=20000)
    note: str = ""

class PurgeReq(BaseModel):
    query: str
    start: str
    end: str
    archive_first: bool = True
    limit: int = Field(default=1000, ge=1, le=20000)
    note: str = ""

class AskReq(BaseModel):
    question: str
    service_name: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None

def ensure_dirs() -> None:
    ARCHIVE_DIR_PATH.mkdir(parents=True, exist_ok=True)
    DATA_DIR_PATH.mkdir(parents=True, exist_ok=True)
    for p in [MANIFEST_PATH, EVENTS_PATH, INCIDENTS_PATH]:
        p.touch(exist_ok=True)

def append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    ensure_dirs()
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")

def read_jsonl(path: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    if limit:
        out = out[-limit:]
    return out

def parse_timeish(value: str) -> datetime:
    s = str(value).strip()
    if s.isdigit():
        raw = int(s)
        if len(s) >= 16:
            return datetime.fromtimestamp(raw / 1_000_000_000, tz=timezone.utc)
        if len(s) >= 13:
            return datetime.fromtimestamp(raw / 1_000, tz=timezone.utc)
        return datetime.fromtimestamp(raw, tz=timezone.utc)
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def to_ns(value: str) -> str:
    return str(int(parse_timeish(value).timestamp() * 1_000_000_000))

def iso_utc(value: str) -> str:
    return parse_timeish(value).isoformat().replace("+00:00", "Z")

def loki_headers() -> Dict[str, str]:
    headers = {}
    if LOKI_TENANT_ID:
        headers["X-Scope-OrgID"] = LOKI_TENANT_ID
    return headers

def loki_query(query: str, start: str, end: str, limit: int) -> List[Dict[str, Any]]:
    r = requests.get(
        f"{LOKI_URL}/loki/api/v1/query_range",
        params={"query": query, "start": to_ns(start), "end": to_ns(end), "limit": limit, "direction": "backward"},
        headers=loki_headers(),
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("data", {}).get("result", [])

def flatten(results: List[Dict[str, Any]]) -> List[str]:
    lines = []
    for stream in results:
        for _, line in stream.get("values", []):
            lines.append(line.strip())
    return lines

def normalize(line: str) -> str:
    line = re.sub(r"\b\d{2,}\b", "<num>", line)
    line = re.sub(r"\b\d+\.\d+\.\d+\.\d+\b", "<ip>", line)
    line = re.sub(r"[a-f0-9]{8,}", "<hex>", line, flags=re.I)
    return line[:220]

def top_patterns(lines: List[str], topn: int = 8) -> List[str]:
    counts = {}
    for line in lines:
        key = normalize(line)
        counts[key] = counts.get(key, 0) + 1
    ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return [f"{count}x {msg}" for msg, count in ranked[:topn]]

def classify(lines: List[str]) -> str:
    if not lines:
        return "healthy"
    text = "\n".join(lines).lower()
    if any(x in text for x in ["panic", "fatal", "segmentation fault", "crashloop", "no space left on device"]):
        return "unhealthy"
    if any(x in text for x in ["error", "exception", "failed", "refused", "timeout", "denied", "too far behind"]):
        return "error"
    if any(x in text for x in ["warn", "warning"]):
        return "info"
    return "healthy"

def matched_runbooks(lines: List[str]) -> List[Dict[str, str]]:
    text = "\n".join(lines).lower()
    out = []
    for key, remedy in RUNBOOKS.items():
        if key in text:
            out.append({"pattern": key, "remedy": remedy})
    return out

def fallback_summary(status: str, pats: List[str], runbooks: List[Dict[str, str]], lines: List[str]) -> Dict[str, Any]:
    root = runbooks[0]["pattern"] if runbooks else "log anomalies detected"
    remedy = runbooks[0]["remedy"] if runbooks else "Check recent logs, service health, container restarts, and dependency reachability."
    return {
        "status": status,
        "summary": f"Fallback summary generated without LLM. {len(lines)} log lines matched.",
        "root_cause": root,
        "evidence": pats[:3],
        "remedy": remedy,
        "confidence": "medium",
    }

def coerce_json_payload(text: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    return fallback

def redact_line(line: str) -> str:
    text = line or ""
    text = re.sub(r"(?i)(authorization\s*:\s*bearer\s+)[^\s]+", r"\1<redacted>", text)
    text = re.sub(r"(?i)(api[-_ ]?key\s*[=:]\s*)[^\s,;]+", r"\1<redacted>", text)
    text = re.sub(r"(?i)(password\s*[=:]\s*)[^\s,;]+", r"\1<redacted>", text)
    text = re.sub(r"(?i)(token\s*[=:]\s*)[^\s,;]+", r"\1<redacted>", text)
    return text

def sanitize_lines(lines: List[str]) -> List[str]:
    return [redact_line(x) for x in lines]

def resolve_provider(provider_override: Optional[str]) -> str:
    provider = (provider_override or LLM_PROVIDER or "ollama").strip().lower()
    if provider not in {"ollama", "openai", "auto"}:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    return provider

def openai_json(prompt: str, model_override: Optional[str], fallback: Dict[str, Any]) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    if not OpenAI:
        raise RuntimeError("openai package is not installed")
    model = (model_override or OPENAI_MODEL or "").strip()
    if not model:
        raise RuntimeError("OPENAI_MODEL is not configured")
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.responses.create(model=model, input=prompt)
    content = getattr(response, "output_text", "") or ""
    return coerce_json_payload(content, fallback)

def ollama_json(prompt: str, model_override: Optional[str], fallback: Dict[str, Any], max_tokens: int) -> Dict[str, Any]:
    model = (model_override or OLLAMA_MODEL or "").strip()
    if not model:
        raise RuntimeError("OLLAMA_MODEL is not configured")
    r = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.1, "num_ctx": 4096, "num_predict": max_tokens},
        },
        timeout=90,
    )
    r.raise_for_status()
    content = r.json().get("message", {}).get("content", "")
    return coerce_json_payload(content, fallback)

def llm_json(prompt: str, provider_override: Optional[str], model_override: Optional[str], fallback: Dict[str, Any], max_tokens: int = 260) -> Dict[str, Any]:
    provider = resolve_provider(provider_override)
    errors = []

    def try_provider(name: str):
        try:
            if name == "openai":
                return openai_json(prompt, model_override, fallback)
            if name == "ollama":
                return ollama_json(prompt, model_override, fallback, max_tokens)
        except Exception as exc:
            errors.append(f"{name}: {exc}")
        return None

    order = [provider] if provider != "auto" else [LLM_PROVIDER, "ollama", "openai"]
    seen = set()
    for name in order:
        name = (name or "").strip().lower()
        if not name or name in seen or name == "auto":
            continue
        seen.add(name)
        payload = try_provider(name)
        if isinstance(payload, dict) and payload:
            payload["provider_used"] = name
            payload.setdefault("llm_error", None)
            return payload

    out = dict(fallback)
    out["provider_used"] = "fallback"
    out["llm_error"] = "; ".join(errors) if errors else "no provider available"
    return out

def build_summary(query: str, start: str, end: str, limit: int, provider: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
    results = loki_query(query, start, end, limit)
    lines = sanitize_lines(flatten(results))
    status = classify(lines)

    if not lines:
        return {
            "status": "healthy",
            "summary": "No log lines found in the selected time range.",
            "root_cause": "none",
            "evidence": [],
            "remedy": "No action required.",
            "confidence": "high",
            "patterns": [],
            "runbooks": [],
            "raw_evidence": [],
            "provider_used": "none",
            "llm_error": None,
        }

    working_lines = lines[:120]
    sample_lines = lines[:25]
    pats = top_patterns(working_lines)
    runbooks = matched_runbooks(working_lines)
    fallback = fallback_summary(status, pats, runbooks, sample_lines)

    prompt = f'''
You are an SRE log analyst.
Return compact valid JSON with exactly these keys:
status, summary, root_cause, evidence, remedy, confidence

Detected status: {status}
Query: {query}
Top patterns: {json.dumps(pats, ensure_ascii=False)}
Known runbook hints: {json.dumps(runbooks[:3], ensure_ascii=False)}
Recent raw lines: {json.dumps(sample_lines, ensure_ascii=False)}
'''.strip()

    payload = llm_json(prompt, provider, model, fallback, max_tokens=260)
    payload.setdefault("status", status)
    payload.setdefault("summary", fallback["summary"])
    payload.setdefault("root_cause", fallback["root_cause"])
    payload.setdefault("evidence", fallback["evidence"])
    payload.setdefault("remedy", fallback["remedy"])
    payload.setdefault("confidence", fallback["confidence"])
    payload["patterns"] = pats
    payload["runbooks"] = runbooks
    payload["raw_evidence"] = sample_lines[:10]
    payload["selected_provider"] = resolve_provider(provider)
    if model:
        payload["selected_model"] = model
    return payload

def archive_query(query: str, start: str, end: str, limit: int, note: str = "") -> Dict[str, Any]:
    ensure_dirs()
    r = requests.get(
        f"{LOKI_URL}/loki/api/v1/query_range",
        params={"query": query, "start": to_ns(start), "end": to_ns(end), "limit": limit, "direction": "forward"},
        headers=loki_headers(),
        timeout=120,
    )
    r.raise_for_status()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha1(f"{query}|{start}|{end}|{limit}".encode()).hexdigest()[:10]
    path = ARCHIVE_DIR_PATH / f"loki_archive_{stamp}_{digest}.json.gz"

    with gzip.open(path, "wb") as fh:
        fh.write(r.content)

    record = {
        "type": "archive",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "query": query,
        "start": iso_utc(start),
        "end": iso_utc(end),
        "limit": limit,
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "note": note,
    }
    append_jsonl(MANIFEST_PATH, record)
    return record

def submit_delete_request(query: str, start: str, end: str) -> Dict[str, Any]:
    r = requests.post(
        f"{LOKI_URL}/loki/api/v1/delete",
        params={"query": query, "start": to_ns(start), "end": to_ns(end)},
        headers=loki_headers(),
        timeout=60,
    )
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return {"message": r.text or "delete request accepted"}

def build_incidents(service_name: str) -> List[Dict[str, Any]]:
    events = [e for e in read_jsonl(EVENTS_PATH) if e.get("service_name") == service_name]
    def evt_dt(e): return parse_timeish(e.get("event_time"))
    incidents = []
    pending_stop = None
    for e in sorted(events, key=evt_dt):
        et = str(e.get("event_type", "")).lower()
        if et in {"stop", "die", "kill"}:
            pending_stop = e
        elif et in {"start", "restart"} and pending_stop:
            stopped_at = evt_dt(pending_stop)
            started_at = evt_dt(e)
            incidents.append({
                "service_name": service_name,
                "stopped_at": stopped_at.isoformat().replace("+00:00", "Z"),
                "started_at": started_at.isoformat().replace("+00:00", "Z"),
                "downtime_seconds": int((started_at - stopped_at).total_seconds()),
                "stop_event": pending_stop.get("event_type"),
                "start_event": e.get("event_type"),
            })
            pending_stop = None
    return incidents[-20:]

def latest_status(service_name: str) -> Dict[str, Any]:
    events = [e for e in read_jsonl(EVENTS_PATH) if e.get("service_name") == service_name]
    if not events:
        return {"service_name": service_name, "current_state": "unknown", "last_event": None}
    def evt_dt(e): return parse_timeish(e.get("event_time"))
    last = sorted(events, key=evt_dt)[-1]
    et = str(last.get("event_type", "")).lower()
    state = "running" if et in {"start", "restart", "unpause"} else "stopped"
    return {"service_name": service_name, "current_state": state, "last_event": last}

def infer_service(question: str) -> Optional[str]:
    services = sorted({e.get("service_name") for e in read_jsonl(EVENTS_PATH) if e.get("service_name")})
    q = question.lower()
    for s in services:
        if s.lower() in q:
            return s
    return None

def ask_observability(question: str, service_name: Optional[str], provider: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
    service_name = service_name or infer_service(question)
    facts: Dict[str, Any] = {"question": question, "service_name": service_name}
    logs: List[str] = []

    if service_name:
        facts["status"] = latest_status(service_name)
        facts["incidents"] = build_incidents(service_name)[-5:]
        try:
            end = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            start = datetime.fromtimestamp(datetime.now(timezone.utc).timestamp() - 3600, tz=timezone.utc).isoformat().replace("+00:00", "Z")
            logs = sanitize_lines(flatten(loki_query(f'{{service_name="{service_name}"}}', start, end, 30))[:20])
        except Exception:
            logs = []

    fallback_answer = {
        "answer": f"I found service facts for {service_name or 'the requested service'}.",
        "facts": facts,
        "evidence": logs[:10],
        "provider_used": "fallback",
        "llm_error": None,
    }

    prompt = f'''
You are an observability copilot.
Answer using only the provided facts and logs.
If a fact is missing, say it is not available.
Be concise.
Return valid JSON with keys: answer, facts_used, confidence

Question: {question}
Facts: {json.dumps(facts, ensure_ascii=False)}
Recent logs: {json.dumps(logs[:10], ensure_ascii=False)}
'''.strip()

    parsed = llm_json(prompt, provider, model, {}, max_tokens=320)
    if isinstance(parsed, dict) and parsed.get("answer"):
        parsed["facts"] = facts
        parsed["evidence"] = logs[:10]
        parsed["selected_provider"] = resolve_provider(provider)
        if model:
            parsed["selected_model"] = model
        return parsed

    fallback_answer["llm_error"] = parsed.get("llm_error") if isinstance(parsed, dict) else "llm failed"
    fallback_answer["selected_provider"] = resolve_provider(provider)
    if model:
        fallback_answer["selected_model"] = model
    return fallback_answer

@app.get("/health")
def health():
    ensure_dirs()
    return {
        "status": "ok",
        "loki_url": LOKI_URL,
        "default_provider": LLM_PROVIDER,
        "ollama_url": OLLAMA_URL,
        "ollama_model": OLLAMA_MODEL,
        "openai_model": OPENAI_MODEL,
        "openai_configured": bool(OPENAI_API_KEY),
    }

@app.get("/config")
def config():
    ensure_dirs()
    return {
        "status": "ok",
        "loki_url": LOKI_URL,
        "default_provider": LLM_PROVIDER,
        "ollama_url": OLLAMA_URL,
        "ollama_model": OLLAMA_MODEL,
        "openai_model": OPENAI_MODEL,
        "openai_configured": bool(OPENAI_API_KEY),
        "retention_period": LOKI_RETENTION_PERIOD,
        "archive_dir": ARCHIVE_DIR,
        "data_dir": DATA_DIR,
    }

@app.get("/providers")
def providers():
    return {
        "default_provider": LLM_PROVIDER,
        "providers": ["auto", "ollama", "openai"],
        "ollama": {"configured": bool(OLLAMA_MODEL), "url": OLLAMA_URL, "model": OLLAMA_MODEL},
        "openai": {"configured": bool(OPENAI_API_KEY and OPENAI_MODEL), "model": OPENAI_MODEL},
    }

@app.get("/service/status")
def service_status(service_name: str):
    ensure_dirs()
    return latest_status(service_name)

@app.get("/service/history")
def service_history(service_name: str, limit: int = 50):
    ensure_dirs()
    items = [e for e in read_jsonl(EVENTS_PATH) if e.get("service_name") == service_name]
    return {"items": items[-limit:],
            "stream": False
        }

@app.get("/service/incidents")
def service_incidents(service_name: str):
    ensure_dirs()
    return {"items": build_incidents(service_name)}

@app.post("/ask")
def ask(req: AskReq):
    ensure_dirs()
    return ask_observability(req.question, req.service_name, req.provider, req.model)

@app.post("/summarize")
def summarize(req: SummaryReq):
    try:
        return build_summary(req.query, req.start, req.end, req.limit, req.provider, req.model)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/archive")
def archive(req: ArchiveReq):
    try:
        return archive_query(req.query, req.start, req.end, req.limit, req.note)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/archive/list")
def archive_list(limit: int = Query(default=20, ge=1, le=200)):
    ensure_dirs()
    return {"items": read_jsonl(MANIFEST_PATH, limit)}

@app.post("/purge")
def purge(req: PurgeReq):
    try:
        archive_record: Optional[Dict[str, Any]] = None
        if req.archive_first:
            archive_record = archive_query(req.query, req.start, req.end, req.limit, note=f"pre-purge: {req.note}".strip())
        delete_response = submit_delete_request(req.query, req.start, req.end)
        record = {
            "type": "purge",
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "query": req.query,
            "start": iso_utc(req.start),
            "end": iso_utc(req.end),
            "archive_first": req.archive_first,
            "archive_path": archive_record.get("path") if archive_record else None,
            "note": req.note,
            "delete_response": delete_response,
        }
        append_jsonl(MANIFEST_PATH, record)
        return {"status": "delete_requested", "archive": archive_record, "delete_response": delete_response, "note": "Delete request submitted."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# ---------------- DevOps Q&A API ----------------

class DevopsAskReq(BaseModel):
    question: str
    service_name: Optional[str] = None

@app.post("/devops/ask")
def devops_ask(req: DevopsAskReq):
    question = req.question.lower()
    service = req.service_name or "unknown"

    answer = {
        "answer": f"I analyzed logs for {service}.",
        "summary": "DevOps AI analysis placeholder.",
        "root_cause": "log anomalies detected",
        "remedy_steps": [
            "Check recent logs",
            "Check container restart history",
            "Verify dependent services",
            "Validate configuration"
        ],
        "next_checks": [
            "Check health endpoint",
            "Check metrics in Grafana",
            "Restart service if needed"
        ],
        "confidence": "medium"
    }

    return answer

