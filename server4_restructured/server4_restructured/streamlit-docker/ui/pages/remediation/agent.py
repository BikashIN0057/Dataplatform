import streamlit as st
import pandas as pd
from ui.services.remediation import list_pending, approve_action, reject_action, trigger_remediation
from ui.config import REMEDIATION_API_URL


def page_remediation_agent():
    st.title("Remediation Agent")
    st.caption(f"Remediation API: {REMEDIATION_API_URL}")

    st.subheader("Pending Actions")
    pending = list_pending()
    if pending:
        df = pd.DataFrame(pending)
        st.dataframe(df, use_container_width=True, hide_index=True)
        action_id = st.text_input("Action ID to approve / reject")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Approve", type="primary"):
                r = approve_action(action_id)
                st.success(r["body"]) if r["ok"] else st.error(r["body"])
        with c2:
            if st.button("❌ Reject"):
                r = reject_action(action_id)
                st.success(r["body"]) if r["ok"] else st.error(r["body"])
    else:
        st.success("No pending actions — all clear.")

    st.divider()
    st.subheader("Trigger Manual Remediation")
    service = st.text_input("Service name", "grafana", key="rem_svc")
    if st.button("Trigger Remediation"):
        with st.spinner("Triggering..."):
            r = trigger_remediation(service)
        st.success(r["body"]) if r["ok"] else st.error(r["body"])
