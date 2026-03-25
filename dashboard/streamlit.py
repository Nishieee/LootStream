import streamlit as st
import pandas as pd

st.set_page_config(page_title="LootStream", layout="wide")

conn = st.connection("snowflake")
session = conn.session()

# ─── Helper ───
def run_query(sql):
    return session.sql(sql).to_pandas()

# ─── Sidebar ───
st.sidebar.title("LootStream")
st.sidebar.caption("Gaming economy analytics")
page = st.sidebar.radio(
    "Navigate",
    ["Overview", "Revenue", "Retention", "Player Segments", "Economy", "Live Feed"]
)

# ═══════════════════════════════════════
# OVERVIEW
# ═══════════════════════════════════════
if page == "Overview":
    st.title("LootStream — Gaming economy analytics")
    st.caption("All metrics auto-refresh as new events stream in from Kafka")

    latest = run_query("""
        SELECT * FROM LOOTSTREAM.ANALYTICS.GOLD_DAILY_REVENUE
        ORDER BY ACTIVITY_DATE DESC LIMIT 1
    """)

    if not latest.empty:
        row = latest.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("DAU", f"{int(row['DAU']):,}")
        c2.metric("Revenue", f"${row['TOTAL_REVENUE']:,.2f}")
        c3.metric("ARPDAU", f"${row['ARPDAU']:.4f}")
        c4.metric("Conversion", f"{row['CONVERSION_RATE_PCT']:.1f}%")

    st.divider()

    counts = run_query("""
        SELECT 'Bronze' AS layer, COUNT(*) AS row_count FROM LOOTSTREAM.RAW.RAW_GEM_PURCHASES
        UNION ALL SELECT 'Bronze', COUNT(*) FROM LOOTSTREAM.RAW.RAW_CARD_UPGRADES
        UNION ALL SELECT 'Bronze', COUNT(*) FROM LOOTSTREAM.RAW.RAW_CHEST_OPENINGS
        UNION ALL SELECT 'Bronze', COUNT(*) FROM LOOTSTREAM.RAW.RAW_PLAYER_TRADES
        UNION ALL SELECT 'Silver', COUNT(*) FROM LOOTSTREAM.STAGING.SILVER_GEM_PURCHASES
        UNION ALL SELECT 'Silver', COUNT(*) FROM LOOTSTREAM.STAGING.SILVER_CARD_UPGRADES
        UNION ALL SELECT 'Silver', COUNT(*) FROM LOOTSTREAM.STAGING.SILVER_CHEST_OPENINGS
        UNION ALL SELECT 'Silver', COUNT(*) FROM LOOTSTREAM.STAGING.SILVER_PLAYER_TRADES
        UNION ALL SELECT 'Gold', COUNT(*) FROM LOOTSTREAM.ANALYTICS.GOLD_DAILY_REVENUE
    """)
    total_events = counts[counts['LAYER'] == 'Bronze']['ROW_COUNT'].sum()
    st.metric("Total events processed (bronze)", f"{int(total_events):,}")
# ═══════════════════════════════════════
# REVENUE
# ═══════════════════════════════════════
elif page == "Revenue":
    st.title("Revenue & ARPDAU")

    revenue = run_query("""
        SELECT * FROM LOOTSTREAM.ANALYTICS.GOLD_DAILY_REVENUE
        ORDER BY ACTIVITY_DATE
    """)

    if not revenue.empty:
        st.subheader("Daily revenue")
        st.line_chart(revenue, x="ACTIVITY_DATE", y="TOTAL_REVENUE")

        st.subheader("ARPDAU trend")
        st.line_chart(revenue, x="ACTIVITY_DATE", y="ARPDAU")

        st.subheader("Paying users vs DAU")
        st.line_chart(revenue, x="ACTIVITY_DATE", y=["DAU", "PAYING_USERS"])

    spending = run_query("""
        SELECT * FROM LOOTSTREAM.ANALYTICS.GOLD_SPENDING_DISTRIBUTION
        ORDER BY PURCHASE_DATE
    """)

    if not spending.empty:
        st.subheader("Revenue by player segment")
        pivot = spending.pivot_table(
            index="PURCHASE_DATE",
            columns="PLAYER_SEGMENT",
            values="TOTAL_REVENUE",
            aggfunc="sum"
        ).fillna(0)
        st.bar_chart(pivot)


# ═══════════════════════════════════════
# RETENTION
# ═══════════════════════════════════════
elif page == "Retention":
    st.title("Retention cohorts")

    retention = run_query("""
        SELECT * FROM LOOTSTREAM.ANALYTICS.GOLD_RETENTION_COHORTS
        ORDER BY COHORT_DATE
    """)

    if not retention.empty:
        st.subheader("Retention trends over time")
        st.line_chart(
            retention,
            x="COHORT_DATE",
            y=["D1_RETENTION_PCT", "D7_RETENTION_PCT", "D30_RETENTION_PCT"]
        )

        st.subheader("Latest cohort metrics")
        latest = retention.iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("D1 retention", f"{latest['D1_RETENTION_PCT']}%")
        c2.metric("D7 retention", f"{latest['D7_RETENTION_PCT']}%")
        c3.metric("D30 retention", f"{latest['D30_RETENTION_PCT']}%")

        st.subheader("Cohort detail")
        st.dataframe(retention, use_container_width=True)


# ═══════════════════════════════════════
# PLAYER SEGMENTS
# ═══════════════════════════════════════
elif page == "Player Segments":
    st.title("Player segments & LTV")

    ltv = run_query("""
        SELECT * FROM LOOTSTREAM.ANALYTICS.GOLD_LTV_BY_SEGMENT
        ORDER BY AVG_LTV DESC
    """)

    if not ltv.empty:
        st.subheader("Segment breakdown")
        c1, c2 = st.columns(2)

        with c1:
            st.caption("Player distribution")
            st.bar_chart(ltv, x="PLAYER_SEGMENT", y="PLAYER_COUNT")

        with c2:
            st.caption("Average LTV by segment")
            st.bar_chart(ltv, x="PLAYER_SEGMENT", y="AVG_LTV")

        st.subheader("Revenue contribution")
        st.bar_chart(ltv, x="PLAYER_SEGMENT", y="TOTAL_REVENUE")

        st.subheader("Full segment detail")
        st.dataframe(ltv, use_container_width=True)

    profiles_sample = run_query("""
        SELECT TOTAL_SPEND_USD, ACTIVE_DAYS, PLAYER_SEGMENT
        FROM LOOTSTREAM.STAGING.SILVER_PLAYER_PROFILES
        LIMIT 1000
    """)

    if not profiles_sample.empty:
        st.subheader("Spend vs activity (sample of 1000 players)")
        st.scatter_chart(
            profiles_sample,
            x="ACTIVE_DAYS",
            y="TOTAL_SPEND_USD",
            color="PLAYER_SEGMENT"
        )


# ═══════════════════════════════════════
# ECONOMY
# ═══════════════════════════════════════
elif page == "Economy":
    st.title("Card economy health")

    economy = run_query("""
        SELECT * FROM LOOTSTREAM.ANALYTICS.GOLD_CARD_ECONOMY
        ORDER BY ACTIVITY_DATE DESC
    """)

    if not economy.empty:
        st.subheader("Top 10 most upgraded cards")
        top_upgraded = economy.groupby("CARD_ID")["UPGRADE_COUNT"].sum().nlargest(10).reset_index()
        st.bar_chart(top_upgraded, x="CARD_ID", y="UPGRADE_COUNT")

        st.subheader("Top 10 most requested in trades")
        top_traded = economy.groupby("CARD_ID")["TRADE_DEMAND"].sum().nlargest(10).reset_index()
        st.bar_chart(top_traded, x="CARD_ID", y="TRADE_DEMAND")

        st.subheader("Demand / supply ratio by card")
        cards_list = economy["CARD_ID"].dropna().unique().tolist()
        selected_card = st.selectbox("Select a card", sorted(cards_list))

        card_data = economy[economy["CARD_ID"] == selected_card].sort_values("ACTIVITY_DATE")
        if not card_data.empty:
            st.line_chart(card_data, x="ACTIVITY_DATE", y="DEMAND_SUPPLY_RATIO")

        st.subheader("Economy imbalance (highest demand/supply)")
        imbalance = economy[economy["DEMAND_SUPPLY_RATIO"].notna()].nlargest(10, "DEMAND_SUPPLY_RATIO")
        st.dataframe(
            imbalance[["CARD_ID", "CARD_RARITY", "ACTIVITY_DATE", "TRADE_DEMAND", "CHEST_SUPPLY", "DEMAND_SUPPLY_RATIO"]],
            use_container_width=True
        )


# ═══════════════════════════════════════
# LIVE FEED
# ═══════════════════════════════════════
elif page == "Live Feed":
    st.title("Live event feed")
    st.caption("Latest events flowing through the pipeline")

    event_type = st.multiselect(
        "Filter event types",
        ["Gem purchases", "Card upgrades", "Chest openings", "Trades"],
        default=["Gem purchases", "Card upgrades", "Chest openings", "Trades"]
    )

    queries = []
    if "Gem purchases" in event_type:
        queries.append("""
            SELECT EVENT_TIMESTAMP, PLAYER_ID, 'Gem purchase' AS EVENT_TYPE,
              'Bought ' || GEM_AMOUNT || ' gems for $' || USD_PRICE AS SUMMARY
            FROM LOOTSTREAM.STAGING.SILVER_GEM_PURCHASES
        """)
    if "Card upgrades" in event_type:
        queries.append("""
            SELECT EVENT_TIMESTAMP, PLAYER_ID, 'Card upgrade' AS EVENT_TYPE,
              'Upgraded ' || CARD_ID || ' to level ' || NEW_LEVEL AS SUMMARY
            FROM LOOTSTREAM.STAGING.SILVER_CARD_UPGRADES
        """)
    if "Chest openings" in event_type:
        queries.append("""
            SELECT EVENT_TIMESTAMP, PLAYER_ID, 'Chest opening' AS EVENT_TYPE,
              'Opened ' || CHEST_TYPE || ' chest (' || CHEST_SOURCE || ')' AS SUMMARY
            FROM LOOTSTREAM.STAGING.SILVER_CHEST_OPENINGS
        """)
    if "Trades" in event_type:
        queries.append("""
            SELECT EVENT_TIMESTAMP, PLAYER_ID, 'Trade' AS EVENT_TYPE,
              TRADE_STATUS || ': offered ' || OFFERED_CARD_ID || ' for ' || REQUESTED_CARD_ID AS SUMMARY
            FROM LOOTSTREAM.STAGING.SILVER_PLAYER_TRADES
        """)

    if queries:
        combined = " UNION ALL ".join(queries)
        feed = run_query(f"""
            SELECT * FROM ({combined})
            ORDER BY EVENT_TIMESTAMP DESC
            LIMIT 50
        """)
        st.dataframe(feed, use_container_width=True, hide_index=True)

    if st.button("Refresh"):
        st.rerun()