import streamlit as st
from ui.services.kafka import get_messages
from ui.config import GRAFANA_KAFKA_DASH_URL


def page_kafka_logs():
    st.title("Kafka Logs")
    st.markdown(f"📊 [Open Kafka Grafana Dashboard]({GRAFANA_KAFKA_DASH_URL})")

    topic = st.text_input("Topic to tail", "crm.contacts")
    limit = st.slider("Max messages", 10, 200, 50)

    if st.button("Fetch Messages", type="primary"):
        messages = get_messages(topic, limit)
        if messages:
            st.json(messages)
        else:
            st.info("No messages returned or Kafka API unreachable.")
