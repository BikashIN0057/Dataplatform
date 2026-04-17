import streamlit as st
from ui.services.loki import query_range
from ui.services.obs_ai import ask
from ui.config import LOKI_BASE_URL, OBS_AI_API_URL


def page_log_explorer():
    st.title("Log Explorer")
    st.caption(f"Loki: {LOKI_BASE_URL}  ·  OBS AI: {OBS_AI_API_URL}")

    c1, c2 = st.columns([2, 1])
    with c1:
        logql = st.text_area("LogQL query", '{service_name=~".+"} |= ""', height=80)
    with c2:
        limit = st.number_input("Limit", 50, 1000, 100)
        direction = st.selectbox("Direction", ["backward", "forward"])

    if st.button("Run Query", type="primary"):
        result = query_range(logql, int(limit), direction)
        if "error" in result:
            st.error(result["error"])
        else:
            streams = result.get("data", {}).get("result", [])
            if not streams:
                st.info("No results.")
            for stream in streams[:20]:
                st.markdown(f"**{stream.get('stream', {})}**")
                for ts, line in stream.get("values", [])[:20]:
                    st.text(f"{ts}  {line}")

    st.divider()
    st.subheader("🤖 Ask OBS AI")
    question = st.text_input("Ask about your logs", "What errors occurred in the last hour?")
    if st.button("Ask AI"):
        with st.spinner("Thinking..."):
            answer = ask(question)
        st.markdown(answer)
