#!/usr/bin/env bash
set -euo pipefail

GRAFANA_URL="http://10.155.38.64:3000"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="admin"
FOLDER_TITLE="Ckuens Observability"

TMP_DIR="$(mktemp -d)"

api() {
  curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
    -H "Content-Type: application/json" \
    -X "$1" \
    "${GRAFANA_URL}$2" \
    ${3:+-d "$3"}
}

create_folder() {
  api GET "/api/folders" > /tmp/folders.json

  FOUND_FOLDER_UID=$(
    python3 - <<EOF
import json
data = json.load(open("/tmp/folders.json"))
for f in data:
    if f["title"] == "$FOLDER_TITLE":
        print(f["uid"])
        raise SystemExit
print("")
EOF
  )

  if [ -z "$FOUND_FOLDER_UID" ]; then
    FOUND_FOLDER_UID=$(
      api POST "/api/folders" "{\"title\":\"$FOLDER_TITLE\"}" | \
      python3 -c 'import sys,json;print(json.load(sys.stdin)["uid"])'
    )
  fi

  echo "$FOUND_FOLDER_UID"
}

PROM_UID=$(
  api GET "/api/datasources" | python3 -c '
import sys, json
for d in json.load(sys.stdin):
    if d["type"] == "prometheus":
        print(d["uid"])
        break
'
)

LOKI_UID=$(
  api GET "/api/datasources" | python3 -c '
import sys, json
for d in json.load(sys.stdin):
    if d["type"] == "loki":
        print(d["uid"])
        break
'
)

FOLDER_UID="$(create_folder)"

echo "Folder: $FOLDER_UID"

generate_dashboard() {
python3 - <<EOF > "$TMP_DIR/$1.json"
import json

def logs(title, expr):
    return {
        "type": "logs",
        "title": title,
        "datasource": {"type": "loki", "uid": "$LOKI_UID"},
        "targets": [{"expr": expr}],
        "gridPos": {"x": 0, "y": 0, "w": 24, "h": 10}
    }

def stat(title, expr, x, y):
    return {
        "type": "stat",
        "title": title,
        "datasource": {"type": "prometheus", "uid": "$PROM_UID"},
        "targets": [{"expr": expr}],
        "gridPos": {"x": x, "y": y, "w": 6, "h": 4}
    }

def ts(title, expr, x, y):
    return {
        "type": "timeseries",
        "title": title,
        "datasource": {"type": "prometheus", "uid": "$PROM_UID"},
        "targets": [{"expr": expr}],
        "gridPos": {"x": x, "y": y, "w": 12, "h": 8}
    }

dashboard = {
    "uid": "$2",
    "title": "Ckuens - $3",
    "time": {"from": "6h", "to": "now"},
    "refresh": "15s",
    "panels": [
        logs("$3 Logs", '{source="server1"} |= "$4"'),

        stat("Up", 'max(up{job="$5"})', 0, 10),
        stat("Uptime", 'time()-process_start_time_seconds{job="$5"}', 6, 10),

        ts("CPU", 'rate(process_cpu_seconds_total{job="$5"}[1m])', 0, 14),
        ts("Memory", 'process_resident_memory_bytes{job="$5"}', 12, 14),

        ts("Net In", 'rate(process_network_receive_bytes_total{job="$5"}[1m])', 0, 22),
        ts("Net Out", 'rate(process_network_transmit_bytes_total{job="$5"}[1m])', 12, 22),

        ts("Requests", 'sum(rate(promhttp_metric_handler_requests_total{job="$5"}[1m]))', 0, 30)
    ]
}

print(json.dumps({
    "dashboard": dashboard,
    "folderUid": "$FOLDER_UID",
    "overwrite": True
}))
EOF
}

# Create dashboards
generate_dashboard airflow ckuens-airflow Airflow airflow airflow
generate_dashboard keycloak ckuens-keycloak Keycloak keycloak keycloak
generate_dashboard spark ckuens-spark Spark spark spark
generate_dashboard prometheus ckuens-prometheus Prometheus prometheus prometheus
generate_dashboard grafana ckuens-grafana Grafana grafana grafana
generate_dashboard minio ckuens-minio Minio minio minio
generate_dashboard kafka ckuens-kafka Kafka kafka kafka
generate_dashboard fastapi svc-fastapi FastAPI fastapi fastapi

# Import
for f in "$TMP_DIR"/*.json; do
  api POST "/api/dashboards/db" "$(cat "$f")" > /dev/null
  echo "Imported $f"
done

echo "Done"
