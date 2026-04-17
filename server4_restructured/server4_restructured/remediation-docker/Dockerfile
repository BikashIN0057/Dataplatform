FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY remediation_agent/ ./remediation_agent/
RUN pip install --no-cache-dir fastapi uvicorn pyyaml requests aiosqlite
EXPOSE 8808
CMD ["uvicorn", "remediation_agent.api:app", "--host", "0.0.0.0", "--port", "8808"]
