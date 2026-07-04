"""Prepare tables for the MLB calibration analysis (analysis/mlb_calibration.ipynb).

Third layer of db/scripts/ (pull -> build -> prepare): tables prepared for
one specific analysis, namespaced mlb_calib_*. Owns the dataset definition
that would otherwise live in notebook temp views: universe filter, game
mapping, scheduled-start resolution, side, dedup, weather parsing. The
notebook loads these tables with straightforward reads and nothing else.

Run manually, not from refresh.py: a finished analysis's prepared tables
are the exact dataset its write-up was computed from, and auto-rebuilding
them on refresh would silently desync the write-up's numbers from the db.
Rebuilds from scratch on every run:

    uv run db/scripts/prepare_mlb_calibration.py

Tables:
- mlb_calib_pre_snapshots: one row per (game, side), the last trade
  before scheduled start within 24 hours, with parsed weather
- mlb_calib_inning_snapshots: one row per (game, side, entering inning
  2-10), the last trade during the preceding inning
- mlb_calib_pre_window_trades: every trade in the 24h pre-start window,
  for the method checks the snapshot tables cannot serve
- mlb_calib_build_info: single row making the freeze visible
"""

import duckdb

# Analysis choices (bucket boundaries, condition grouping, season-half
# splits) stay in the notebook. Everything here is dataset definition.


def create_source_views(con: duckdb.DuckDBPyConnection) -> None:
    """Temp views over the mirrors; the tables below select from these."""
    # universe: markets that settled yes or no, excluding the All-Star
    # events (yes_sub_title AL/NL). Team label fix: one market is labeled
    # 'Chicago W'; rename so it groups with the rest of the White Sox
    con.sql("""
        CREATE OR REPLACE TEMP VIEW calib_universe AS
        SELECT ticker,
               event_ticker,
               CASE WHEN yes_sub_title = 'Chicago W' THEN 'Chicago WS'
                    ELSE yes_sub_title END AS team,
               CASE WHEN result = 'yes' THEN 1 ELSE 0 END AS y,
               regexp_extract(ticker, '-([A-Z]+)$', 1) AS yes_abbr
        FROM markets_typed
        WHERE status = 'finalized'
          AND market_type = 'binary'
          AND result IN ('yes', 'no')
          AND coalesce(yes_sub_title, '') NOT IN ('AL', 'NL')
    """)
    # game mapping and scheduled start. 2026 tickers carry a start time
    # (ticker_start_utc); 2025 tickers don't, so those games fall back to
    # the MLB schedule's game_date
    con.sql("""
        CREATE OR REPLACE TEMP VIEW calib_markets AS
        SELECT u.ticker, u.event_ticker, u.team, u.y,
               k.game_pk,
               CASE WHEN u.yes_abbr = k.home_abbr THEN 'home'
                    ELSE 'away' END AS side,
               coalesce(
                   CAST(replace(k.ticker_start_utc, '+00:00', '')
                        AS TIMESTAMP),
                   g.game_date
               ) AS sched_start
        FROM calib_universe u
        JOIN kalshi_mlb_map k USING (event_ticker)
        JOIN mlb_games_typed g USING (game_pk)
    """)
    con.sql("""
        CREATE OR REPLACE TEMP VIEW calib_inning_starts AS
        SELECT game_pk, inning, min(start_time) AS inning_start
        FROM mlb_plays_typed
        GROUP BY game_pk, inning
    """)


def create_tables(con: duckdb.DuckDBPyConnection) -> None:
    con.sql(r"""
        CREATE OR REPLACE TABLE mlb_calib_pre_window_trades AS
        SELECT cm.game_pk,
               cm.ticker,
               cm.side,
               CAST(t.yes_price_dollars AS DOUBLE) AS p,
               cm.y,
               t.taker_outcome_side,
               t.created_time,
               cm.sched_start
        FROM trades_typed t
        JOIN calib_markets cm USING (ticker)
        WHERE t.created_time < cm.sched_start
          AND t.created_time >= cm.sched_start - INTERVAL 24 HOURS
    """)
    # dedup: one row per (game, side), the last trade wins. The seven
    # games listed twice on 2025-04-18 have two markets per side;
    # partitioning by (game_pk, side) collapses them to one snapshot
    # each. Hundreds of snapshots have several trades sharing the last
    # timestamp (one taker order sweeping several book levels), so "the
    # last trade" is ambiguous; p averages the tied prices, which is
    # deterministic and at worst half a tick from any single print.
    # Weather: raw parsed values only; grouping conditions is an analysis
    # choice and stays in the notebook, like bucket boundaries
    con.sql(r"""
        CREATE OR REPLACE TABLE mlb_calib_pre_snapshots AS
        WITH last_trades AS (
            SELECT cm.game_pk,
                   cm.event_ticker,
                   cm.ticker,
                   cm.team,
                   cm.side,
                   cm.sched_start,
                   cm.y,
                   CAST(t.yes_price_dollars * 100 AS BIGINT) AS p_cents,
                   t.created_time
            FROM trades_typed t
            JOIN calib_markets cm USING (ticker)
            WHERE t.created_time < cm.sched_start
              AND t.created_time >= cm.sched_start - INTERVAL 24 HOURS
            QUALIFY t.created_time = max(t.created_time) OVER (
                PARTITION BY cm.game_pk, cm.side)
        ),
        snap AS (
            SELECT game_pk,
                   side,
                   min(event_ticker) AS event_ticker,
                   min(ticker) AS ticker,
                   min(team) AS team,
                   min(y) AS y,
                   -- integer-cent sum, one division: exact and
                   -- order-independent, unlike avg() over DOUBLEs
                   sum(p_cents) / (100.0 * count(*)) AS p,
                   min(created_time) AS created_time,
                   min(sched_start) AS sched_start
            FROM last_trades
            GROUP BY game_pk, side
        )
        SELECT s.game_pk,
               s.event_ticker,
               s.ticker,
               s.team,
               s.side,
               year(s.sched_start) AS season,
               s.p,
               s.y,
               s.created_time,
               s.sched_start,
               w.condition,
               CAST(w.temp AS INT) AS temp_f,
               CAST(regexp_extract(w.wind, '(\d+) mph', 1) AS INT)
                   AS wind_mph
        FROM snap s
        LEFT JOIN mlb_weather w ON w.game_pk = s.game_pk
    """)
    # inning start times come from play-by-play wall clock timestamps;
    # entering = 10 is the price entering extras. Same tie handling as
    # the pre-game snapshots: p averages trades sharing the last
    # timestamp of the preceding inning
    con.sql("""
        CREATE OR REPLACE TABLE mlb_calib_inning_snapshots AS
        WITH last_trades AS (
            SELECT cm.game_pk,
                   cm.ticker,
                   cm.team,
                   cm.side,
                   b.inning AS entering,
                   CAST(t.yes_price_dollars * 100 AS BIGINT) AS p_cents,
                   cm.y,
                   t.created_time
            FROM trades_typed t
            JOIN calib_markets cm USING (ticker)
            JOIN calib_inning_starts prev ON prev.game_pk = cm.game_pk
            JOIN calib_inning_starts b
                ON b.game_pk = cm.game_pk AND b.inning = prev.inning + 1
            WHERE b.inning BETWEEN 2 AND 10
              AND t.created_time >= prev.inning_start
              AND t.created_time < b.inning_start
            QUALIFY t.created_time = max(t.created_time) OVER (
                PARTITION BY cm.game_pk, cm.side, b.inning)
        )
        SELECT game_pk,
               min(ticker) AS ticker,
               min(team) AS team,
               side,
               entering,
               sum(p_cents) / (100.0 * count(*)) AS p,
               min(y) AS y,
               min(created_time) AS created_time
        FROM last_trades
        GROUP BY game_pk, side, entering
    """)
    # a prepared table pinned to old data must not be mistaken for a
    # current one; this row makes the freeze visible
    con.sql("""
        CREATE OR REPLACE TABLE mlb_calib_build_info AS
        SELECT now() AS built_at,
               (SELECT min(t.created_time)::DATE
                FROM trades_typed t
                JOIN calib_markets cm USING (ticker)) AS data_start,
               (SELECT max(t.created_time)::DATE
                FROM trades_typed t
                JOIN calib_markets cm USING (ticker)) AS data_end,
               (SELECT count(DISTINCT game_pk) FROM calib_markets)
                   AS n_games,
               (SELECT count(*) FROM calib_markets) AS n_markets,
               (SELECT count(*) FROM mlb_calib_pre_snapshots)
                   AS n_pre_snapshots,
               (SELECT count(*) FROM mlb_calib_inning_snapshots)
                   AS n_inning_snapshots
    """)


def report(con: duckdb.DuckDBPyConnection) -> None:
    print("Exclusion accounting (markets_typed):")
    dispositions = con.sql("""
        SELECT CASE
                   WHEN status != 'finalized' THEN 'not finalized'
                   WHEN market_type != 'binary' THEN 'not binary'
                   WHEN result = 'scalar' THEN 'scalar result'
                   WHEN coalesce(yes_sub_title, '') IN ('AL', 'NL')
                       THEN 'All-Star'
                   ELSE 'kept'
               END AS disposition,
               count(*) AS n
        FROM markets_typed
        GROUP BY disposition ORDER BY n DESC
    """).fetchall()
    for disposition, n in dispositions:
        print(f"  {disposition}: {n}")

    n_events, n_games = con.sql("""
        SELECT count(DISTINCT event_ticker), count(DISTINCT game_pk)
        FROM calib_markets
    """).fetchone()
    print(f"Events vs distinct games: {n_events} events, {n_games} games "
          f"({n_events - n_games} duplicate listings)")

    (n_fixed,) = con.sql("""
        SELECT count(*) FROM markets_typed
        WHERE yes_sub_title = 'Chicago W'
    """).fetchone()
    print(f"Label-fixed markets ('Chicago W' -> 'Chicago WS'): {n_fixed}")

    (n_no_window,) = con.sql("""
        SELECT count(*) FROM calib_markets
        WHERE ticker NOT IN (
            SELECT DISTINCT ticker FROM mlb_calib_pre_window_trades)
    """).fetchone()
    (n_games_no_window,) = con.sql("""
        SELECT count(DISTINCT game_pk) FROM calib_markets
        WHERE game_pk NOT IN (
            SELECT DISTINCT game_pk FROM mlb_calib_pre_window_trades)
    """).fetchone()
    print(f"Markets with no trade in the 24h pre-start window: "
          f"{n_no_window}")
    print(f"Games with no trade in the 24h pre-start window: "
          f"{n_games_no_window}")

    print("Inning snapshots per entering inning:")
    per_inning = con.sql("""
        SELECT entering, count(*) FROM mlb_calib_inning_snapshots
        GROUP BY entering ORDER BY entering
    """).fetchall()
    for entering, n in per_inning:
        print(f"  entering {entering}: {n}")

    print("Build info:")
    info = con.sql("SELECT * FROM mlb_calib_build_info").pl()
    for col in info.columns:
        print(f"  {col}: {info[col][0]}")


def check(con: duckdb.DuckDBPyConnection) -> None:
    """Asserted invariants, not frozen counts, so they survive refreshes."""
    (n_universe,) = con.sql("SELECT count(*) FROM calib_universe").fetchone()
    (n_mapped,) = con.sql("SELECT count(*) FROM calib_markets").fetchone()
    assert n_mapped == n_universe, (
        f"{n_universe - n_mapped} universe markets have no game in "
        f"kalshi_mlb_map"
    )

    (dup_pre,) = con.sql("""
        SELECT count(*) FROM (
            SELECT game_pk, side FROM mlb_calib_pre_snapshots
            GROUP BY game_pk, side HAVING count(*) > 1
        )
    """).fetchone()
    assert dup_pre == 0, f"{dup_pre} (game, side) pairs duplicated in pre_snapshots"

    (dup_inn,) = con.sql("""
        SELECT count(*) FROM (
            SELECT game_pk, side, entering FROM mlb_calib_inning_snapshots
            GROUP BY game_pk, side, entering HAVING count(*) > 1
        )
    """).fetchone()
    assert dup_inn == 0, (
        f"{dup_inn} (game, side, entering) triples duplicated in "
        f"inning_snapshots"
    )

    for table in ("mlb_calib_pre_snapshots", "mlb_calib_inning_snapshots",
                  "mlb_calib_pre_window_trades"):
        (bad,) = con.sql(f"""
            SELECT count(*) FROM {table}
            WHERE p <= 0 OR p >= 1 OR y NOT IN (0, 1)
        """).fetchone()
        assert bad == 0, f"{bad} rows in {table} with p outside (0, 1) or bad y"
    (null_start,) = con.sql("""
        SELECT count(*) FROM mlb_calib_pre_snapshots
        WHERE sched_start IS NULL
    """).fetchone()
    assert null_start == 0, f"{null_start} pre_snapshots with null sched_start"

    (n_teams,) = con.sql(
        "SELECT count(DISTINCT team) FROM mlb_calib_pre_snapshots"
    ).fetchone()
    assert n_teams == 30, f"{n_teams} distinct team labels, expected 30"

    (one_sided,) = con.sql("""
        SELECT count(*) FROM (
            SELECT game_pk FROM mlb_calib_pre_snapshots
            GROUP BY game_pk HAVING count(DISTINCT side) != 2
        )
    """).fetchone()
    assert one_sided == 0, f"{one_sided} games without both sides in pre_snapshots"

    print("All checks passed")


def main(db_path: str = "db/pma.db") -> None:
    con = duckdb.connect(db_path)
    create_source_views(con)
    create_tables(con)
    report(con)
    check(con)
    con.close()


if __name__ == "__main__":
    main()
