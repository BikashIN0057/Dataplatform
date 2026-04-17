import streamlit as st
from ui.config import (
    GRAFANA_BASE_URL, GRAFANA_KAFKA_DASH_URL, GRAFANA_MINIO_DASH_URL,
    GRAFANA_PROMETHEUS_DASH, GRAFANA_GRAFANA_DASH,
    GRAFANA_AIRFLOW_DASH, GRAFANA_SPARK_DASH, GRAFANA_TRINO_DASH,
    GRAFANA_VAULT_DASH, GRAFANA_KEYCLOAK_DASH,
    PROMETHEUS_BASE_URL, LOKI_BASE_URL, ALLOY_UI_URL,
)


def page_dashboards():
    st.title("Observability Dashboards")
    dashboards = [
        ("📊 Kafka Monitoring",    GRAFANA_KAFKA_DASH_URL,    "Kafka topic & consumer metrics"),
        ("🪣 MinIO Dashboard",     GRAFANA_MINIO_DASH_URL,    "Object storage metrics"),
        ("📈 Prometheus Overview",  GRAFANA_PROMETHEUS_DASH,   "Prometheus 2.0 overview"),
        ("📉 Grafana Metrics",     GRAFANA_GRAFANA_DASH,      "Grafana self-metrics"),
        ("🌀 Airflow",             GRAFANA_AIRFLOW_DASH,      "Airflow pipeline metrics"),
        ("⚡ Spark",               GRAFANA_SPARK_DASH,        "Spark job metrics"),
        ("🔍 Trino",               GRAFANA_TRINO_DASH,        "Trino query metrics"),
        ("🔐 Vault",               GRAFANA_VAULT_DASH,        "Vault secret metrics"),
        ("🔑 Keycloak",            GRAFANA_KEYCLOAK_DASH,     "Keycloak auth metrics"),
        ("🏠 Grafana Home",        GRAFANA_BASE_URL,          "All dashboards"),
        ("📡 Prometheus UI",       PROMETHEUS_BASE_URL,       "PromQL query & targets"),
        ("📝 Loki API",            LOKI_BASE_URL,             "Log aggregation endpoint"),
        ("🔀 Alloy Pipeline",      ALLOY_UI_URL,              "Telemetry pipeline UI"),
    ]
    cols = st.columns(2)
    for i, (name, url, desc) in enumerate(dashboards):
        with cols[i % 2]:
            st.markdown(f"### [{name}]({url})")
            st.caption(desc)
            st.markdown(f"`{url}`")
            st.markdown("---")
