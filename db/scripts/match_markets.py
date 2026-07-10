from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from auth import require_env
from kalshi_adapter import KalshiAdapter
from poly_adapter import PolyAdapter

_STOP_WORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "or", "she",
    "that", "the", "to", "was", "were", "will", "with",
})

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_DATE_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})(?:\b|T)")

_TICKER_DATE = re.compile(
    r"-(\d{2})(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)(\d{2})",
    re.IGNORECASE,
)
_MONTH_ABBR = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}

_CANDIDATES_PATH = Path("db/data/candidates.json")
_MATCHES_PATH = Path("db/data/matches.json")
_REJECTED_PATH = Path("db/data/rejected_matches.json")


# ---- Data types ----

@dataclass(frozen=True)
class KalshiEvent:
    event_ticker: str
    series_ticker: str
    title: str
    strike_date: str | None
    category: str
    market_count: int
    sport: str | None


@dataclass(frozen=True)
class PolyGame:
    game_id: str | None
    slug: str
    question: str
    category: str
    sport_type: str | None
    slugs: tuple[str, ...]
    sport: str | None


@dataclass(frozen=True)
class EventCandidate:
    kalshi_event: KalshiEvent
    poly_game: PolyGame
    score: float


# ---- Text utilities ----

def normalize_title(title: str) -> set[str]:
    lowered = title.lower()
    stripped = _PUNCT.sub(" ", lowered)
    tokens = stripped.split()
    return {t for t in tokens if t not in _STOP_WORDS}


def jaccard_score(set_a: set[str], set_b: set[str]) -> float:
    if not set_a and not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


# ---- Grouping ----

_SPORT_FROM_TITLE: list[tuple[str, str]] = [
    ("ncaa football", "cfb"),
    ("college football", "cfb"),
    ("ncaaf", "cfb"),
    ("ncaa basketball", "cbb"),
    ("college basketball", "cbb"),
    ("ncaab", "cbb"),
    ("premier league", "epl"),
    ("formula 1", "f1"),
    ("wnba", "wnba"),
    ("nba", "nba"),
    ("nfl", "nfl"),
    ("mlb", "mlb"),
    ("nhl", "nhl"),
    ("mls", "mls"),
    ("epl", "epl"),
    ("ufc", "ufc"),
    ("pga", "pga"),
    ("baseball", "mlb"),
    ("hockey", "nhl"),
    ("soccer", "mls"),
]


def _extract_sport_from_title(title: str) -> str | None:
    low = title.lower()
    for keyword, sport in _SPORT_FROM_TITLE:
        if keyword in low:
            return sport
    return None


_SPORT_SLUG_PREFIXES = frozenset({"aec", "atc", "tec"})


def _extract_sport_from_slug(slug: str) -> str | None:
    parts = slug.split("-")
    if len(parts) >= 2 and parts[0] in _SPORT_SLUG_PREFIXES:
        code = parts[1].lower()
        normalize = {"ncaaf": "cfb", "ncaab": "cbb"}
        return normalize.get(code, code)
    return None


def group_kalshi_events(
    events: list[dict],
    series_map: dict[str, dict[str, str]],
) -> list[KalshiEvent]:
    result: list[KalshiEvent] = []
    for ev in events:
        series = ev.get("series_ticker", "")
        series_info = series_map.get(series, {})
        category = series_info.get("category", "")
        markets = ev.get("markets", [])
        result.append(KalshiEvent(
            event_ticker=ev["event_ticker"],
            series_ticker=series,
            title=ev.get("title", ev["event_ticker"]),
            strike_date=ev.get("strike_date"),
            category=category,
            market_count=len(markets) if markets else 0,
            sport=_extract_sport_from_title(series_info.get("title", "")),
        ))
    return result


def _is_moneyline(sport_type: str | None) -> bool:
    if not sport_type:
        return False
    return "MONEYLINE" in sport_type.upper()


def _slug_game_key(slug: str) -> str | None:
    m = _DATE_ISO.search(slug)
    if m:
        return slug[:m.end()]
    return None


def group_poly_markets(markets: list[dict]) -> list[PolyGame]:
    games: dict[str, list[dict]] = {}
    standalone: list[dict] = []

    for m in markets:
        gid = m.get("gameId") or m.get("game_id")
        if not gid:
            gid = _slug_game_key(m.get("slug", ""))
        if gid:
            games.setdefault(gid, []).append(m)
        else:
            standalone.append(m)

    result: list[PolyGame] = []

    for gid, group in games.items():
        moneylines = [m for m in group if _is_moneyline(m.get("sportsMarketTypeV2"))]
        rep = moneylines[0] if moneylines else group[0]
        rep_slug = rep.get("slug", "")
        result.append(PolyGame(
            game_id=gid,
            slug=rep_slug,
            question=rep.get("question", rep.get("title", "")),
            category=rep.get("category", ""),
            sport_type=rep.get("sportsMarketTypeV2"),
            slugs=tuple(m.get("slug", "") for m in group),
            sport=_extract_sport_from_slug(rep_slug),
        ))

    for m in standalone:
        slug = m.get("slug", "")
        result.append(PolyGame(
            game_id=None,
            slug=slug,
            question=m.get("question", m.get("title", "")),
            category=m.get("category", ""),
            sport_type=m.get("sportsMarketTypeV2"),
            slugs=(slug,),
            sport=_extract_sport_from_slug(slug),
        ))

    return result


# ---- Pre-filters ----

_CATEGORY_MAP: dict[str, set[str]] = {
    "sports": {"sports", "sport"},
    "politics": {"politics", "political", "elections", "world"},
    "economics": {
        "economics", "economy", "finance", "financial",
        "financials", "commodities",
    },
    "crypto": {"crypto", "cryptocurrency", "digital assets"},
    "weather": {"weather", "climate", "climate and weather"},
    "culture": {"culture", "entertainment", "pop culture", "social", "mentions"},
    "tech": {"tech", "technology", "science", "science and technology"},
    "companies": {"companies"},
    "health": {"health"},
    "transportation": {"transportation"},
    "education": {"education"},
}


def _normalize_category(cat: str) -> str:
    low = cat.strip().lower()
    for canonical, aliases in _CATEGORY_MAP.items():
        if low in aliases or low == canonical:
            return canonical
    return low


def categories_compatible(kalshi_cat: str, poly_cat: str) -> bool:
    if not kalshi_cat or not poly_cat:
        return True
    return _normalize_category(kalshi_cat) == _normalize_category(poly_cat)


def sport_types_compatible(k_sport: str | None, p_sport: str | None) -> bool:
    if k_sport is None or p_sport is None:
        return True
    return k_sport == p_sport


_KALSHI_BET_TYPES: list[tuple[str, str]] = [
    ("EXACTMATCH", "prop"),
    ("GAME", "moneyline"),
    ("MATCH", "moneyline"),
    ("TOTAL", "total"),
    ("SPREAD", "spread"),
]


def _extract_kalshi_bet_type(series_ticker: str) -> str | None:
    upper = series_ticker.upper()
    for suffix, bet_type in _KALSHI_BET_TYPES:
        if upper.endswith(suffix):
            return bet_type
    return None


_POLY_BET_TYPE_MAP: dict[str, str] = {
    "SPORTS_MARKET_TYPE_MONEYLINE": "moneyline",
    "SPORTS_MARKET_TYPE_DRAWABLE_OUTCOME": "moneyline",
    "SPORTS_MARKET_TYPE_TOTAL": "total",
    "SPORTS_MARKET_TYPE_SPREAD": "spread",
}


def _extract_poly_bet_type(sport_type: str | None) -> str | None:
    if not sport_type:
        return None
    return _POLY_BET_TYPE_MAP.get(sport_type)


def bet_types_compatible(
    kalshi_series_ticker: str, poly_sport_type: str | None,
) -> bool:
    k_type = _extract_kalshi_bet_type(kalshi_series_ticker)
    p_type = _extract_poly_bet_type(poly_sport_type)
    if k_type is None or p_type is None:
        if p_type == "moneyline" and k_type is None:
            return False
        return True
    return k_type == p_type


def _extract_date(text: str) -> date | None:
    m = _DATE_ISO.search(text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


def _extract_date_from_ticker(ticker: str) -> date | None:
    m = _TICKER_DATE.search(ticker)
    if m:
        try:
            year = 2000 + int(m.group(1))
            month = _MONTH_ABBR[m.group(2).upper()]
            day = int(m.group(3))
            return date(year, month, day)
        except (ValueError, KeyError):
            return None
    return None


def dates_overlap(
    strike_date: str | None,
    poly_game: PolyGame,
    *,
    is_sports: bool = False,
    kalshi_event_ticker: str = "",
) -> bool:
    kalshi_date = _extract_date(strike_date) if strike_date else None
    if kalshi_date is None and kalshi_event_ticker:
        kalshi_date = _extract_date_from_ticker(kalshi_event_ticker)
    poly_date = _extract_date(poly_game.slug)
    if poly_date is None:
        poly_date = _extract_date(poly_game.question)
    if kalshi_date is not None and poly_date is not None:
        return kalshi_date == poly_date
    if is_sports and (kalshi_date is not None or poly_date is not None):
        return False
    return True


# ---- Pipeline ----

def find_candidates(
    kalshi_events: list[KalshiEvent],
    poly_games: list[PolyGame],
    threshold: float = 0.3,
) -> list[EventCandidate]:
    poly_normalized = [
        (pg, normalize_title(pg.question)) for pg in poly_games
    ]

    candidates: list[EventCandidate] = []
    for ke in kalshi_events:
        k_tokens = normalize_title(ke.title)
        for pg, p_tokens in poly_normalized:
            if not categories_compatible(ke.category, pg.category):
                continue
            if not sport_types_compatible(ke.sport, pg.sport):
                continue
            if not bet_types_compatible(ke.series_ticker, pg.sport_type):
                continue
            is_sports = (
                _normalize_category(ke.category) == "sports"
                or _normalize_category(pg.category) == "sports"
            )
            if not dates_overlap(
                ke.strike_date, pg,
                is_sports=is_sports,
                kalshi_event_ticker=ke.event_ticker,
            ):
                continue
            score = jaccard_score(k_tokens, p_tokens)
            if score >= threshold:
                candidates.append(EventCandidate(
                    kalshi_event=ke,
                    poly_game=pg,
                    score=score,
                ))

    candidates.sort(key=lambda c: c.score, reverse=True)

    seen_poly: set[str] = set()
    deduped: list[EventCandidate] = []
    for c in candidates:
        if c.poly_game.slug not in seen_poly:
            seen_poly.add(c.poly_game.slug)
            deduped.append(c)
    return deduped


# ---- CLI ----

def _load_known_slugs() -> set[str]:
    known: set[str] = set()
    if _MATCHES_PATH.exists():
        for m in json.loads(_MATCHES_PATH.read_text()):
            known.add(m.get("polymarket_slug", ""))
    if _REJECTED_PATH.exists():
        for r in json.loads(_REJECTED_PATH.read_text()):
            ps = r.get("polymarket_slug", "")
            if ps:
                known.add(ps)
    return known


async def _run(threshold: float = 0.3) -> None:
    kalshi = KalshiAdapter(
        api_key_id=require_env("KALSHI_API_KEY_ID"),
        private_key_path=Path(require_env("KALSHI_PRIVATE_KEY_PATH")),
    )
    poly = PolyAdapter(
        api_key_id=require_env("POLYMARKET_US_API_KEY_ID"),
        private_key=require_env("POLYMARKET_US_PRIVATE_KEY"),
    )

    try:
        print("Fetching Kalshi series...", end=" ", flush=True)
        raw_series = await kalshi.fetch_series()
        series_map: dict[str, dict[str, str]] = {}
        for s in raw_series:
            series_map[s["ticker"]] = {
                "category": s.get("category", ""),
                "title": s.get("title", ""),
            }
        print(f"{len(series_map)} series")

        print("Fetching Kalshi events...", end=" ", flush=True)
        raw_events = await kalshi.fetch_events()
        print(f"{len(raw_events)} events")

        today = date.today().isoformat() + "T00:00:00Z"
        print("Fetching Polymarket US markets...", end=" ", flush=True)
        raw_poly = await poly.fetch_markets(end_date_min=today)
        print(f"{len(raw_poly)} markets")

        kalshi_events = group_kalshi_events(raw_events, series_map)
        poly_games = group_poly_markets(raw_poly)
        print(
            f"Grouped: {len(kalshi_events)} Kalshi events, "
            f"{len(poly_games)} Polymarket games/markets"
        )

        print(f"Matching (threshold {threshold:.2f})...", end=" ", flush=True)
        all_candidates = find_candidates(kalshi_events, poly_games, threshold)
        print(f"{len(all_candidates)} candidates")

        known_slugs = _load_known_slugs()
        new = [
            c for c in all_candidates
            if not any(s in known_slugs for s in c.poly_game.slugs)
        ]

        if not new:
            print(
                f"No new candidates. {len(all_candidates)} total scored,"
                " all already known."
            )
            return

        print(f"Fetching Kalshi markets for {len(new)} candidates...")
        results = []
        for c in new:
            markets = await kalshi.fetch_event_markets(
                c.kalshi_event.event_ticker,
            )
            results.append({
                "score": round(c.score, 4),
                "kalshi_event": {
                    "event_ticker": c.kalshi_event.event_ticker,
                    "series_ticker": c.kalshi_event.series_ticker,
                    "title": c.kalshi_event.title,
                    "category": c.kalshi_event.category,
                    "strike_date": c.kalshi_event.strike_date,
                },
                "kalshi_markets": [
                    {
                        "ticker": m["ticker"],
                        "title": m.get(
                            "yes_sub_title", m.get("title", m["ticker"]),
                        ),
                    }
                    for m in markets
                ],
                "polymarket": {
                    "slug": c.poly_game.slug,
                    "question": c.poly_game.question,
                    "category": c.poly_game.category,
                    "sport_type": c.poly_game.sport_type,
                    "game_id": c.poly_game.game_id,
                },
            })

        _CANDIDATES_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CANDIDATES_PATH.write_text(json.dumps(results, indent=2))
        print(f"Wrote {len(results)} candidates to {_CANDIDATES_PATH}")

    finally:
        await kalshi.close()
        await poly.close()


def main() -> None:
    load_dotenv()
    asyncio.run(_run())


if __name__ == "__main__":
    main()
