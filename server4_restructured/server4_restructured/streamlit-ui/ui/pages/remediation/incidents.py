import streamlit as st
import requests
import pandas as pd
from ui.config import REMEDIATION_API_URL, REMEDIATION_SHARED_TOKEN


def _headers():
    return {"Authorization": f"Bearer {REMEDIATION_SHARED_TOKEN}"}


def page_incidents():
    st.title("Remediation Incidents")
    st.caption(f"Remediation API: {REMEDIATION_API_URL}")

    try:
        r = requests.get(f"{REMEDIATION_API_URL}/incidents", headers=_headers(), timeout=8)
        if r.ok:
            incidents = r.json()
            if incidents:
                df = pd.DataFrame(incidents)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No incidents found.")
        else:
            st.error(f"API error: {r.text}")
    except Exception as e:
        st.error(f"Cannot reach Remediation API: {e}")

    st.divider()
    st.subheader("Create Incident")
    col1, col2 = st.columns(2)
    with col1:
        service = st.text_input("Service", "grafana")
        issue = st.text_input("Issue", "unhealthy")
    with col2:
        severity = st.selectbox("Severity", ["low", "medium", "high", "critical"])
        description = st.text_area("Description", "Service is not responding to health checks.")

    if st.button("Create Incident", type="primary"):
        try:
            payload = {"service": service, "issue": issue, "severity": severity, "description": description}
            r = requests.post(f"{REMEDIATION_API_URL}/incidents", json=payload, headers=_headers(), timeout=10)
            if r.ok:
                st.success(f"Incident created: {r.json()}")
            else:
                st.error(f"Error: {r.text}")
        except Exception as e:
            st.error(f"Cannot reach Remediation API: {e}")
