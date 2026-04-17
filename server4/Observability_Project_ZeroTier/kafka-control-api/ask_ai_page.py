import os
import requests
import streamlit as st

OBS_AI_API_URL = os.getenv("OBS_AI_API_URL", "http://10.155.38.64:8088")

SERVICES = [
    "",
    "obs-grafana",
    "obs-prometheus",
    "obs-loki",
    "obs-ollama",
    "kafka-control-api",
    "kafka-streamlit",
    "localhost",
    "obs-log-ai-api",
    "obs-alloy",
]

TIME_RANGES = {
    "Last 15 minutes": "last_15_min",
    "Last 1 hour": "last_1_hour",
    "Last 6 hours": "last_6_hours",
    "Last 24 hours": "last_24_hours",
    "Last 2 days": "last_2_days",
    "Last 7 days": "last_7_days",
}

PROVIDERS = ["auto", "ollama", "openai"]

def page_ask_ai():
    st.title("DevOps Q&A Assistant")
    st.caption("Ask service-related questions for troubleshooting, root cause, incidents, and remedy steps.")

    c1, c2, c3 = st.columns(3)
    with c1:
        service = st.selectbox("Service", SERVICES, index=0)
    with c2:
        time_label = st.selectbox("Time Range", list(TIME_RANGES.keys()), index=4)
    with c3:
        provider = st.selectbox("AI Provider", PROVIDERS, index=0)

    question = st.text_area(
        "Ask your question",
        value="Check last 2 days logs for obs-grafana and give remedy steps accordingly",
        height=120
    )

    if st.button("Ask DevOps AI", type="primary"):
        try:
            payload = {
                "question": question,
                "service_name": service or None,
                "provider": provider,
                "time_range": TIME_RANGES[time_label],
            }
            r = requests.post(f"{OBS_AI_API_URL}/devops/ask", json=payload, timeout=180)
            r.raise_for_status()
            data = r.json()

            st.subheader("Answer")
            st.write(data.get("answer", ""))

            st.subheader("Summary")
            st.write(data.get("summary", ""))

            st.subheader("Root Cause")
            st.write(data.get("root_cause", ""))

            st.subheader("Remedy Steps")
            for i, step in enumerate(data.get("remedy_steps", []), 1):
                st.write(f"{i}. {step}")

            st.subheader("Next Checks")
            for i, step in enumerate(data.get("next_checks", []), 1):
                st.write(f"{i}. {step}")

            if data.get("status"):
                st.subheader("Current Status")
                st.json(data.get("status"))

            if data.get("incidents"):
                st.subheader("Incident History")
                st.json(data.get("incidents"))

            if data.get("evidence"):
                with st.expander("Evidence Logs"):
                    st.json(data.get("evidence"))

            if data.get("patterns"):
                with st.expander("Detected Patterns"):
                    st.json(data.get("patterns"))

            if data.get("runbooks"):
                with st.expander("Matched Runbooks"):
                    st.json(data.get("runbooks"))

            st.caption(f"Provider requested: {data.get('selected_provider', provider)} | Provider used: {data.get('provider_used', 'unknown')}")
            st.caption(f"Confidence: {data.get('confidence', 'unknown')}")

            if data.get("llm_error"):
                st.warning(f"LLM fallback was used: {data.get('llm_error')}")

        except Exception as exc:
            st.error(f"Ask failed: {exc}")
