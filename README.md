# LootStream

Synthetic game economy events are generated in Python, written to Kafka as Avro, and streamed into Snowflake landing tables via Kafka Connect (Snowpipe Streaming). Docker runs Kafka, Schema Registry, and Connect locally.

## Architecture

Mermaid renders on GitHub; paste any block into [mermaid.live](https://mermaid.live) to edit. This repo implements the simulator, Kafka, Connect, and **bronze** (`RAW_*`) landing. Silver, gold, and Streamlit are the target warehouse shape.

### Tech stack

```mermaid
graph LR
    A["Python"] --> B["Kafka"]
    B --> C["Connect +\nSnowpipe Streaming"]
    C --> D["Snowflake"]
    D --> E["Dynamic Tables"]
    E --> F["Streamlit"]

    style A fill:#EEEDFE,stroke:#534AB7,color:#26215C
    style B fill:#FAECE7,stroke:#993C1D,color:#4A1B0C
    style C fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A
    style D fill:#E6F1FB,stroke:#185FA5,color:#042C53
    style E fill:#FAEEDA,stroke:#854F0B,color:#412402
    style F fill:#E1F5EE,stroke:#0F6E56,color:#04342C
```

### End-to-end pipeline

Kafka topics: `game.events.gem_purchases`, `game.events.card_upgrades`, `game.events.chest_openings`, `game.events.player_trades`.

```mermaid
flowchart TD
    subgraph GEN["Generate"]
        SIM["Python simulator\nAvro · Schema Registry"]
    end

    subgraph STREAM["Stream"]
        K["Kafka\nfour event topics"]
        KC["Kafka Connect\nSnowflake sink · Snowpipe Streaming"]
    end

    subgraph SF["Snowflake"]
        subgraph BRONZE["Bronze · RAW (this repo)"]
            B1["RAW_GEM_PURCHASES"]
            B2["RAW_CARD_UPGRADES"]
            B3["RAW_CHEST_OPENINGS"]
            B4["RAW_PLAYER_TRADES"]
        end
        subgraph PLAN["Planned"]
            SV["Silver · STAGING\ntyped, deduped, flatten"]
            GD["Gold · ANALYTICS\nrevenue, retention, LTV, card economy"]
            UI["Streamlit"]
        end
    end

    SIM --> K --> KC
    KC --> B1
    KC --> B2
    KC --> B3
    KC --> B4
    B1 --> SV
    B2 --> SV
    B3 --> SV
    B4 --> SV
    SV --> GD --> UI

    style GEN fill:#EEEDFE,stroke:#534AB7,color:#26215C
    style STREAM fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A
    style K fill:#EEEDFE,stroke:#534AB7,color:#26215C
    style BRONZE fill:#FAECE7,stroke:#993C1D,color:#4A1B0C
    style PLAN fill:#E6F1FB,stroke:#185FA5,color:#042C53
    style SV fill:#E1F5EE,stroke:#0F6E56,color:#04342C
    style GD fill:#FAEEDA,stroke:#854F0B,color:#412402
```

### Snowflake warehouse layers

```mermaid
flowchart LR
    subgraph BRONZE["RAW · Bronze"]
        direction TB
        B1["RAW_GEM_PURCHASES"]
        B2["RAW_CARD_UPGRADES"]
        B3["RAW_CHEST_OPENINGS"]
        B4["RAW_PLAYER_TRADES"]
    end

    subgraph SILVER["STAGING · Silver"]
        direction TB
        S1["Typed event tables\nfour streams"]
        S2["Flatten chest cards\n+ player profiles"]
    end

    subgraph GOLD["ANALYTICS · Gold"]
        G1["Marts: revenue, retention,\nLTV, card economy, spend"]
    end

    B1 --> S1
    B2 --> S1
    B3 --> S1
    B4 --> S1
    B3 --> S2
    S1 --> G1
    S2 --> G1

    style BRONZE fill:#FAECE7,stroke:#993C1D,color:#4A1B0C
    style SILVER fill:#E1F5EE,stroke:#0F6E56,color:#04342C
    style GOLD fill:#FAEEDA,stroke:#854F0B,color:#412402
```

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
