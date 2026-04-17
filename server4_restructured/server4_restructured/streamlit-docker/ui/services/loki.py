import requests
from ui.config import LOKI_BASE_URL


def query_range(logql: str, limit: int = 100, direction: str = "backward") -> dict:
    try:
        r = requests.get(
            f"{LOKI_BASE_URL}/loki/api/v1/query_range",
            params={"query": logql, "limit": limit, "direction": direction},
            timeout=10,
        )
        return r.json() if r.ok else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}
