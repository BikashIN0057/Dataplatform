#!/usr/bin/env bash
set -euo pipefail
QUERY="${1:-{service_name=\"obs-alloy\"}}"
START="${2:-$(date -u -d '6 hours ago' +%FT%TZ)}"
END="${3:-$(date -u +%FT%TZ)}"
export QUERY START END
python3 - <<'PY' > /tmp/obs-ai-archive.json
import json, os
print(json.dumps({
    "query": os.environ["QUERY"],
    "start": os.environ["START"],
    "end": os.environ["END"],
    "limit": 200
}))
PY
curl -sS -X POST http://10.155.38.64:8088/archive \
  -H 'Content-Type: application/json' \
  --data @/tmp/obs-ai-archive.json
echo
