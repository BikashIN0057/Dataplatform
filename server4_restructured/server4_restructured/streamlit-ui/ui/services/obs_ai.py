import requests
from ui.config import OBS_AI_API_URL


def ask(question: str) -> str:
    try:
        r = requests.post(f"{OBS_AI_API_URL}/query", json={"question": question}, timeout=30)
        return r.json().get("answer", "No answer returned.") if r.ok else f"Error: {r.text}"
    except Exception as e:
        return f"Cannot reach OBS AI: {e}"
