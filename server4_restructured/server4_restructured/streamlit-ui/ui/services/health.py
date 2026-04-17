import requests
from ui.config import HEALTH_API_URL


def get_health() -> dict:
    """Fetch health data from the Health API. Returns {} on failure."""
    try:
        r = requests.get(HEALTH_API_URL, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}
