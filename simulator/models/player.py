from __future__ import annotations

import random
from enum import Enum
from typing import Optional
from uuid import uuid4

from faker import Faker
from pydantic import BaseModel, Field


fake = Faker()


class Platform(str, Enum):
    IOS = "IOS"
    ANDROID = "ANDROID"
    PC = "PC"


class PlayerSegment(str, Enum):
    WHALE = "WHALE"
    DOLPHIN = "DOLPHIN"
    MINNOW = "MINNOW"
    FREE_TO_PLAY = "FREE_TO_PLAY"


class Player(BaseModel):
    player_id: str = Field(default_factory=lambda: str(uuid4()))
    username: str
    platform: Platform
    account_age_days: int
    trophy_count: int
    arena_level: int
    total_spend_usd: float
    is_pass_royale_subscriber: bool
    clan_id: Optional[str]
    player_segment: PlayerSegment


class PlayerFactory:
    @staticmethod
    def _sample_platform() -> Platform:
        return random.choices(
            [Platform.IOS, Platform.ANDROID, Platform.PC],
            weights=[45, 45, 10],
            k=1,
        )[0]

    @staticmethod
    def _segment_from_spend(total_spend: float) -> PlayerSegment:
        if total_spend > 500:
            return PlayerSegment.WHALE
        if total_spend >= 50:
            return PlayerSegment.DOLPHIN
        if total_spend >= 1:
            return PlayerSegment.MINNOW
        return PlayerSegment.FREE_TO_PLAY

    @staticmethod
    def _sample_spend() -> float:
        roll = random.random()
        if roll < 0.75:
            return 0.0
        if roll < 0.90:
            return round(random.uniform(1, 50), 2)
        if roll < 0.98:
            return round(random.uniform(50, 500), 2)
        return round(random.uniform(500, 2500), 2)

    @staticmethod
    def _arena_from_trophies(trophies: int) -> int:
        if trophies <= 300:
            return 1
        arena = 1 + (trophies // 400)
        return max(1, min(20, arena))

    @classmethod
    def create(cls) -> Player:
        spend = cls._sample_spend()
        trophies = random.randint(0, 8000)
        return Player(
            username=fake.user_name(),
            platform=cls._sample_platform(),
            account_age_days=random.randint(1, 1500),
            trophy_count=trophies,
            arena_level=cls._arena_from_trophies(trophies),
            total_spend_usd=spend,
            is_pass_royale_subscriber=random.random() < 0.08,
            clan_id=str(uuid4()) if random.random() < 0.70 else None,
            player_segment=cls._segment_from_spend(spend),
        )


def generate_player_pool(num_players: int) -> list[Player]:
    return [PlayerFactory.create() for _ in range(num_players)]
