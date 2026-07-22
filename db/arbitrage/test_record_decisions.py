from __future__ import annotations

import json

import pytest

from db.arbitrage.record_decisions import record


def _entry(id="slug-a-2026-07-22--A", ticker="EV1-A", slug="slug-a-2026-07-22",
           direction="kalshi_yes_eq_poly_yes", **kw):
    e = {
        "id": id, "kalshi_ticker": ticker, "polymarket_slug": slug,
        "direction": direction, "poly_yes": "Player A",
        "event_date": "2026-07-22", "notes": "n",
    }
    e.update(kw)
    return e


def _reject(event="EV1", slug="slug-b-2026-07-22", reason="different event"):
    return {"kalshi_event_ticker": event, "polymarket_slug": slug,
            "reason": reason}


@pytest.fixture()
def paths(tmp_path):
    return tmp_path / "matches.json", tmp_path / "rejected.json"


class TestRecord:
    def test_appends_and_reruns_idempotently(self, paths):
        matches, rejected = paths
        decisions = {"approve": [_entry()], "reject": [_reject()]}
        counts = record(decisions, matches, rejected)
        assert counts == {"approved": 1, "rejected": 1, "skipped": 0}
        counts = record(decisions, matches, rejected)
        assert counts == {"approved": 0, "rejected": 0, "skipped": 2}
        assert len(json.loads(matches.read_text())) == 1
        assert len(json.loads(rejected.read_text())) == 1

    def test_appends_to_existing_files(self, paths):
        matches, rejected = paths
        matches.write_text(json.dumps([_entry(id="old", ticker="EV0-B",
                                              slug="slug-old")]))
        record({"approve": [_entry()]}, matches, rejected)
        assert [m["id"] for m in json.loads(matches.read_text())] == [
            "old", "slug-a-2026-07-22--A"]

    def test_missing_field_rejected_without_write(self, paths):
        matches, rejected = paths
        bad = _entry()
        del bad["poly_yes"]
        with pytest.raises(SystemExit, match="poly_yes"):
            record({"approve": [bad]}, matches, rejected)
        assert not matches.exists()

    def test_bad_direction_rejected(self, paths):
        matches, rejected = paths
        with pytest.raises(SystemExit, match="bad direction"):
            record({"approve": [_entry(direction="poly_eq_kalshi")]},
                   matches, rejected)

    def test_entry_without_expiry_info_rejected(self, paths):
        matches, rejected = paths
        e = _entry()
        e["event_date"] = ""
        with pytest.raises(SystemExit, match="expires"):
            record({"approve": [e]}, matches, rejected)

    def test_reject_needs_reason(self, paths):
        matches, rejected = paths
        with pytest.raises(SystemExit, match="reason"):
            record({"reject": [_reject(reason="")]}, matches, rejected)

    def test_one_kalshi_market_two_poly_slugs_blocked(self, paths):
        # The Hundred failure mode: one Kalshi market quoting two Poly
        # markets — at most one pairing is the same real-world event.
        matches, rejected = paths
        decisions = {"approve": [
            _entry(id="a--LON", ticker="KXT20-LON", slug="aec-hundred-a"),
            _entry(id="b--LON", ticker="KXT20-LON", slug="aec-hundredw-a"),
        ]}
        with pytest.raises(SystemExit, match="several Poly markets"):
            record(decisions, matches, rejected)
        assert not matches.exists()  # nothing written on invariant failure

    def test_duplicate_ids_blocked(self, paths):
        matches, rejected = paths
        matches.write_text(json.dumps([_entry()]))
        # same id sneaking in via a pre-existing file with different ticker
        dup = _entry(ticker="EV9-Z", slug="slug-z")
        matches.write_text(json.dumps([_entry(), dup]))
        with pytest.raises(SystemExit, match="duplicate match ids"):
            record({"approve": []}, matches, rejected)
