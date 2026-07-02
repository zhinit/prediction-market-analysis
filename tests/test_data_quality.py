"""Reasonability checks for db/pma.db after a pull_kalshi_mlb.py run.

Run with: uv run pytest tests/
"""

from datetime import datetime, timedelta
from pathlib import Path

import duckdb
import pytest

DB_PATH = Path(__file__).parent.parent / "db" / "pma.db"

# from wiki/kalshi-market-object.md
KNOWN_MARKET_STATUSES = {
    "initialized",
    "inactive",
    "active",
    "closed",
    "determined",
    "disputed",
    "amended",
    "finalized",
}


@pytest.fixture(scope="module")
def con():
    if not DB_PATH.exists():
        pytest.skip(f"{DB_PATH} does not exist, run the pull script first")
    connection = duckdb.connect(str(DB_PATH), read_only=True)
    yield connection
    connection.close()


def one(con, query):
    return con.sql(query).fetchone()[0]


# schema


def test_tables_and_views_exist(con):
    names = {r[0] for r in con.sql("SELECT table_name FROM duckdb_tables()").fetchall()}
    assert {"events", "markets", "trades"} <= names
    views = {r[0] for r in con.sql("SELECT view_name FROM duckdb_views()").fetchall()}
    assert {"markets_typed", "trades_typed"} <= views


def test_tables_not_empty(con):
    assert one(con, "SELECT count(*) FROM events") > 1000
    assert one(con, "SELECT count(*) FROM markets") > 1000
    assert one(con, "SELECT count(*) FROM trades") > 1_000_000


# referential integrity


def test_every_trade_has_a_market(con):
    orphans = one(
        con,
        """
        SELECT count(*) FROM trades t
        LEFT JOIN markets m ON t.ticker = m.ticker
        WHERE m.ticker IS NULL
        """,
    )
    assert orphans == 0


def test_every_market_has_an_event(con):
    orphans = one(
        con,
        """
        SELECT count(*) FROM markets m
        LEFT JOIN events e ON m.event_ticker = e.event_ticker
        WHERE e.event_ticker IS NULL
        """,
    )
    assert orphans == 0


# typed views cast cleanly


def test_all_casts_succeed(con):
    checks = {
        "trades": {
            "created_time": "TIMESTAMP",
            "count_fp": "DECIMAL(18,6)",
            "yes_price_dollars": "DECIMAL(18,6)",
            "no_price_dollars": "DECIMAL(18,6)",
        },
        "markets": {
            "open_time": "TIMESTAMP",
            "close_time": "TIMESTAMP",
            "settlement_ts": "TIMESTAMP",
            "volume_fp": "DECIMAL(18,6)",
            "open_interest_fp": "DECIMAL(18,6)",
            "settlement_value_dollars": "DECIMAL(18,6)",
        },
    }
    for table, columns in checks.items():
        for col, target_type in columns.items():
            bad = one(
                con,
                f"SELECT count(*) FROM {table} WHERE {col} IS NOT NULL "
                f"AND TRY_CAST({col} AS {target_type}) IS NULL",
            )
            assert bad == 0, f"{table}.{col} has values that fail casting"


# value ranges


def test_prices_are_valid_probabilities(con):
    assert one(
        con,
        """
        SELECT count(*) FROM trades_typed
        WHERE yes_price_dollars <= 0 OR yes_price_dollars >= 1
           OR no_price_dollars <= 0 OR no_price_dollars >= 1
        """,
    ) == 0


def test_yes_and_no_prices_sum_to_one(con):
    assert one(
        con,
        """
        SELECT count(*) FROM trades_typed
        WHERE abs(yes_price_dollars + no_price_dollars - 1) > 0.000001
        """,
    ) == 0


def test_trade_counts_positive(con):
    assert one(con, "SELECT count(*) FROM trades_typed WHERE count_fp <= 0") == 0


# market consistency


def test_market_statuses_are_known(con):
    statuses = {r[0] for r in con.sql("SELECT DISTINCT status FROM markets").fetchall()}
    assert statuses <= KNOWN_MARKET_STATUSES


def test_markets_close_after_open(con):
    assert one(
        con, "SELECT count(*) FROM markets_typed WHERE close_time <= open_time"
    ) == 0


def test_finalized_markets_have_result(con):
    assert one(
        con,
        """
        SELECT count(*) FROM markets
        WHERE status = 'finalized' AND (result IS NULL OR result = '')
        """,
    ) == 0


# trade timing


def test_no_trades_before_market_open(con):
    assert one(
        con,
        """
        SELECT count(*) FROM trades_typed t
        JOIN markets_typed m ON t.ticker = m.ticker
        WHERE t.created_time < m.open_time
        """,
    ) == 0


def test_trades_after_close_within_tolerance(con):
    # trading runs seconds past the scheduled close; observed max is < 60s
    assert one(
        con,
        """
        SELECT count(*) FROM trades_typed t
        JOIN markets_typed m ON t.ticker = m.ticker
        WHERE t.created_time > m.close_time + INTERVAL 5 MINUTES
        """,
    ) == 0


def test_no_trades_from_the_future(con):
    max_created = one(con, "SELECT max(created_time) FROM trades_typed")
    assert max_created < datetime.now() + timedelta(days=1)
