"""Mirror MLB Stats API data into db/pma.db.

Pulls the schedule (2025-04-16 -> today) into mlb_games, then per-game
play-by-play, win probability, and weather for every finalized game.
Companion to pull_kalshi_mlb.py; join logic lives in build_kalshi_mlb_map.py.
"""

import asyncio
import json
from datetime import date, timedelta

import duckdb
import httpx
import polars as pl
from pydantic import BaseModel, Field
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

BASE_URL = "https://statsapi.mlb.com/api/v1"
TIMEOUTS = httpx.Timeout(connect=2.0, read=10.0, write=5.0, pool=5.0)
SCHEDULE_START = date(2025, 4, 16)  # first day of Kalshi MLB data
# regular season, wild card, division, league championship, world series;
# excludes spring training (S), exhibition (E), all-star (A)
GAME_TYPES = {"R", "F", "D", "L", "W"}
GAME_CONCURRENCY = 5


class Team(BaseModel):
    id: int
    name: str


class ScheduleTeamSide(BaseModel):
    team: Team
    score: int | None = None
    is_winner: bool | None = Field(default=None, alias="isWinner")


class ScheduleTeams(BaseModel):
    away: ScheduleTeamSide
    home: ScheduleTeamSide


class GameStatus(BaseModel):
    coded_game_state: str = Field(alias="codedGameState")
    detailed_state: str = Field(alias="detailedState")


class Venue(BaseModel):
    id: int | None = None
    name: str | None = None


class ScheduleGame(BaseModel):
    game_pk: int = Field(alias="gamePk")
    game_type: str = Field(alias="gameType")
    game_date: str = Field(alias="gameDate")
    official_date: str = Field(alias="officialDate")
    status: GameStatus
    teams: ScheduleTeams
    venue: Venue
    double_header: str = Field(alias="doubleHeader")
    game_number: int = Field(alias="gameNumber")
    day_night: str | None = Field(default=None, alias="dayNight")


class ScheduleDate(BaseModel):
    date: str
    games: list[ScheduleGame]


class ScheduleResponse(BaseModel):
    dates: list[ScheduleDate]


class PlayAbout(BaseModel):
    at_bat_index: int = Field(alias="atBatIndex")
    half_inning: str = Field(alias="halfInning")
    inning: int
    start_time: str | None = Field(default=None, alias="startTime")
    end_time: str | None = Field(default=None, alias="endTime")
    is_scoring_play: bool | None = Field(default=None, alias="isScoringPlay")


class PlayResult(BaseModel):
    event: str | None = None
    away_score: int | None = Field(default=None, alias="awayScore")
    home_score: int | None = Field(default=None, alias="homeScore")


class Play(BaseModel):
    about: PlayAbout
    result: PlayResult


class PlayByPlayResponse(BaseModel):
    all_plays: list[Play] = Field(alias="allPlays")


class WinProbabilityPlay(BaseModel):
    at_bat_index: int = Field(alias="atBatIndex")
    home_wp: float | None = Field(default=None, alias="homeTeamWinProbability")
    away_wp: float | None = Field(default=None, alias="awayTeamWinProbability")
    home_wp_added: float | None = Field(
        default=None, alias="homeTeamWinProbabilityAdded"
    )
    play_end_time: str | None = Field(default=None, alias="playEndTime")


class Weather(BaseModel):
    condition: str | None = None
    temp: str | None = None
    wind: str | None = None


class LiveFeedGameData(BaseModel):
    weather: Weather | None = None


class LiveFeedResponse(BaseModel):
    game_data: LiveFeedGameData | None = Field(default=None, alias="gameData")


# Retry timeouts, 429s, and 5xx. Other 4xx fail immediately.
def is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.ReadTimeout):
        return True
    return isinstance(exc, httpx.HTTPStatusError) and (
        exc.response.status_code == 429 or exc.response.status_code >= 500
    )


@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, max=60),
    retry=retry_if_exception(is_retryable),
    reraise=True,
)
async def fetch(client: httpx.AsyncClient, path: str, params: dict) -> bytes:
    r = await client.get(path, params=params)
    r.raise_for_status()
    return r.content


def month_chunks(start: date, end: date) -> list[tuple[date, date]]:
    """Split [start, end] into calendar-month-sized [from, to] ranges."""
    chunks = []
    chunk_start = start
    while chunk_start <= end:
        if chunk_start.month == 12:
            next_month = date(chunk_start.year + 1, 1, 1)
        else:
            next_month = date(chunk_start.year, chunk_start.month + 1, 1)
        chunk_end = min(next_month - timedelta(days=1), end)
        chunks.append((chunk_start, chunk_end))
        chunk_start = next_month
    return chunks


def init_db(path: str = "db/pma.db") -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(path)
    con.sql("""
        CREATE TABLE IF NOT EXISTS mlb_games (
            game_pk BIGINT PRIMARY KEY,
            game_type TEXT NOT NULL,
            game_date TEXT NOT NULL,
            official_date TEXT NOT NULL,
            coded_game_state TEXT,
            detailed_state TEXT,
            away_team_id INTEGER,
            away_team_name TEXT,
            away_score INTEGER,
            away_is_winner BOOLEAN,
            home_team_id INTEGER,
            home_team_name TEXT,
            home_score INTEGER,
            home_is_winner BOOLEAN,
            venue_id INTEGER,
            venue_name TEXT,
            double_header TEXT,
            game_number INTEGER,
            day_night TEXT
        )
    """)
    con.sql("""
        CREATE TABLE IF NOT EXISTS mlb_plays (
            game_pk BIGINT NOT NULL,
            at_bat_index INTEGER NOT NULL,
            inning INTEGER,
            half_inning TEXT,
            start_time TEXT,
            end_time TEXT,
            event TEXT,
            away_score INTEGER,
            home_score INTEGER,
            is_scoring_play BOOLEAN,
            PRIMARY KEY (game_pk, at_bat_index)
        )
    """)
    con.sql("""
        CREATE TABLE IF NOT EXISTS mlb_win_probability (
            game_pk BIGINT NOT NULL,
            at_bat_index INTEGER NOT NULL,
            home_wp DOUBLE,
            away_wp DOUBLE,
            home_wp_added DOUBLE,
            play_end_time TEXT,
            PRIMARY KEY (game_pk, at_bat_index)
        )
    """)
    con.sql("""
        CREATE TABLE IF NOT EXISTS mlb_weather (
            game_pk BIGINT PRIMARY KEY,
            condition TEXT,
            temp TEXT,
            wind TEXT
        )
    """)
    # resume bookkeeping: a row means per-game data was fully pulled
    con.sql("""
        CREATE TABLE IF NOT EXISTS mlb_game_pulls (
            game_pk BIGINT PRIMARY KEY
        )
    """)
    con.sql("""
        CREATE OR REPLACE VIEW mlb_games_typed AS
        SELECT * REPLACE (CAST(game_date AS TIMESTAMP) AS game_date,
                          CAST(official_date AS DATE) AS official_date)
        FROM mlb_games
    """)
    con.sql("""
        CREATE OR REPLACE VIEW mlb_plays_typed AS
        SELECT * REPLACE (CAST(start_time AS TIMESTAMP) AS start_time,
                          CAST(end_time AS TIMESTAMP) AS end_time)
        FROM mlb_plays
    """)
    con.sql("""
        CREATE OR REPLACE VIEW mlb_win_probability_typed AS
        SELECT * REPLACE (CAST(play_end_time AS TIMESTAMP) AS play_end_time)
        FROM mlb_win_probability
    """)
    return con


def game_row(g: ScheduleGame) -> dict:
    return {
        "game_pk": g.game_pk,
        "game_type": g.game_type,
        "game_date": g.game_date,
        "official_date": g.official_date,
        "coded_game_state": g.status.coded_game_state,
        "detailed_state": g.status.detailed_state,
        "away_team_id": g.teams.away.team.id,
        "away_team_name": g.teams.away.team.name,
        "away_score": g.teams.away.score,
        "away_is_winner": g.teams.away.is_winner,
        "home_team_id": g.teams.home.team.id,
        "home_team_name": g.teams.home.team.name,
        "home_score": g.teams.home.score,
        "home_is_winner": g.teams.home.is_winner,
        "venue_id": g.venue.id,
        "venue_name": g.venue.name,
        "double_header": g.double_header,
        "game_number": g.game_number,
        "day_night": g.day_night,
    }


async def pull_schedule(
    client: httpx.AsyncClient, con: duckdb.DuckDBPyConnection
) -> None:
    games: list[ScheduleGame] = []
    # +10 days so already-listed markets for upcoming games can be mapped
    for chunk_start, chunk_end in month_chunks(
        SCHEDULE_START, date.today() + timedelta(days=10)
    ):
        raw = await fetch(
            client,
            "/schedule",
            {
                "sportId": 1,
                "startDate": chunk_start.isoformat(),
                "endDate": chunk_end.isoformat(),
            },
        )
        response = ScheduleResponse.model_validate_json(raw)
        games.extend(g for d in response.dates for g in d.games)
    games = [g for g in games if g.game_type in GAME_TYPES]
    if not games:
        raise SystemExit("No games returned from /schedule, aborting")
    # dedupe by game_pk (a rescheduled game can appear on two dates)
    games = list({g.game_pk: g for g in games}.values())
    games_df = pl.DataFrame([game_row(g) for g in games])
    con.sql("INSERT OR REPLACE INTO mlb_games BY NAME SELECT * FROM games_df")
    print(f"Saved {len(games)} games to mlb_games")


async def fetch_game_data(
    client: httpx.AsyncClient, game_pk: int
) -> tuple[pl.DataFrame | None, pl.DataFrame | None, pl.DataFrame | None]:
    pbp_raw, wp_raw, live_raw = await asyncio.gather(
        fetch(client, f"/game/{game_pk}/playByPlay", {}),
        fetch(client, f"/game/{game_pk}/winProbability", {}),
        fetch(
            client,
            f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live",
            {"fields": "gameData,weather,condition,temp,wind"},
        ),
    )

    pbp = PlayByPlayResponse.model_validate_json(pbp_raw)
    plays_df = (
        pl.DataFrame(
            [
                {
                    "game_pk": game_pk,
                    "at_bat_index": p.about.at_bat_index,
                    "inning": p.about.inning,
                    "half_inning": p.about.half_inning,
                    "start_time": p.about.start_time,
                    "end_time": p.about.end_time,
                    "event": p.result.event,
                    "away_score": p.result.away_score,
                    "home_score": p.result.home_score,
                    "is_scoring_play": p.about.is_scoring_play,
                }
                for p in pbp.all_plays
            ]
        )
        if pbp.all_plays
        else None
    )

    wp_plays = [WinProbabilityPlay.model_validate(p) for p in json.loads(wp_raw)]
    wp_df = (
        pl.DataFrame(
            [
                {
                    "game_pk": game_pk,
                    "at_bat_index": p.at_bat_index,
                    "home_wp": p.home_wp,
                    "away_wp": p.away_wp,
                    "home_wp_added": p.home_wp_added,
                    "play_end_time": p.play_end_time,
                }
                for p in wp_plays
            ]
        )
        if wp_plays
        else None
    )

    live = LiveFeedResponse.model_validate_json(live_raw)
    weather = live.game_data.weather if live.game_data else None
    weather_df = (
        pl.DataFrame(
            [
                {
                    "game_pk": game_pk,
                    "condition": weather.condition,
                    "temp": weather.temp,
                    "wind": weather.wind,
                }
            ]
        )
        if weather
        else None
    )
    return plays_df, wp_df, weather_df


async def pull_game_data(
    client: httpx.AsyncClient, con: duckdb.DuckDBPyConnection
) -> None:
    already_pulled = {
        pk for (pk,) in con.sql("SELECT game_pk FROM mlb_game_pulls").fetchall()
    }
    todo = [
        pk
        for (pk,) in con.sql(
            "SELECT game_pk FROM mlb_games WHERE coded_game_state = 'F' ORDER BY game_date"
        ).fetchall()
        if pk not in already_pulled
    ]
    print(f"Games to fetch per-game data for: {len(todo)}")

    semaphore = asyncio.Semaphore(GAME_CONCURRENCY)
    done = 0

    async def process(game_pk: int) -> None:
        nonlocal done
        async with semaphore:
            try:
                plays_df, wp_df, weather_df = await fetch_game_data(client, game_pk)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code != 404:
                    raise
                # endpoint missing for this game: record and move on
                print(f"  ! game {game_pk}: 404 on {exc.request.url.path}")
                con.sql(f"INSERT OR REPLACE INTO mlb_game_pulls VALUES ({game_pk})")
                return
        if plays_df is not None:
            con.sql("INSERT OR REPLACE INTO mlb_plays BY NAME SELECT * FROM plays_df")
        if wp_df is not None:
            con.sql(
                "INSERT OR REPLACE INTO mlb_win_probability BY NAME SELECT * FROM wp_df"
            )
        if weather_df is not None:
            con.sql(
                "INSERT OR REPLACE INTO mlb_weather BY NAME SELECT * FROM weather_df"
            )
        con.sql(f"INSERT OR REPLACE INTO mlb_game_pulls VALUES ({game_pk})")
        done += 1
        if done % 100 == 0:
            print(f"  ... {done}/{len(todo)} games")

    await asyncio.gather(*(process(pk) for pk in todo))
    print("Per-game data done")


async def main() -> None:
    con = init_db()
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUTS) as client:
        await pull_schedule(client, con)
        await pull_game_data(client, con)
    con.close()


if __name__ == "__main__":
    asyncio.run(main())
