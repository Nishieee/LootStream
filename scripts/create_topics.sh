#!/usr/bin/env bash
set -euo pipefail

BROKER_CONTAINER="lootstream-kafka"
PARTITIONS=3
REPLICATION=1

TOPICS=(
  "game.events.gem_purchases"
  "game.events.card_upgrades"
  "game.events.chest_openings"
  "game.events.player_trades"
)

for topic in "${TOPICS[@]}"; do
  echo "Creating topic: ${topic}"
  docker exec "${BROKER_CONTAINER}" kafka-topics \
    --bootstrap-server localhost:9092 \
    --create \
    --if-not-exists \
    --topic "${topic}" \
    --partitions "${PARTITIONS}" \
    --replication-factor "${REPLICATION}"
done

echo "Topics created."
