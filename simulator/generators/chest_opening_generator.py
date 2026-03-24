from __future__ import annotations

import random

from simulator.models.economy import CARD_CATALOG, CHEST_DROP_TABLES
from simulator.models.events import CardDrop, CardRarity, ChestOpeningEvent, ChestSource, ChestType, Platform
from simulator.models.player import Player


class ChestOpeningGenerator:
    def __init__(self, players: list[Player]) -> None:
        self.players = players

    def _eligible_cards(self, player: Player) -> list[dict]:
        return [card for card in CARD_CATALOG if card["arena_unlock"] <= player.arena_level]

    def _pick_rarity(self, weights: list[int]) -> str:
        return random.choices(["COMMON", "RARE", "EPIC", "LEGENDARY", "CHAMPION"], weights=weights, k=1)[0]

    def generate(self) -> ChestOpeningEvent:
        player = random.choice(self.players)
        chest_type = random.choices(
            ["SILVER", "GOLD", "GIANT", "MAGICAL", "LEGENDARY", "MEGA_LIGHTNING", "ROYAL_WILD"],
            weights=[40, 28, 10, 9, 3, 7, 3],
            k=1,
        )[0]
        config = CHEST_DROP_TABLES[chest_type]
        eligible_cards = self._eligible_cards(player)

        drops: list[CardDrop] = []
        for _ in range(config["cards"]):
            rarity = self._pick_rarity(config["rarity_weights"])
            candidates = [c for c in eligible_cards if c["card_rarity"] == rarity]
            if not candidates:
                candidates = [c for c in eligible_cards if c["card_rarity"] in ("COMMON", "RARE")]
            card = random.choice(candidates)
            qty = random.randint(1, 8 if rarity == "COMMON" else 3)
            drops.append(CardDrop(card_id=card["card_id"], card_rarity=CardRarity(rarity), quantity=qty))

        contains_legendary = any(d.card_rarity == CardRarity.LEGENDARY for d in drops)

        return ChestOpeningEvent(
            player_id=player.player_id,
            platform=Platform(player.platform.value),
            app_version=random.choice(["4.1.0", "4.1.1", "4.2.0"]),
            chest_type=ChestType(chest_type),
            chest_source=random.choices(
                [
                    ChestSource.BATTLE_REWARD,
                    ChestSource.SHOP_PURCHASE,
                    ChestSource.CHALLENGE_REWARD,
                    ChestSource.PASS_ROYALE,
                    ChestSource.CLAN_WAR,
                ],
                weights=[52, 8, 18, 17, 5],
                k=1,
            )[0],
            cards_received=drops,
            gold_received=random.randint(*config["gold_range"]),
            gems_received=random.choices([0, 1, 2, 3, 5, 8, 12], weights=[62, 14, 9, 6, 5, 3, 1], k=1)[0],
            contained_legendary=contains_legendary,
            queue_position=random.choice([None, None, None, random.randint(1, 4)]),
        )
