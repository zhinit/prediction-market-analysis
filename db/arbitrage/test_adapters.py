from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from db.arbitrage.kalshi_adapter import KalshiAdapter
from db.arbitrage.poly_adapter import PolyAdapter

FIXTURES = Path(__file__).parent / "fixtures"

_FAKE_REQUEST = httpx.Request("GET", "https://test.example.com")


def _mock_rsa_key():
    from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
    return generate_private_key(public_exponent=65537, key_size=2048)


def _mock_ed25519_key():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    return Ed25519PrivateKey.generate()


class TestKalshiAdapter:
    @pytest.fixture()
    def adapter(self, tmp_path):
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            NoEncryption,
            PrivateFormat,
        )
        key = _mock_rsa_key()
        pem_path = tmp_path / "key.pem"
        pem_path.write_bytes(
            key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())
        )
        return KalshiAdapter(
            api_key_id="test-key",
            private_key_path=pem_path,
            base_url="https://test.kalshi.com/trade-api/v2",
        )

    @pytest.mark.asyncio
    async def test_fetch_events_pagination(self, adapter):
        page1 = httpx.Response(200, request=_FAKE_REQUEST, json={
            "events": [{"event_ticker": "EV1", "title": "Event 1"}],
            "cursor": "abc123",
        })
        page2 = httpx.Response(200, request=_FAKE_REQUEST, json={
            "events": [{"event_ticker": "EV2", "title": "Event 2"}],
            "cursor": None,
        })
        responses = iter([page1, page2])

        async def mock_request(*args, **kwargs):
            return next(responses)

        adapter._client.request = mock_request
        events = await adapter.fetch_events()
        assert len(events) == 2
        assert events[0]["event_ticker"] == "EV1"
        assert events[1]["event_ticker"] == "EV2"
        await adapter.close()

    @pytest.mark.asyncio
    async def test_fetch_events_empty(self, adapter):
        resp = httpx.Response(200, request=_FAKE_REQUEST, json={"events": [], "cursor": None})

        async def mock_request(*args, **kwargs):
            return resp

        adapter._client.request = mock_request
        events = await adapter.fetch_events()
        assert events == []
        await adapter.close()

    @pytest.mark.asyncio
    async def test_fetch_event_markets(self, adapter):
        resp = httpx.Response(200, request=_FAKE_REQUEST, json={
            "markets": [
                {"ticker": "MKT-A", "title": "Market A"},
                {"ticker": "MKT-B", "title": "Market B"},
            ],
        })

        async def mock_request(*args, **kwargs):
            return resp

        adapter._client.request = mock_request
        markets = await adapter.fetch_event_markets("EV1")
        assert len(markets) == 2
        await adapter.close()

    @pytest.mark.asyncio
    async def test_fetch_events_skips_invalid(self, adapter):
        resp = httpx.Response(200, request=_FAKE_REQUEST, json={
            "events": [
                {"event_ticker": "EV1", "title": "Event 1"},
                {"title": "no ticker"},
                {"event_ticker": ""},
            ],
            "cursor": None,
        })

        async def mock_request(*args, **kwargs):
            return resp

        adapter._client.request = mock_request
        events = await adapter.fetch_events()
        assert [e["event_ticker"] for e in events] == ["EV1"]
        await adapter.close()

    def test_parse_kalshi_fixture(self):
        data = json.loads((FIXTURES / "kalshi_events.json").read_text())
        events = data["events"]
        assert len(events) == 2
        assert events[0]["event_ticker"] == "KXMLBGAME-26JUL10-TEX-NYY"
        assert len(events[0]["markets"]) == 2

    def test_parse_kalshi_series_fixture(self):
        data = json.loads((FIXTURES / "kalshi_series.json").read_text())
        assert len(data) == 3
        assert data[0]["ticker"] == "KXMLBGAME"


class TestPolyAdapter:
    @pytest.fixture()
    def adapter(self):
        ed_key = _mock_ed25519_key()
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            NoEncryption,
            PrivateFormat,
        )
        hex_key = ed_key.private_bytes(
            Encoding.Raw, PrivateFormat.Raw, NoEncryption(),
        ).hex()
        return PolyAdapter(
            api_key_id="test-key",
            private_key=hex_key,
            base_url="https://test.polymarket.us",
        )

    @pytest.mark.asyncio
    async def test_fetch_markets_pagination(self, adapter):
        page1_items = [
            {"slug": f"market-{i}", "question": f"Q{i}", "category": "sports"}
            for i in range(100)
        ]
        page2_items = [
            {"slug": "market-100", "question": "Q100", "category": "sports"}
        ]
        page1 = httpx.Response(200, request=_FAKE_REQUEST, json=page1_items)
        page2 = httpx.Response(200, request=_FAKE_REQUEST, json=page2_items)
        responses = iter([page1, page2])

        async def mock_request(*args, **kwargs):
            return next(responses)

        adapter._client.request = mock_request
        markets = await adapter.fetch_markets(end_date_min="2026-07-10T00:00:00Z")
        assert len(markets) == 101
        await adapter.close()

    @pytest.mark.asyncio
    async def test_fetch_markets_empty_stops(self, adapter):
        resp = httpx.Response(200, request=_FAKE_REQUEST, json=[])

        async def mock_request(*args, **kwargs):
            return resp

        adapter._client.request = mock_request
        markets = await adapter.fetch_markets(end_date_min="2026-07-10T00:00:00Z")
        assert markets == []
        await adapter.close()

    @pytest.mark.asyncio
    async def test_end_date_min_always_set(self, adapter):
        captured_params = {}

        async def mock_request(method, url, *, params=None, headers=None):
            captured_params.update(params or {})
            return httpx.Response(200, request=_FAKE_REQUEST, json=[])

        adapter._client.request = mock_request
        await adapter.fetch_markets(end_date_min="2026-07-10T00:00:00Z")
        assert "endDateMin" in captured_params
        assert captured_params["endDateMin"] == "2026-07-10T00:00:00Z"
        await adapter.close()

    @pytest.mark.asyncio
    async def test_fetch_markets_skips_invalid(self, adapter):
        resp = httpx.Response(200, request=_FAKE_REQUEST, json=[
            {"slug": "good-market", "question": "Q"},
            {"question": "no slug"},
            {"slug": ""},
        ])
        responses = iter([resp, httpx.Response(200, request=_FAKE_REQUEST, json=[])])

        async def mock_request(*args, **kwargs):
            return next(responses)

        adapter._client.request = mock_request
        markets = await adapter.fetch_markets(end_date_min="2026-07-10T00:00:00Z")
        assert [m["slug"] for m in markets] == ["good-market"]
        await adapter.close()

    def test_parse_poly_fixture(self):
        data = json.loads((FIXTURES / "poly_markets.json").read_text())
        assert len(data) == 4
        assert data[0]["slug"] == "aec-mlb-tex-nyy-2026-07-10-moneyline"
        assert data[0]["sportsMarketTypeV2"] == "SPORTS_MARKET_TYPE_MONEYLINE"
