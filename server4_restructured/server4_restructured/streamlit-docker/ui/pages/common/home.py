import streamlit as st
from ui.config import (
    GRAFANA_BASE_URL, PROMETHEUS_BASE_URL, LOKI_BASE_URL,
    HEALTH_API_URL, ALLOY_UI_URL, KAFKA_API_BASE_URL,
    OBS_AI_API_URL, REMEDIATION_API_URL, SERVER4_IP,
)


def page_home():
    st.title("🖥️ Observability Console — Server4")
    st.caption(f"ZeroTier IP: `{SERVER4_IP}`")
    st.markdown("### Quick Links")
    cols = st.columns(4)
    links = [
        ("📊 Grafana",      GRAFANA_BASE_URL,     "Dashboards & alerting"),
        ("📈 Prometheus",    PROMETHEUS_BASE_URL,  "Metrics & queries"),
        ("📝 Loki",          LOKI_BASE_URL,        "Log aggregation"),
        ("🔀 Alloy",         ALLOY_UI_URL,         "Pipeline UI"),
        ("⚡ Kafka API",     KAFKA_API_BASE_URL,   "Topic control"),
        ("🤖 OBS AI",        OBS_AI_API_URL,       "Log AI assistant"),
        ("🛠️ Remediation",  REMEDIATION_API_URL,  "Auto-remediation"),
        ("❤️ Health API",   HEALTH_API_URL,        "Service health"),
    ]
    for i, (label, url, desc) in enumerate(links):
        with cols[i % 4]:
            st.markdown(f"**[{label}]({url})**")
            st.caption(desc)
    st.divider()
    st.info("Use the sidebar to navigate Kafka, Observability, and Remediation tools.")
