import json
import os

import requests
import streamlit as st

st.set_page_config(page_title="Remediation Agent", page_icon="🛠️", layout="wide")

API_URL = st.secrets.get("REMEDIATION_API_URL", os.getenv("REMEDIATION_API_URL", "http://127.0.0.1:8808"))
TOKEN = st.secrets.get("REMEDIATION_SHARED_TOKEN", os.getenv("REMEDIATION_SHARED_TOKEN", ""))

def api(method: str, path: str, payload=None):
    headers = {"X-Remediation-Token": TOKEN}
    if payload is None:
        r = requests.request(method, f"{API_URL}{path}", headers=headers, timeout=120)
    else:
        r = requests.request(method, f"{API_URL}{path}", headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()

st.title("🛠️ Remediation Agent")

if not TOKEN:
    st.error("REMEDIATION_SHARED_TOKEN not found in Streamlit secrets or environment.")
    st.stop()

left, right = st.columns([1, 1])

with left:
    st.subheader("Propose Remedy")
    service = st.text_input("Service", value=st.session_state.get("selected_service", "grafana"))
    runtime = st.selectbox("Runtime", ["systemd", "docker", "docker-compose"])
    issue_type = st.selectbox("Issue Type", ["unhealthy", "down", "crash_loop", "dependency_timeout"])
    node = st.text_input("Node", value="local")
    evidence_text = st.text_area(
        "Evidence JSON",
        value='{"source":"logs-page","hint":"service unhealthy"}',
        height=120,
    )

    if st.button("Propose Remedy", use_container_width=True):
        try:
            evidence = json.loads(evidence_text) if evidence_text.strip() else {}
            resp = api(
                "POST",
                "/incidents/propose",
                {
                    "service": service,
                    "runtime": runtime,
                    "issue_type": issue_type,
                    "node": node,
                    "evidence": evidence,
                },
            )
            st.session_state["incident_id"] = resp["incident_id"]
            st.success(f"Incident created: {resp['incident_id']}")
            st.json(resp)
        except Exception as e:
            st.exception(e)

with right:
    st.subheader("Approve / Execute")
    incident_id = st.text_input("Inciden", value=st.session_state.get("incident_id", ""))
    approved_by = st.text_input("Approved By", value="admin")

    c1, c2 = st.columns(2)
    if c1.button("Dry Run", use_container_width=True):
        try:
            resp = api(
                "POST",
                f"/incidents/{incident_id}/approve",
                {"approved_by": approved_by, "dry_run": True},
            )
            st.json(resp)
        except Exception as e:
            st.exception(e)

    if c2.button("Approve and Execute", _container_width=True):
        try:
            resp = api(
                "POST",
                f"/incidents/{incident_id}/approve",
                {"approved_by": approved_by, "dry_run": False},
            )
            st.json(resp)
        except Exception as e:
            st.exception(e)

st.divider()
st.subheader("Recent Incidents")

try:
    incidents = api("GET", "/incidents")
    if not incidents:
        st.info("No incidents yet.")
    for inc in incidents:
        label = f"{inc['created_| {inc['service']} | {inc['runtime']} | {inc['status']} | {inc['id']}"
        with st.expander(label):
            st.json(inc)
except Exception as e:
    st.exception(e)
