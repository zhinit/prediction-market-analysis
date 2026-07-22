from __future__ import annotations

from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from db.arbitrage.api_models import PolyMarket, validate_items
from db.shared.auth import load_ed25519_key, sign_ed25519

_PUBLIC_BASE_URL = "https://gateway.polymarket.us"

_TRANSIENT = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
    ConnectionError,
    OSError,
)


class PolyAdapter:

    def __init__(
        self,
        api_key_id: str,
        private_key: str,
        *,
        base_url: str = _PUBLIC_BASE_URL,
    ) -> None:
        self._api_key_id = api_key_id
        self._private_key = load_ed25519_key(private_key)
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=10.0)

    def _auth_headers(self, method: str, path: str) -> dict[str, str]:
        timestamp, signature = sign_ed25519(self._private_key, method, path)
        return {
            "X-PM-Access-Key": self._api_key_id,
            "X-PM-Timestamp": timestamp,
            "X-PM-Signature": signature,
        }

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential_jitter(initial=1, max=30, jitter=5),
        retry=retry_if_exception_type(_TRANSIENT),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        headers: dict[str, str] = {}
        resp = await self._client.request(
            method, url, params=params, headers=headers,
        )
        if resp.status_code == 429:
            raise httpx.TimeoutException("Rate limited")
        resp.raise_for_status()
        return resp.json()

    async def fetch_markets(
        self, *, end_date_min: str, active: bool = True,
    ) -> list[dict[str, Any]]:
        markets: list[dict[str, Any]] = []
        offset = 0
        limit = 100
        while True:
            params: dict[str, Any] = {
                "limit": limit,
                "offset": offset,
                "active": str(active).lower(),
                "endDateMin": end_date_min,
            }
            resp = await self._request("GET", "/v1/markets", params=params)
            items = resp if isinstance(resp, list) else resp.get("markets", [])
            if not items:
                break
            for pm in validate_items(PolyMarket, items, label="Polymarket markets"):
                markets.append({
                    "slug": pm.slug,
                    "question": pm.question or pm.title or pm.slug,
                    "category": pm.category,
                    "sportsMarketTypeV2": pm.sports_market_type,
                    "gameId": pm.game_id,
                    "line": pm.line,
                    "gameStartTime": pm.game_start_time,
                })
            offset += limit
            if len(items) < limit:
                break
        return markets

    async def close(self) -> None:
        await self._client.aclose()
