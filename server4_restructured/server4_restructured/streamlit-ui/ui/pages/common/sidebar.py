import streamlit as st
from datetime import datetime


def sidebar():
    with st.sidebar:
        st.image("https://grafana.com/static/img/logos/grafana_logo.svg", width=140)
        st.markdown("## Observability Console")
        st.caption(f"Server4 · 10.155.38.64")
        st.divider()

        pages = [
            "Home",
            "Health",
            "─── Kafka ───",
            "Kafka Topics",
            "Kafka Logs",
            "─── Observability ───",
            "Dashboards",
            "Log Explorer",
            "─── Remediation ───",
            "Incidents",
            "Remediation Agent",
        ]

        nav_pages = [p for p in pages if not p.startswith("─")]
        labels = pages

        choice = st.radio(
            "Navigate",
            nav_pages,
            index=nav_pages.index(st.session_state.page) if st.session_state.page in nav_pages else 0,
            key="nav_radio",
        )
        st.session_state.page = choice
        st.divider()
        st.caption(datetime.now().strftime("%Y-%m-%d %H:%M"))
