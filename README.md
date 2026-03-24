# LootStream

Synthetic game economy events are generated in Python, written to Kafka as Avro, and streamed into Snowflake landing tables via Kafka Connect (Snowpipe Streaming). Docker runs Kafka, Schema Registry, and Connect locally.

## Architecture

Mermaid renders on GitHub; paste any block into [mermaid.live](https://mermaid.live) to edit. This repo implements the simulator, Kafka, Connect, and **bronze** (`RAW_*`) landing. Silver, gold, and Streamlit are the target warehouse shape.

### Tech stack

```mermaid
graph LR
    A["Python"] --> B["Apache Kafka"]
    B --> C["Snowpipe Streaming"]
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

Kafka topics in this repo are `game.events.gem_purchases`, `game.events.card_upgrades`, `game.events.chest_openings`, and `game.events.player_trades` (labels in the diagram are shorthand).

```mermaid
flowchart TD
    subgraph EVENT_GENERATION["Event generation"]
        SIM["Python simulator\n1000 players, 50 events/sec"]
        SCHEMAS["Avro schemas\n4 event types"]
        SIM -->|validates against| SCHEMAS
    end

    subgraph KAFKA["Apache Kafka (Docker)"]
        T1["gem_purchases"]
        T2["card_upgrades"]
        T3["chest_openings"]
        T4["player_trades"]
    end

    SIM -->|produces to| T1
    SIM -->|produces to| T2
    SIM -->|produces to| T3
    SIM -->|produces to| T4

    subgraph CONNECT["Kafka Connect"]
        SINK["Snowflake Sink Connector\nSnowpipe Streaming"]
    end

    T1 --> SINK
    T2 --> SINK
    T3 --> SINK
    T4 --> SINK

    subgraph SNOWFLAKE["Snowflake Data Warehouse"]
        subgraph BRONZE["Bronze — RAW schema"]
            B1["RAW_GEM_PURCHASES"]
            B2["RAW_CARD_UPGRADES"]
            B3["RAW_CHEST_OPENINGS"]
            B4["RAW_PLAYER_TRADES"]
        end

        subgraph SILVER["Silver — STAGING schema"]
            S1["SILVER_GEM_PURCHASES"]
            S2["SILVER_CARD_UPGRADES"]
            S3["SILVER_CHEST_OPENINGS"]
            S4["SILVER_PLAYER_TRADES"]
            S5["SILVER_CHEST_CARDS_FLATTENED"]
            S6["SILVER_PLAYER_PROFILES"]
        end

        subgraph GOLD["Gold — ANALYTICS schema"]
            G1["GOLD_DAILY_REVENUE\nDAU, ARPDAU, conversion"]
            G2["GOLD_RETENTION_COHORTS\nD1, D7, D30"]
            G3["GOLD_LTV_BY_SEGMENT\navg/median LTV"]
            G4["GOLD_CARD_ECONOMY\ndemand/supply ratio"]
            G5["GOLD_SPENDING_DISTRIBUTION\nrevenue by segment"]
        end
    end

    SINK -->|seconds latency| B1
    SINK --> B2
    SINK --> B3
    SINK --> B4

    B1 -->|Dynamic Table\n5 min lag| S1
    B2 -->|Dynamic Table\n5 min lag| S2
    B3 -->|Dynamic Table\n5 min lag| S3
    B4 -->|Dynamic Table\n5 min lag| S4
    S3 -->|LATERAL FLATTEN| S5
    S1 & S2 & S3 & S4 -->|aggregated| S6

    S1 & S2 & S3 & S4 -->|Dynamic Table\n10 min lag| G1
    S1 & S2 & S3 & S4 --> G2
    S6 --> G3
    S2 & S4 & S5 --> G4
    S1 & S6 --> G5

    subgraph DASHBOARD["Streamlit in Snowflake"]
        D1["Revenue & ARPDAU"]
        D2["Retention cohorts"]
        D3["Player segments & LTV"]
        D4["Card economy health"]
        D5["Live event feed"]
    end

    G1 --> D1
    G2 --> D2
    G3 --> D3
    G4 --> D4
    S1 & S2 & S3 & S4 --> D5

    style BRONZE fill:#FAECE7,stroke:#993C1D,color:#4A1B0C
    style SILVER fill:#E1F5EE,stroke:#0F6E56,color:#04342C
    style GOLD fill:#FAEEDA,stroke:#854F0B,color:#412402
    style KAFKA fill:#EEEDFE,stroke:#534AB7,color:#26215C
    style EVENT_GENERATION fill:#EEEDFE,stroke:#534AB7,color:#26215C
    style CONNECT fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A
    style SNOWFLAKE fill:#E6F1FB,stroke:#185FA5,color:#042C53
    style DASHBOARD fill:#EEEDFE,stroke:#534AB7,color:#26215C
```

### Snowflake warehouse layers

```mermaid
flowchart LR
    subgraph BRONZE["RAW schema (Bronze)"]
        direction TB
        B1["RAW_GEM_PURCHASES\nVARIANT columns"]
        B2["RAW_CARD_UPGRADES\nVARIANT columns"]
        B3["RAW_CHEST_OPENINGS\nVARIANT columns"]
        B4["RAW_PLAYER_TRADES\nVARIANT columns"]
    end

    subgraph SILVER["STAGING schema (Silver)"]
        direction TB
        S1["SILVER_GEM_PURCHASES\ntyped, deduped"]
        S2["SILVER_CARD_UPGRADES\ntyped, deduped"]
        S3["SILVER_CHEST_OPENINGS\ntyped, deduped"]
        S4["SILVER_PLAYER_TRADES\ntyped, deduped"]
        S5["SILVER_CHEST_CARDS_FLATTENED\none row per card drop"]
        S6["SILVER_PLAYER_PROFILES\nsegment, LTV, activity"]
    end

    subgraph GOLD["ANALYTICS schema (Gold)"]
        direction TB
        G1["GOLD_DAILY_REVENUE\nDAU, ARPDAU, conversion %"]
        G2["GOLD_RETENTION_COHORTS\nD1/D7/D30 by cohort date"]
        G3["GOLD_LTV_BY_SEGMENT\nwhale/dolphin/minnow/F2P"]
        G4["GOLD_CARD_ECONOMY\ndemand vs supply per card"]
        G5["GOLD_SPENDING_DISTRIBUTION\nrevenue by segment + promos"]
    end

    B1 -->|"Dynamic Table (5 min)"| S1
    B2 -->|"Dynamic Table (5 min)"| S2
    B3 -->|"Dynamic Table (5 min)"| S3
    B4 -->|"Dynamic Table (5 min)"| S4
    S3 -->|"FLATTEN array"| S5
    S1 & S2 & S3 & S4 -->|"aggregate"| S6

    S1 & S4 -->|"Dynamic Table (10 min)"| G1
    S1 & S2 & S3 & S4 --> G2
    S6 --> G3
    S2 & S4 & S5 --> G4
    S1 & S6 --> G5

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
