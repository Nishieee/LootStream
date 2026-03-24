#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEY_PATH="${ROOT_DIR}/connect/keys/rsa_key.p8"
TEMPLATE_PATH="${ROOT_DIR}/connect/snowflake-connector.json"
CONNECT_URL="http://localhost:8083/connectors"

if [[ ! -f "${KEY_PATH}" ]]; then
  echo "Missing key file: ${KEY_PATH}"
  exit 1
fi

if [[ ! -f "${ROOT_DIR}/.env" ]]; then
  echo "Missing .env at project root"
  exit 1
fi

set -a
# shellcheck disable=SC1091
source "${ROOT_DIR}/.env"
set +a

required_vars=(
  SNOWFLAKE_ACCOUNT_URL
  SNOWFLAKE_USER
  SNOWFLAKE_ROLE
  SNOWFLAKE_DATABASE
  SNOWFLAKE_SCHEMA
  SNOWFLAKE_WAREHOUSE
)

for v in "${required_vars[@]}"; do
  if [[ -z "${!v:-}" ]]; then
    echo "Missing required env var: ${v}"
    exit 1
  fi
done

SNOWFLAKE_PRIVATE_KEY_CONTENT="$(sed '/BEGIN PRIVATE KEY/d;/END PRIVATE KEY/d' "${KEY_PATH}" | tr -d '\n\r[:space:]')"
if [[ -z "${SNOWFLAKE_PRIVATE_KEY_CONTENT}" ]]; then
  echo "Private key content was empty after normalization"
  exit 1
fi

PAYLOAD="$(
  SNOWFLAKE_PRIVATE_KEY_CONTENT="${SNOWFLAKE_PRIVATE_KEY_CONTENT}" python3 - <<'PY' "${TEMPLATE_PATH}"
import json
import os
import re
import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

pattern = re.compile(r"\$\{([A-Z0-9_]+)\}")

def repl(match):
    key = match.group(1)
    value = os.getenv(key)
    if value is None:
        raise SystemExit(f"Missing template variable: {key}")
    return value

rendered = pattern.sub(repl, text)
obj = json.loads(rendered)
print(json.dumps(obj))
PY
)"

echo "Deploying connector to ${CONNECT_URL}"
response_code="$(curl -s -o /tmp/lootstream_connector_response.json -w "%{http_code}" -X POST "${CONNECT_URL}" -H "Content-Type: application/json" -d "${PAYLOAD}")"

if [[ "${response_code}" != "201" && "${response_code}" != "409" ]]; then
  echo "Connector deployment failed (HTTP ${response_code})"
  cat /tmp/lootstream_connector_response.json
  exit 1
fi

if [[ "${response_code}" == "409" ]]; then
  echo "Connector already exists, attempting config update"
  curl -s -X PUT "${CONNECT_URL}/lootstream-snowflake-sink/config" \
    -H "Content-Type: application/json" \
    -d "$(echo "${PAYLOAD}" | python3 -c 'import json,sys; print(json.dumps(json.load(sys.stdin)["config"]))')" \
    >/tmp/lootstream_connector_update_response.json
fi

echo "Connector deployed. Fetching status..."
sleep 5
curl -s "${CONNECT_URL}/lootstream-snowflake-sink/status" | (jq . 2>/dev/null || cat)
