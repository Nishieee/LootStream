USE DATABASE LOOTSTREAM;
USE WAREHOUSE LOOTSTREAM_WH;

-- 1. Gem purchases
CREATE OR REPLACE DYNAMIC TABLE STAGING.SILVER_GEM_PURCHASES
  TARGET_LAG = '5 minutes'
  WAREHOUSE = LOOTSTREAM_WH
  REFRESH_MODE = AUTO
  INITIALIZE = ON_CREATE
AS
SELECT
  RECORD_CONTENT:event_id::STRING                          AS event_id,
  TO_TIMESTAMP_NTZ(RECORD_CONTENT:event_timestamp::NUMBER, 3) AS event_timestamp,
  RECORD_CONTENT:player_id::STRING                         AS player_id,
  RECORD_CONTENT:session_id::STRING                        AS session_id,
  RECORD_CONTENT:platform::STRING                          AS platform,
  RECORD_CONTENT:app_version::STRING                       AS app_version,
  RECORD_CONTENT:gem_package_id::STRING                    AS gem_package_id,
  RECORD_CONTENT:gem_amount::INT                           AS gem_amount,
  RECORD_CONTENT:usd_price::FLOAT                          AS usd_price,
  RECORD_CONTENT:payment_method::STRING                    AS payment_method,
  RECORD_CONTENT:is_first_purchase::BOOLEAN                AS is_first_purchase,
  RECORD_CONTENT:promotion_id::STRING                      AS promotion_id,
  RECORD_METADATA:offset::INT                              AS kafka_offset,
  RECORD_METADATA:partition::INT                           AS kafka_partition,
  RECORD_METADATA:CreateTime::TIMESTAMP_NTZ                AS kafka_ingested_at
FROM RAW.RAW_GEM_PURCHASES
QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY kafka_ingested_at DESC) = 1;

-- 2. Card upgrades
CREATE OR REPLACE DYNAMIC TABLE STAGING.SILVER_CARD_UPGRADES
  TARGET_LAG = '5 minutes'
  WAREHOUSE = LOOTSTREAM_WH
  REFRESH_MODE = AUTO
  INITIALIZE = ON_CREATE
AS
SELECT
  RECORD_CONTENT:event_id::STRING                          AS event_id,
  TO_TIMESTAMP_NTZ(RECORD_CONTENT:event_timestamp::NUMBER, 3) AS event_timestamp,
  RECORD_CONTENT:player_id::STRING                         AS player_id,
  RECORD_CONTENT:session_id::STRING                        AS session_id,
  RECORD_CONTENT:platform::STRING                          AS platform,
  RECORD_CONTENT:app_version::STRING                       AS app_version,
  RECORD_CONTENT:card_id::STRING                           AS card_id,
  RECORD_CONTENT:card_rarity::STRING                       AS card_rarity,
  RECORD_CONTENT:previous_level::INT                       AS previous_level,
  RECORD_CONTENT:new_level::INT                            AS new_level,
  RECORD_CONTENT:gold_cost::INT                            AS gold_cost,
  RECORD_CONTENT:cards_consumed::INT                       AS cards_consumed,
  RECORD_CONTENT:upgrade_source::STRING                    AS upgrade_source,
  RECORD_METADATA:offset::INT                              AS kafka_offset,
  RECORD_METADATA:partition::INT                           AS kafka_partition,
  RECORD_METADATA:CreateTime::TIMESTAMP_NTZ                AS kafka_ingested_at
FROM RAW.RAW_CARD_UPGRADES
QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY kafka_ingested_at DESC) = 1;

-- 3. Chest openings
CREATE OR REPLACE DYNAMIC TABLE STAGING.SILVER_CHEST_OPENINGS
  TARGET_LAG = '5 minutes'
  WAREHOUSE = LOOTSTREAM_WH
  REFRESH_MODE = AUTO
  INITIALIZE = ON_CREATE
AS
SELECT
  RECORD_CONTENT:event_id::STRING                          AS event_id,
  TO_TIMESTAMP_NTZ(RECORD_CONTENT:event_timestamp::NUMBER, 3) AS event_timestamp,
  RECORD_CONTENT:player_id::STRING                         AS player_id,
  RECORD_CONTENT:session_id::STRING                        AS session_id,
  RECORD_CONTENT:platform::STRING                          AS platform,
  RECORD_CONTENT:app_version::STRING                       AS app_version,
  RECORD_CONTENT:chest_type::STRING                        AS chest_type,
  RECORD_CONTENT:chest_source::STRING                      AS chest_source,
  RECORD_CONTENT:cards_received::VARIANT                   AS cards_received_raw,
  RECORD_CONTENT:gold_received::INT                        AS gold_received,
  RECORD_CONTENT:gems_received::INT                        AS gems_received,
  RECORD_CONTENT:contained_legendary::BOOLEAN              AS contained_legendary,
  RECORD_CONTENT:queue_position::INT                       AS queue_position,
  RECORD_METADATA:offset::INT                              AS kafka_offset,
  RECORD_METADATA:partition::INT                           AS kafka_partition,
  RECORD_METADATA:CreateTime::TIMESTAMP_NTZ                AS kafka_ingested_at
FROM RAW.RAW_CHEST_OPENINGS
QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY kafka_ingested_at DESC) = 1;

-- 4. Chest cards flattened
CREATE OR REPLACE DYNAMIC TABLE STAGING.SILVER_CHEST_CARDS_FLATTENED
  TARGET_LAG = 'DOWNSTREAM'
  WAREHOUSE = LOOTSTREAM_WH
  REFRESH_MODE = AUTO
  INITIALIZE = ON_CREATE
AS
SELECT
  co.event_id,
  co.event_timestamp,
  co.player_id,
  co.chest_type,
  co.chest_source,
  card.value:card_id::STRING         AS card_id,
  card.value:card_rarity::STRING     AS card_rarity,
  card.value:quantity::INT           AS quantity
FROM STAGING.SILVER_CHEST_OPENINGS co,
  LATERAL FLATTEN(input => co.cards_received_raw) card;

-- 5. Player trades
CREATE OR REPLACE DYNAMIC TABLE STAGING.SILVER_PLAYER_TRADES
  TARGET_LAG = '5 minutes'
  WAREHOUSE = LOOTSTREAM_WH
  REFRESH_MODE = AUTO
  INITIALIZE = ON_CREATE
AS
SELECT
  RECORD_CONTENT:event_id::STRING                          AS event_id,
  TO_TIMESTAMP_NTZ(RECORD_CONTENT:event_timestamp::NUMBER, 3) AS event_timestamp,
  RECORD_CONTENT:player_id::STRING                         AS player_id,
  RECORD_CONTENT:session_id::STRING                        AS session_id,
  RECORD_CONTENT:platform::STRING                          AS platform,
  RECORD_CONTENT:app_version::STRING                       AS app_version,
  RECORD_CONTENT:trade_id::STRING                          AS trade_id,
  RECORD_CONTENT:trade_type::STRING                        AS trade_type,
  RECORD_CONTENT:offered_card_id::STRING                   AS offered_card_id,
  RECORD_CONTENT:offered_card_rarity::STRING               AS offered_card_rarity,
  RECORD_CONTENT:offered_card_quantity::INT                 AS offered_card_quantity,
  RECORD_CONTENT:requested_card_id::STRING                 AS requested_card_id,
  RECORD_CONTENT:requested_card_rarity::STRING             AS requested_card_rarity,
  RECORD_CONTENT:requested_card_quantity::INT               AS requested_card_quantity,
  RECORD_CONTENT:trade_status::STRING                      AS trade_status,
  RECORD_CONTENT:counterparty_player_id::STRING            AS counterparty_player_id,
  RECORD_CONTENT:trade_token_used::BOOLEAN                 AS trade_token_used,
  RECORD_METADATA:offset::INT                              AS kafka_offset,
  RECORD_METADATA:partition::INT                           AS kafka_partition,
  RECORD_METADATA:CreateTime::TIMESTAMP_NTZ                AS kafka_ingested_at
FROM RAW.RAW_PLAYER_TRADES
QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY kafka_ingested_at DESC) = 1;

-- 6. Player profiles (run AFTER 1-5 are all created)
CREATE OR REPLACE DYNAMIC TABLE STAGING.SILVER_PLAYER_PROFILES
  TARGET_LAG = '10 minutes'
  WAREHOUSE = LOOTSTREAM_WH
  REFRESH_MODE = AUTO
  INITIALIZE = ON_CREATE
AS
WITH all_events AS (
  SELECT player_id, platform, event_timestamp
  FROM STAGING.SILVER_GEM_PURCHASES
  UNION ALL
  SELECT player_id, platform, event_timestamp
  FROM STAGING.SILVER_CARD_UPGRADES
  UNION ALL
  SELECT player_id, platform, event_timestamp
  FROM STAGING.SILVER_CHEST_OPENINGS
  UNION ALL
  SELECT player_id, platform, event_timestamp
  FROM STAGING.SILVER_PLAYER_TRADES
),
player_spend AS (
  SELECT
    player_id,
    SUM(usd_price)              AS total_spend_usd,
    COUNT(*)                    AS total_purchases,
    MIN(event_timestamp)        AS first_purchase_at,
    MAX(event_timestamp)        AS last_purchase_at
  FROM STAGING.SILVER_GEM_PURCHASES
  GROUP BY player_id
),
player_activity AS (
  SELECT
    player_id,
    MIN(event_timestamp)        AS first_seen_at,
    MAX(event_timestamp)        AS last_seen_at,
    COUNT(DISTINCT DATE(event_timestamp)) AS active_days
  FROM all_events
  GROUP BY player_id
)
SELECT
  a.player_id,
  a.first_seen_at,
  a.last_seen_at,
  a.active_days,
  COALESCE(s.total_spend_usd, 0)    AS total_spend_usd,
  COALESCE(s.total_purchases, 0)    AS total_purchases,
  s.first_purchase_at,
  s.last_purchase_at,
  CASE
    WHEN COALESCE(s.total_spend_usd, 0) > 500 THEN 'WHALE'
    WHEN COALESCE(s.total_spend_usd, 0) > 50  THEN 'DOLPHIN'
    WHEN COALESCE(s.total_spend_usd, 0) > 1   THEN 'MINNOW'
    ELSE 'FREE_TO_PLAY'
  END                                AS player_segment,
  DATEDIFF('day', a.first_seen_at, a.last_seen_at) AS account_age_days
FROM player_activity a
LEFT JOIN player_spend s ON a.player_id = s.player_id;