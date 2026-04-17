import streamlit as st
import requests
import pandas as pd
from ui.config import HEALTH_API_URL, GRAFANA_DASHBOARDS, ALL_SERVICES


def page_health():
    st.title("Platform Health")

    try:
        resp = requests.get(HEALTH_API_URL, timeout=5)
        data = resp.json()
        services = data.get("services", {})
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
            url = GRAFANA_DASHBOARDS[key]
            badge = f'<a href="{url}" target="_blank">{badge}</a>'

        rows.append({"Service": key.capitalize(), "Purpose": purpose, "Status": badge})

    df = pd.DataFrame(rows)
    table_html = df.to_html(classes="health-table", escape=False, index=False)
    st.markdown("""
    <style>
    .health-table { width:100%; border-collapse:collapse; }
    .health-table th, .health-table td { padding:10px; text-align:left; border-bottom:1px solid #ddd; }
    </style>""", unsafe_allow_html=True)
    st.markdown(table_html, unsafe_allow_html=True)
