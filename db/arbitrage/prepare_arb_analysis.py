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
               and matches_archive.json (expired matches keep their metadata
               there), plus flip_corrected and mid_gap from the flip check
- arb_build_info: single row recording the freeze (row counts, orphaned
               rows, time span)

Flip check: the two venues quote the same outcome, so their mids should
agree; if they instead agree as complements (k_mid + p_mid ≈ 1) by more than
the books' own spreads can explain, the recorded Polymarket book is the
other side of the market. Those matches are auto-corrected (the capture is
valid, just mirrored) and marked flip_corrected. Each match's residual
median mid gap is stored as arb_matches.mid_gap; what gap disqualifies a
match is an analysis decision, made in the notebook, not here.

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
import re
from pathlib import Path

import duckdb

_SRC = Path("db/pma.db")
_DST = Path("db/arbitrage/arb_data.db")
_MATCHES = Path("db/arbitrage/matches.json")
_ARCHIVE = Path("db/arbitrage/matches_archive.json")


def _market_label(match_id: str) -> str:
    """Sport and bet kind from the match id's slug prefix
    (asc-mlb-... -> 'MLB spread', atc-mlb-...-f5-... -> 'MLB F5',
    astatc-cs2-...-map1 -> 'CS2 map', aec-wta-... -> 'WTA')."""
    parts = match_id.lower().split("--")[0].split("-")
    if len(parts) < 2:
        return "other"
    sport = parts[1].upper()
    kind = {"asc": "spread", "tsc": "total"}.get(parts[0], "")
    if parts[0] == "astatc":
        kind = ("map" if any(re.fullmatch(r"(?:map|game)\d+", p)
                             for p in parts) else "prop")
    if "f5" in parts:
        kind = f"F5 {kind}".strip()
    return f"{sport} {kind}".strip()


def build(
    con: duckdb.DuckDBPyConnection,
    src: Path = _SRC,
    matches_path: Path = _MATCHES,
    archive_path: Path = _ARCHIVE,
) -> None:
    con.execute(f"ATTACH '{src.as_posix()}' AS src (READ_ONLY)")

    # ---- arb_matches: metadata from matches.json + archive ----------------
    # The archive holds matches pruned after their event ended; entries
    # without a direction (metadata lost before archiving existed, or purged
    # wrong matches) are excluded and their snapshots counted as orphaned.
    matches = json.loads(matches_path.read_text())
    if archive_path.exists():
        known_ids = {m["id"] for m in matches}
        matches += [
            m for m in json.loads(archive_path.read_text())
            if m.get("direction") and m["id"] not in known_ids
        ]
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

    # ---- tmp_base: deduped best-bid/ask change events ---------------------
    # One row only when a platform's top-of-book PRICE actually moves; this is
    # the state the alignment forward-fills between. Sizes are therefore the
    # size at each price state's first tick, not the latest. Valid books only
    # (the collector already drops crossed states, but keep the guard
    # explicit). Kalshi rows whose top level holds under 1 contract are
    # dropped: pre-fix captures carry ~1e-6-contract dust levels (float
    # residue in the book reconstruction) quoted at phantom prices. The guard
    # is Kalshi-only — Polymarket books arrive as exchange-sent snapshots
    # where fractional share sizes are legitimate (dropping them orphaned 11%
    # of Poly rows, observed 2026-07-22). Empty-side sentinels (bid 0 @ size
    # 0, ask 1 @ size 0) are legitimate states and are kept. The guard is
    # flip-invariant: the flip maps one side's condition onto the other's,
    # so raw pre-flip columns are checked.
    # Snapshots are stored as received; Polymarket rows for
    # kalshi_yes_eq_poly_no matches are flipped onto the Kalshi YES basis here
    # (bid/ask := 1-ask/1-bid, sizes swap — order-preserving, so the crossed
    # guard applies equally before and after).
    con.execute("""
        CREATE OR REPLACE TEMP TABLE tmp_base AS
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
              AND NOT (s.platform = 'kalshi'
                       AND s.best_bid > 0 AND s.bid_size < 1)
              AND NOT (s.platform = 'kalshi'
                       AND s.best_ask < 1 AND s.ask_size < 1)
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

    # ---- flip check -------------------------------------------------------
    # The venues quote the same outcome, so their mids should agree. A match
    # is flipped when the mids do NOT agree as recorded but DO agree as
    # complements (k + p ≈ 1), "agree" meaning within the books' combined
    # half-spreads — how far apart two mids can sit while the books still
    # overlap. Requiring the mirrored fit to actually be within noise (not
    # merely smaller than the as-recorded error) stops a wrongly-matched
    # pair, which fits badly both ways, from being "corrected" into a fake
    # edge. Near 50c both orientations fit and nothing is flipped — there a
    # swap is both undetectable and harmless.
    con.execute("""
        CREATE OR REPLACE TEMP TABLE flip_check AS
        WITH tk AS (
            SELECT match_id, ts, (best_bid + best_ask) / 2 AS k_mid,
                   (best_ask - best_bid) / 2 AS k_hs
            FROM tmp_base WHERE platform = 'kalshi'
        ),
        tp AS (
            SELECT match_id, ts, (best_bid + best_ask) / 2 AS p_mid,
                   (best_ask - best_bid) / 2 AS p_hs
            FROM tmp_base WHERE platform = 'polymarket'
        ),
        aligned AS (
            SELECT ev.match_id, tk.k_mid, tp.p_mid, tk.k_hs + tp.p_hs AS noise
            FROM (SELECT match_id, ts FROM tmp_base) ev
            ASOF LEFT JOIN tk
                ON ev.match_id = tk.match_id AND ev.ts >= tk.ts
            ASOF LEFT JOIN tp
                ON ev.match_id = tp.match_id AND ev.ts >= tp.ts
            WHERE tk.ts IS NOT NULL AND tp.ts IS NOT NULL
        ),
        fit AS (
            SELECT match_id,
                   median(abs(k_mid - p_mid)) AS same_err,
                   median(abs(k_mid + p_mid - 1)) AS flip_err,
                   median(noise) AS noise
            FROM aligned GROUP BY match_id
        )
        SELECT match_id,
               flip_err <= noise AND same_err > noise AS flipped,
               CASE WHEN flip_err <= noise AND same_err > noise
                    THEN flip_err ELSE same_err END AS mid_gap
        FROM fit
    """)
    con.execute("ALTER TABLE arb_matches ADD COLUMN flip_corrected BOOLEAN")
    con.execute("ALTER TABLE arb_matches ADD COLUMN mid_gap DOUBLE")
    con.execute("""
        UPDATE arb_matches SET
            flip_corrected = coalesce((SELECT f.flipped FROM flip_check f
                WHERE f.match_id = arb_matches.match_id), false),
            mid_gap = (SELECT f.mid_gap FROM flip_check f
                WHERE f.match_id = arb_matches.match_id)
    """)

    # ---- arb_events: flip-corrected books ---------------------------------
    # A flipped match's capture is valid, just mirrored: correct the
    # Polymarket rows onto the other side. Order-preserving, so the
    # change-dedup done in tmp_base still holds.
    con.execute("""
        CREATE OR REPLACE TABLE arb_events AS
        SELECT b.platform, b.match_id, b.sport, b.ts,
               CASE WHEN b.platform = 'polymarket' AND f.flipped
                    THEN 1 - b.best_ask ELSE b.best_bid END AS best_bid,
               CASE WHEN b.platform = 'polymarket' AND f.flipped
                    THEN 1 - b.best_bid ELSE b.best_ask END AS best_ask,
               CASE WHEN b.platform = 'polymarket' AND f.flipped
                    THEN b.ask_size ELSE b.bid_size END AS bid_size,
               CASE WHEN b.platform = 'polymarket' AND f.flipped
                    THEN b.bid_size ELSE b.ask_size END AS ask_size
        FROM tmp_base b
        LEFT JOIN flip_check f USING (match_id)
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
    # orphaned_rows: snapshots whose match_id has no (direction-carrying)
    # metadata and is therefore excluded from every arb_* table. Non-zero
    # means capture data is not represented in the freeze — silent exclusion
    # is what this column exists to prevent.
    con.execute("""
        CREATE OR REPLACE TABLE arb_build_info AS
        SELECT
            (SELECT count(*) FROM src.orderbook_snapshots) AS raw_snapshots,
            (SELECT count(*) FROM src.orderbook_snapshots s
             WHERE s.match_id NOT IN (SELECT match_id FROM arb_matches)
            ) AS orphaned_rows,
            (SELECT count(*) FROM arb_events) AS events,
            (SELECT count(*) FROM arb_aligned) AS aligned_ticks,
            (SELECT count(DISTINCT match_id) FROM arb_aligned) AS matches_both,
            (SELECT count(*) FROM arb_matches
             WHERE flip_corrected) AS matches_flipped,
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

    flipped = con.sql("""
        SELECT match_id FROM arb_matches WHERE flip_corrected ORDER BY match_id
    """).fetchall()
    if flipped:
        print(f"flip-corrected {len(flipped)} matches (fix direction in "
              f"{_MATCHES}):")
        for (mid,) in flipped:
            print(f"  {mid}")
    con.close()
    print(f"wrote {_DST}")


if __name__ == "__main__":
    main()
