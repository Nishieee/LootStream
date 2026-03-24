from __future__ import annotations

from simulator.models.player import Player, generate_player_pool


class PlayerGenerator:
    @staticmethod
    def generate_pool(num_players: int) -> list[Player]:
        return generate_player_pool(num_players)
