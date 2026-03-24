#!/usr/bin/env bash
set -euo pipefail

CONNECT_BASE="http://localhost:8083"
CONNECTOR_NAME="lootstream-snowflake-sink"

if ! curl -fsS "${CONNECT_BASE}/connectors" >/dev/null; then
  echo "Kafka Connect API is not reachable at ${CONNECT_BASE}"
  exit 1
fi

echo "=== Registered connectors ==="
curl -s "${CONNECT_BASE}/connectors" | (jq . 2>/dev/null || cat)

echo "=== Connector status: ${CONNECTOR_NAME} ==="
curl -s "${CONNECT_BASE}/connectors/${CONNECTOR_NAME}/status" | (jq . 2>/dev/null || cat)

echo "=== Consumer group lag: connect-${CONNECTOR_NAME} ==="
docker exec lootstream-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group "connect-${CONNECTOR_NAME}" || true
