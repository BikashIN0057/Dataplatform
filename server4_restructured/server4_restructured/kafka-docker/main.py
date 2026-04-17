from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from kafka_admin import create_topic_if_not_exists

from confluent_kafka import Producer
import json
import threading
import time

app = FastAPI(title="Kafka Control API")

# ----------------------------------
# CORS (Allow Streamlit UI to call)
# ----------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict later to UI URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------
# Kafka Config
# ----------------------------------
KAFKA_BOOTSTRAP = "10.155.38.64:9092"

producer = Producer({
    "bootstrap.servers": KAFKA_BOOTSTRAP
})

# ----------------------------------
# Streaming Control Store
# ----------------------------------
active_streams = {}   # topic -> thread
stop_flags = {}       # topic -> bool


# ----------------------------------
# Request Models
# ----------------------------------
class TopicRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    partitions: int = Field(3, ge=1, le=100)
    replicationFactor: int = Field(1, ge=1, le=3)


# ----------------------------------
# Streaming Logic
# ----------------------------------
def stream_messages(topic: str):
    stop_flags[topic] = False

    while not stop_flags.get(topic, False):
        message = {
            "event_id": int(time.time()),
            "event_type": "UPSERT",
            "source": "fastapi-stream"
        }

        producer.produce(topic, json.dumps(message))
        producer.flush()
        time.sleep(3)

    # cleanup when stopped
    active_streams.pop(topic, None)
    stop_flags.pop(topic, None)


# ----------------------------------
# APIs
# ----------------------------------

@app.get("/health")
def health():
    return {"status": "UP"}


@app.get("/api/stream/status")
def stream_status():
    return {
        "active_streams": list(active_streams.keys())
    }


@app.post("/api/topics/create-if-not-exists")
def create_topic(req: TopicRequest):
    return create_topic_if_not_exists(
        topic=req.topic.strip(),
        partitions=req.partitions,
        replication=req.replicationFactor
    )


@app.post("/api/stream/start")
def start_stream(req: TopicRequest):

    topic = req.topic.strip()

    # ensure topic exists
    create_topic_if_not_exists(
        topic=topic,
        partitions=req.partitions,
        replication=req.replicationFactor
    )

    # if already streaming
    if topic in active_streams:
        return {
            "topic": topic,
            "status": "ALREADY_STREAMING"
        }

    thread = threading.Thread(target=stream_messages, args=(topic,))
    thread.daemon = True
    thread.start()

    active_streams[topic] = thread

    return {
        "topic": topic,
        "status": "STREAMING_STARTED"
    }


@app.post("/api/stream/stop")
def stop_stream(req: TopicRequest):

    topic = req.topic.strip()

    if topic not in active_streams:
        return {
            "topic": topic,
            "status": "NOT_STREAMING"
        }

    stop_flags[topic] = True

    return {
        "topic": topic,
        "status": "STOPPING"
    }
