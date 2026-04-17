import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import docker

DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
EVENTS_FILE = DATA_DIR / "service_events.jsonl"

WATCHED = {
    "obs-grafana",
    "obs-prometheus",
    "obs-loki",
    "obs-alloy",
    "obs-health-api",
    "obs-log-ai-api",
    "obs-ollama",
    "kafka-streamlit",
    "kafka-control-api",
}

def now_utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def append_event(obj):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with EVENTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def normalize_event(evt):
    if evt.get("Type") != "container":
        return None

    actor = evt.get("Actor", {}) or {}
    attrs = actor.get("Attributes", {}) or {}
    name = attrs.get("name", "")
    if name not in WATCHED:
        return None

    t = evt.get("timeNano")
    if t:
        event_time = datetime.fromtimestamp(int(t) / 1_000_000_000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    else:
        event_time = now_utc()

    return {
        "service_name": name,
        "event_type": evt.get("Action", ""),
        "event_time": event_time,
        "container_id": actor.get("ID", ""),
        "details": attrs,
    }

def snapshot_running(client):
    for c in client.containers.list(all=True):
        name = c.name
        if name not in WATCHED:
            continue
        append_event({
            "service_name": name,
            "event_type": f"snapshot_{c.status}",
            "event_time": now_utc(),
            "container_id": c.id,
            "details": {"status": c.status},
        })

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EVENTS_FILE.touch(exist_ok=True)

    while True:
        try:
            client = docker.DockerClient(base_url="unix://var/run/docker.sock")
            snapshot_running(client)

            for evt in client.events(decode=True):
                rec = normalize_event(evt)
                if rec:
                    append_event(rec)
        except Exception as exc:
            append_event({
                "service_name": "obs-event-collector",
                "event_type": "collector_error",
                "event_time": now_utc(),
                "container_id": "",
                "details": {"error": str(exc)},
            })
            time.sleep(5)

if __name__ == "__main__":
    main()
