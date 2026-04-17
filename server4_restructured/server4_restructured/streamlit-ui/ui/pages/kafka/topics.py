import streamlit as st
import requests
from ui.config import KAFKA_API_BASE_URL


def page_kafka_topics():
    st.title("Kafka Topics")
    st.caption(f"Kafka API: {KAFKA_API_BASE_URL}")

    # List topics
    st.subheader("All Topics")
    try:
        r = requests.get(f"{KAFKA_API_BASE_URL}/topics", timeout=8)
        topics = r.json() if r.ok else []
        if topics:
            for t in topics:
                st.code(str(t))
        else:
            st.info("No topics found or Kafka API unreachable.")
    except Exception as e:
        st.error(f"Cannot reach Kafka API: {e}")

    st.divider()

    # Create topic
    st.subheader("Create Topic")
    col1, col2, col3 = st.columns(3)
    with col1:
        topic_name = st.text_input("Topic name", "my.new.topic")
    with col2:
        partitions = st.number_input("Partitions", min_value=1, value=3)
    with col3:
        replication = st.number_input("Replication factor", min_value=1, value=1)

    if st.button("Create Topic", type="primary"):
        try:
            r = requests.post(
                f"{KAFKA_API_BASE_URL}/topics",
                json={"topic": topic_name, "partitions": int(partitions), "replication": int(replication)},
                timeout=10,
            )
            if r.ok:
                st.success(f"Topic `{topic_name}` created successfully.")
            else:
                st.error(f"Error: {r.text}")
        except Exception as e:
            st.error(f"Cannot reach Kafka API: {e}")
