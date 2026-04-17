import streamlit as st
import requests
import pandas as pd
from ui.config import HEALTH_API_URL, GRAFANA_DASHBOARDS, ALL_SERVICES


def page_health():
    st.title("Platform Health")
    try:
        resp = requests.get(HEALTH_API_URL, timeout=5)
        services = resp.json().get("services", {})
    except Exception as e:
        st.error(f"Health API not reachable: {e}")
        services = {}

    rows = []
    for key, purpose in ALL_SERVICES.items():
        svc = services.get(key, {})
        status = svc.get("status", "unknown").lower()
        if status == "healthy":
            badge = "<span style='color:limegreen;font-weight:700;'>● Healthy</span>"
        elif status == "unhealthy":
            badge = "<span style='color:crimson;font-weight:700;'>● Unhealthy</span>"
        else:
            badge = "<span style='color:gray;'>● Unknown</span>"
        if key in GRAFANA_DASHBOARDS:
            badge = f'<a href="{GRAFANA_DASHBOARDS[key]}" target="_blank">{badge}</a>'
        rows.append({"Service": key.capitalize(), "Purpose": purpose, "Status": badge})

    df = pd.DataFrame(rows)
    st.markdown("""
    <style>
    .htable{width:100%;border-collapse:collapse;}
    .htable th,.htable td{padding:10px;text-align:left;border-bottom:1px solid #ddd;}
    </style>""", unsafe_allow_html=True)
    st.markdown(df.to_html(classes="htable", escape=False, index=False), unsafe_allow_html=True)
