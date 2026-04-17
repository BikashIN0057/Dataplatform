import json
import os

import requests
import streamlit as st

st.set_page_config(page_title="Remediation Agent", page_icon="🛠️", layout="wide")

API_URL = os.getenv("REMEDIATION_API_URL", "http://127.0.0.1:8808")
TOKEN = os.getenv("REMEDIATION_SHARED_TOKEN", "")

try:
    API_URL = st.secrets.get("REMEDIATION_API_URL", API_URL)
    TOKEN = st.secrets.get("REMEDIATION_SHARED_TOKEN", TOKEN)
except Exception:
    pass


def api(method: str, path: str, payload=None):
    headers = {"X-Remediation-Token": TOKEN}
    url = f"{API_URL}{path}"
    if payload is None:
        r = requests.request(method, url, headers=headers, timeout=120)
    else:
        r = requests.request(method, url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()


st.title("🛠️ Remediation Agent")

if not TOKEN:
    st.error("REMEDIATION_SHARED_TOKEN not found in environment or Streamlit secrets.")
    st.stop()

left, right = st.columns(2)

with left:
    st.subheader("Create Agent Request")

    service = st.text_input("Service", value=st.session_state.get("selected_service", "grafana"))
    runtime = st.selectbox("Runtime", ["systemd", "docker", "docker-compose"])
    issue_type = st.selectbox("Issue Type", ["unhealthy", "down", "crash_loop", "dependency_timeout"])
    node = st.text_input("Node", value="local")
    evidence_text = st.text_area(
        "Evidence JSON",
        value=json.dumps(
            {
                "source": "remediation_page",
                "service_name": service,
                "container_name": service,
                "compose_service": service,
            },
            indent=2,
        ),
        height=180,
    )

    if st.button("Create Agent Request", use_container_width=True):
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
    st.subheader("Admin Approval / Execution")

    incident_id = st.text_input("Incident ID", value=st.session_state.get("incident_id", ""))
    approved_by = st.text_input("Approved By", value="admin")

    c1, c2, c3 = st.columns(3)

    if c1.button("Refresh Status", use_container_width=True):
        try:
            if not incident_id:
                st.warning("Enter or create an incident first.")
            else:
                resp = api("GET", f"/incidents/{incident_id}")
                st.session_state["incident_result"] = resp
                st.json(resp)
        except Exception as e:
            st.exception(e)

    if c2.button("Dry Run", use_container_width=True):
        try:
            if not incident_id:
                st.warning("Enter or create an incident first.")
            else:
                resp = api(
                    "POST",
                    f"/incidents/{incident_id}/approve",
                    {"approved_by": approved_by, "dry_run": True},
                )
                st.session_state["incident_result"] = resp
                st.json(resp)
        except Exception as e:
            st.exception(e)

    if c3.button("Admin Approve and Execute", use_container_width=True):
        try:
            if not incident_id:
                st.warning("Enter or create an incident first.")
            else:
                resp = api(
                    "POST",
                    f"/incidents/{incident_id}/approve",
                    {"approved_by": approved_by, "dry_run": False},
                )
                st.session_state["incident_result"] = resp
                st.json(resp)
        except Exception as e:
            st.exception(e)

if st.session_state.get("incident_result"):
    st.markdown("### Latest Agent Result")
    st.json(st.session_state["incident_result"])

st.divider()
st.subheader("Recent Agent Requests")

try:
    incidents = api("GET", "/incidents")
    if not incidents:
        st.info("No incidents yet.")
    for inc in incidents:
        label = f"{inc['created_at']} | {inc['service']} | {inc['runtime']} | {inc['status']} | {inc['id']}"
        with st.expander(label):
            st.json(inc)
except Exception as e:
    st.exception(e)
