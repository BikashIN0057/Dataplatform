import requests
from ui.config import KAFKA_API_BASE_URL


def list_topics() -> list:
    try:
        r = requests.get(f"{KAFKA_API_BASE_URL}/topics", timeout=8)
        return r.json() if r.ok else []
    except Exception:
        return []


def create_topic(topic: str, partitions: int = 3, replication: int = 1) -> dict:
    try:
        r = requests.post(
            f"{KAFKA_API_BASE_URL}/topics",
            json={"topic": topic, "partitions": partitions, "replication": replication},
            timeout=10,
        )
        return {"ok": r.ok, "body": r.json() if r.ok else r.text}
    except Exception as e:
        return {"ok": False, "body": str(e)}


def get_messages(topic: str, limit: int = 100) -> list:
    try:
        r = requests.get(
            f"{KAFKA_API_BASE_URL}/topics/{topic}/messages",
            params={"limit": limit},
            timeout=10,
        )
        return r.json() if r.ok else []
    except Exception:
        return []
