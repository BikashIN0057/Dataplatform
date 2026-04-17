import streamlit as st
import pandas as pd
from ui.services.remediation import list_incidents, create_incident
from ui.config import REMEDIATION_API_URL


def page_incidents():
    st.title("Remediation Incidents")
    st.caption(f"Remediation API: {REMEDIATION_API_URL}")

    incidents = list_incidents()
    if incidents:
        st.dataframe(pd.DataFrame(incidents), use_container_width=True, hide_index=True)
    else:
        st.info("No incidents found or API unreachable.")

    st.divider()
    st.subheader("Create Incident")
    c1, c2 = st.columns(2)
    with c1:
        service = st.text_input("Service", "grafana")
        issue = st.text_input("Issue", "unhealthy")
    with c2:
        severity = st.selectbox("Severity", ["low", "medium", "high", "critical"])
        description = st.text_area("Description", "Service is not responding to health checks.")

    if st.button("Create Incident", type="primary"):
        result = create_incident(service, issue, severity, description)
        if result["ok"]:
            st.success(f"Incident created: {result['body']}")
        else:
            st.error(f"Error: {result['body']}")
