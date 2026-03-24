# LootStream

Synthetic game economy events are generated in Python, written to Kafka as Avro, and streamed into Snowflake landing tables via Kafka Connect (Snowpipe Streaming). Docker runs Kafka, Schema Registry, and Connect locally.

## Architecture

Mermaid diagrams render on GitHub. To edit or export, paste the fenced block into [mermaid.live](https://mermaid.live).

**Pipeline**

```mermaid
flowchart LR
  subgraph local["Local"]
    SIM["Simulator"]
  end
  subgraph docker["Docker"]
    K["Kafka"]
    SR["Schema Registry"]
    KC["Kafka Connect"]
  end
  subgraph sf["Snowflake"]
    WH["LOOTSTREAM_WH"]
    DB["LOOTSTREAM"]
    RAW["RAW"]
  end
  SIM --> K
  K --> SR
  K --> KC
  SR --> KC
  KC --> WH
  WH --> DB
  DB --> RAW
```

**Landing tables** (`LOOTSTREAM.RAW`)

```mermaid
flowchart TB
  WH["Warehouse: LOOTSTREAM_WH"]
  DB["Database: LOOTSTREAM"]
  SCH["Schema: RAW"]
  T1["RAW_GEM_PURCHASES"]
  T2["RAW_CARD_UPGRADES"]
  T3["RAW_CHEST_OPENINGS"]
  T4["RAW_PLAYER_TRADES"]
  WH --> DB --> SCH
  SCH --> T1
  SCH --> T2
  SCH --> T3
  SCH --> T4
```

| Kafka topic | Table |
|-------------|--------|
| `game.events.gem_purchases` | `RAW_GEM_PURCHASES` |
| `game.events.card_upgrades` | `RAW_CARD_UPGRADES` |
| `game.events.chest_openings` | `RAW_CHEST_OPENINGS` |
| `game.events.player_trades` | `RAW_PLAYER_TRADES` |

## Layout

| Path | Purpose |
|------|---------|
| `docker/` | Compose stack: Zookeeper, Kafka, Schema Registry, Kafka Connect, optional UI |
| `simulator/` | Event models, generators, Avro producer, CLI entrypoint |
| `schemas/` | Avro definitions for the four event types |
| `connect/` | Connect image Dockerfile, Snowflake connector JSON template, `keys/` for RSA private key (gitignored) |
| `scripts/` | `create_topics.sh`, `deploy-connector.sh`, `connector-status.sh` |

## Quick start

**Stack and topics**

```bash
cd docker && docker compose up -d --build
cd .. && bash scripts/create_topics.sh
```

**Simulator only** (needs Kafka + Schema Registry up)

```bash
pip install -r requirements.txt
python -m simulator.main --players 1000 --eps 50
```

**Snowflake sink** — place `rsa_key.p8` in `connect/keys/`, set `.env`, wait for Connect on port 8083, then:

```bash
bash scripts/deploy-connector.sh
bash scripts/connector-status.sh
```

**Verify in Snowflake**

```sql
SELECT COUNT(*) FROM LOOTSTREAM.RAW.RAW_GEM_PURCHASES;
```
