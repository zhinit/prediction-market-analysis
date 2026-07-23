"""Market matcher: discover today's MLB game-winner markets on Kalshi and
Polymarket US, match them by team abbreviation + date."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

from db.arbitrage.models import (
    KalshiEvent,
    KalshiEventResponse,
    KalshiMarket,
    KalshiMarketResponse,
    MatchedMarket,
    PolyEvent,
    PolyLeagueResponse,
)
from db.arbitrage.teams import ABBR_TO_MLB_ID

EASTERN = ZoneInfo("America/New_York")

KALSHI_BASE = "https://external-api.kalshi.com/trade-api/v2"
POLY_GATEWAY = "https://gateway.polymarket.us"
TIMEOUTS = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)

MONTHS = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}

TICKER_RE = re.compile(
    r"^KXMLBGAME-(?P<yy>\d{2})(?P<mon>[A-Z]{3})(?P<dd>\d{2})"
    r"(?P<hhmm>\d{4})?(?P<pair>[A-Z]+?)(?:G?(?P<gamenum>\d))?$"
)


def is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    return isinstance(exc, httpx.HTTPStatusError) and (
        exc.response.status_code == 429 or exc.response.status_code >= 500
    )


@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, max=30),
    retry=retry_if_exception(is_retryable),
    reraise=True,
)
def fetch(client: httpx.Client, url: str, params: dict | None = None) -> bytes:
    r = client.get(url, params=params or {})
    r.raise_for_status()
    return r.content


def fetch_all_kalshi(
    client: httpx.Client, path: str, params: dict, response_model: type, key: str,
) -> list:
    results = []
    cursor = None
    while True:
        p = {**params, "limit": 200}
        if cursor:
            p["cursor"] = cursor
        raw = fetch(client, path, p)
        resp = response_model.model_validate_json(raw)
        results.extend(getattr(resp, key))
        cursor = resp.cursor
        if not cursor:
            break
    return results


# ── Kalshi market discovery ───────────────────────────────────────────

@dataclass(frozen=True)
class ParsedKalshiTicker:
    et_date: date
    away: str
    home: str


def parse_kalshi_event_ticker(ticker: str) -> ParsedKalshiTicker | None:
    m = TICKER_RE.match(ticker)
    if not m:
        return None
    mon = MONTHS.get(m["mon"])
    if mon is None:
        return None
    try:
        et_date = date(2000 + int(m["yy"]), mon, int(m["dd"]))
    except ValueError:
        return None
    return ParsedKalshiTicker(et_date=et_date, away="", home="", )


def discover_kalshi_markets(
    client: httpx.Client, target_date: date,
) -> list[tuple[KalshiEvent, list[KalshiMarket]]]:
    events: list[KalshiEvent] = fetch_all_kalshi(
        client, f"{KALSHI_BASE}/events",
        {"series_ticker": "KXMLBGAME", "status": "open"},
        KalshiEventResponse, "events",
    )

    yy = target_date.strftime("%y")
    mon = target_date.strftime("%b").upper()
    dd = target_date.strftime("%d")
    date_prefix = f"KXMLBGAME-{yy}{mon}{dd}"

    today_events = [e for e in events if e.event_ticker.startswith(date_prefix)]

    results = []
    for event in today_events:
        markets: list[KalshiMarket] = fetch_all_kalshi(
            client, f"{KALSHI_BASE}/markets",
            {"event_ticker": event.event_ticker},
            KalshiMarketResponse, "markets",
        )
        results.append((event, markets))
    return results


def extract_kalshi_teams(
    event: KalshiEvent, markets: list[KalshiMarket],
) -> tuple[str, str, str, str] | None:
    """Returns (away_abbr, home_abbr, away_ticker, home_ticker) or None."""
    suffixes = []
    for m in markets:
        suffix = m.ticker.rsplit("-", 1)[-1]
        if suffix in ABBR_TO_MLB_ID:
            suffixes.append((suffix, m.ticker))

    if len(suffixes) != 2:
        return None

    # Kalshi event ticker has teams as away+home concatenation.
    # Parse the team pair from the event ticker to determine order.
    m = TICKER_RE.match(event.event_ticker)
    if not m:
        return None
    pair = m["pair"]
    a, b = suffixes[0][0], suffixes[1][0]

    if pair == a + b:
        away, home = suffixes[0], suffixes[1]
    elif pair == b + a:
        away, home = suffixes[1], suffixes[0]
    else:
        return None

    return away[0], home[0], away[1], home[1]


# ── Polymarket market discovery ───────────────────────────────────────

@dataclass(frozen=True)
class PolyMoneyline:
    event: PolyEvent
    slug: str
    away_abbr: str
    home_abbr: str


def discover_poly_markets(
    client: httpx.Client, target_date: date,
) -> list[PolyMoneyline]:
    date_str = target_date.isoformat()
    raw = fetch(client, f"{POLY_GATEWAY}/v2/leagues/mlb/events", {"limit": 100})
    resp = PolyLeagueResponse.model_validate_json(raw)

    results = []
    for event in resp.events:
        event_date = event.slug.split("-")[-3:]
        try:
            event_date_str = "-".join(event_date)
            if event_date_str != date_str:
                continue
        except (ValueError, IndexError):
            continue

        for market in event.markets:
            if market.sports_market_type != "baseball_team_full_game_winner":
                continue

            away = home = None
            for side in market.market_sides:
                if not side.team or side.team.league != "mlb":
                    continue
                abbr = side.team.display_abbreviation or side.team.abbreviation.upper()
                ordering = getattr(side.team, "ordering", None)
                if ordering == "away":
                    away = abbr
                elif ordering == "home":
                    home = abbr

            if away and home:
                results.append(PolyMoneyline(
                    event=event, slug=market.slug,
                    away_abbr=away, home_abbr=home,
                ))
    return results


# ── Matching ──────────────────────────────────────────────────────────

def match_markets(target_date: date) -> tuple[list[MatchedMarket], list[str]]:
    """Discover and match today's markets. Returns (matched, log_messages)."""
    log: list[str] = []

    with httpx.Client(timeout=TIMEOUTS) as client:
        kalshi_pairs = discover_kalshi_markets(client, target_date)
        poly_markets = discover_poly_markets(client, target_date)

    log.append(f"Kalshi: {len(kalshi_pairs)} events for {target_date}")
    log.append(f"Polymarket: {len(poly_markets)} moneyline markets for {target_date}")

    # Build Kalshi lookup: frozenset({away, home}) → (event, away_ticker, home_ticker)
    kalshi_by_teams: dict[frozenset[str], tuple[KalshiEvent, str, str, str, str]] = {}
    for event, markets in kalshi_pairs:
        teams = extract_kalshi_teams(event, markets)
        if teams is None:
            log.append(f"  Kalshi skip (can't parse teams): {event.event_ticker}")
            continue
        away, home, away_ticker, home_ticker = teams
        key = frozenset({away, home})
        kalshi_by_teams[key] = (event, away, home, away_ticker, home_ticker)

    matched: list[MatchedMarket] = []
    for pm in poly_markets:
        key = frozenset({pm.away_abbr, pm.home_abbr})
        if key not in kalshi_by_teams:
            log.append(
                f"  Polymarket no Kalshi match: {pm.slug} "
                f"({pm.away_abbr} @ {pm.home_abbr})"
            )
            continue

        k_event, k_away, k_home, k_away_ticker, k_home_ticker = kalshi_by_teams[key]
        matched.append(MatchedMarket(
            game_date=target_date,
            away_team=pm.away_abbr,
            home_team=pm.home_abbr,
            kalshi_ticker_away=k_away_ticker,
            kalshi_ticker_home=k_home_ticker,
            poly_slug=pm.slug,
            kalshi_event_ticker=k_event.event_ticker,
            poly_event_slug=pm.event.slug,
        ))
        kalshi_by_teams.pop(key)

    for key, (event, away, home, _, _) in kalshi_by_teams.items():
        log.append(
            f"  Kalshi no Polymarket match: {event.event_ticker} ({away} @ {home})"
        )

    log.append(f"Matched: {len(matched)} market pairs")
    return matched, log


if __name__ == "__main__":
    from datetime import date

    today = datetime.now(EASTERN).date()
    matched, log = match_markets(today)
    for msg in log:
        print(msg)
    print()
    for m in matched:
        print(
            f"  {m.away_team:4s} @ {m.home_team:4s} | "
            f"K: {m.kalshi_ticker_away}, {m.kalshi_ticker_home} | "
            f"P: {m.poly_slug}"
        )
