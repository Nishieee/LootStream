from __future__ import annotations

import random

from simulator.models.economy import CARD_CATALOG, CARDS_REQUIRED, UPGRADE_GOLD_COST
from simulator.models.events import CardRarity, CardUpgradeEvent, Platform, UpgradeSource
from simulator.models.player import Player


class CardUpgradeGenerator:
    def __init__(self, players: list[Player]) -> None:
        self.players = players

    def _eligible_cards(self, player: Player) -> list[dict]:
        return [card for card in CARD_CATALOG if card["arena_unlock"] <= player.arena_level]

    def generate(self) -> CardUpgradeEvent:
        player = random.choice(self.players)
        card = random.choice(self._eligible_cards(player))
        previous_level = random.choices(range(1, 15), weights=[25, 22, 18, 12, 8, 5, 3, 2, 1, 1, 1, 1, 1, 0.5], k=1)[0]
        rarity = card["card_rarity"]

        return CardUpgradeEvent(
            player_id=player.player_id,
            platform=Platform(player.platform.value),
            app_version=random.choice(["4.1.0", "4.1.1", "4.2.0"]),
            card_id=card["card_id"],
            card_rarity=CardRarity(rarity),
            previous_level=previous_level,
            new_level=previous_level + 1,
            gold_cost=UPGRADE_GOLD_COST[rarity][previous_level],
            cards_consumed=CARDS_REQUIRED[rarity][previous_level],
            upgrade_source=random.choices(
                [UpgradeSource.MANUAL, UpgradeSource.AUTO_UPGRADE, UpgradeSource.MAGIC_ITEM],
                weights=[70, 20, 10],
                k=1,
            )[0],
        )
