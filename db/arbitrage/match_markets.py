from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from db.shared.auth import require_env
from db.arbitrage.fetch_poly_sides import fetch_sides
from db.arbitrage.kalshi_adapter import KalshiAdapter
from db.arbitrage.poly_adapter import PolyAdapter

_ET = ZoneInfo("America/New_York")

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

_CANDIDATES_PATH = Path("db/arbitrage/candidates.json")
_MATCHES_PATH = Path("db/arbitrage/matches.json")
_REJECTED_PATH = Path("db/arbitrage/rejected_matches.json")
_ARCHIVE_PATH = Path("db/arbitrage/matches_archive.json")


# ---- Data types ----

@dataclass(frozen=True)
class KalshiEvent:
    event_ticker: str
    series_ticker: str
    title: str
    strike_date: str | None
    category: str
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
    line: str | None = None
    game_start_time: str | None = None


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
]


def _extract_sport_from_title(title: str) -> str | None:
    low = title.lower()
    for keyword, sport in _SPORT_FROM_TITLE:
        if keyword in low:
            return sport
    return None


# Kalshi series tickers embed the sport (KXMLBSPREAD, KXCS2MAP); used when
# the series title has no sport keyword. Without this, esports and several
# league events carried sport=None and the fail-open sport gate let
# cross-sport candidates through (CS2 vs Valorant/Dota 2, MLB vs MLS —
# observed wrong matches 2026-07-22). Ordered: WNBA before NBA.
_SPORT_FROM_TICKER: list[tuple[str, str]] = [
    ("WNBA", "wnba"),
    ("NCAAF", "cfb"),
    ("NCAAB", "cbb"),
    ("NBA", "nba"),
    ("NFL", "nfl"),
    ("MLB", "mlb"),
    ("NHL", "nhl"),
    ("MLS", "mls"),
    ("EPL", "epl"),
    ("UFC", "ufc"),
    ("PGA", "pga"),
    ("ATP", "atp"),
    ("WTA", "wta"),
    ("CS2", "cs2"),
    ("VALORANT", "valorant"),
    ("DOTA", "dota2"),
    ("LOL", "lol"),
]


def _extract_sport_from_ticker(series_ticker: str) -> str | None:
    upper = series_ticker.upper()
    for token, sport in _SPORT_FROM_TICKER:
        if token in upper:
            return sport
    return None


_SPORT_SLUG_PREFIXES = frozenset({
    "aec", "arankc", "asc", "astatc", "atc", "tec", "tsc",
})


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
        result.append(KalshiEvent(
            event_ticker=ev["event_ticker"],
            series_ticker=series,
            title=ev.get("title", ev["event_ticker"]),
            strike_date=ev.get("strike_date"),
            category=category,
            sport=(
                _extract_sport_from_title(series_info.get("title", ""))
                or _extract_sport_from_ticker(series)
            ),
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
        # Markets with a line (spreads, totals) match individually — grouping
        # them by game would collapse distinct lines into one candidate.
        if m.get("line") is not None:
            standalone.append(m)
            continue
        gid = m.get("gameId") or m.get("game_id")
        if not gid:
            gid = _slug_game_key(m.get("slug", ""))
        if gid:
            games.setdefault(gid, []).append(m)
        else:
            standalone.append(m)

    result: list[PolyGame] = []

    for gid, group in games.items():
        # In live data groups are single-type (gameId is null and each market
        # type has its own slug prefix), so this preference is a safety net
        # for the case where a shared gameId ever bundles types together.
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
            line=rep.get("line"),
            game_start_time=rep.get("gameStartTime"),
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
            line=m.get("line"),
            game_start_time=m.get("gameStartTime"),
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


# Series-ticker suffix -> bet type. Checked in order, so compound suffixes
# (F5SPREAD, GSPREAD) must come before their generic tails (SPREAD).
_KALSHI_BET_TYPES: list[tuple[str, str]] = [
    ("F5SPREAD", "f5_spread"),
    ("F5TOTAL", "f5_total"),
    ("F5", "f5_moneyline"),
    ("GSPREAD", "game_spread"),
    ("GTOTAL", "game_total"),
    ("SETWINNER", "set_winner"),
    ("EXACTMATCH", "exact_score"),
    ("SCORE", "exact_score"),
    ("EXTRAS", "extras"),
    ("HRR", "player_hrr"),
    ("TB", "player_tb"),
    ("FTTS", "ftts"),
    ("MAP", "map_winner"),
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


# Poly slugs mark the bet variant after the event date: -f5- (first 5
# innings), -fh-/-sh- (half), -gs-/-ss- (tennis games/sets spread),
# -tg-/-st- (tennis games/sets total), -hrr-/-tb- (player props),
# -mapN/-gameN (esports map winners), -btts. Only tokens after the date
# count: team codes before it collide (e.g. Tampa Bay = tb).
_SLUG_TAIL = re.compile(r"\d{4}-\d{2}-\d{2}-(.+)$")


def _slug_tail_tokens(slug: str) -> set[str]:
    m = _SLUG_TAIL.search(slug.lower())
    return set(m.group(1).split("-")) if m else set()


def _extract_poly_bet_type(sport_type: str | None, slug: str) -> str | None:
    tail = _slug_tail_tokens(slug)
    if sport_type in (
        "SPORTS_MARKET_TYPE_MONEYLINE", "SPORTS_MARKET_TYPE_DRAWABLE_OUTCOME",
    ):
        return "moneyline"
    if sport_type == "SPORTS_MARKET_TYPE_SPREAD":
        if "gs" in tail:
            return "game_spread"
        if "ss" in tail:
            return "set_spread"
        if "fh" in tail or "sh" in tail:
            return "half_spread"
        if "f5" in tail:
            return "f5_spread"
        return "spread"
    if sport_type == "SPORTS_MARKET_TYPE_TOTAL":
        if "tg" in tail:
            return "game_total"
        if "st" in tail:
            return "set_total"
        if "fh" in tail or "sh" in tail:
            return "half_total"
        if "f5" in tail:
            return "f5_total"
        return "total"
    if sport_type == "SPORTS_MARKET_TYPE_PROP":
        if "hrr" in tail:
            return "player_hrr"
        if "f5" in tail:
            return "f5_moneyline"
        if "tb" in tail:
            return "player_tb"
        if any(t.startswith(("map", "game")) for t in tail):
            return "map_winner"
        if "btts" in tail:
            return "btts"
        return None
    return None


def bet_types_compatible(
    kalshi_series_ticker: str,
    poly_sport_type: str | None,
    poly_slug: str = "",
) -> bool:
    # Strict: both sides must classify, and to the same type. An
    # unclassified side means we cannot verify the bets are the same
    # contract, which is exactly how correct-score events ended up matched
    # to spreads (observed 2026-07-21).
    k_type = _extract_kalshi_bet_type(kalshi_series_ticker)
    p_type = _extract_poly_bet_type(poly_sport_type, poly_slug)
    return k_type is not None and p_type is not None and k_type == p_type


# Player-prop questions name only the player, so title tokens cannot
# distinguish games. Both sides carry team codes for MLB props (Kalshi
# ticker tail e.g. -26JUL211940SFKC, Poly slug astatc-mlb-nym-mil-...),
# so require them to agree. Applied to player_hrr / player_tb only:
# other sports' codes do not align across platforms.
_TICKER_TEAMS = re.compile(r"-\d{2}[A-Z]{3}\d{2}\d*([A-Z]+?)(?:G\d)?$")

_PLAYER_PROP_TYPES = frozenset({"player_hrr", "player_tb"})


def player_prop_teams_match(kalshi_event_ticker: str, poly_slug: str) -> bool:
    m = _TICKER_TEAMS.search(kalshi_event_ticker.upper())
    parts = poly_slug.split("-")
    if not m or len(parts) < 4:
        # Fail closed: this gate is the only wrong-game defense for props
        # (questions name just the player), so a ticker-format drift must
        # surface as missing candidates, not as unverified ones.
        return False
    return m.group(1) == (parts[2] + parts[3]).upper()


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


def _kalshi_date(ke: KalshiEvent) -> date | None:
    d = _extract_date(ke.strike_date) if ke.strike_date else None
    if d is None:
        d = _extract_date_from_ticker(ke.event_ticker)
    return d


def _poly_date(pg: PolyGame) -> date | None:
    return _extract_date(pg.slug) or _extract_date(pg.question)


def _dates_compatible(
    k_date: date | None, p_date: date | None, *, is_sports: bool,
) -> bool:
    if k_date is not None and p_date is not None:
        return k_date == p_date
    if is_sports and (k_date is not None or p_date is not None):
        return False
    return True


# ---- Pipeline ----

def _is_sports_category(cat: str) -> bool:
    return _normalize_category(cat) == "sports"


def find_candidates(
    kalshi_events: list[KalshiEvent],
    poly_games: list[PolyGame],
    threshold: float = 0.3,
) -> list[EventCandidate]:
    # Project scope is sports only. The Kalshi side must be categorized
    # Sports; Poly markets with a blank category are kept and resolved by the
    # category gate against the Kalshi side.
    kalshi_events = [
        ke for ke in kalshi_events if _is_sports_category(ke.category)
    ]
    poly_games = [
        pg for pg in poly_games
        if not pg.category or _is_sports_category(pg.category)
    ]

    # Block on event date: a pair whose dates are both known but different can
    # never pass the date gate, so each Kalshi event only scores against Poly
    # games on the same date (plus undated ones).
    _PolyEntry = tuple[PolyGame, set[str], date | None]
    dated_poly: dict[date, list[_PolyEntry]] = {}
    undated_poly: list[_PolyEntry] = []
    for pg in poly_games:
        p_date = _poly_date(pg)
        entry = (pg, normalize_title(pg.question), p_date)
        if p_date is None:
            undated_poly.append(entry)
        else:
            dated_poly.setdefault(p_date, []).append(entry)
    all_poly = [e for grp in dated_poly.values() for e in grp] + undated_poly

    candidates: list[EventCandidate] = []
    for ke in kalshi_events:
        k_tokens = normalize_title(ke.title)
        k_date = _kalshi_date(ke)
        pool = (
            dated_poly.get(k_date, []) + undated_poly
            if k_date is not None else all_poly
        )
        for pg, p_tokens, p_date in pool:
            if not categories_compatible(ke.category, pg.category):
                continue
            if not sport_types_compatible(ke.sport, pg.sport):
                continue
            if not bet_types_compatible(ke.series_ticker, pg.sport_type, pg.slug):
                continue
            if (
                _extract_kalshi_bet_type(ke.series_ticker) in _PLAYER_PROP_TYPES
                and not player_prop_teams_match(ke.event_ticker, pg.slug)
            ):
                continue
            if not _dates_compatible(k_date, p_date, is_sports=True):
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


# ---- Match file maintenance ----

def ensure_match_files(
    paths: tuple[Path, ...] = (_MATCHES_PATH, _REJECTED_PATH),
) -> None:
    for path in paths:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("[]")


def match_is_live(m: dict, now: datetime) -> bool:
    """Whether a match's event is still ahead of us.

    Prefers Kalshi's expected_expiration_time ("expires"), which is a real
    timestamp for the underlying event. event_date is only a label parsed
    from the Poly slug, and for events that run past their labelled ET date
    (observed on tennis, 2026-07-22) it prunes a market that is still
    trading. It stays as the fallback for entries written before "expires".
    """
    expires = m.get("expires")
    if expires:
        dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            # Kalshi timestamps are UTC; a naive value must not crash the
            # aware comparison (and with it collector startup).
            dt = dt.replace(tzinfo=timezone.utc)
        return dt >= now
    if not m.get("event_date"):
        return True
    # event_date labels are ET on both platforms, so compare in ET.
    return date.fromisoformat(m["event_date"]) >= now.astimezone(_ET).date()


def prune_expired_matches(
    now: datetime,
    path: Path = _MATCHES_PATH,
    archive_path: Path = _ARCHIVE_PATH,
) -> int:
    """Move expired matches to the archive instead of deleting them.

    Deleting destroyed the direction metadata, which silently excluded the
    pruned matches' snapshots from the analysis freeze (observed 2026-07-22:
    74% of captured rows orphaned). prepare_arb_analysis reads the archive.
    """
    matches = json.loads(path.read_text())
    kept = [m for m in matches if match_is_live(m, now)]
    expired = [m for m in matches if not match_is_live(m, now)]
    if expired:
        archived = (
            json.loads(archive_path.read_text())
            if archive_path.exists() else []
        )
        archive_path.write_text(json.dumps(archived + expired, indent=2))
        path.write_text(json.dumps(kept, indent=2))
    return len(expired)


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
    ensure_match_files()
    pruned = prune_expired_matches(datetime.now(timezone.utc))
    if pruned:
        print(f"Pruned {pruned} expired matches")

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

        # The Poly market detail carries the settlement description and the
        # YES side (marketSides long:true) — the verification evidence the
        # /matcher review reads. The YES side is fetched mechanically, never
        # inferred (see docs/market-matching.md, Direction).
        print(f"Fetching Poly details for {len(new)} candidates...")
        slugs = list({c.poly_game.slug for c in new})
        sides = {s["slug"]: s for s in await fetch_sides(slugs)}

        print(f"Fetching Kalshi markets for {len(new)} candidates...")
        results = []
        for c in new:
            markets = await kalshi.fetch_event_markets(
                c.kalshi_event.event_ticker,
            )
            side = sides.get(c.poly_game.slug, {})
            poly = {
                "slug": c.poly_game.slug,
                "question": c.poly_game.question,
                "description": side.get("description"),
                "yes_side": side.get("yes_side"),
                "category": c.poly_game.category,
                "sport_type": c.poly_game.sport_type,
                "game_id": c.poly_game.game_id,
                "line": c.poly_game.line,
                "game_start_time": c.poly_game.game_start_time,
            }
            if side.get("error"):
                poly["yes_side_error"] = side["error"]
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
                        "rules": m.get("rules_primary"),
                        "expires": m.get("expected_expiration_time"),
                    }
                    for m in markets
                ],
                "polymarket": poly,
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
