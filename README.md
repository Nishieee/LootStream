# LootStream

LootStream is a small project that simulates game player activity and streams those events in real time.
It is built as a learning/demo setup to show how game events can be generated and sent through a local pipeline.

## What each file does (one line each)

- `docker/docker-compose.yml` - Starts the local services used by this project.
- `simulator/__init__.py` - Marks `simulator` as a Python package.
- `simulator/config.py` - Loads app settings from environment variables.
- `simulator/models/__init__.py` - Marks `models` as a Python package.
- `simulator/models/player.py` - Defines the player model and creates sample players.
- `simulator/models/events.py` - Defines the event models used by the simulator.
- `simulator/models/economy.py` - Stores game economy data like cards, chests, and prices.
- `simulator/generators/__init__.py` - Marks `generators` as a Python package.
- `simulator/generators/player_generator.py` - Creates a pool of players for the simulation.
- `simulator/generators/gem_purchase_generator.py` - Generates gem purchase events.
- `simulator/generators/card_upgrade_generator.py` - Generates card upgrade events.
- `simulator/generators/chest_opening_generator.py` - Generates chest opening events.
- `simulator/generators/trade_generator.py` - Generates player trade events.
- `simulator/producer.py` - Sends generated events to Kafka.
- `simulator/main.py` - Runs the simulator from the command line.
- `schemas/gem_purchase.avsc` - Schema for gem purchase events.
- `schemas/card_upgrade.avsc` - Schema for card upgrade events.
- `schemas/chest_opening.avsc` - Schema for chest opening events.
- `schemas/player_trade.avsc` - Schema for player trade events.
- `scripts/create_topics.sh` - Creates required Kafka topics.
- `requirements.txt` - Lists Python dependencies.
- `.env` - Contains local runtime configuration values.
- `.gitignore` - Lists files/folders Git should ignore.
- `README.md` - Project overview and quick file guide.

## Quick start

```bash
cd docker && docker compose up -d
sleep 30
bash ../scripts/create_topics.sh
pip install -r requirements.txt
python -m simulator.main --players 1000 --eps 50
```
