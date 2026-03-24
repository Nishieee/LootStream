from __future__ import annotations

import random

from simulator.models.economy import GEM_PACKAGES
from simulator.models.events import GemPurchaseEvent, PaymentMethod, Platform
from simulator.models.player import Player, PlayerSegment


class GemPurchaseGenerator:
    def __init__(self, players: list[Player]) -> None:
        self.players = players
        self.purchase_counts: dict[str, int] = {}

    def _purchase_probability(self, player: Player) -> float:
        segment_prob = {
            PlayerSegment.WHALE: 0.38,
            PlayerSegment.DOLPHIN: 0.19,
            PlayerSegment.MINNOW: 0.05,
            PlayerSegment.FREE_TO_PLAY: 0.004,
        }
        return segment_prob[player.player_segment]

    def _pick_package(self, player: Player) -> dict:
        if player.player_segment == PlayerSegment.WHALE:
            weights = [2, 5, 10, 20, 30, 33]
        elif player.player_segment == PlayerSegment.DOLPHIN:
            weights = [12, 20, 24, 24, 14, 6]
        elif player.player_segment == PlayerSegment.MINNOW:
            weights = [40, 28, 18, 10, 3, 1]
        else:
            weights = [65, 22, 9, 3, 1, 0]
        return random.choices(GEM_PACKAGES, weights=weights, k=1)[0]

    def generate(self) -> GemPurchaseEvent:
        player = random.choice(self.players)
        if random.random() > self._purchase_probability(player):
            player = random.choice([p for p in self.players if p.player_segment != PlayerSegment.FREE_TO_PLAY])

        package = self._pick_package(player)
        player_count = self.purchase_counts.get(player.player_id, 0)
        self.purchase_counts[player.player_id] = player_count + 1

        return GemPurchaseEvent(
            player_id=player.player_id,
            platform=Platform(player.platform.value),
            app_version=random.choice(["4.1.0", "4.1.1", "4.2.0"]),
            gem_package_id=package["gem_package_id"],
            gem_amount=package["gem_amount"],
            usd_price=float(package["usd_price"]),
            payment_method=random.choices(
                [PaymentMethod.APPLE_IAP, PaymentMethod.GOOGLE_PLAY, PaymentMethod.CREDIT_CARD, PaymentMethod.PAYPAL],
                weights=[40, 40, 15, 5],
                k=1,
            )[0],
            is_first_purchase=player_count == 0,
            promotion_id=random.choice([None, None, None, "spring_blast", "bundle_weekend"]),
        )
