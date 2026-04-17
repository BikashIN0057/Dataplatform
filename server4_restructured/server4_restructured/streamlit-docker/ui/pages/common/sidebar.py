import streamlit as st
from datetime import datetime


def sidebar():
    with st.sidebar:
        st.markdown("## 🖥️ Observability Console")
        st.caption(f"Server4  ·  10.155.38.64")
        st.divider()

        nav_pages = [
            "Home", "Health",
            "Kafka Topics", "Kafka Logs",
            "Dashboards", "Log Explorer",
            "Incidents", "Remediation Agent",
        ]

        choice = st.radio(
            "Navigate",
            nav_pages,
            index=nav_pages.index(st.session_state.page) if st.session_state.page in nav_pages else 0,
            key="nav_radio",
        )
        st.session_state.page = choice
        st.divider()
        st.caption(datetime.now().strftime("%Y-%m-%d %H:%M"))
