from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    schema_registry_url: str = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")
    events_per_second: int = int(os.getenv("EVENTS_PER_SECOND", "50"))
    num_players: int = int(os.getenv("NUM_PLAYERS", "1000"))
    simulation_speed: float = float(os.getenv("SIMULATION_SPEED", "1.0"))


settings = Settings()
