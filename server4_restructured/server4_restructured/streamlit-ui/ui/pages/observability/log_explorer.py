import streamlit as st
import requests
from ui.config import LOKI_BASE_URL, OBS_AI_API_URL


def page_log_explorer():
    st.title("Log Explorer")
    st.caption(f"Loki: {LOKI_BASE_URL}  |  OBS AI: {OBS_AI_API_URL}")

    col1, col2 = st.columns([2, 1])
    with col1:
        logql = st.text_area("LogQL query", '{service_name=~".+"} |= ""', height=80)
    with col2:
        limit = st.number_input("Limit", 50, 1000, 100)
        direction = st.selectbox("Direction", ["backward", "forward"])

    if st.button("Run Query", type="primary"):
        try:
            r = requests.get(
                f"{LOKI_BASE_URL}/loki/api/v1/query_range",
                params={"query": logql, "limit": limit, "direction": direction},
                timeout=10,
            )
            if r.ok:
                result = r.json()
                streams = result.get("data", {}).get("result", [])
                for stream in streams[:20]:
                    labels = stream.get("stream", {})
                    st.markdown(f"**{labels}**")
                    for ts, line in stream.get("values", [])[:20]:
                        st.text(f"{ts}  {line}")
            else:
                st.error(f"Loki error: {r.text}")
        except Exception as e:
            st.error(f"Cannot reach Loki: {e}")

    st.divider()
    st.subheader("🤖 Ask OBS AI")
    question = st.text_input("Ask about your logs", "What errors occurred in the last hour?")
    if st.button("Ask AI"):
        try:
            r = requests.post(
                f"{OBS_AI_API_URL}/query",
                json={"question": question},
                timeout=30,
            )
            if r.ok:
                st.markdown(r.json().get("answer", "No answer returned."))
            else:
                st.error(f"OBS AI error: {r.text}")
        except Exception as e:
            st.error(f"Cannot reach OBS AI: {e}")
