from __future__ import annotations

import argparse
import logging
import random
import signal
import time
from dataclasses import dataclass

from simulator.config import settings
from simulator.generators.card_upgrade_generator import CardUpgradeGenerator
from simulator.generators.chest_opening_generator import ChestOpeningGenerator
from simulator.generators.gem_purchase_generator import GemPurchaseGenerator
from simulator.generators.player_generator import PlayerGenerator
from simulator.generators.trade_generator import TradeGenerator
from simulator.producer import EventProducer


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("lootstream")


RUNNING = True


def _handle_signal(_sig, _frame) -> None:
    global RUNNING
    RUNNING = False


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


@dataclass(frozen=True)
class GeneratorBinding:
    name: str
    topic: str
    generator: object
    weight: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LootStream event simulator")
    parser.add_argument("--players", type=int, default=settings.num_players)
    parser.add_argument("--eps", type=int, default=settings.events_per_second)
    parser.add_argument("--speed", type=float, default=settings.simulation_speed)
    parser.add_argument("--duration", type=int, default=0, help="Duration in seconds (0 = run forever)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logger.info("Generating player pool: %d players", args.players)
    players = PlayerGenerator.generate_pool(args.players)

    producer = EventProducer()
    generators = [
        GeneratorBinding(
            name="chest_openings",
            topic="game.events.chest_openings",
            generator=ChestOpeningGenerator(players),
            weight=35,
        ),
        GeneratorBinding(
            name="card_upgrades",
            topic="game.events.card_upgrades",
            generator=CardUpgradeGenerator(players),
            weight=25,
        ),
        GeneratorBinding(
            name="gem_purchases",
            topic="game.events.gem_purchases",
            generator=GemPurchaseGenerator(players),
            weight=25,
        ),
        GeneratorBinding(
            name="player_trades",
            topic="game.events.player_trades",
            generator=TradeGenerator(players),
            weight=15,
        ),
    ]

    interval = 1.0 / max(1, int(args.eps * args.speed))
    start = time.time()
    last_log = start
    total_events = 0

    logger.info("Starting simulation eps=%s speed=%s duration=%s", args.eps, args.speed, args.duration)

    while RUNNING:
        now = time.time()
        if args.duration > 0 and now - start >= args.duration:
            break

        selected = random.choices(generators, weights=[g.weight for g in generators], k=1)[0]
        event = selected.generator.generate()
        producer.produce(selected.topic, event)
        total_events += 1

        if now - last_log >= 10:
            elapsed = max(1e-6, now - start)
            throughput = total_events / elapsed
            logger.info("Events sent=%d throughput=%.2f events/sec", total_events, throughput)
            last_log = now

        if interval > 0:
            time.sleep(interval)

    logger.info("Shutting down, flushing producer")
    producer.flush()
    logger.info("Simulation stopped after sending %d events", total_events)


if __name__ == "__main__":
    main()
