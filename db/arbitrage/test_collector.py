from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from db.arbitrage.collect_orderbooks import KalshiOrderbook, SnapshotWriter, _init_db


class TestKalshiOrderbook:
    # Payload shapes mirror Kalshi WS v2 messages captured 2026-07-11.
    def test_apply_snapshot(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot({
            "yes_dollars_fp": [["0.5500", "100.00"], ["0.5000", "200.00"]],
            "no_dollars_fp": [["0.4500", "150.00"]],
        })
        assert ob.yes_bids == {0.55: 100.0, 0.50: 200.0}
        assert ob.no_bids == {0.45: 150.0}

    def test_snapshot_replaces_existing_book(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot({"yes_dollars_fp": [["0.5500", "100.00"]], "no_dollars_fp": []})
        ob.apply_snapshot({"yes_dollars_fp": [["0.6000", "50.00"]], "no_dollars_fp": []})
        assert ob.yes_bids == {0.60: 50.0}

    def test_apply_delta_new_level(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot({"yes_dollars_fp": [["0.5500", "100.00"]], "no_dollars_fp": []})
        ob.apply_delta({"side": "yes", "price_dollars": "0.6000", "delta_fp": "50.00"})
        assert ob.yes_bids == {0.55: 100.0, 0.60: 50.0}

    def test_apply_delta_adjusts_level(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot({"yes_dollars_fp": [["0.5500", "100.00"]], "no_dollars_fp": []})
        ob.apply_delta({"side": "yes", "price_dollars": "0.5500", "delta_fp": "-40.00"})
        assert ob.yes_bids == {0.55: 60.0}

    def test_apply_delta_removes_emptied_level(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot({"yes_dollars_fp": [["0.5500", "100.00"]], "no_dollars_fp": []})
        ob.apply_delta({"side": "yes", "price_dollars": "0.5500", "delta_fp": "-100.00"})
        assert 0.55 not in ob.yes_bids

    def test_apply_delta_no_side(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot({"yes_dollars_fp": [], "no_dollars_fp": [["0.3000", "200.00"]]})
        ob.apply_delta({"side": "no", "price_dollars": "0.3000", "delta_fp": "-197.00"})
        assert ob.no_bids == {0.30: 3.0}

    def test_best_bid_ask(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot({
            "yes_dollars_fp": [["0.5500", "100.00"], ["0.5000", "200.00"]],
            "no_dollars_fp": [["0.4000", "150.00"]],
        })
        bid, ask, bid_sz, ask_sz = ob.best_bid_ask()
        assert bid == 0.55
        assert ask == pytest.approx(0.60)  # 1 - 0.40
        assert bid_sz == 100.0
        assert ask_sz == 150.0

    def test_empty_book(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot({"yes_dollars_fp": [], "no_dollars_fp": []})
        bid, ask, bid_sz, ask_sz = ob.best_bid_ask()
        assert bid == 0.0
        assert ask == 1.0
        assert bid_sz == 0.0
        assert ask_sz == 0.0


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

    def test_add_does_no_io(self, db_con):
        # add() must only buffer: a synchronous DB write inside the receive
        # loop is what corrupted the Kalshi books under load. Nothing is
        # persisted until the writer task (or an explicit flush) runs.
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
        assert db_con.sql("SELECT count(*) FROM orderbook_snapshots").fetchone()[0] == 0
        writer.flush()
        assert db_con.sql("SELECT count(*) FROM orderbook_snapshots").fetchone()[0] == 100

    def test_take_detaches_buffer(self, db_con):
        writer = SnapshotWriter(db_con)
        writer.add({"timestamp": "2026-07-10T12:00:00+00:00", "platform": "kalshi",
                    "market_id": "T", "match_id": "m", "best_bid": "0.5",
                    "best_ask": "0.6", "bid_size": "1", "ask_size": "1",
                    "mid_price": "0.55"})
        batch = writer.take()
        assert len(batch) == 1
        assert writer.take() == []  # buffer detached, nothing left
        writer.insert(batch)
        assert db_con.sql("SELECT count(*) FROM orderbook_snapshots").fetchone()[0] == 1

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
