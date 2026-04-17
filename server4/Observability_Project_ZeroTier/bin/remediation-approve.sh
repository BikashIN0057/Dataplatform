#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
set -a
source ./.env.remediation
set +a

INCIDENT_ID="${1:?incident_id required}"
APPROVED_BY="${2:-admin}"
DRY_RUN="${3:-true}"

curl -sS \
  -X POST "${REMEDIATION_API_URL}/incidents/${INCIDENT_ID}/approve" \
  -H "Content-Type: application/json" \
  -H "X-Remediation-Token: ${REMEDIATION_SHARED_TOKEN}" \
  -d "{\"approved_by\":\"${APPROVED_BY}\",\"dry_run\":${DRY_RUN}}"
echo
