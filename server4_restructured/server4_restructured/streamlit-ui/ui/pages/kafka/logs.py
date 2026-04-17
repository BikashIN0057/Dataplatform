import streamlit as st
import requests
from ui.config import KAFKA_API_BASE_URL, GRAFANA_KAFKA_DASH_URL


def page_kafka_logs():
    st.title("Kafka Logs")
    st.markdown(f"📊 [Open Kafka Grafana Dashboard]({GRAFANA_KAFKA_DASH_URL})")

    topic = st.text_input("Topic to tail", "crm.contacts")
    limit = st.slider("Max messages", 10, 200, 50)

    if st.button("Fetch Messages", type="primary"):
        try:
            r = requests.get(
                f"{KAFKA_API_BASE_URL}/topics/{topic}/messages",
                params={"limit": limit},
                timeout=10,
            )
            if r.ok:
                messages = r.json()
                st.json(messages)
            else:
                st.error(f"Error: {r.text}")
        except Exception as e:
            st.error(f"Cannot reach Kafka API: {e}")
