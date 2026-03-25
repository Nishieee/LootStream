
USE DATABASE LOOTSTREAM
use warehouse lootstream_wh


-- daily active users and revenue (ARPDAU)

CREATE OR REPLACE DYNAMIC TABLE ANALYTICS.GOLD_DAILY_REVENUE
  TARGET_LAG = '10 minutes'
  WAREHOUSE = LOOTSTREAM_WH
  REFRESH_MODE = AUTO
  INITIALIZE = ON_CREATE
AS
WITH daily_players AS (
  SELECT DATE(event_timestamp) AS activity_date, player_id
  FROM STAGING.SILVER_GEM_PURCHASES
  UNION
  SELECT DATE(event_timestamp), player_id FROM STAGING.SILVER_CARD_UPGRADES
  UNION
  SELECT DATE(event_timestamp), player_id FROM STAGING.SILVER_CHEST_OPENINGS
  UNION
  SELECT DATE(event_timestamp), player_id FROM STAGING.SILVER_PLAYER_TRADES
),
daily_dau AS (
  SELECT activity_date, COUNT(DISTINCT player_id) AS dau
  FROM daily_players
  GROUP BY activity_date
),
daily_revenue AS (
  SELECT
    DATE(event_timestamp) AS revenue_date,
    SUM(usd_price)        AS total_revenue,
    COUNT(*)              AS total_transactions,
    COUNT(DISTINCT player_id) AS paying_users
  FROM STAGING.SILVER_GEM_PURCHASES
  GROUP BY DATE(event_timestamp)
)
SELECT
  d.activity_date,
  d.dau,
  COALESCE(r.total_revenue, 0)        AS total_revenue,
  COALESCE(r.total_transactions, 0)   AS total_transactions,
  COALESCE(r.paying_users, 0)         AS paying_users,
  CASE WHEN d.dau > 0
    THEN ROUND(COALESCE(r.total_revenue, 0) / d.dau, 4)
    ELSE 0
  END                                  AS arpdau,
  CASE WHEN d.dau > 0
    THEN ROUND(COALESCE(r.paying_users, 0)::FLOAT / d.dau * 100, 2)
    ELSE 0
  END                                  AS conversion_rate_pct
FROM daily_dau d
LEFT JOIN daily_revenue r ON d.activity_date = r.revenue_date
ORDER BY d.activity_date;


-- Gold: retention cohorts (D1, D7, D10, D30)

CREATE OR REPLACE DYNAMIC TABLE ANALYTICS.GOLD_RETENTION_COHORTS
  TARGET_LAG = '10 minutes'
  WAREHOUSE = LOOTSTREAM_WH
  REFRESH_MODE = AUTO
  INITIALIZE = ON_CREATE
AS
WITH all_activity AS (
  SELECT player_id, DATE(event_timestamp) AS activity_date
  FROM STAGING.SILVER_GEM_PURCHASES
  UNION
  SELECT player_id, DATE(event_timestamp) FROM STAGING.SILVER_CARD_UPGRADES
  UNION
  SELECT player_id, DATE(event_timestamp) FROM STAGING.SILVER_CHEST_OPENINGS
  UNION
  SELECT player_id, DATE(event_timestamp) FROM STAGING.SILVER_PLAYER_TRADES
),
first_seen AS (
  SELECT player_id, MIN(activity_date) AS cohort_date
  FROM all_activity
  GROUP BY player_id
),
retention_base AS (
  SELECT
    f.cohort_date,
    f.player_id,
    a.activity_date,
    DATEDIFF('day', f.cohort_date, a.activity_date) AS days_since_first
  FROM first_seen f
  JOIN all_activity a ON f.player_id = a.player_id
)
SELECT
  cohort_date,
  COUNT(DISTINCT player_id)                                                        AS cohort_size,
  COUNT(DISTINCT CASE WHEN days_since_first = 1 THEN player_id END)                AS retained_d1,
  COUNT(DISTINCT CASE WHEN days_since_first = 7 THEN player_id END)                AS retained_d7,
  COUNT(DISTINCT CASE WHEN days_since_first = 10 THEN player_id END)               AS retained_d10,
  COUNT(DISTINCT CASE WHEN days_since_first = 30 THEN player_id END)               AS retained_d30,
  ROUND(COUNT(DISTINCT CASE WHEN days_since_first = 1 THEN player_id END)::FLOAT
    / NULLIF(COUNT(DISTINCT player_id), 0) * 100, 2)                               AS d1_retention_pct,
  ROUND(COUNT(DISTINCT CASE WHEN days_since_first = 7 THEN player_id END)::FLOAT
    / NULLIF(COUNT(DISTINCT player_id), 0) * 100, 2)                               AS d7_retention_pct,
  ROUND(COUNT(DISTINCT CASE WHEN days_since_first = 10 THEN player_id END)::FLOAT
    / NULLIF(COUNT(DISTINCT player_id), 0) * 100, 2)                               AS d10_retention_pct,
  ROUND(COUNT(DISTINCT CASE WHEN days_since_first = 30 THEN player_id END)::FLOAT
    / NULLIF(COUNT(DISTINCT player_id), 0) * 100, 2)                               AS d30_retention_pct
FROM retention_base
GROUP BY cohort_date
ORDER BY cohort_date;


-- Gold: LTV by player segment

CREATE OR REPLACE DYNAMIC TABLE ANALYTICS.GOLD_LTV_BY_SEGMENT
  TARGET_LAG = '10 minutes'
  WAREHOUSE = LOOTSTREAM_WH
  REFRESH_MODE = AUTO
  INITIALIZE = ON_CREATE
AS
SELECT
  player_segment,
  COUNT(*)                                          AS player_count,
  ROUND(AVG(total_spend_usd), 2)                    AS avg_ltv,
  ROUND(MEDIAN(total_spend_usd), 2)                 AS median_ltv,
  MAX(total_spend_usd)                              AS max_ltv,
  ROUND(SUM(total_spend_usd), 2)                    AS total_revenue,
  ROUND(AVG(active_days), 1)                        AS avg_active_days,
  ROUND(AVG(total_purchases), 1)                    AS avg_purchases,
  ROUND(
    CASE WHEN SUM(total_purchases) > 0
      THEN SUM(total_spend_usd) / SUM(total_purchases)
      ELSE 0
    END, 2)                                         AS avg_revenue_per_transaction
FROM STAGING.SILVER_PLAYER_PROFILES
GROUP BY player_segment
ORDER BY avg_ltv DESC;



-- Gold: card valuation index (economy health)
CREATE OR REPLACE DYNAMIC TABLE ANALYTICS.GOLD_CARD_ECONOMY
  TARGET_LAG = '10 minutes'
  WAREHOUSE = LOOTSTREAM_WH
  REFRESH_MODE = AUTO
  INITIALIZE = ON_CREATE
AS
WITH upgrade_demand AS (
  SELECT
    card_id,
    card_rarity,
    DATE(event_timestamp) AS activity_date,
    COUNT(*)              AS upgrade_count,
    SUM(gold_cost)        AS total_gold_spent,
    AVG(gold_cost)        AS avg_gold_cost,
    AVG(new_level)        AS avg_level_reached
  FROM STAGING.SILVER_CARD_UPGRADES
  GROUP BY card_id, card_rarity, DATE(event_timestamp)
),
trade_demand AS (
  SELECT
    requested_card_id     AS card_id,
    DATE(event_timestamp) AS activity_date,
    COUNT(*)              AS times_requested,
    COUNT(CASE WHEN trade_status = 'COMPLETED' THEN 1 END) AS times_traded
  FROM STAGING.SILVER_PLAYER_TRADES
  GROUP BY requested_card_id, DATE(event_timestamp)
),
chest_supply AS (
  SELECT
    card_id,
    DATE(event_timestamp) AS activity_date,
    SUM(quantity)         AS cards_dropped
  FROM STAGING.SILVER_CHEST_CARDS_FLATTENED
  GROUP BY card_id, DATE(event_timestamp)
)
SELECT
  COALESCE(u.card_id, t.card_id, c.card_id)       AS card_id,
  COALESCE(u.activity_date, t.activity_date, c.activity_date) AS activity_date,
  u.card_rarity,
  COALESCE(u.upgrade_count, 0)                     AS upgrade_count,
  COALESCE(u.total_gold_spent, 0)                  AS total_gold_spent,
  COALESCE(u.avg_gold_cost, 0)                     AS avg_gold_cost,
  COALESCE(t.times_requested, 0)                   AS trade_demand,
  COALESCE(t.times_traded, 0)                      AS trades_completed,
  COALESCE(c.cards_dropped, 0)                     AS chest_supply,
  CASE WHEN COALESCE(c.cards_dropped, 0) > 0
    THEN ROUND(COALESCE(t.times_requested, 0)::FLOAT / c.cards_dropped, 3)
    ELSE NULL
  END                                              AS demand_supply_ratio
FROM upgrade_demand u
FULL OUTER JOIN trade_demand t
  ON u.card_id = t.card_id AND u.activity_date = t.activity_date
FULL OUTER JOIN chest_supply c
  ON COALESCE(u.card_id, t.card_id) = c.card_id
  AND COALESCE(u.activity_date, t.activity_date) = c.activity_date;



  -- Gold: spending distribution by segment

CREATE OR REPLACE DYNAMIC TABLE ANALYTICS.GOLD_SPENDING_DISTRIBUTION
  TARGET_LAG = '10 minutes'
  WAREHOUSE = LOOTSTREAM_WH
  REFRESH_MODE = AUTO
  INITIALIZE = ON_CREATE
AS
SELECT
  DATE(g.event_timestamp)                           AS purchase_date,
  p.player_segment,
  COUNT(*)                                          AS transaction_count,
  COUNT(DISTINCT g.player_id)                       AS unique_buyers,
  SUM(g.usd_price)                                  AS total_revenue,
  AVG(g.usd_price)                                  AS avg_transaction_value,
  SUM(g.gem_amount)                                 AS total_gems_sold,
  COUNT(CASE WHEN g.is_first_purchase THEN 1 END)   AS first_time_buyers,
  COUNT(CASE WHEN g.promotion_id IS NOT NULL THEN 1 END) AS promo_purchases
FROM STAGING.SILVER_GEM_PURCHASES g
JOIN STAGING.SILVER_PLAYER_PROFILES p ON g.player_id = p.player_id
GROUP BY DATE(g.event_timestamp), p.player_segment
ORDER BY purchase_date, player_segment;