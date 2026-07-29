"""DuckDB schema and write operations for the arbitrage collector."""

from __future__ import annotations

import duckdb
import polars as pl

from db.arbitrage.models import MatchedMarket

DB_PATH = "db/arb_orderbooks.db"


def _ensure_sequences(con: duckdb.DuckDBPyConnection) -> None:
    for name in ("matched_markets_seq", "orderbook_snapshots_seq", "collection_metadata_seq"):
        con.sql(f"CREATE SEQUENCE IF NOT EXISTS {name} START 1")


def init_db(path: str = DB_PATH) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(path)
    _ensure_sequences(con)

    con.sql("""
        CREATE TABLE IF NOT EXISTS matched_markets (
            id INTEGER PRIMARY KEY DEFAULT(nextval('matched_markets_seq')),
            game_date DATE NOT NULL,
            away_team VARCHAR NOT NULL,
            home_team VARCHAR NOT NULL,
            kalshi_ticker_away VARCHAR NOT NULL,
            kalshi_ticker_home VARCHAR NOT NULL,
            poly_slug VARCHAR NOT NULL,
            kalshi_event_ticker VARCHAR NOT NULL,
            poly_event_slug VARCHAR NOT NULL
        )
    """)

    con.sql("""
        CREATE TABLE IF NOT EXISTS orderbook_snapshots (
            id INTEGER PRIMARY KEY DEFAULT(nextval('orderbook_snapshots_seq')),
            timestamp TIMESTAMP NOT NULL,
            platform VARCHAR NOT NULL,
            market_id VARCHAR NOT NULL,
            side VARCHAR NOT NULL,
            book_json JSON NOT NULL,
            source_timestamp VARCHAR
        )
    """)

    con.sql("""
        CREATE TABLE IF NOT EXISTS collection_metadata (
            id INTEGER PRIMARY KEY DEFAULT(nextval('collection_metadata_seq')),
            event VARCHAR NOT NULL,
            platform VARCHAR NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            details VARCHAR
        )
    """)

    return con


def save_matched_markets(
    con: duckdb.DuckDBPyConnection, matches: list[MatchedMarket],
) -> None:
    """Upsert matched pairs keyed on kalshi_event_ticker. Pairs matched by
    an earlier run the same day are kept, so a restart never orphans
    snapshots already collected for games that have since closed."""
    if not matches:
        return
    rows = [m.model_dump() for m in matches]
    df = pl.DataFrame(rows)
    con.sql("""
        DELETE FROM matched_markets
        WHERE kalshi_event_ticker IN (SELECT kalshi_event_ticker FROM df)
    """)
    con.sql("INSERT INTO matched_markets BY NAME SELECT * FROM df")


def load_matched_markets(
    con: duckdb.DuckDBPyConnection, game_date,
) -> list[tuple[str, str, str]]:
    """All of today's pairs (this run's and earlier runs'), as
    (kalshi_ticker_away, kalshi_ticker_home, poly_slug)."""
    return con.execute(
        "SELECT kalshi_ticker_away, kalshi_ticker_home, poly_slug"
        " FROM matched_markets WHERE game_date = $1",
        [game_date],
    ).fetchall()


def save_snapshot(
    con: duckdb.DuckDBPyConnection,
    platform: str,
    market_id: str,
    side: str,
    book_json: str,
    source_timestamp: str | None = None,
) -> None:
    con.execute(
        "INSERT INTO orderbook_snapshots"
        " (timestamp, platform, market_id, side, book_json, source_timestamp)"
        " VALUES (now(), $1, $2, $3, $4, $5)",
        [platform, market_id, side, book_json, source_timestamp],
    )


def log_event(
    con: duckdb.DuckDBPyConnection,
    event: str,
    platform: str,
    details: str | None = None,
) -> None:
    con.execute(
        "INSERT INTO collection_metadata (event, platform, timestamp, details)"
        " VALUES ($1, $2, now(), $3)",
        [event, platform, details],
    )
