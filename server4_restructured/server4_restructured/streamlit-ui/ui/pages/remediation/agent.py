import streamlit as st
import requests
import pandas as pd
from ui.config import REMEDIATION_API_URL, REMEDIATION_SHARED_TOKEN


def _headers():
    return {"Authorization": f"Bearer {REMEDIATION_SHARED_TOKEN}"}


def page_remediation_agent():
    st.title("Remediation Agent")
    st.caption(f"Remediation API: {REMEDIATION_API_URL}")

    # Pending actions
    st.subheader("Pending Actions")
    try:
        r = requests.get(f"{REMEDIATION_API_URL}/pending", headers=_headers(), timeout=8)
        if r.ok:
            pending = r.json()
            if pending:
                df = pd.DataFrame(pending)
                st.dataframe(df, use_container_width=True, hide_index=True)

                action_id = st.text_input("Action ID to approve/reject")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve", type="primary"):
                        ra = requests.post(
                            f"{REMEDIATION_API_URL}/approve/{action_id}",
                            headers=_headers(), timeout=10,
                        )
                        st.success(ra.text) if ra.ok else st.error(ra.text)
                with col2:
                    if st.button("❌ Reject"):
                        ra = requests.post(
                            f"{REMEDIATION_API_URL}/reject/{action_id}",
                            headers=_headers(), timeout=10,
                        )
                        st.success(ra.text) if ra.ok else st.error(ra.text)
            else:
                st.success("No pending actions — all clear.")
        else:
            st.error(f"API error: {r.text}")
    except Exception as e:
        st.error(f"Cannot reach Remediation API: {e}")

    st.divider()
    st.subheader("Trigger Manual Remediation")
    service = st.text_input("Service name", "grafana", key="rem_svc")
    if st.button("Trigger Remediation"):
        try:
            r = requests.post(
                f"{REMEDIATION_API_URL}/trigger",
                json={"service": service},
                headers=_headers(),
                timeout=15,
            )
            st.success(r.json()) if r.ok else st.error(r.text)
        except Exception as e:
            st.error(f"Cannot reach Remediation API: {e}")
