#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
set -a
source ./.env.remediation
set +a
exec ./.venv/bin/uvicorn remediation_agent.api:app --host 0.0.0.0 --port 8808 --app-dir .
