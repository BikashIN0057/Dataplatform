from confluent_kafka.admin import AdminClient, NewTopic

KAFKA_BOOTSTRAP = "10.155.38.64:9092"   # your Kafka laptop IP:port

admin = AdminClient({"bootstrap.servers": KAFKA_BOOTSTRAP})

def create_topic_if_not_exists(topic: str, partitions: int = 3, replication: int = 1):
    md = admin.list_topics(timeout=10)

    if topic in md.topics and md.topics[topic].error is None:
        return {"topic": topic, "status": "EXISTS"}

    new_topic = NewTopic(topic=topic, num_partitions=partitions, replication_factor=replication)
    fs = admin.create_topics([new_topic])

    try:
        fs[topic].result()  # wait result
        return {"topic": topic, "status": "CREATED"}
    except Exception as e:
        return {"topic": topic, "status": "ERROR", "error": str(e)}

