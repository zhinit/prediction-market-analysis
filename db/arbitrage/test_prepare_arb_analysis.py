from __future__ import annotations

import json

import duckdb
import pytest

from db.arbitrage.collect_orderbooks import _init_db
from db.arbitrage.prepare_arb_analysis import build


def _insert(con, platform, match_id, ts, bid, ask, bid_sz, ask_sz):
    con.execute(
        "INSERT INTO orderbook_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [ts, platform, f"mkt-{match_id}", match_id,
         str(bid), str(ask), str(bid_sz), str(ask_sz),
         str((bid + ask) / 2)],
    )


@pytest.fixture()
def prepared(tmp_path):
    src = tmp_path / "src.db"
    src_con = _init_db(src)
    for match_id in ("aec-mlb-a-b-2026-07-21-x", "aec-mlb-c-d-2026-07-21-y"):
        _insert(src_con, "kalshi", match_id,
                "2026-07-21T12:00:00+00:00", 0.50, 0.55, 5, 6)
        _insert(src_con, "polymarket", match_id,
                "2026-07-21T12:00:01+00:00", 0.40, 0.45, 10, 20)
    src_con.close()

    matches = tmp_path / "matches.json"
    matches.write_text(json.dumps([
        {"id": "aec-mlb-a-b-2026-07-21-x", "kalshi_ticker": "K1",
         "polymarket_slug": "s1", "direction": "kalshi_yes_eq_poly_yes"},
        {"id": "aec-mlb-c-d-2026-07-21-y", "kalshi_ticker": "K2",
         "polymarket_slug": "s2", "direction": "kalshi_yes_eq_poly_no"},
    ]))

    con = duckdb.connect(":memory:")
    build(con, src=src, matches_path=matches,
          archive_path=tmp_path / "matches_archive.json")
    yield con
    con.close()


def _poly_row(con, match_id):
    return con.sql(
        "SELECT best_bid, best_ask, bid_size, ask_size FROM arb_events"
        " WHERE platform = 'polymarket' AND match_id = ?",
        params=[match_id],
    ).fetchone()


class TestDirectionNormalisation:
    def test_same_direction_unchanged(self, prepared):
        bid, ask, bid_sz, ask_sz = _poly_row(prepared, "aec-mlb-a-b-2026-07-21-x")
        assert float(bid) == pytest.approx(0.40)
        assert float(ask) == pytest.approx(0.45)
        assert float(bid_sz) == pytest.approx(10)
        assert float(ask_sz) == pytest.approx(20)

    def test_opposite_direction_flipped(self, prepared):
        bid, ask, bid_sz, ask_sz = _poly_row(prepared, "aec-mlb-c-d-2026-07-21-y")
        assert float(bid) == pytest.approx(0.55)   # 1 - 0.45
        assert float(ask) == pytest.approx(0.60)   # 1 - 0.40
        assert float(bid_sz) == pytest.approx(20)  # sizes swap
        assert float(ask_sz) == pytest.approx(10)

    def test_kalshi_rows_never_flipped(self, prepared):
        rows = prepared.sql(
            "SELECT DISTINCT best_bid, best_ask FROM arb_events"
            " WHERE platform = 'kalshi'"
        ).fetchall()
        assert all(
            float(b) == pytest.approx(0.50) and float(a) == pytest.approx(0.55)
            for b, a in rows
        )

    def test_dust_top_levels_dropped(self, tmp_path):
        src = tmp_path / "src.db"
        src_con = _init_db(src)
        match_id = "aec-mlb-a-b-2026-07-21-x"
        # dust bid level (phantom price), valid ask
        _insert(src_con, "kalshi", match_id,
                "2026-07-21T12:00:00+00:00", 0.50, 0.55, 0.000001, 6)
        # dust ask level, valid bid
        _insert(src_con, "kalshi", match_id,
                "2026-07-21T12:00:01+00:00", 0.50, 0.55, 5, 0.000001)
        # empty-side sentinels (no bids / no asks) are kept
        _insert(src_con, "kalshi", match_id,
                "2026-07-21T12:00:02+00:00", 0, 0.55, 0, 6)
        _insert(src_con, "kalshi", match_id,
                "2026-07-21T12:00:03+00:00", 0.50, 1, 5, 0)
        src_con.close()

        matches = tmp_path / "matches.json"
        matches.write_text(json.dumps([
            {"id": match_id, "kalshi_ticker": "K1",
             "polymarket_slug": "s1", "direction": "kalshi_yes_eq_poly_yes"},
        ]))
        con = duckdb.connect(":memory:")
        build(con, src=src, matches_path=matches,
              archive_path=tmp_path / "matches_archive.json")
        rows = con.sql(
            "SELECT best_bid, best_ask FROM arb_events ORDER BY ts"
        ).fetchall()
        con.close()
        assert [(float(b), float(a)) for b, a in rows] == [(0.0, 0.55), (0.50, 1.0)]

    def test_dust_guard_boundary_and_kalshi_only(self, tmp_path):
        src = tmp_path / "src.db"
        src_con = _init_db(src)
        match_id = "aec-mlb-a-b-2026-07-21-x"
        # Kalshi: exactly 1 contract kept, 0.99 dropped
        _insert(src_con, "kalshi", match_id,
                "2026-07-21T12:00:00+00:00", 0.50, 0.55, 1, 6)
        _insert(src_con, "kalshi", match_id,
                "2026-07-21T12:00:01+00:00", 0.51, 0.55, 0.99, 6)
        # Polymarket: fractional share sizes are legitimate exchange-sent
        # book states, never dust — dropping them orphaned 11% of Poly rows
        # (observed 2026-07-22).
        _insert(src_con, "polymarket", match_id,
                "2026-07-21T12:00:02+00:00", 0.40, 0.45, 0.30, 0.25)
        src_con.close()

        matches = tmp_path / "matches.json"
        matches.write_text(json.dumps([
            {"id": match_id, "kalshi_ticker": "K1",
             "polymarket_slug": "s1", "direction": "kalshi_yes_eq_poly_yes"},
        ]))
        con = duckdb.connect(":memory:")
        build(con, src=src, matches_path=matches,
              archive_path=tmp_path / "matches_archive.json")
        rows = con.sql(
            "SELECT platform, best_bid FROM arb_events ORDER BY ts"
        ).fetchall()
        con.close()
        assert [(p, float(b)) for p, b in rows] == [
            ("kalshi", 0.50), ("polymarket", 0.40)]

    def test_aligned_uses_normalised_books(self, prepared):
        row = prepared.sql(
            "SELECT p_bid, p_ask FROM arb_aligned"
            " WHERE match_id = 'aec-mlb-c-d-2026-07-21-y'"
            " ORDER BY ts DESC LIMIT 1"
        ).fetchone()
        assert float(row[0]) == pytest.approx(0.55)
        assert float(row[1]) == pytest.approx(0.60)


def _build_one_match(tmp_path, rows, direction="kalshi_yes_eq_poly_yes"):
    """Build from one match ('aec-mlb-a-b-2026-07-21-x') whose snapshots are
    the given (platform, ts, bid, ask, bid_sz, ask_sz)."""
    src = tmp_path / "src.db"
    src_con = _init_db(src)
    match_id = "aec-mlb-a-b-2026-07-21-x"
    for platform, ts, bid, ask, bid_sz, ask_sz in rows:
        _insert(src_con, platform, match_id, ts, bid, ask, bid_sz, ask_sz)
    src_con.close()
    matches = tmp_path / "matches.json"
    matches.write_text(json.dumps([
        {"id": match_id, "kalshi_ticker": "K1",
         "polymarket_slug": "s1", "direction": direction},
    ]))
    con = duckdb.connect(":memory:")
    build(con, src=src, matches_path=matches,
          archive_path=tmp_path / "matches_archive.json")
    return con


class TestFlipCheck:
    def test_agreeing_mids_not_flipped(self, prepared):
        rows = prepared.sql(
            "SELECT flip_corrected, mid_gap FROM arb_matches").fetchall()
        assert all(not flipped for flipped, _ in rows)
        assert all(gap is not None for _, gap in rows)

    def test_mirrored_match_corrected(self, tmp_path):
        # Kalshi mid ~0.80, recorded Poly mid ~0.20: the mids agree only as
        # complements, so the Poly capture is the other side of the market.
        con = _build_one_match(tmp_path, [
            ("kalshi", "2026-07-21T12:00:00+00:00", 0.78, 0.82, 100, 200),
            ("polymarket", "2026-07-21T12:00:01+00:00", 0.18, 0.22, 5, 6),
            ("kalshi", "2026-07-21T12:00:02+00:00", 0.79, 0.83, 100, 200),
            ("polymarket", "2026-07-21T12:00:03+00:00", 0.17, 0.21, 5, 6),
        ])
        assert con.sql("SELECT flip_corrected FROM arb_matches").fetchone()[0]
        bid, ask, bid_sz, ask_sz = con.sql(
            "SELECT best_bid, best_ask, bid_size, ask_size FROM arb_events"
            " WHERE platform = 'polymarket' ORDER BY ts LIMIT 1").fetchone()
        assert float(bid) == pytest.approx(0.78)   # 1 - 0.22
        assert float(ask) == pytest.approx(0.82)   # 1 - 0.18
        assert float(bid_sz) == pytest.approx(6)   # sizes swap
        assert float(ask_sz) == pytest.approx(5)
        con.close()

    def test_near_50c_not_flipped(self, tmp_path):
        # At 50c a mid and its complement are the same number: both errors
        # are equal, so the spread margin refuses to flip.
        con = _build_one_match(tmp_path, [
            ("kalshi", "2026-07-21T12:00:00+00:00", 0.49, 0.53, 100, 200),
            ("polymarket", "2026-07-21T12:00:01+00:00", 0.47, 0.51, 5, 6),
        ])
        assert not con.sql("SELECT flip_corrected FROM arb_matches").fetchone()[0]
        con.close()

    def test_disagreeing_match_kept_with_gap(self, tmp_path):
        # Persistent disagreement is recorded, not silently dropped: the
        # cutoff is an analysis decision made in the notebook.
        con = _build_one_match(tmp_path, [
            ("kalshi", "2026-07-21T12:00:00+00:00", 0.78, 0.82, 100, 200),
            ("polymarket", "2026-07-21T12:00:01+00:00", 0.53, 0.57, 5, 6),
        ])
        flipped, gap = con.sql(
            "SELECT flip_corrected, mid_gap FROM arb_matches").fetchone()
        assert not flipped
        assert float(gap) == pytest.approx(0.25)
        assert con.sql("SELECT count(*) FROM arb_events").fetchone()[0] == 2
        con.close()

    def test_single_platform_match_kept(self, tmp_path):
        con = _build_one_match(tmp_path, [
            ("kalshi", "2026-07-21T12:00:00+00:00", 0.50, 0.55, 5, 6),
        ])
        flipped, gap = con.sql(
            "SELECT flip_corrected, mid_gap FROM arb_matches").fetchone()
        assert not flipped
        assert gap is None
        assert con.sql("SELECT count(*) FROM arb_events").fetchone()[0] == 1
        con.close()

    def test_wrong_direction_double_flip_restores_orientation(self, tmp_path):
        # matches.json says kalshi_yes_eq_poly_no but the capture is actually
        # the same side: the direction flip in tmp_base mirrors it, the flip
        # check detects the mirroring, and arb_events flips it back — final
        # orientation agrees with Kalshi and the match is marked corrected.
        con = _build_one_match(tmp_path, [
            ("kalshi", "2026-07-21T12:00:00+00:00", 0.78, 0.82, 100, 200),
            ("polymarket", "2026-07-21T12:00:01+00:00", 0.77, 0.81, 5, 6),
            ("kalshi", "2026-07-21T12:00:02+00:00", 0.79, 0.83, 100, 200),
            ("polymarket", "2026-07-21T12:00:03+00:00", 0.78, 0.82, 5, 6),
        ], direction="kalshi_yes_eq_poly_no")
        assert con.sql("SELECT flip_corrected FROM arb_matches").fetchone()[0]
        bid, ask, bid_sz, ask_sz = con.sql(
            "SELECT best_bid, best_ask, bid_size, ask_size FROM arb_events"
            " WHERE platform = 'polymarket' ORDER BY ts LIMIT 1").fetchone()
        # back on the raw (Kalshi-agreeing) side: two flips cancel
        assert float(bid) == pytest.approx(0.77)
        assert float(ask) == pytest.approx(0.81)
        assert float(bid_sz) == pytest.approx(5)
        assert float(ask_sz) == pytest.approx(6)
        con.close()


class TestArchive:
    def test_archived_direction_used_and_stubs_orphaned(self, tmp_path):
        src = tmp_path / "src.db"
        src_con = _init_db(src)
        # one live match, one archived (expired) match, one stub (direction
        # lost) whose rows must be excluded and counted as orphaned
        _insert(src_con, "kalshi", "aec-mlb-a-b-2026-07-21-x",
                "2026-07-21T12:00:00+00:00", 0.50, 0.55, 5, 6)
        _insert(src_con, "kalshi", "aec-mlb-c-d-2026-07-20-y",
                "2026-07-20T12:00:00+00:00", 0.60, 0.65, 5, 6)
        _insert(src_con, "kalshi", "aec-mlb-e-f-2026-07-19-z",
                "2026-07-19T12:00:00+00:00", 0.70, 0.75, 5, 6)
        src_con.close()

        matches = tmp_path / "matches.json"
        matches.write_text(json.dumps([
            {"id": "aec-mlb-a-b-2026-07-21-x", "kalshi_ticker": "K1",
             "polymarket_slug": "s1", "direction": "kalshi_yes_eq_poly_yes"},
        ]))
        archive = tmp_path / "matches_archive.json"
        archive.write_text(json.dumps([
            {"id": "aec-mlb-c-d-2026-07-20-y", "kalshi_ticker": "K2",
             "polymarket_slug": "s2", "direction": "kalshi_yes_eq_poly_yes"},
            {"id": "aec-mlb-e-f-2026-07-19-z", "kalshi_ticker": "K3",
             "polymarket_slug": "s3", "direction": None,
             "notes": "metadata lost to pre-archive pruning"},
        ]))
        con = duckdb.connect(":memory:")
        build(con, src=src, matches_path=matches, archive_path=archive)
        match_ids = {r[0] for r in con.sql(
            "SELECT match_id FROM arb_matches").fetchall()}
        assert match_ids == {
            "aec-mlb-a-b-2026-07-21-x", "aec-mlb-c-d-2026-07-20-y"}
        orphaned = con.sql(
            "SELECT orphaned_rows FROM arb_build_info").fetchone()[0]
        assert orphaned == 1
        con.close()
