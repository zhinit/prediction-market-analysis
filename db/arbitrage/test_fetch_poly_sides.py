from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from db.arbitrage.api_models import PolyMarketDetail
from db.arbitrage.fetch_poly_sides import (
    extract_yes_side,
    fetch_sides,
    slugs_from_candidates,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _detail() -> dict:
    return json.loads((FIXTURES / "poly_market_detail.json").read_text())


def _market() -> PolyMarketDetail:
    return PolyMarketDetail.model_validate(_detail()["market"])


class TestExtractYesSide:
    def test_long_side_is_yes(self):
        yes = extract_yes_side(_market())
        assert yes["name"] == "Texas Rangers"
        assert yes["abbreviation"] == "tex"
        assert yes["description"] == "Texas Rangers"

    def test_no_long_side_raises(self):
        market = _market()
        for side in market.market_sides:
            side.long = False
        with pytest.raises(ValueError, match="got 0"):
            extract_yes_side(market)

    def test_multiple_long_sides_raises(self):
        market = _market()
        for side in market.market_sides:
            side.long = True
        with pytest.raises(ValueError, match="got 2"):
            extract_yes_side(market)

    def test_missing_team_falls_back_to_description(self):
        market = _market()
        market.market_sides[0].team = None
        yes = extract_yes_side(market)
        assert yes["name"] is None
        assert yes["description"] == "Texas Rangers"


class TestSlugsFromCandidates:
    def test_dedupes_and_preserves_order(self, tmp_path):
        path = tmp_path / "candidates.json"
        path.write_text(json.dumps([
            {"polymarket": {"slug": "slug-b"}},
            {"polymarket": {"slug": "slug-a"}},
            {"polymarket": {"slug": "slug-b"}},
            {"polymarket": {}},
        ]))
        assert slugs_from_candidates(path) == ["slug-b", "slug-a"]


class TestFetchSides:
    def _transport(self) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            slug = request.url.path.rsplit("/", 1)[-1]
            if slug == "missing-market":
                return httpx.Response(404)
            return httpx.Response(200, json=_detail())

        return httpx.MockTransport(handler)

    def test_fetch_and_parse(self):
        results = asyncio.run(fetch_sides(
            ["aec-mlb-tex-nyy-2026-07-10-moneyline"],
            transport=self._transport(),
        ))
        assert results == [{
            "slug": "aec-mlb-tex-nyy-2026-07-10-moneyline",
            "question": "Rangers vs. Yankees",
            "description": "This market will settle to the winner of the "
                           "Texas Rangers vs New York Yankees MLB game "
                           "scheduled for Jul 10, 2026.",
            "yes_side": {
                "name": "Texas Rangers",
                "abbreviation": "tex",
                "description": "Texas Rangers",
            },
        }]

    def test_http_error_reported_per_slug(self):
        results = asyncio.run(fetch_sides(
            ["missing-market", "aec-mlb-tex-nyy-2026-07-10-moneyline"],
            transport=self._transport(),
        ))
        assert "error" in results[0]
        assert results[0]["slug"] == "missing-market"
        assert results[1]["yes_side"]["name"] == "Texas Rangers"
