"""Fetch the YES side of Polymarket US markets by slug.

The market detail endpoint is public (no auth). The YES side — the outcome
the orderbook quotes — is the ``marketSides`` entry with ``long: true``;
``team.ordering`` and slug order do not indicate it.

Usage:
    uv run python -m db.arbitrage.fetch_poly_sides <slug> [<slug> ...]
    uv run python -m db.arbitrage.fetch_poly_sides --from-candidates
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

_BASE_URL = "https://gateway.polymarket.us"
_CANDIDATES_PATH = Path("db/arbitrage/candidates.json")

_TRANSIENT = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
    ConnectionError,
    OSError,
)


def extract_yes_side(market: dict[str, Any]) -> dict[str, Any]:
    sides = market.get("marketSides") or []
    long_sides = [s for s in sides if s.get("long") is True]
    if len(long_sides) != 1:
        raise ValueError(
            f"expected exactly one marketSides entry with long=true, "
            f"got {len(long_sides)}"
        )
    side = long_sides[0]
    team = side.get("team") or {}
    return {
        "name": team.get("name"),
        "abbreviation": team.get("abbreviation"),
        "description": side.get("description"),
    }


def slugs_from_candidates(path: Path = _CANDIDATES_PATH) -> list[str]:
    candidates = json.loads(path.read_text())
    seen: set[str] = set()
    slugs: list[str] = []
    for c in candidates:
        slug = c.get("polymarket", {}).get("slug", "")
        if slug and slug not in seen:
            seen.add(slug)
            slugs.append(slug)
    return slugs


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential_jitter(initial=1, max=30, jitter=5),
    retry=retry_if_exception_type(_TRANSIENT),
    reraise=True,
)
async def _fetch_detail(
    client: httpx.AsyncClient, base_url: str, slug: str,
) -> Any:
    resp = await client.get(f"{base_url}/v1/market/slug/{slug}")
    if resp.status_code == 429:
        raise httpx.TimeoutException("Rate limited")
    resp.raise_for_status()
    return resp.json()


async def fetch_sides(
    slugs: list[str],
    *,
    base_url: str = _BASE_URL,
    concurrency: int = 5,
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[dict[str, Any]]:
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(timeout=10.0, transport=transport) as client:

        async def one(slug: str) -> dict[str, Any]:
            async with sem:
                try:
                    resp = await _fetch_detail(client, base_url, slug)
                except httpx.HTTPError as e:
                    return {"slug": slug, "error": str(e)}
            market = resp.get("market") or {}
            try:
                yes_side = extract_yes_side(market)
            except ValueError as e:
                return {"slug": slug, "error": str(e)}
            return {
                "slug": slug,
                "question": market.get("question"),
                "yes_side": yes_side,
            }

        return list(await asyncio.gather(*(one(s) for s in slugs)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slugs", nargs="*", help="Polymarket US market slugs")
    parser.add_argument(
        "--from-candidates",
        action="store_true",
        help=f"read slugs from {_CANDIDATES_PATH}",
    )
    args = parser.parse_args()

    if args.from_candidates:
        slugs = slugs_from_candidates()
    else:
        slugs = args.slugs
    if not slugs:
        parser.error("no slugs given (pass slugs or --from-candidates)")

    results = asyncio.run(fetch_sides(slugs))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
