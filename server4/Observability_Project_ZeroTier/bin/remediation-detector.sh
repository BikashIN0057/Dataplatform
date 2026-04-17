#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
set -a
source ./.env.remediation
set +a
exec ./.venv/bin/python -m remediation_agent.detector
