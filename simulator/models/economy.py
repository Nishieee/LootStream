from __future__ import annotations

CARD_CATALOG = [
    {"card_id": "knight", "card_rarity": "COMMON", "arena_unlock": 1},
    {"card_id": "archers", "card_rarity": "COMMON", "arena_unlock": 1},
    {"card_id": "goblins", "card_rarity": "COMMON", "arena_unlock": 1},
    {"card_id": "spear_goblins", "card_rarity": "COMMON", "arena_unlock": 1},
    {"card_id": "fireball", "card_rarity": "RARE", "arena_unlock": 2},
    {"card_id": "musketeer", "card_rarity": "RARE", "arena_unlock": 2},
    {"card_id": "mini_pekka", "card_rarity": "RARE", "arena_unlock": 3},
    {"card_id": "hog_rider", "card_rarity": "RARE", "arena_unlock": 5},
    {"card_id": "baby_dragon", "card_rarity": "EPIC", "arena_unlock": 6},
    {"card_id": "prince", "card_rarity": "EPIC", "arena_unlock": 7},
    {"card_id": "witch", "card_rarity": "EPIC", "arena_unlock": 8},
    {"card_id": "balloon", "card_rarity": "EPIC", "arena_unlock": 9},
    {"card_id": "lava_hound", "card_rarity": "LEGENDARY", "arena_unlock": 10},
    {"card_id": "miner", "card_rarity": "LEGENDARY", "arena_unlock": 10},
    {"card_id": "log", "card_rarity": "LEGENDARY", "arena_unlock": 11},
    {"card_id": "night_witch", "card_rarity": "LEGENDARY", "arena_unlock": 12},
    {"card_id": "golden_knight", "card_rarity": "CHAMPION", "arena_unlock": 16},
    {"card_id": "skeleton_king", "card_rarity": "CHAMPION", "arena_unlock": 16},
    {"card_id": "archer_queen", "card_rarity": "CHAMPION", "arena_unlock": 17},
    {"card_id": "mighty_miner", "card_rarity": "CHAMPION", "arena_unlock": 18},
    {"card_id": "monk", "card_rarity": "CHAMPION", "arena_unlock": 19}
]

UPGRADE_GOLD_COST = {
    "COMMON": {level: 100 * level for level in range(1, 15)},
    "RARE": {level: 200 * level for level in range(1, 15)},
    "EPIC": {level: 400 * level for level in range(1, 15)},
    "LEGENDARY": {level: 800 * level for level in range(1, 15)},
    "CHAMPION": {level: 1200 * level for level in range(1, 15)},
}

CARDS_REQUIRED = {
    "COMMON": {level: 2 * level for level in range(1, 15)},
    "RARE": {level: max(1, level) for level in range(1, 15)},
    "EPIC": {level: max(1, level // 2) for level in range(1, 15)},
    "LEGENDARY": {level: 1 for level in range(1, 15)},
    "CHAMPION": {level: 1 for level in range(1, 15)},
}

CHEST_DROP_TABLES = {
    "SILVER": {"gold_range": (50, 180), "cards": 3, "rarity_weights": [85, 12, 3, 0, 0]},
    "GOLD": {"gold_range": (180, 420), "cards": 8, "rarity_weights": [78, 16, 5, 1, 0]},
    "GIANT": {"gold_range": (500, 1200), "cards": 35, "rarity_weights": [75, 18, 6, 1, 0]},
    "MAGICAL": {"gold_range": (800, 1600), "cards": 20, "rarity_weights": [58, 26, 12, 4, 0]},
    "LEGENDARY": {"gold_range": (400, 1000), "cards": 1, "rarity_weights": [0, 0, 0, 100, 0]},
    "MEGA_LIGHTNING": {"gold_range": (1400, 2800), "cards": 58, "rarity_weights": [48, 28, 16, 7, 1]},
    "ROYAL_WILD": {"gold_range": (1000, 2200), "cards": 32, "rarity_weights": [52, 26, 14, 6, 2]},
}

GEM_PACKAGES = [
    {"gem_package_id": "pack_100", "gem_amount": 100, "usd_price": 0.99},
    {"gem_package_id": "pack_500", "gem_amount": 500, "usd_price": 4.99},
    {"gem_package_id": "pack_1200", "gem_amount": 1200, "usd_price": 9.99},
    {"gem_package_id": "pack_2500", "gem_amount": 2500, "usd_price": 19.99},
    {"gem_package_id": "pack_6500", "gem_amount": 6500, "usd_price": 49.99},
    {"gem_package_id": "pack_14000", "gem_amount": 14000, "usd_price": 99.99},
]
