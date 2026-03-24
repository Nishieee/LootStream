from __future__ import annotations

import random
from uuid import uuid4

from simulator.models.economy import CARD_CATALOG
from simulator.models.events import CardRarity, Platform, PlayerTradeEvent, TradeStatus, TradeType
from simulator.models.player import Player


class TradeGenerator:
    def __init__(self, players: list[Player]) -> None:
        self.players = players
        self.clan_players = [p for p in players if p.clan_id is not None]

    def _eligible_cards(self, player: Player) -> list[dict]:
        return [card for card in CARD_CATALOG if card["arena_unlock"] <= player.arena_level]

    def generate(self) -> PlayerTradeEvent:
        player = random.choice(self.clan_players)
        counterparty = random.choice(self.clan_players)

        cards = self._eligible_cards(player)
        offered = random.choice(cards)
        requested = random.choice(cards)

        rarity = offered["card_rarity"]
        qty = random.randint(5, 50) if rarity == "COMMON" else random.randint(1, 10)
        requested_qty = random.randint(5, 50) if requested["card_rarity"] == "COMMON" else random.randint(1, 10)

        status = random.choices(
            [TradeStatus.POSTED, TradeStatus.COMPLETED, TradeStatus.CANCELLED, TradeStatus.EXPIRED],
            weights=[20, 62, 8, 10],
            k=1,
        )[0]

        return PlayerTradeEvent(
            player_id=player.player_id,
            platform=Platform(player.platform.value),
            app_version=random.choice(["4.1.0", "4.1.1", "4.2.0"]),
            trade_id=str(uuid4()),
            trade_type=random.choices([TradeType.CLAN_TRADE, TradeType.GLOBAL_TRADE], weights=[88, 12], k=1)[0],
            offered_card_id=offered["card_id"],
            offered_card_rarity=CardRarity(offered["card_rarity"]),
            offered_card_quantity=qty,
            requested_card_id=requested["card_id"],
            requested_card_rarity=CardRarity(requested["card_rarity"]),
            requested_card_quantity=requested_qty,
            trade_status=status,
            counterparty_player_id=counterparty.player_id if status == TradeStatus.COMPLETED else None,
            trade_token_used=random.random() < 0.2,
        )
