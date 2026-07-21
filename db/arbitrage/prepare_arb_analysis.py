"""Prepare the frozen dataset for the cross-platform arbitrage analysis
(analysis/arbitrage_opportunities.ipynb).

Reads the live orderbook capture from db/pma.db (read-only) and writes a
self-contained, frozen analysis database to db/arbitrage/arb_data.db. Kept in a
separate file, not pma.db, so the freeze is stable while /collect-arb-data keeps
appending to pma.db (a finished analysis's numbers must not silently move).

Run manually after a collection window:

    uv run python -m db.arbitrage.prepare_arb_analysis

Tables (all namespaced arb_*):
- arb_events:  deduped best-bid/ask change events per platform per match,
               the point-in-time books both downstream tables build on
- arb_aligned: one row per book-change on either platform, carrying the
               latest book from BOTH platforms (as-of) plus each leg's age,
               so the notebook can compute the cross-platform edge at any tick
- arb_matches: per-match metadata (market type, direction) from matches.json
- arb_build_info: single row recording the freeze (row counts, time span)

Each match_id is one YES outcome quoted on both venues. The collector stores
each platform's book exactly as received; this script normalises Polymarket
rows onto the Kalshi YES basis using the match's direction (for
kalshi_yes_eq_poly_no: bid/ask become 1-ask/1-bid, sizes swap). The
cross-platform edge at a tick is then
    max(kalshi_bid - poly_ask, poly_bid - kalshi_ask)
i.e. buy YES where the ask is lower, sell YES where the bid is higher.
"""
from __future__ import annotations

import json
from pathlib import Path

import duckdb

_SRC = Path("db/pma.db")
_DST = Path("db/arbitrage/arb_data.db")
_MATCHES = Path("db/arbitrage/matches.json")


def _market_label(match_id: str) -> str:
    """Human market type from the match id (atc-mlb-...-f5-..., aec-wta-..., aec-atp-...)."""
    mid = match_id.lower()
    if "-f5-" in mid or "-mlb-" in mid:
        return "MLB F5"
    if "-wta-" in mid:
        return "WTA"
    if "-atp-" in mid:
        return "ATP"
    return mid.split("-")[1] if "-" in mid else "other"


def build(
    con: duckdb.DuckDBPyConnection,
    src: Path = _SRC,
    matches_path: Path = _MATCHES,
) -> None:
    con.execute(f"ATTACH '{src.as_posix()}' AS src (READ_ONLY)")

    # ---- arb_matches: metadata from matches.json --------------------------
    matches = json.loads(matches_path.read_text())
    con.execute("""
        CREATE OR REPLACE TABLE arb_matches (
            match_id TEXT, kalshi_ticker TEXT, polymarket_slug TEXT,
            direction TEXT, market TEXT, notes TEXT
        )
    """)
    con.executemany(
        "INSERT INTO arb_matches VALUES (?, ?, ?, ?, ?, ?)",
        [(m["id"], m["kalshi_ticker"], m["polymarket_slug"], m["direction"],
          _market_label(m["id"]), m.get("notes", "")) for m in matches],
    )

    # ---- arb_events: deduped best-bid/ask change events -------------------
    # One row only when a platform's top-of-book price actually moves; this is
    # the state the alignment forward-fills between. Valid books only (the
    # collector already drops crossed states, but keep the guard explicit).
    # Snapshots are stored as received; Polymarket rows for
    # kalshi_yes_eq_poly_no matches are flipped onto the Kalshi YES basis here
    # (bid/ask := 1-ask/1-bid, sizes swap — order-preserving, so the crossed
    # guard applies equally before and after).
    con.execute("""
        CREATE OR REPLACE TABLE arb_events AS
        WITH flips AS (
            SELECT match_id,
                   direction = 'kalshi_yes_eq_poly_no' AS flip
            FROM arb_matches
        ),
        base AS (
            SELECT s.platform, s.match_id,
                   split_part(s.match_id, '-', 2) AS sport,
                   s.timestamp AS ts,
                   CASE WHEN s.platform = 'polymarket' AND f.flip
                        THEN 1 - s.best_ask ELSE s.best_bid END AS best_bid,
                   CASE WHEN s.platform = 'polymarket' AND f.flip
                        THEN 1 - s.best_bid ELSE s.best_ask END AS best_ask,
                   CASE WHEN s.platform = 'polymarket' AND f.flip
                        THEN s.ask_size ELSE s.bid_size END AS bid_size,
                   CASE WHEN s.platform = 'polymarket' AND f.flip
                        THEN s.bid_size ELSE s.ask_size END AS ask_size
            FROM src.orderbook_snapshots_typed s
            JOIN flips f USING (match_id)
            WHERE s.best_bid >= 0 AND s.best_ask <= 1 AND s.best_bid < s.best_ask
        ),
        flagged AS (
            SELECT *,
                   lag(best_bid) OVER w AS pb,
                   lag(best_ask) OVER w AS pa
            FROM base
            WINDOW w AS (PARTITION BY platform, match_id ORDER BY ts)
        )
        SELECT platform, match_id, sport, ts,
               best_bid, best_ask, bid_size, ask_size
        FROM flagged
        WHERE pb IS NULL OR best_bid <> pb OR best_ask <> pa
    """)

    # ---- per-platform streams for the as-of alignment ---------------------
    con.execute("""
        CREATE OR REPLACE TEMP TABLE k AS
        SELECT match_id, ts,
               best_bid AS k_bid, best_ask AS k_ask,
               bid_size AS k_bidsz, ask_size AS k_asksz
        FROM arb_events WHERE platform = 'kalshi'
    """)
    con.execute("""
        CREATE OR REPLACE TEMP TABLE p AS
        SELECT match_id, ts,
               best_bid AS p_bid, best_ask AS p_ask,
               bid_size AS p_bidsz, ask_size AS p_asksz
        FROM arb_events WHERE platform = 'polymarket'
    """)

    # ---- arb_aligned: every book-change tick with both venues' latest book -
    # Each event on either venue becomes a tick; both legs are the most recent
    # book at-or-before that tick (ASOF). Leg ages expose staleness so the
    # notebook can require both books be fresh before trusting an edge.
    con.execute("""
        CREATE OR REPLACE TABLE arb_aligned AS
        WITH ev AS (
            SELECT match_id, sport, ts FROM arb_events
        )
        SELECT
            ev.match_id,
            ev.sport,
            ev.ts,
            k.ts AS k_ts, k.k_bid, k.k_ask, k.k_bidsz, k.k_asksz,
            p.ts AS p_ts, p.p_bid, p.p_ask, p.p_bidsz, p.p_asksz,
            epoch(ev.ts - k.ts) AS k_age_s,
            epoch(ev.ts - p.ts) AS p_age_s
        FROM ev
        ASOF LEFT JOIN k
            ON ev.match_id = k.match_id AND ev.ts >= k.ts
        ASOF LEFT JOIN p
            ON ev.match_id = p.match_id AND ev.ts >= p.ts
        WHERE k.ts IS NOT NULL AND p.ts IS NOT NULL
    """)

    # ---- arb_build_info ---------------------------------------------------
    con.execute("""
        CREATE OR REPLACE TABLE arb_build_info AS
        SELECT
            (SELECT count(*) FROM src.orderbook_snapshots) AS raw_snapshots,
            (SELECT count(*) FROM arb_events) AS events,
            (SELECT count(*) FROM arb_aligned) AS aligned_ticks,
            (SELECT count(DISTINCT match_id) FROM arb_aligned) AS matches_both,
            (SELECT min(ts) FROM arb_events) AS first_ts,
            (SELECT max(ts) FROM arb_events) AS last_ts
    """)

    # documentation-as-code
    con.execute("COMMENT ON TABLE arb_aligned IS "
                "'One row per top-of-book change on either venue, carrying the "
                "latest kalshi and polymarket book (as-of) for the same YES "
                "outcome, with each leg''s age in seconds.'")


def main() -> None:
    if not _SRC.exists():
        raise SystemExit(f"{_SRC} not found.")
    _DST.parent.mkdir(parents=True, exist_ok=True)
    if _DST.exists():
        _DST.unlink()
    con = duckdb.connect(str(_DST))
    build(con)
    info = con.sql("SELECT * FROM arb_build_info").pl()
    print(info)
    print(con.sql("""
        SELECT market, count(DISTINCT match_id) AS matches, count(*) AS ticks
        FROM arb_aligned a JOIN arb_matches m USING (match_id)
        GROUP BY market ORDER BY ticks DESC
    """).pl())
    con.close()
    print(f"wrote {_DST}")


if __name__ == "__main__":
    main()
