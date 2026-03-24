from __future__ import annotations

import json
import logging
from pathlib import Path
from queue import Queue

from confluent_kafka import KafkaError
from confluent_kafka.avro import CachedSchemaRegistryClient, loads
from confluent_kafka.avro.serializer import SerializerError
from confluent_kafka.avro import AvroProducer

from simulator.config import settings


logger = logging.getLogger(__name__)


TOPIC_SCHEMA_MAP = {
    "game.events.gem_purchases": "gem_purchase.avsc",
    "game.events.card_upgrades": "card_upgrade.avsc",
    "game.events.chest_openings": "chest_opening.avsc",
    "game.events.player_trades": "player_trade.avsc",
}


class EventProducer:
    def __init__(self) -> None:
        schema_registry = CachedSchemaRegistryClient({"url": settings.schema_registry_url})
        self._key_schema = loads('"string"')
        self.producer = AvroProducer(
            {
                "bootstrap.servers": settings.kafka_bootstrap_servers,
                "queue.buffering.max.messages": 100000,
                "queue.buffering.max.ms": 100,
                "linger.ms": 10,
                "acks": "1",
            },
            schema_registry=schema_registry,
        )
        self._schema_cache = self._load_and_register_schemas(schema_registry)
        self.delivery_failures: Queue[str] = Queue()

    def _load_and_register_schemas(self, schema_registry: CachedSchemaRegistryClient) -> dict[str, object]:
        schema_dir = Path(__file__).resolve().parent.parent / "schemas"
        schema_map: dict[str, object] = {}
        for topic, schema_file in TOPIC_SCHEMA_MAP.items():
            schema_path = schema_dir / schema_file
            schema_str = schema_path.read_text(encoding="utf-8")
            schema = loads(schema_str)
            subject = f"{topic}-value"
            schema_registry.register(subject, schema)
            schema_map[topic] = schema
            logger.info("Registered schema subject=%s", subject)
        return schema_map

    def _delivery_callback(self, err, msg) -> None:
        if err is not None:
            self.delivery_failures.put(str(err))
            logger.error("Delivery failed: %s", err)
            return
        if msg is not None and msg.error() not in (None, KafkaError.NO_ERROR):
            self.delivery_failures.put(str(msg.error()))
            logger.error("Message error: %s", msg.error())

    def produce(self, topic: str, event) -> None:
        try:
            self.producer.produce(
                topic=topic,
                key=event.to_kafka_key().decode("utf-8"),
                key_schema=self._key_schema,
                value=event.to_dict(),
                value_schema=self._schema_cache[topic],
                callback=self._delivery_callback,
            )
            self.producer.poll(0)
        except BufferError:
            logger.warning("Producer queue full, flushing before retry")
            self.producer.flush(5)
            self.producer.produce(
                topic=topic,
                key=event.to_kafka_key().decode("utf-8"),
                key_schema=self._key_schema,
                value=event.to_dict(),
                value_schema=self._schema_cache[topic],
                callback=self._delivery_callback,
            )
            self.producer.poll(0)
        except (SerializerError, json.JSONDecodeError) as exc:
            logger.exception("Serialization error: %s", exc)
            raise

    def flush(self, timeout: int = 10) -> None:
        self.producer.flush(timeout)
