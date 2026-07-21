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
    build(con, src=src, matches_path=matches)
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

    def test_aligned_uses_normalised_books(self, prepared):
        row = prepared.sql(
            "SELECT p_bid, p_ask FROM arb_aligned"
            " WHERE match_id = 'aec-mlb-c-d-2026-07-21-y'"
            " ORDER BY ts DESC LIMIT 1"
        ).fetchone()
        assert float(row[0]) == pytest.approx(0.55)
        assert float(row[1]) == pytest.approx(0.60)
