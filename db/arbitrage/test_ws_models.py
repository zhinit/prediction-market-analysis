from __future__ import annotations

import pytest
from pydantic import ValidationError

from db.arbitrage.ws_models import (
    KalshiDelta,
    KalshiEnvelope,
    KalshiSnapshot,
    PolyEnvelope,
)


class TestKalshiModels:
    def test_envelope_parses_book_message(self):
        raw = (
            '{"type": "orderbook_delta", "seq": 42,'
            ' "msg": {"market_ticker": "T", "side": "yes",'
            ' "price_dollars": "0.55", "delta_fp": "10.00"}}'
        )
        env = KalshiEnvelope.model_validate_json(raw)
        assert env.type == "orderbook_delta"
        assert env.seq == 42
        delta = KalshiDelta.model_validate(env.msg)
        assert delta.price_dollars == pytest.approx(0.55)
        assert delta.delta_fp == pytest.approx(10.0)

    def test_envelope_tolerates_non_book_messages(self):
        env = KalshiEnvelope.model_validate_json('{"type": "subscribed", "id": 1}')
        assert env.type == "subscribed"
        assert env.seq is None

    def test_snapshot_converts_price_strings(self):
        snap = KalshiSnapshot.model_validate({
            "market_ticker": "T",
            "yes_dollars_fp": [["0.5500", "100.00"]],
        })
        assert snap.yes_dollars_fp == [(0.55, 100.0)]
        assert snap.no_dollars_fp == []

    def test_snapshot_rejects_garbage_price(self):
        with pytest.raises(ValidationError):
            KalshiSnapshot.model_validate({
                "market_ticker": "T",
                "yes_dollars_fp": [["not-a-price", "100.00"]],
            })

    def test_delta_rejects_unknown_side(self):
        with pytest.raises(ValidationError):
            KalshiDelta.model_validate({
                "market_ticker": "T", "side": "maybe",
                "price_dollars": "0.5", "delta_fp": "1",
            })


class TestPolyModels:
    def test_market_data_parses_nested_px(self):
        raw = (
            '{"marketData": {"marketSlug": "s",'
            ' "bids": [{"px": {"value": "0.423", "currency": "USD"}, "qty": "10"}],'
            ' "offers": [{"px": {"value": "0.55", "currency": "USD"}, "qty": "25.5"}]}}'
        )
        env = PolyEnvelope.model_validate_json(raw)
        md = env.market_data
        assert md.market_slug == "s"
        assert md.bids[0].px.value == pytest.approx(0.423)
        assert md.offers[0].qty == pytest.approx(25.5)

    def test_missing_px_value_rejected(self):
        with pytest.raises(ValidationError):
            PolyEnvelope.model_validate({
                "marketData": {
                    "marketSlug": "s",
                    "bids": [{"px": {}, "qty": "10"}],
                },
            })

    def test_error_message(self):
        env = PolyEnvelope.model_validate({"error": {"code": 1}})
        assert env.error == {"code": 1}
        assert env.market_data is None

    def test_non_book_message(self):
        env = PolyEnvelope.model_validate({"subscribed": {"requestId": "x"}})
        assert env.market_data is None
        assert env.error is None
