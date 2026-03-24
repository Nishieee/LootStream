from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Platform(str, Enum):
    IOS = "IOS"
    ANDROID = "ANDROID"
    PC = "PC"


class CardRarity(str, Enum):
    COMMON = "COMMON"
    RARE = "RARE"
    EPIC = "EPIC"
    LEGENDARY = "LEGENDARY"
    CHAMPION = "CHAMPION"


class PaymentMethod(str, Enum):
    APPLE_IAP = "APPLE_IAP"
    GOOGLE_PLAY = "GOOGLE_PLAY"
    CREDIT_CARD = "CREDIT_CARD"
    PAYPAL = "PAYPAL"


class UpgradeSource(str, Enum):
    MANUAL = "MANUAL"
    AUTO_UPGRADE = "AUTO_UPGRADE"
    MAGIC_ITEM = "MAGIC_ITEM"


class ChestType(str, Enum):
    SILVER = "SILVER"
    GOLD = "GOLD"
    GIANT = "GIANT"
    MAGICAL = "MAGICAL"
    LEGENDARY = "LEGENDARY"
    MEGA_LIGHTNING = "MEGA_LIGHTNING"
    ROYAL_WILD = "ROYAL_WILD"


class ChestSource(str, Enum):
    BATTLE_REWARD = "BATTLE_REWARD"
    SHOP_PURCHASE = "SHOP_PURCHASE"
    CHALLENGE_REWARD = "CHALLENGE_REWARD"
    PASS_ROYALE = "PASS_ROYALE"
    CLAN_WAR = "CLAN_WAR"


class TradeType(str, Enum):
    CLAN_TRADE = "CLAN_TRADE"
    GLOBAL_TRADE = "GLOBAL_TRADE"


class TradeStatus(str, Enum):
    POSTED = "POSTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class EventBase(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_timestamp: int = Field(default_factory=lambda: int(datetime.now(timezone.utc).timestamp() * 1000))
    player_id: str
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    platform: Platform
    app_version: str

    def to_kafka_key(self) -> bytes:
        return self.player_id.encode("utf-8")

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")


class GemPurchaseEvent(EventBase):
    gem_package_id: str
    gem_amount: int
    usd_price: float
    payment_method: PaymentMethod
    is_first_purchase: bool
    promotion_id: Optional[str] = None


class CardUpgradeEvent(EventBase):
    card_id: str
    card_rarity: CardRarity
    previous_level: int = Field(ge=1, le=14)
    new_level: int = Field(ge=2, le=15)
    gold_cost: int
    cards_consumed: int
    upgrade_source: UpgradeSource


class CardDrop(BaseModel):
    card_id: str
    card_rarity: CardRarity
    quantity: int


class ChestOpeningEvent(EventBase):
    chest_type: ChestType
    chest_source: ChestSource
    cards_received: list[CardDrop]
    gold_received: int
    gems_received: int
    contained_legendary: bool
    queue_position: Optional[int] = None


class PlayerTradeEvent(EventBase):
    trade_id: str
    trade_type: TradeType
    offered_card_id: str
    offered_card_rarity: CardRarity
    offered_card_quantity: int
    requested_card_id: str
    requested_card_rarity: CardRarity
    requested_card_quantity: int
    trade_status: TradeStatus
    counterparty_player_id: Optional[str] = None
    trade_token_used: bool
