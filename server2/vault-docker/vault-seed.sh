#!/bin/bash
# ==============================
# Vault Secret Seeder
# Data Platform — All Services
# Run this after every vault container restart
# ==============================

VAULT_ADDR="http://10.155.38.155:8200"
VAULT_TOKEN="root"
BASE="secret/data"

echo "🔐 Seeding secrets into Vault at $VAULT_ADDR"
echo ""

seed() {
  local PATH_=$1
  local DATA=$2
  local RESP=$(curl -s -o /dev/null -w "%{http_code}" \
    --header "X-Vault-Token: $VAULT_TOKEN" \
    --header "Content-Type: application/json" \
    --request POST \
    --data "{\"data\": $DATA}" \
    "$VAULT_ADDR/v1/$BASE/$PATH_")
  if [ "$RESP" == "200" ] || [ "$RESP" == "204" ]; then
    echo "  ✅  secret/$PATH_"
  else
    echo "  ❌  secret/$PATH_ (HTTP $RESP)"
  fi
}

# ==============================
# Keycloak  — Server 1 (10.155.38.139)
# ==============================
echo "▶ Keycloak"
seed "keycloak" '{
  "server":          "https://10.155.38.139:8443",
  "realm":           "ckuens-platform",
  "client_id":       "data-platform-ui",
  "client_secret":   "5BfPmCrKteVEo6ZhqscJymaX3cjJPrGf",
  "redirect_uri":    "http://10.155.38.139:8501",
  "admin_url":       "http://10.155.38.139:8090",
  "admin_username":  "dataplatform",
  "admin_password":  "Dataplatform@123",
  "postgres_db":     "keycloak",
  "postgres_user":   "keycloak",
  "postgres_password": "s9O0JjWiXoSe6qYbC3wP"
}'

# ==============================
# PostgreSQL — Server 2 (10.155.38.155)
# ==============================
echo "▶ PostgreSQL"
seed "postgresql" '{
  "host":      "10.155.38.155",
  "port":      "5432",
  "database":  "mydb",
  "username":  "dataplatform",
  "password":  "Dataplatform@123",
  "jdbc_url":  "jdbc:postgresql://10.155.38.155:5432/mydb"
}'

# ==============================
# MinIO — Server 2 (10.155.38.155)
# ==============================
echo "▶ MinIO"
seed "minio" '{
  "console_url":  "http://10.155.38.155:9001",
  "endpoint":     "http://10.155.38.155:9000",
  "access_key":   "dataplatform",
  "secret_key":   "Dataplatform@123"
}'

# ==============================
# Hive Metastore — Server 2 (10.155.38.155)
# ==============================
echo "▶ Hive Metastore"
seed "hive" '{
  "thrift_uri":    "thrift://10.155.38.155:9083",
  "db_username":   "dataplatform",
  "db_password":   "Dataplatform@123",
  "backend_db_url":"jdbc:postgresql://host.docker.internal:5432/mydb"
}'

# ==============================
# Kafka — Server 3 (10.155.38.206)
# ==============================
echo "▶ Kafka"
seed "kafka" '{
  "bootstrap_server":  "10.155.38.206:9092",
  "internal_broker":   "broker:29092",
  "schema_registry":   "http://10.155.38.206:8181",
  "rest_proxy":        "http://10.155.38.206:8082",
  "connect_api":       "http://10.155.38.206:8083",
  "control_center":    "http://10.155.38.206:9021"
}'

# ==============================
# Airbyte — Server 3 (10.155.38.206)
# ==============================
echo "▶ Airbyte"
seed "airbyte" '{
  "ui_url":       "http://10.155.38.206:8000",
  "api_url":      "http://10.155.38.206:8001",
  "username":     "dataplatform",
  "password":     "Dataplatform@123",
  "internal_db_user": "docker",
  "internal_db_password": "docker"
}'

# ==============================
# Spark — Server 3 (10.155.38.206)
# ==============================
echo "▶ Spark"
seed "spark" '{
  "master_url":    "spark://10.155.38.206:7077",
  "master_ui":     "http://10.155.38.206:8080",
  "rest_api":      "http://10.155.38.206:6066",
  "connect_grpc":  "10.155.38.206:15002",
  "custom_api":    "http://10.155.38.206:9003",
  "s3a_access_key":"minioadmin",
  "s3a_secret_key":"minioadmin123",
  "s3a_endpoint":  "http://10.80.211.139:9000"
}'

# ==============================
# Trino — Server 3 (10.155.38.206)
# ==============================
echo "▶ Trino"
seed "trino" '{
  "ui_url":   "http://10.155.38.206:8090",
  "jdbc_url": "jdbc:trino://10.155.38.206:8090"
}'

# ==============================
# Ollama — Server 3 (10.155.38.206)
# ==============================
echo "▶ Ollama"
seed "ollama" '{
  "api_url":      "http://10.155.38.206:11434",
  "base_url":     "http://10.155.38.206:11434",
  "default_model":"llama3.2:1b"
}'

# ==============================
# Airflow — Server 1 (10.155.38.139)
# ==============================
echo "▶ Airflow"
seed "airflow" '{
  "ui_url":       "http://10.155.38.139:8080",
  "api_url":      "http://10.155.38.139:8080/api/v2",
  "username":     "dataplatform",
  "password":     "Dataplatform@123",
  "fernet_key":   "9LyFjl9Hdo0tqMO97AI3ilsPumxykD8DiqnmYutCdiU=",
  "celery_broker":"redis://10.155.38.139:6379/0",
  "postgres_url": "postgresql+psycopg2://airflow:airflow@10.155.38.139/airflow"
}'

# ==============================
# FastAPI — Server 1 (10.155.38.139)
# ==============================
echo "▶ FastAPI"
seed "fastapi" '{
  "base_url":      "http://10.155.38.139:8000",
  "health_url":    "http://10.155.38.139:8000/health",
  "minio_access":  "admin",
  "minio_secret":  "admin12345",
  "minio_url":     "http://10.155.38.139:9000",
  "postgres_host": "10.155.38.139",
  "postgres_db":   "feature_db",
  "postgres_user": "dataplatform",
  "postgres_password": "Dataplatform@123"
}'

# ==============================
# Feast — Server 1 (10.155.38.139)
# ==============================
echo "▶ Feast"
seed "feast" '{
  "feature_server":   "http://10.155.38.139:6566",
  "registry_server":  "http://10.155.38.139:6572",
  "postgres_user":    "dataplatform",
  "postgres_password":"Dataplatform@123",
  "registry_db":      "feast_registry"
}'

# ==============================
# MLflow — Server 1 (10.155.38.139)
# ==============================
echo "▶ MLflow"
seed "mlflow" '{
  "ui_url":         "http://10.155.38.139:5000",
  "api_url":        "http://10.155.38.139:5000/api/2.0/mlflow",
  "minio_access":   "dataplatform",
  "minio_secret":   "Dataplatform@123",
  "artifact_bucket":"mlflow-artifacts",
  "postgres_url":   "postgresql+psycopg2://airflow:airflow@10.155.38.139:5432/airflow"
}'

# ==============================
# OpenLineage / Marquez — Server 1 (10.155.38.139)
# ==============================
echo "▶ OpenLineage / Marquez"
seed "openlineage" '{
  "marquez_ui":       "http://10.155.38.139:3000",
  "marquez_api":      "http://10.155.38.139:5000",
  "lineage_endpoint": "http://10.155.38.139:5000/api/v1/lineage",
  "admin_url":        "http://10.155.38.139:5001/healthcheck",
  "postgres_user":    "airflow",
  "postgres_password":"airflow",
  "postgres_root_password": "ZycDOFHWBhp4510YTLMd"
}'

# ==============================
# OpenMetadata — Server 1 (10.155.38.139)
# ==============================
echo "▶ OpenMetadata"
seed "openmetadata" '{
  "ui_url":            "http://10.155.38.139:8585",
  "api_url":           "http://10.155.38.139:8585/api/v1",
  "admin_username":    "admin",
  "admin_password":    "admin",
  "elasticsearch_url": "http://10.155.38.139:9200",
  "postgres_db":       "openmetadata_db",
  "postgres_user":     "openmetadata_user",
  "postgres_password": "openmetadata_password",
  "fernet_key":        "tNx65XKV/YGQx8YHwWpgO0hxFV+63x0WOiQA2qkeLAw="
}'

# ==============================
# Shared Platform Credentials
# ==============================
echo "▶ Shared Credentials"
seed "platform" '{
  "username": "dataplatform",
  "password": "Dataplatform@123"
}'

echo ""
echo "✅ Done! All secrets seeded."
echo "🌐 View at: http://10.155.38.155:8200/ui/vault/secrets/secret/list"
