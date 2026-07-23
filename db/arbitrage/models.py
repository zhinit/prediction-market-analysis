from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


# ── Kalshi ────────────────────────────────────────────────────────────

class KalshiEvent(BaseModel):
    event_ticker: str
    series_ticker: str
    title: str
    category: str
    sub_title: str | None = None


class KalshiEventResponse(BaseModel):
    events: list[KalshiEvent]
    cursor: str | None = None


class KalshiMarket(BaseModel):
    ticker: str
    event_ticker: str
    market_type: str
    yes_sub_title: str | None = None
    no_sub_title: str | None = None
    status: str


class KalshiMarketResponse(BaseModel):
    markets: list[KalshiMarket]
    cursor: str | None = None


# ── Polymarket US ─────────────────────────────────────────────────────

class PolyTeam(BaseModel):
    id: int
    name: str
    abbreviation: str
    league: str
    display_abbreviation: str | None = None
    ordering: str | None = None

    class Config:
        alias_generator = lambda s: "".join(
            w.capitalize() if i else w
            for i, w in enumerate(s.split("_"))
        )
        populate_by_name = True


class PolyMarketSide(BaseModel):
    id: str
    description: str | None = None
    team_id: int | None = None
    team: PolyTeam | None = None
    identifier: str | None = None
    long: bool | None = None

    class Config:
        alias_generator = lambda s: "".join(
            w.capitalize() if i else w
            for i, w in enumerate(s.split("_"))
        )
        populate_by_name = True


class PolyMarket(BaseModel):
    id: str
    slug: str
    question: str | None = None
    sports_market_type: str | None = None
    market_type: str | None = None
    market_sides: list[PolyMarketSide] = []
    active: bool | None = None
    closed: bool | None = None
    game_start_time: str | None = None
    end_date: str | None = None

    class Config:
        alias_generator = lambda s: "".join(
            w.capitalize() if i else w
            for i, w in enumerate(s.split("_"))
        )
        populate_by_name = True


class PolyEvent(BaseModel):
    id: str
    slug: str
    title: str
    start_date: str | None = None
    end_date: str | None = None
    active: bool | None = None
    closed: bool | None = None
    live: bool | None = None
    ended: bool | None = None
    markets: list[PolyMarket] = []

    class Config:
        alias_generator = lambda s: "".join(
            w.capitalize() if i else w
            for i, w in enumerate(s.split("_"))
        )
        populate_by_name = True


class PolyLeagueResponse(BaseModel):
    events: list[PolyEvent] = []


# ── Matched pair (output) ────────────────────────────────────────────

class MatchedMarket(BaseModel):
    game_date: date
    away_team: str
    home_team: str
    kalshi_ticker_away: str
    kalshi_ticker_home: str
    poly_slug: str
    kalshi_event_ticker: str
    poly_event_slug: str
