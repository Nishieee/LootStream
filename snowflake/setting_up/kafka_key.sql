-- ============================================
-- STEP 4A: Create the role
-- ============================================

USE ROLE SECURITYADMIN;

CREATE ROLE IF NOT EXISTS KAFKA_CONNECTOR_ROLE
  COMMENT = 'Role for Kafka Snowpipe Streaming connector';

-- Grant role to SYSADMIN so it inherits into the role hierarchy
GRANT ROLE KAFKA_CONNECTOR_ROLE TO ROLE SYSADMIN;

-- ============================================
-- STEP 4B: Create a dedicated service user
-- ============================================

CREATE USER IF NOT EXISTS KAFKA_CONNECTOR_USER
  DEFAULT_ROLE = KAFKA_CONNECTOR_ROLE
  DEFAULT_WAREHOUSE = LOOTSTREAM_WH
  MUST_CHANGE_PASSWORD = FALSE
  COMMENT = 'Service user for Kafka connector';

GRANT ROLE KAFKA_CONNECTOR_ROLE TO USER KAFKA_CONNECTOR_USER;

-- ============================================
-- STEP 4C: Assign the RSA public key
-- ============================================
-- IMPORTANT: Paste your public key from Step 1 (the base64 string, no headers)

ALTER USER KAFKA_CONNECTOR_USER SET RSA_PUBLIC_KEY = 'key_here';

-- ============================================
-- STEP 4D: Verify key assignment
-- ============================================
DESC USER KAFKA_CONNECTOR_USER;
-- Look for RSA_PUBLIC_KEY_FP in the output — it should show a SHA256 fingerprint