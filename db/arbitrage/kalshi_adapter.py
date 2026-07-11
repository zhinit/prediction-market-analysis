from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from db.shared.auth import load_rsa_key, sign_rsa

_BASE_URL = "https://external-api.kalshi.com/trade-api/v2"

_TRANSIENT = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
    ConnectionError,
    OSError,
)


class KalshiAdapter:

    def __init__(
        self,
        api_key_id: str,
        private_key_path: Path,
        *,
        base_url: str = _BASE_URL,
    ) -> None:
        self._api_key_id = api_key_id
        self._private_key = load_rsa_key(private_key_path)
        self._base_url = base_url.rstrip("/")
        self._path_prefix = urlparse(self._base_url).path
        self._client = httpx.AsyncClient(timeout=10.0)

    def _auth_headers(self, method: str, full_path: str) -> dict[str, str]:
        timestamp, signature = sign_rsa(self._private_key, method, full_path)
        return {
            "KALSHI-ACCESS-KEY": self._api_key_id,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "KALSHI-ACCESS-SIGNATURE": signature,
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
        sign_path = f"{self._path_prefix}{path}"
        headers = self._auth_headers(method, sign_path)
        resp = await self._client.request(
            method, url, params=params, headers=headers,
        )
        if resp.status_code == 429:
            raise httpx.TimeoutException("Rate limited")
        resp.raise_for_status()
        return resp.json()

    async def fetch_series(self) -> list[dict[str, Any]]:
        resp = await self._request("GET", "/series")
        series_list = resp if isinstance(resp, list) else resp.get("series", [])
        return series_list

    async def fetch_events(self, *, status: str = "open") -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            params: dict[str, Any] = {"limit": 200, "status": status}
            if cursor:
                params["cursor"] = cursor
            resp = await self._request("GET", "/events", params=params)
            events.extend(resp.get("events", []))
            cursor = resp.get("cursor")
            if not cursor:
                break
        return events

    async def fetch_event_markets(self, event_ticker: str) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"event_ticker": event_ticker, "limit": 200}
        resp = await self._request("GET", "/markets", params=params)
        return resp.get("markets", [])

    async def close(self) -> None:
        await self._client.aclose()
