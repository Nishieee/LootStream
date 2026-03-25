-- ============================================
-- STEP 2A: Create the warehouse
-- ============================================

CREATE WAREHOUSE IF NOT EXISTS LOOTSTREAM_WH
  WITH WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'LootStream gaming economy analytics';

-- ============================================
-- STEP 2B: Create the database
-- ============================================

CREATE DATABASE IF NOT EXISTS LOOTSTREAM
  COMMENT = 'Gaming economy analytics platform';

-- ============================================
-- STEP 2C: Create schemas (medallion architecture)
-- ============================================

USE DATABASE LOOTSTREAM;

-- Bronze layer: raw Kafka events land here
CREATE SCHEMA IF NOT EXISTS RAW
  COMMENT = 'Bronze layer — raw events from Kafka';

-- Silver layer: cleaned + transformed (for Phase 3 dbt)
CREATE SCHEMA IF NOT EXISTS STAGING
  COMMENT = 'Silver layer — cleaned and deduplicated events';

-- Gold layer: business metrics (for Phase 3 dbt)
CREATE SCHEMA IF NOT EXISTS ANALYTICS
  COMMENT = 'Gold layer — aggregated metrics and KPIs';