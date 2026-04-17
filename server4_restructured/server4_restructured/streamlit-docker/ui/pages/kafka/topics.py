import streamlit as st
from ui.services.kafka import list_topics, create_topic


def page_kafka_topics():
    st.title("Kafka Topics")

    st.subheader("All Topics")
    topics = list_topics()
    if topics:
        for t in topics:
            st.code(str(t))
    else:
        st.info("No topics found or Kafka API unreachable.")

    st.divider()
    st.subheader("Create Topic")
    c1, c2, c3 = st.columns(3)
    with c1:
        name = st.text_input("Topic name", "my.new.topic")
    with c2:
        partitions = st.number_input("Partitions", min_value=1, value=3)
    with c3:
        replication = st.number_input("Replication factor", min_value=1, value=1)

    if st.button("Create Topic", type="primary"):
        result = create_topic(name, int(partitions), int(replication))
        if result["ok"]:
            st.success(f"Topic `{name}` created.")
        else:
            st.error(f"Error: {result['body']}")
