#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
set -a
source ./.env.remediation
set +a

SERVICE="${1:?service required}"
RUNTIME="${2:-systemd}"
ISSUE_TYPE="${3:-unhealthy}"
NODE="${4:-local}"

curl -sS \
  -X POST "${REMEDIATION_API_URL}/incidents/propose" \
  -H "Content-Type: application/json" \
  -H "X-Remediation-Token: ${REMEDIATION_SHARED_TOKEN}" \
  -d "{\"service\":\"${SERVICE}\",\"runtime\":\"${RUNTIME}\",\"issue_type\":\"${ISSUE_TYPE}\",\"node\":\"${NODE}\",\"evidence\":{\"source\":\"cli\"}}"
echo
