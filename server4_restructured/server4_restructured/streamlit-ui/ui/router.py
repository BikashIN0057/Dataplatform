import streamlit as st
from ui.pages.common.sidebar import sidebar
from ui.pages.common.home import page_home
from ui.pages.common.health import page_health
from ui.pages.kafka.topics import page_kafka_topics
from ui.pages.kafka.logs import page_kafka_logs
from ui.pages.observability.dashboards import page_dashboards
from ui.pages.observability.log_explorer import page_log_explorer
from ui.pages.remediation.incidents import page_incidents
from ui.pages.remediation.agent import page_remediation_agent
from ui.runtime import handle_deferred_rerun


def router():
    sidebar()
    page = st.session_state.page

    if page == "Home":
        page_home()
    elif page == "Health":
        page_health()
    elif page == "Kafka Topics":
        page_kafka_topics()
    elif page == "Kafka Logs":
        page_kafka_logs()
    elif page == "Dashboards":
        page_dashboards()
    elif page == "Log Explorer":
        page_log_explorer()
    elif page == "Incidents":
        page_incidents()
    elif page == "Remediation Agent":
        page_remediation_agent()

    handle_deferred_rerun()
