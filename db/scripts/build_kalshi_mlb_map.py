"""Build kalshi_mlb_map: Kalshi event_ticker <-> MLB gamePk.

Derived data over the two mirrors (pull_kalshi_mlb.py, pull_mlb_stats.py).
Cheap to re-run alone; prints a match report and fails loudly if match
quality drops below threshold.

Ticker conventions (verified empirically, see plans/mlb_data_pull.md).
Two formats:
- 2025: `KXMLBGAME-25SEP24KCLAA` = date + team pair, with an optional
  G1/G2 suffix for doubleheaders (`KXMLBGAME-25APR26BALDETG1`).
- 2026: `KXMLBGAME-26APR301235STLPIT` = date + start time (US/Eastern)
  + team pair; doubleheaders disambiguated by start time.
The team pair is the concatenation of the event's two market ticker
suffixes (e.g. -STL, -PIT), away team first.
"""

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import duckdb

EASTERN = ZoneInfo("America/New_York")

TICKER_RE = re.compile(
    r"^KXMLBGAME-(?P<yy>\d{2})(?P<mon>[A-Z]{3})(?P<dd>\d{2})"
    r"(?P<hhmm>\d{4})?(?P<pair>[A-Z]+?)(?:G?(?P<gamenum>\d))?$"
)

MONTHS = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}

# Kalshi market-ticker suffix -> MLB Stats API team id (wiki/mlb-team-ids.md).
# Arizona appears as both ARI (2025) and AZ (2026).
KALSHI_TO_MLB_TEAM_ID = {
    "LAA": 108, "ARI": 109, "AZ": 109, "BAL": 110, "BOS": 111, "CHC": 112,
    "CIN": 113, "CLE": 114, "COL": 115, "DET": 116, "HOU": 117, "KC": 118,
    "LAD": 119, "WSH": 120, "NYM": 121, "ATH": 133, "PIT": 134, "SD": 135,
    "SEA": 136, "SF": 137, "STL": 138, "TB": 139, "TEX": 140, "TOR": 141,
    "MIN": 142, "PHI": 143, "ATL": 144, "CWS": 145, "MIA": 146, "NYY": 147,
    "MIL": 158,
}

# All-Star events, not games; skipped before matching
NON_GAME_SUFFIXES = {"ALHS", "ALLS", "NLHS", "NLLS"}

# a matched game's scheduled start must be within this window of the
# ticker's start time (generous: covers rescheduled first pitches)
START_TIME_TOLERANCE = timedelta(hours=6)

# settlement fallback for postponed games: the market settles shortly
# after its makeup game ends, at most this long after. The makeup can be
# months later (next visit of the opponent), so the day window is loose —
# the tight SETTLEMENT_WINDOW does the disambiguation.
SETTLEMENT_WINDOW = timedelta(hours=24)
MAKEUP_MAX_DAYS = 200

MIN_MATCH_RATE = 0.99


@dataclass(frozen=True)
class ParsedTicker:
    start_utc: datetime | None  # None for the 2025 format (date only)
    et_date: date
    pair: str
    game_number: int | None  # from the 2025 G1/G2 doubleheader suffix


@dataclass(frozen=True)
class GameRow:
    game_pk: int
    game_date: datetime  # scheduled start, UTC
    official_date: date
    away_team_id: int
    home_team_id: int
    game_number: int = 1  # 1 or 2 within a doubleheader
    actual_end: datetime | None = None  # last play's end_time, from mlb_plays


def parse_event_ticker(event_ticker: str) -> ParsedTicker | None:
    m = TICKER_RE.match(event_ticker)
    if not m:
        return None
    mon = MONTHS.get(m["mon"])
    if mon is None:
        return None
    hhmm = m["hhmm"]
    try:
        if hhmm is not None:
            start_et = datetime(
                2000 + int(m["yy"]), mon, int(m["dd"]),
                int(hhmm[:2]), int(hhmm[2:]), tzinfo=EASTERN,
            )
            start_utc = start_et.astimezone(timezone.utc)
            et_date = start_et.date()
        else:
            start_utc = None
            et_date = date(2000 + int(m["yy"]), mon, int(m["dd"]))
    except ValueError:
        return None
    return ParsedTicker(
        start_utc=start_utc,
        et_date=et_date,
        pair=m["pair"],
        game_number=int(m["gamenum"]) if m["gamenum"] else None,
    )


def split_pair(pair: str, suffixes: set[str]) -> tuple[str, str] | None:
    """Split the ticker's team-pair string using the event's two market
    suffixes. Returns (away, home) — ticker order is away then home."""
    if len(suffixes) != 2:
        return None
    a, b = sorted(suffixes)
    if pair == a + b:
        return (a, b)
    if pair == b + a:
        return (b, a)
    return None


def settled_on(candidates: list[GameRow], settle_time: datetime) -> GameRow | None:
    """The game whose actual end the settlement follows, if unambiguous.
    A market settles shortly after its game ends."""
    ended_before = [
        g
        for g in candidates
        if g.actual_end is not None
        and g.actual_end <= settle_time <= g.actual_end + SETTLEMENT_WINDOW
    ]
    if not ended_before:
        return None
    return max(ended_before, key=lambda g: g.actual_end)


def pick_game(
    candidates: list[GameRow],
    ticker: ParsedTicker,
    settle_time: datetime | None = None,
) -> GameRow | None:
    """Choose the schedule row for this ticker. Candidates already share
    the team pair and date. Doubleheaders are resolved by the G1/G2 game
    number (2025 format), by which game ended just before the market
    settled, or by scheduled-start proximity (2026 format) — in that
    order, because a traditional doubleheader's two scheduled starts can
    be minutes apart, making start proximity meaningless."""
    if ticker.game_number is not None:
        candidates = [g for g in candidates if g.game_number == ticker.game_number]
    if ticker.start_utc is not None:
        candidates = [
            g
            for g in candidates
            if abs(g.game_date - ticker.start_utc) <= START_TIME_TOLERANCE
        ]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    if settle_time is not None:
        by_settlement = settled_on(candidates, settle_time)
        if by_settlement is not None:
            return by_settlement
    if ticker.start_utc is not None:
        return min(candidates, key=lambda g: abs(g.game_date - ticker.start_utc))
    return None




def parse_utc(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


@dataclass(frozen=True)
class EventInfo:
    event_ticker: str
    suffixes: set[str]
    # when the event settled — only for markets that resolved yes/no.
    # Scalar results (cancelled games) must never settlement-match: their
    # settlement follows no game, and the agreement check can't catch a
    # scalar mis-match.
    settle_time: datetime | None
    resolved_scalar: bool


def load_events(con: duckdb.DuckDBPyConnection) -> list[EventInfo]:
    """Game events with their market-ticker suffixes and, for events that
    resolved yes/no, when they settled (used for doubleheader and
    postponed-game disambiguation)."""
    rows = con.sql("""
        SELECT e.event_ticker,
               list(regexp_extract(m.ticker, '-([A-Z]+)$', 1)) AS suffixes,
               max(m.close_time) FILTER (
                   m.status = 'finalized' AND m.result IN ('yes', 'no')
               ) AS settle_time,
               bool_or(m.result = 'scalar') AS resolved_scalar
        FROM events e
        JOIN markets m ON m.event_ticker = e.event_ticker
        WHERE e.series_ticker = 'KXMLBGAME'
        GROUP BY e.event_ticker
    """).fetchall()
    return [
        EventInfo(
            event_ticker=event_ticker,
            suffixes=set(suffixes),
            settle_time=parse_utc(settle_time) if settle_time else None,
            resolved_scalar=bool(resolved_scalar),
        )
        for event_ticker, suffixes, settle_time, resolved_scalar in rows
        if not set(suffixes) & NON_GAME_SUFFIXES
    ]


def load_games(con: duckdb.DuckDBPyConnection) -> list[GameRow]:
    rows = con.sql("""
        SELECT g.game_pk, g.game_date, g.official_date,
               g.away_team_id, g.home_team_id, g.game_number,
               p.actual_end
        FROM mlb_games g
        LEFT JOIN (
            SELECT game_pk, max(end_time) AS actual_end
            FROM mlb_plays GROUP BY game_pk
        ) p USING (game_pk)
    """).fetchall()
    return [
        GameRow(
            game_pk=pk,
            game_date=parse_utc(game_date),
            official_date=date.fromisoformat(official_date),
            away_team_id=away_id,
            home_team_id=home_id,
            game_number=game_number,
            actual_end=parse_utc(actual_end) if actual_end else None,
        )
        for pk, game_date, official_date, away_id, home_id, game_number, actual_end in rows
    ]


def build_map(
    events: list[EventInfo], games: list[GameRow]
) -> tuple[list[dict], list[tuple[str, str]]]:
    """Returns (matched rows, [(event_ticker, unmatched reason)])."""
    by_date_teams: dict[tuple[date, frozenset[int]], list[GameRow]] = {}
    by_teams: dict[frozenset[int], list[GameRow]] = {}
    for g in games:
        teams = frozenset({g.away_team_id, g.home_team_id})
        by_date_teams.setdefault((g.official_date, teams), []).append(g)
        by_teams.setdefault(teams, []).append(g)

    matched: list[dict] = []
    unmatched: list[tuple[str, str]] = []
    for event in events:
        event_ticker = event.event_ticker
        ticker = parse_event_ticker(event_ticker)
        if ticker is None:
            unmatched.append((event_ticker, "unparseable ticker"))
            continue
        pair = split_pair(ticker.pair, event.suffixes)
        if pair is None:
            unmatched.append(
                (
                    event_ticker,
                    f"pair {ticker.pair!r} != suffixes {sorted(event.suffixes)}",
                )
            )
            continue
        away_abbr, home_abbr = pair
        away_id = KALSHI_TO_MLB_TEAM_ID.get(away_abbr)
        home_id = KALSHI_TO_MLB_TEAM_ID.get(home_abbr)
        if away_id is None or home_id is None:
            unmatched.append((event_ticker, f"unknown team abbr in {pair}"))
            continue

        # ET date usually equals the schedule's local officialDate. For
        # timed tickers a start after midnight ET lands on the next ET
        # date, so try ±1 (the start-time tolerance guards mismatches).
        # For date-only tickers there is no such guard: d=0 only, so a
        # postponed game's event stays unmatched instead of latching onto
        # the adjacent day's game.
        offsets = (0, -1, 1) if ticker.start_utc is not None else (0,)
        candidates = []
        for d in offsets:
            key = (
                ticker.et_date + timedelta(days=d),
                frozenset({away_id, home_id}),
            )
            candidates = by_date_teams.get(key, [])
            if candidates:
                break
        game = pick_game(candidates, ticker, event.settle_time)
        match_method = "date"
        if game is None and event.settle_time is not None:
            # postponed game: find the makeup via settlement time
            makeup_candidates = [
                g
                for g in by_teams.get(frozenset({away_id, home_id}), [])
                if ticker.et_date
                <= g.official_date
                <= ticker.et_date + timedelta(days=MAKEUP_MAX_DAYS)
            ]
            game = settled_on(makeup_candidates, event.settle_time)
            match_method = "settlement"
        if game is None:
            if event.resolved_scalar:
                reason = "resolved scalar (cancelled game)"
            elif not candidates:
                reason = "no schedule game on ticker date (postponed?)"
            else:
                reason = "doubleheader ambiguous or start time out of tolerance"
            unmatched.append((event_ticker, reason))
            continue

        matched.append(
            {
                "match_method": match_method,
                "event_ticker": event_ticker,
                "game_pk": game.game_pk,
                "away_abbr": away_abbr,
                "home_abbr": home_abbr,
                "away_team_id": away_id,
                "home_team_id": home_id,
                "ticker_start_utc": ticker.start_utc.isoformat()
                if ticker.start_utc
                else None,
                "orientation_ok": game.away_team_id == away_id
                and game.home_team_id == home_id,
                "start_delta_minutes": abs(
                    game.game_date - ticker.start_utc
                ).total_seconds()
                / 60
                if ticker.start_utc
                else None,
            }
        )
    return matched, unmatched


def report_and_check(
    con: duckdb.DuckDBPyConnection,
    matched: list[dict],
    unmatched: list[tuple[str, str]],
) -> None:
    total = len(matched) + len(unmatched)
    rate = len(matched) / total if total else 0.0
    by_method: dict[str, int] = {}
    for m in matched:
        by_method[m["match_method"]] = by_method.get(m["match_method"], 0) + 1
    print(f"Matched {len(matched)}/{total} game events ({rate:.2%}), {by_method}")
    for event_ticker, reason in sorted(unmatched):
        print(f"  unmatched {event_ticker}: {reason}")

    # usually one event per game; exceptions are duplicate Kalshi listings
    # (seven zombie relistings on 2025-04-18) and postponed events that
    # settled on a makeup game which has its own event
    dupes = con.sql("""
        SELECT game_pk, count(*) FROM kalshi_mlb_map
        GROUP BY game_pk HAVING count(*) > 1
    """).fetchall()
    print(f"Games with more than one event: {len(dupes)}")

    # ticker team order must mean away-then-home for every date match
    # (a rescheduled makeup game may legitimately swap venues)
    flipped = [
        m for m in matched if m["match_method"] == "date" and not m["orientation_ok"]
    ]
    assert not flipped, (
        f"{len(flipped)} events violate the away-then-home convention, "
        f"e.g. {flipped[:3]}"
    )

    assert rate >= MIN_MATCH_RATE, (
        f"match rate {rate:.2%} below {MIN_MATCH_RATE:.0%}"
    )

    # semantic spot check across everything checkable: a finalized market
    # that resolved yes must name the team the schedule says won (compared
    # by team id, not away/home slot, since a makeup game can swap venues)
    agree, disagree = con.sql("""
        WITH checks AS (
            SELECT (m.result = 'yes') = (
                       CASE regexp_extract(m.ticker, '-([A-Z]+)$', 1)
                            WHEN map.away_abbr THEN map.away_team_id
                            ELSE map.home_team_id
                       END = CASE WHEN g.away_is_winner
                                  THEN g.away_team_id ELSE g.home_team_id END
                   ) AS ok
            FROM markets m
            JOIN kalshi_mlb_map map ON m.event_ticker = map.event_ticker
            JOIN mlb_games g ON g.game_pk = map.game_pk
            WHERE m.status = 'finalized' AND m.result IN ('yes', 'no')
              AND g.away_is_winner IS NOT NULL AND g.home_is_winner IS NOT NULL
        )
        SELECT count(*) FILTER (ok), count(*) FILTER (NOT ok) FROM checks
    """).fetchone()
    print(f"Result-vs-winner agreement: {agree} agree, {disagree} disagree")
    assert disagree == 0, f"{disagree} finalized markets disagree with schedule winner"


def main(db_path: str = "db/pma.db") -> None:
    con = duckdb.connect(db_path)
    events = load_events(con)
    games = load_games(con)
    print(f"{len(events)} game events, {len(games)} schedule games")

    matched, unmatched = build_map(events, games)

    con.sql("""
        CREATE OR REPLACE TABLE kalshi_mlb_map (
            event_ticker TEXT PRIMARY KEY,
            game_pk BIGINT NOT NULL,
            away_abbr TEXT NOT NULL,
            home_abbr TEXT NOT NULL,
            away_team_id INTEGER NOT NULL,
            home_team_id INTEGER NOT NULL,
            ticker_start_utc TEXT,
            orientation_ok BOOLEAN NOT NULL,
            start_delta_minutes DOUBLE,
            match_method TEXT NOT NULL
        )
    """)
    if matched:
        import polars as pl

        matched_df = pl.DataFrame(matched)
        con.sql("INSERT INTO kalshi_mlb_map BY NAME SELECT * FROM matched_df")

    report_and_check(con, matched, unmatched)
    con.close()


if __name__ == "__main__":
    main()
