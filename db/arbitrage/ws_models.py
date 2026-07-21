"""Pydantic models for the two orderbook websocket feeds.

Every message is validated (and its price/quantity strings converted) before
anything reaches the local book state or the database; a message that fails
validation is logged and skipped rather than becoming a silently wrong
snapshot. Shapes follow the payloads captured 2026-07-11.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# ---- Kalshi (trade-api/ws/v2) ----

class KalshiEnvelope(BaseModel):
    """Message envelope; seq is per-connection and lives here, not in msg."""

    type: str = ""
    seq: int | None = None
    msg: dict[str, Any] = {}


class KalshiSnapshot(BaseModel):
    """Full book: [price_dollars, qty] pairs per side; either side may be absent."""

    market_ticker: str
    yes_dollars_fp: list[tuple[float, float]] = []
    no_dollars_fp: list[tuple[float, float]] = []


class KalshiDelta(BaseModel):
    """Single price-level adjustment on one side."""

    market_ticker: str
    side: Literal["yes", "no"]
    price_dollars: float
    delta_fp: float


# ---- Polymarket US (v1/ws/markets) ----

class PolyPrice(BaseModel):
    value: float


class PolyLevel(BaseModel):
    px: PolyPrice
    qty: float


class PolyMarketData(BaseModel):
    market_slug: str = Field(alias="marketSlug")
    bids: list[PolyLevel] = []
    offers: list[PolyLevel] = []


class PolyEnvelope(BaseModel):
    market_data: PolyMarketData | None = Field(default=None, alias="marketData")
    error: Any = None
