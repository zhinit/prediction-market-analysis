from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest

from db.arbitrage.collect_orderbooks import KalshiOrderbook, SnapshotWriter, _init_db
from db.arbitrage.ws_models import KalshiDelta, KalshiSnapshot


def _snap(yes=(), no=()):
    return KalshiSnapshot.model_validate({
        "market_ticker": "T",
        "yes_dollars_fp": list(yes),
        "no_dollars_fp": list(no),
    })


def _delta(side, price, delta):
    return KalshiDelta.model_validate({
        "market_ticker": "T", "side": side,
        "price_dollars": price, "delta_fp": delta,
    })


class TestKalshiOrderbook:
    # Payload shapes mirror Kalshi WS v2 messages captured 2026-07-11.
    def test_apply_snapshot(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot(_snap(
            yes=[["0.5500", "100.00"], ["0.5000", "200.00"]],
            no=[["0.4500", "150.00"]],
        ))
        assert ob.yes_bids == {0.55: 100.0, 0.50: 200.0}
        assert ob.no_bids == {0.45: 150.0}

    def test_snapshot_replaces_existing_book(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot(_snap(yes=[["0.5500", "100.00"]]))
        ob.apply_snapshot(_snap(yes=[["0.6000", "50.00"]]))
        assert ob.yes_bids == {0.60: 50.0}

    def test_apply_delta_new_level(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot(_snap(yes=[["0.5500", "100.00"]]))
        ob.apply_delta(_delta("yes", "0.6000", "50.00"))
        assert ob.yes_bids == {0.55: 100.0, 0.60: 50.0}

    def test_apply_delta_adjusts_level(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot(_snap(yes=[["0.5500", "100.00"]]))
        ob.apply_delta(_delta("yes", "0.5500", "-40.00"))
        assert ob.yes_bids == {0.55: 60.0}

    def test_apply_delta_removes_emptied_level(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot(_snap(yes=[["0.5500", "100.00"]]))
        ob.apply_delta(_delta("yes", "0.5500", "-100.00"))
        assert 0.55 not in ob.yes_bids

    def test_apply_delta_removes_dust_residue(self):
        # Float summation can leave ~1e-6 contracts on an emptied level,
        # which then quotes a phantom top-of-book price.
        ob = KalshiOrderbook()
        ob.apply_snapshot(_snap(yes=[["0.5500", "100.00"], ["0.5000", "50.00"]]))
        ob.apply_delta(_delta("yes", "0.5500", "-99.999999"))
        assert 0.55 not in ob.yes_bids
        assert ob.best_bid_ask()[0] == 0.50

    def test_apply_delta_no_side(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot(_snap(no=[["0.3000", "200.00"]]))
        ob.apply_delta(_delta("no", "0.3000", "-197.00"))
        assert ob.no_bids == {0.30: 3.0}

    def test_best_bid_ask(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot(_snap(
            yes=[["0.5500", "100.00"], ["0.5000", "200.00"]],
            no=[["0.4000", "150.00"]],
        ))
        bid, ask, bid_sz, ask_sz = ob.best_bid_ask()
        assert bid == 0.55
        assert ask == pytest.approx(0.60)  # 1 - 0.40
        assert bid_sz == 100.0
        assert ask_sz == 150.0

    def test_empty_book(self):
        ob = KalshiOrderbook()
        ob.apply_snapshot(_snap())
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
        con1.close()
        con2 = _init_db(tmp_path / "idem.db")
        views = [
            r[0] for r in con2.sql(
                "SELECT view_name FROM duckdb_views()"
                " WHERE NOT internal"
            ).fetchall()
        ]
        con2.close()
        assert views == ["orderbook_snapshots_typed"]


# Polymarket message parsing is covered by test_ws_models.py.


class TestLoadMatches:
    def test_past_event_dates_skipped(self, tmp_path, monkeypatch):
        import db.arbitrage.collect_orderbooks as co

        path = tmp_path / "matches.json"
        path.write_text(json.dumps([
            {"id": "past", "kalshi_ticker": "K1", "polymarket_slug": "s1",
             "direction": "kalshi_yes_eq_poly_yes", "event_date": "2000-01-01"},
            {"id": "future", "kalshi_ticker": "K2", "polymarket_slug": "s2",
             "direction": "kalshi_yes_eq_poly_yes", "event_date": "2100-01-01"},
            {"id": "undated", "kalshi_ticker": "K3", "polymarket_slug": "s3",
             "direction": "kalshi_yes_eq_poly_yes"},
            # Past event_date, but "expires" says it is still trading.
            {"id": "expires-later", "kalshi_ticker": "K4",
             "polymarket_slug": "s4",
             "direction": "kalshi_yes_eq_poly_yes",
             "event_date": "2000-01-01",
             "expires": "2100-01-01T00:00:00Z"},
        ]))
        monkeypatch.setattr(co, "_MATCHES_PATH", path)
        ids = {m["id"] for m in co._load_matches()}
        assert ids == {"future", "undated", "expires-later"}


class TestCrossedBookPolicy:
    def test_blacklists_at_threshold(self):
        from db.arbitrage.collect_orderbooks import CrossedBookPolicy
        p = CrossedBookPolicy(threshold=3)
        assert p.record_crossed("T") is False
        assert p.record_crossed("T") is False
        assert p.record_crossed("T") is True  # threshold hit
        assert "T" in p.blacklist
        assert p.record_crossed("T") is False  # already blacklisted

    def test_valid_book_resets_streak(self):
        from db.arbitrage.collect_orderbooks import CrossedBookPolicy
        p = CrossedBookPolicy(threshold=2)
        p.record_crossed("T")
        p.record_valid("T")
        assert p.record_crossed("T") is False
        assert "T" not in p.blacklist

    def test_streaks_are_per_ticker(self):
        from db.arbitrage.collect_orderbooks import CrossedBookPolicy
        p = CrossedBookPolicy(threshold=2)
        p.record_crossed("A")
        p.record_crossed("B")
        assert p.blacklist == set()
        p.record_crossed("A")
        assert p.blacklist == {"A"}


class TestAuthRejected:
    def _err(self, status):
        from types import SimpleNamespace
        return SimpleNamespace(response=SimpleNamespace(status_code=status))

    def test_401_and_403_stop(self):
        from db.arbitrage.collect_orderbooks import _auth_rejected
        assert _auth_rejected("X", self._err(401)) is True
        assert _auth_rejected("X", self._err(403)) is True

    def test_other_statuses_retry(self):
        from db.arbitrage.collect_orderbooks import _auth_rejected
        assert _auth_rejected("X", self._err(500)) is False
        assert _auth_rejected("X", self._err(429)) is False


class TestSleepBackoff:
    def test_jittered_and_doubles(self, monkeypatch):
        import asyncio

        import db.arbitrage.collect_orderbooks as co

        sleeps = []

        async def fake_sleep(d):
            sleeps.append(d)

        monkeypatch.setattr(co.asyncio, "sleep", fake_sleep)
        nxt = asyncio.run(co._sleep_backoff("X", Exception("boom"), 4.0))
        assert nxt == 8.0
        assert 4.0 <= sleeps[0] <= 8.0  # base + full jitter

    def test_caps_at_60(self, monkeypatch):
        import asyncio

        import db.arbitrage.collect_orderbooks as co

        async def fake_sleep(d):
            pass

        monkeypatch.setattr(co.asyncio, "sleep", fake_sleep)
        assert asyncio.run(co._sleep_backoff("X", Exception("boom"), 60.0)) == 60.0
