"""Pydantic models for the REST API responses used by the matcher pipeline.

Every fetched item is validated before it is returned; entries that fail
validation are skipped with a warning instead of propagating malformed data
downstream. Models declare exactly the fields the pipeline consumes.
"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import AliasChoices, BaseModel, Field, ValidationError


# ---- Kalshi (trade-api/v2) ----

class KalshiSeries(BaseModel):
    ticker: str = Field(min_length=1)
    category: str = ""
    title: str = ""


class KalshiEvent(BaseModel):
    event_ticker: str = Field(min_length=1)
    series_ticker: str | None = None
    title: str | None = None
    strike_date: str | None = None
    markets: list[dict[str, Any]] | None = None


class KalshiMarket(BaseModel):
    ticker: str = Field(min_length=1)
    title: str | None = None
    yes_sub_title: str | None = None
    # When Kalshi expects the underlying event to be over. Unlike close_time
    # (the latest possible close: days out for MLB, weeks for tennis) this
    # tracks the real event, so it is what expiry pruning keys on.
    expected_expiration_time: str | None = None
    # Settlement rules text: names the exact event, competition, gender and
    # start time ("...men's professional The Hundred cricket match...").
    # This is the primary evidence for the /matcher verification pass.
    rules_primary: str | None = None


# ---- Polymarket US (v1) ----

class PolyMarket(BaseModel):
    slug: str = Field(min_length=1)
    question: str | None = None
    title: str | None = None
    category: str = ""
    sports_market_type: str | None = Field(
        default=None, validation_alias="sportsMarketTypeV2",
    )
    game_id: str | None = Field(
        default=None, validation_alias=AliasChoices("gameId", "game_id"),
    )
    line: float | str | None = None
    game_start_time: str | None = Field(
        default=None, validation_alias="gameStartTime",
    )


class PolySideTeam(BaseModel):
    name: str | None = None
    abbreviation: str | None = None


class PolyMarketSide(BaseModel):
    long: bool | None = None
    description: str | None = None
    team: PolySideTeam | None = None


class PolyMarketDetail(BaseModel):
    slug: str = ""
    question: str | None = None
    # Settlement text: names the exact event, competition and gender
    # ("...The Hundred Women match..."), which the question often omits.
    description: str | None = None
    market_sides: list[PolyMarketSide] = Field(
        default_factory=list, validation_alias="marketSides",
    )


class PolyMarketDetailResponse(BaseModel):
    market: PolyMarketDetail | None = None


_M = TypeVar("_M", bound=BaseModel)


def validate_items(
    model: type[_M], items: list[Any], *, label: str,
) -> list[_M]:
    """Validate a list of raw API items, skipping (and counting) bad ones."""
    valid: list[_M] = []
    skipped = 0
    for item in items:
        try:
            valid.append(model.model_validate(item))
        except ValidationError:
            skipped += 1
    if skipped:
        print(f"{label}: skipped {skipped} invalid entries", flush=True)
    return valid
