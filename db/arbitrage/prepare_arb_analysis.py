"""Prepare tables for the cross-platform arbitrage analysis.

Reads from db/arb_orderbooks.db. Writes analysis tables to the same database.

Book structure:
- Kalshi: separate YES/NO books per team ticker, sorted ascending by price.
  All entries are resting buy orders. Best bid = last element (highest price).
  YES best ask = 1 - best NO bid.
- Polymarket: single slug per game for the away team. Bids sorted descending
  (best bid = first element), offers sorted ascending (best ask = first element).

Arb condition: one platform's best bid > the other's best ask on the same
outcome. Two directions checked: buy_poly (buy on Poly, offset on Kalshi)
and buy_kalshi (the reverse).

Tables created:
- arb_bbo: BBO per book side, change detection: a row is kept when the top of
  the book changed (price, size, or the side going empty — empty sides emit a
  NULL-price row so downstream forward-fills stop serving vanished quotes)
- arb_states: cross-platform state at each change, with arb/fee/size
- arb_episodes: contiguous arb windows with duration and metrics
- arb_build_info: dataset metadata

Run:
    uv run db/arbitrage/prepare_arb_analysis.py
"""

import duckdb

DB_PATH = "db/arb_orderbooks.db"

# Top-of-book extractors. An empty book side yields NULL price/size — that row
# still enters arb_bbo so the disappearance of a quote is itself a recorded
# state change.
KALSHI_LAST_PRICE = """CASE WHEN json_array_length(o.book_json) > 0
    THEN CAST(json_extract_string(o.book_json,
        '$[' || (json_array_length(o.book_json) - 1) || '][0]') AS DOUBLE)
    END"""

KALSHI_LAST_SIZE = """CASE WHEN json_array_length(o.book_json) > 0
    THEN CAST(json_extract_string(o.book_json,
        '$[' || (json_array_length(o.book_json) - 1) || '][1]') AS DOUBLE)
    END"""

POLY_FIRST_PRICE = """CASE WHEN json_array_length(o.book_json) > 0
    THEN CAST(json_extract_string(o.book_json, '$[0][0]') AS DOUBLE)
    END"""

POLY_FIRST_SIZE = """CASE WHEN json_array_length(o.book_json) > 0
    THEN CAST(json_extract_string(o.book_json, '$[0][1]') AS DOUBLE)
    END"""

GAME_KEY = "m.away_team || '@' || m.home_team || '-' || m.game_date::VARCHAR"

KALSHI_TAKER_THETA = 0.07
POLY_TAKER_THETA = 0.06
BLACKOUT_SECONDS = 30


def create_bbo(con: duckdb.DuckDBPyConnection) -> None:
    """Extract best bid/offer from each orderbook snapshot.

    Change detection: a row is kept when the top of the book changed — price,
    size, or the side going empty (NULL price/size). Without the empty rows,
    the ASOF join downstream would forward-fill quotes that no longer exist;
    without size in the change key, sizes would freeze at whatever they were
    when the price level first appeared.
    """
    con.sql(f"""
        CREATE OR REPLACE TABLE arb_bbo AS
        WITH raw_bbo AS (
            SELECT o.timestamp, {GAME_KEY} AS game_key, m.game_date,
                   'k_bid' AS update_type,
                   {KALSHI_LAST_PRICE} AS price,
                   {KALSHI_LAST_SIZE} AS size
            FROM orderbook_snapshots o
            JOIN matched_markets m ON o.market_id = m.kalshi_ticker_away
            WHERE o.platform = 'kalshi' AND o.side = 'yes'

            UNION ALL

            SELECT o.timestamp, {GAME_KEY}, m.game_date,
                   'k_ask',
                   1.0 - {KALSHI_LAST_PRICE},
                   {KALSHI_LAST_SIZE}
            FROM orderbook_snapshots o
            JOIN matched_markets m ON o.market_id = m.kalshi_ticker_away
            WHERE o.platform = 'kalshi' AND o.side = 'no'

            UNION ALL

            SELECT o.timestamp, {GAME_KEY}, m.game_date,
                   'p_bid',
                   {POLY_FIRST_PRICE},
                   {POLY_FIRST_SIZE}
            FROM orderbook_snapshots o
            JOIN matched_markets m ON o.market_id = m.poly_slug
            WHERE o.platform = 'polymarket' AND o.side = 'bids'

            UNION ALL

            SELECT o.timestamp, {GAME_KEY}, m.game_date,
                   'p_ask',
                   {POLY_FIRST_PRICE},
                   {POLY_FIRST_SIZE}
            FROM orderbook_snapshots o
            JOIN matched_markets m ON o.market_id = m.poly_slug
            WHERE o.platform = 'polymarket' AND o.side = 'offers'
        )
        SELECT timestamp, game_key, game_date, update_type, price, size
        FROM (
            SELECT *,
                   LAG(price) OVER (
                       PARTITION BY game_key, update_type ORDER BY timestamp
                   ) AS prev_price,
                   LAG(size) OVER (
                       PARTITION BY game_key, update_type ORDER BY timestamp
                   ) AS prev_size,
                   ROW_NUMBER() OVER (
                       PARTITION BY game_key, update_type ORDER BY timestamp
                   ) AS rn
            FROM raw_bbo
        )
        WHERE rn = 1
           OR price IS DISTINCT FROM prev_price
           OR size IS DISTINCT FROM prev_size
    """)
    n, n_empty = con.execute("""
        SELECT count(*), count(*) FILTER (price IS NULL) FROM arb_bbo
    """).fetchone()
    print(f"  arb_bbo: {n:,} top-of-book changes ({n_empty:,} empty-side rows)")


def create_states(con: duckdb.DuckDBPyConnection) -> None:
    """ASOF-join the four BBO streams into a cross-platform state table."""
    kt = KALSHI_TAKER_THETA
    pt = POLY_TAKER_THETA
    con.sql(f"""
        CREATE OR REPLACE TABLE arb_states AS
        WITH all_ts AS (
            SELECT DISTINCT timestamp, game_key, game_date FROM arb_bbo
        ),
        kb AS (SELECT timestamp, game_key, price AS k_bid, size AS k_bid_size
               FROM arb_bbo WHERE update_type = 'k_bid'),
        ka AS (SELECT timestamp, game_key, price AS k_ask, size AS k_ask_size
               FROM arb_bbo WHERE update_type = 'k_ask'),
        pb AS (SELECT timestamp, game_key, price AS p_bid, size AS p_bid_size
               FROM arb_bbo WHERE update_type = 'p_bid'),
        pa AS (SELECT timestamp, game_key, price AS p_ask, size AS p_ask_size
               FROM arb_bbo WHERE update_type = 'p_ask'),
        joined AS (
            SELECT t.timestamp, t.game_key, t.game_date,
                   kb.k_bid, kb.k_bid_size,
                   ka.k_ask, ka.k_ask_size,
                   pb.p_bid, pb.p_bid_size,
                   pa.p_ask, pa.p_ask_size
            FROM all_ts t
            ASOF JOIN kb ON t.game_key = kb.game_key AND t.timestamp >= kb.timestamp
            ASOF JOIN ka ON t.game_key = ka.game_key AND t.timestamp >= ka.timestamp
            ASOF JOIN pb ON t.game_key = pb.game_key AND t.timestamp >= pb.timestamp
            ASOF JOIN pa ON t.game_key = pa.game_key AND t.timestamp >= pa.timestamp
        ),
        with_arb AS (
            SELECT *,
                   k_ask - k_bid AS k_spread,
                   p_ask - p_bid AS p_spread,
                   GREATEST(0, k_bid - p_ask, p_bid - k_ask) AS gross_arb,
                   CASE
                       WHEN k_bid - p_ask >= p_bid - k_ask AND k_bid - p_ask > 0
                           THEN 'buy_poly'
                       WHEN p_bid - k_ask > 0 THEN 'buy_kalshi'
                   END AS direction,
                   CASE
                       WHEN k_bid - p_ask >= p_bid - k_ask AND k_bid - p_ask > 0
                           THEN {pt} * p_ask * (1 - p_ask)
                                + {kt} * (1 - k_bid) * k_bid
                       WHEN p_bid - k_ask > 0
                           THEN {kt} * k_ask * (1 - k_ask)
                                + {pt} * (1 - p_bid) * p_bid
                       ELSE 0
                   END AS total_fee,
                   CASE
                       WHEN k_bid - p_ask >= p_bid - k_ask AND k_bid - p_ask > 0
                           THEN LEAST(p_ask_size, k_bid_size)
                       WHEN p_bid - k_ask > 0
                           THEN LEAST(k_ask_size, p_bid_size)
                       ELSE LEAST(k_bid_size, k_ask_size, p_bid_size, p_ask_size)
                   END AS min_size
            FROM joined
            WHERE k_bid IS NOT NULL AND k_ask IS NOT NULL
              AND p_bid IS NOT NULL AND p_ask IS NOT NULL
              AND k_bid <= k_ask + 0.0001
              AND p_bid <= p_ask + 0.0001
        )
        SELECT *, gross_arb - total_fee AS net_arb
        FROM with_arb
    """)
    n = con.execute("SELECT count(*) FROM arb_states").fetchone()[0]
    n_arb = con.execute(
        "SELECT count(*) FROM arb_states WHERE gross_arb > 0"
    ).fetchone()[0]
    print(f"  arb_states: {n:,} rows ({n_arb:,} with arb > 0)")


def create_episodes(con: duckdb.DuckDBPyConnection) -> None:
    """Detect contiguous arb windows and compute per-episode metrics.

    Excludes episodes that start within BLACKOUT_SECONDS of a collector
    start or reconnect event — those produce phantom arbs from stale
    forward-filled book state.
    """
    con.sql(f"""
        CREATE OR REPLACE TABLE arb_episodes AS
        WITH blackout_windows AS (
            SELECT timestamp - INTERVAL {BLACKOUT_SECONDS} SECOND AS win_start,
                   timestamp + INTERVAL {BLACKOUT_SECONDS} SECOND AS win_end
            FROM collection_metadata
            WHERE event IN ('start', 'reconnect')
        ),
        flagged AS (
            SELECT *,
                   CASE WHEN gross_arb > 0 AND COALESCE(
                       LAG(gross_arb) OVER (
                           PARTITION BY game_key ORDER BY timestamp), 0
                   ) <= 0 THEN 1 ELSE 0 END AS is_start
            FROM arb_states
        ),
        grouped AS (
            SELECT *,
                   SUM(is_start) OVER (
                       PARTITION BY game_key ORDER BY timestamp
                   ) AS ep_grp
            FROM flagged
        ),
        agg AS (
            SELECT game_key, game_date, ep_grp,
                   MIN(timestamp) AS start_ts,
                   MAX(timestamp) AS last_arb_ts,
                   MAX(gross_arb) AS max_gross_arb,
                   AVG(gross_arb) AS avg_gross_arb,
                   MAX(net_arb) AS max_net_arb,
                   AVG(net_arb) AS avg_net_arb,
                   MAX(direction) AS direction,
                   COUNT(*) AS n_states,
                   MIN(min_size) AS bottleneck_liquidity,
                   AVG(total_fee) AS avg_fee
            FROM grouped
            WHERE gross_arb > 0
            GROUP BY game_key, game_date, ep_grp
        ),
        closings AS (
            SELECT a.game_key, a.ep_grp,
                   MIN(s.timestamp) AS close_ts
            FROM agg a
            JOIN arb_states s
              ON s.game_key = a.game_key
             AND s.timestamp > a.last_arb_ts
             AND s.gross_arb <= 0
            GROUP BY a.game_key, a.ep_grp
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY a.start_ts, a.game_key) AS episode_id,
            a.game_key, a.game_date,
            a.start_ts,
            COALESCE(c.close_ts, a.last_arb_ts) AS end_ts,
            EXTRACT(EPOCH FROM
                COALESCE(c.close_ts, a.last_arb_ts) - a.start_ts
            ) AS duration_s,
            a.max_gross_arb, a.avg_gross_arb,
            a.max_net_arb, a.avg_net_arb,
            a.direction, a.n_states,
            a.bottleneck_liquidity, a.avg_fee
        FROM agg a
        LEFT JOIN closings c
          ON c.game_key = a.game_key AND c.ep_grp = a.ep_grp
        WHERE NOT EXISTS (
            SELECT 1 FROM blackout_windows b
            WHERE a.start_ts BETWEEN b.win_start AND b.win_end
        )
    """)
    n = con.execute("SELECT count(*) FROM arb_episodes").fetchone()[0]
    n_net = con.execute(
        "SELECT count(*) FROM arb_episodes WHERE max_net_arb > 0"
    ).fetchone()[0]
    print(f"  arb_episodes: {n:,} total ({n_net:,} profitable after fees)")


def create_build_info(con: duckdb.DuckDBPyConnection) -> None:
    con.sql("""
        CREATE OR REPLACE TABLE arb_build_info AS
        SELECT
            now() AS built_at,
            (SELECT min(timestamp)::DATE FROM arb_states) AS data_start,
            (SELECT max(timestamp)::DATE FROM arb_states) AS data_end,
            (SELECT count(DISTINCT game_key) FROM arb_states) AS n_games,
            (SELECT count(*) FROM arb_bbo) AS n_bbo_changes,
            (SELECT count(*) FROM arb_states) AS n_states,
            (SELECT count(*) FROM arb_states WHERE gross_arb > 0) AS n_arb_states,
            (SELECT count(*) FROM arb_episodes) AS n_episodes,
            (SELECT count(*) FROM arb_episodes WHERE max_net_arb > 0) AS n_profitable
    """)


def report(con: duckdb.DuckDBPyConnection) -> None:
    info = con.execute("SELECT * FROM arb_build_info").fetchone()
    print(f"\nBuild: {info[0]}")
    print(f"Data: {info[1]} to {info[2]}, {info[3]} games")
    print(f"BBO changes: {info[4]:,}")
    print(f"States: {info[5]:,} ({info[6]:,} with arb)")
    print(f"Episodes: {info[7]:,} gross, {info[8]:,} net profitable")

    print("\nPer-game episodes:")
    for r in con.execute("""
        SELECT game_key, count(*) AS n,
               sum(CASE WHEN max_net_arb > 0 THEN 1 ELSE 0 END) AS n_net
        FROM arb_episodes GROUP BY game_key ORDER BY n DESC
    """).fetchall():
        print(f"  {r[0]}: {r[1]} gross, {r[2]} net")

    print("\nDuration buckets:")
    r = con.execute("""
        SELECT
            count(*) FILTER (duration_s < 1) AS under_1s,
            count(*) FILTER (duration_s >= 1 AND duration_s < 2) AS s1,
            count(*) FILTER (duration_s >= 2 AND duration_s < 3) AS s2,
            count(*) FILTER (duration_s >= 3 AND duration_s < 5) AS s3_5,
            count(*) FILTER (duration_s >= 5 AND duration_s < 10) AS s5_10,
            count(*) FILTER (duration_s >= 10) AS s10p
        FROM arb_episodes
    """).fetchone()
    print(f"  <1s: {r[0]}, 1-2s: {r[1]}, 2-3s: {r[2]}, "
          f"3-5s: {r[3]}, 5-10s: {r[4]}, 10s+: {r[5]}")


def check(con: duckdb.DuckDBPyConnection) -> None:
    (bad,) = con.execute(
        "SELECT count(*) FROM arb_states WHERE gross_arb < -1e-10"
    ).fetchone()
    assert bad == 0, f"{bad} rows with negative gross arb"

    (bad,) = con.execute(
        "SELECT count(*) FROM arb_states WHERE k_spread < -0.0002"
    ).fetchone()
    assert bad == 0, f"{bad} rows with negative Kalshi spread"

    (bad,) = con.execute(
        "SELECT count(*) FROM arb_states WHERE p_spread < -0.0002"
    ).fetchone()
    assert bad == 0, f"{bad} rows with negative Poly spread"

    (bad,) = con.execute(
        "SELECT count(*) FROM arb_episodes WHERE duration_s < -1e-10"
    ).fetchone()
    assert bad == 0, f"{bad} episodes with negative duration"

    print("All checks passed")


def main() -> None:
    con = duckdb.connect(DB_PATH)
    print("Step 1: Extracting BBO...")
    create_bbo(con)
    print("Step 2: Building cross-platform states...")
    create_states(con)
    print("Step 3: Detecting episodes...")
    create_episodes(con)
    print("Step 4: Build info...")
    create_build_info(con)
    report(con)
    check(con)
    con.close()


if __name__ == "__main__":
    main()
