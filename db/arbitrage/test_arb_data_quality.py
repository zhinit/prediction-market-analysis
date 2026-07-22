"""Post-collection reasonability checks for orderbook_snapshots.

Run after accumulating some data via /collect-arb-data.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest

DB_PATH = Path(__file__).parent.parent / "pma.db"
MATCHES_PATH = Path(__file__).parent / "matches.json"
ARCHIVE_PATH = Path(__file__).parent / "matches_archive.json"


@pytest.fixture(scope="module")
def con():
    if not DB_PATH.exists():
        pytest.skip(f"{DB_PATH} does not exist")
    c = duckdb.connect(str(DB_PATH), read_only=True)
    tables = [r[0] for r in c.sql("SHOW TABLES").fetchall()]
    if "orderbook_snapshots" not in tables:
        c.close()
        pytest.skip("orderbook_snapshots table does not exist yet")
    count = c.sql("SELECT count(*) FROM orderbook_snapshots").fetchone()[0]
    if count == 0:
        c.close()
        pytest.skip("No orderbook data collected yet")
    yield c
    c.close()


@pytest.fixture(scope="module")
def matches():
    """Live matches plus the archive (expired matches keep their metadata
    there; entries without a direction record purged or pre-archive ids)."""
    if not MATCHES_PATH.exists():
        pytest.skip("matches.json not found")
    data = json.loads(MATCHES_PATH.read_text())
    if ARCHIVE_PATH.exists():
        data += json.loads(ARCHIVE_PATH.read_text())
    if not data:
        pytest.skip("matches.json is empty")
    return data


def test_bid_ask_valid(con):
    bad = con.sql("""
        SELECT count(*) FROM orderbook_snapshots_typed
        WHERE best_bid > best_ask
           OR best_bid < 0 OR best_bid > 1
           OR best_ask < 0 OR best_ask > 1
    """).fetchone()[0]
    assert bad == 0, f"{bad} snapshots with invalid bid/ask"


def test_market_ids_in_matches(con, matches):
    match_ids = {m["id"] for m in matches}
    market_ids = (
        {m["kalshi_ticker"] for m in matches if m.get("kalshi_ticker")}
        | {m["polymarket_slug"] for m in matches if m.get("polymarket_slug")}
    )
    db_match_ids = {
        r[0] for r in con.sql(
            "SELECT DISTINCT match_id FROM orderbook_snapshots"
        ).fetchall()
    }
    db_market_ids = {
        r[0] for r in con.sql(
            "SELECT DISTINCT market_id FROM orderbook_snapshots"
        ).fetchall()
    }
    unknown_matches = db_match_ids - match_ids
    assert not unknown_matches, f"Unknown match_ids: {unknown_matches}"
    unknown_markets = db_market_ids - market_ids
    assert not unknown_markets, f"Unknown market_ids: {unknown_markets}"


def test_both_platforms_represented(con, matches):
    platforms = {
        r[0] for r in con.sql(
            "SELECT DISTINCT platform FROM orderbook_snapshots"
        ).fetchall()
    }
    assert "kalshi" in platforms, "No Kalshi snapshots"
    assert "polymarket" in platforms, "No Polymarket snapshots"


def test_typed_view_returns_numeric(con):
    row = con.sql("""
        SELECT best_bid, best_ask, mid_price
        FROM orderbook_snapshots_typed
        LIMIT 1
    """).fetchone()
    assert row is not None
    for val in row:
        assert isinstance(val, (int, float, type(None))) or hasattr(val, '__float__')
