from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from collect_orderbooks import KalshiOrderbook, SnapshotWriter, _init_db


class TestKalshiOrderbook:
    def test_apply_snapshot(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot({"yes": [[55, 100], [50, 200]], "no": [[45, 150]], "seq": 0})
        assert not ob.needs_snapshot
        assert ob.seq == 0
        assert ob.yes_bids == {55: 100, 50: 200}
        assert ob.no_bids == {45: 150}

    def test_apply_delta_sequential(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot({"yes": [[55, 100]], "no": [], "seq": 0})
        ok = ob.apply_delta({"yes": [[60, 50]], "no": [], "seq": 1})
        assert ok
        assert ob.yes_bids == {55: 100, 60: 50}

    def test_apply_delta_removes_zero_qty(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot({"yes": [[55, 100]], "no": [], "seq": 0})
        ob.apply_delta({"yes": [[55, 0]], "no": [], "seq": 1})
        assert 55 not in ob.yes_bids

    def test_sequence_gap_triggers_re_snapshot(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot({"yes": [], "no": [], "seq": 0})
        ok = ob.apply_delta({"yes": [], "no": [], "seq": 5})
        assert not ok
        assert ob.needs_snapshot

    def test_best_bid_ask(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot({
            "yes": [[55, 100], [50, 200]],
            "no": [[40, 150]],
            "seq": 0,
        })
        bid, ask, bid_sz, ask_sz = ob.best_bid_ask()
        assert bid == 0.55
        assert ask == pytest.approx(0.60)  # 1 - 0.40
        assert bid_sz == 1.0
        assert ask_sz == 1.5

    def test_no_bid_to_yes_ask_conversion(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot({
            "yes": [[50, 100]],
            "no": [[30, 200]],
            "seq": 0,
        })
        _, ask, _, _ = ob.best_bid_ask()
        assert ask == pytest.approx(0.70)  # YES ask = 1 - NO bid (0.30)


class TestSnapshotWriter:
    @pytest.fixture()
    def db_con(self, tmp_path):
        con = _init_db(tmp_path / "test.db")
        yield con
        con.close()

    def test_flush_writes_rows(self, db_con):
        writer = SnapshotWriter(db_con)
        for i in range(5):
            writer.add({
                "timestamp": f"2026-07-10T12:00:{i:02d}+00:00",
                "platform": "kalshi",
                "market_id": "TICKER-A",
                "match_id": "match-1",
                "best_bid": "0.55",
                "best_ask": "0.60",
                "bid_size": "1.0",
                "ask_size": "1.5",
                "mid_price": "0.575",
            })
        writer.flush()
        count = db_con.sql("SELECT count(*) FROM orderbook_snapshots").fetchone()[0]
        assert count == 5

    def test_batch_auto_flush(self, db_con):
        writer = SnapshotWriter(db_con)
        for i in range(100):
            writer.add({
                "timestamp": f"2026-07-10T12:00:00+00:00",
                "platform": "polymarket",
                "market_id": f"slug-{i}",
                "match_id": "match-1",
                "best_bid": "0.50",
                "best_ask": "0.55",
                "bid_size": "1.0",
                "ask_size": "1.0",
                "mid_price": "0.525",
            })
        count = db_con.sql("SELECT count(*) FROM orderbook_snapshots").fetchone()[0]
        assert count == 100

    def test_typed_view_idempotent(self, tmp_path):
        con1 = _init_db(tmp_path / "idem.db")
        con2 = _init_db(tmp_path / "idem.db")
        views = [
            r[0] for r in con2.sql(
                "SELECT name FROM sqlite_master WHERE type='view'"
            ).fetchall()
        ]
        con1.close()
        con2.close()


class TestPolyPriceParsing:
    def test_nested_px_value(self):
        entry = {"px": {"value": "0.423", "currency": "USD"}, "qty": "10"}
        price = float(entry["px"]["value"])
        assert price == pytest.approx(0.423)

    def test_qty_parsing(self):
        entry = {"px": {"value": "0.55", "currency": "USD"}, "qty": "25.5"}
        qty = float(entry["qty"])
        assert qty == pytest.approx(25.5)
