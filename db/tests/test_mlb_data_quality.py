"""Reasonability checks for the MLB tables in db/pma.db after
pull_mlb_stats.py and build_kalshi_mlb_map.py runs.

Run with: uv run pytest db/tests/
"""

from pathlib import Path

import duckdb
import pytest

DB_PATH = Path(__file__).parent.parent / "pma.db"


@pytest.fixture(scope="module")
def con():
    if not DB_PATH.exists():
        pytest.skip(f"{DB_PATH} does not exist, run the pull scripts first")
    connection = duckdb.connect(str(DB_PATH), read_only=True)
    names = {
        r[0]
        for r in connection.sql("SELECT table_name FROM duckdb_tables()").fetchall()
    }
    if "mlb_games" not in names:
        pytest.skip("mlb tables missing, run db/scripts/pull_mlb_stats.py first")
    yield connection
    connection.close()


def one(con, query):
    return con.sql(query).fetchone()[0]


# schema


def test_tables_and_views_exist(con):
    names = {r[0] for r in con.sql("SELECT table_name FROM duckdb_tables()").fetchall()}
    assert {
        "mlb_games",
        "mlb_plays",
        "mlb_win_probability",
        "mlb_weather",
        "kalshi_mlb_map",
    } <= names
    views = {r[0] for r in con.sql("SELECT view_name FROM duckdb_views()").fetchall()}
    assert {"mlb_games_typed", "mlb_plays_typed", "mlb_win_probability_typed"} <= views


def test_tables_not_empty(con):
    assert one(con, "SELECT count(*) FROM mlb_games") > 3000
    assert one(con, "SELECT count(*) FROM mlb_plays") > 100_000
    assert one(con, "SELECT count(*) FROM mlb_win_probability") > 100_000
    assert one(con, "SELECT count(*) FROM kalshi_mlb_map") > 3000


# typed views cast cleanly


def test_all_casts_succeed(con):
    checks = {
        "mlb_games": {"game_date": "TIMESTAMP", "official_date": "DATE"},
        "mlb_plays": {"start_time": "TIMESTAMP", "end_time": "TIMESTAMP"},
        "mlb_win_probability": {"play_end_time": "TIMESTAMP"},
    }
    for table, columns in checks.items():
        for col, target_type in columns.items():
            bad = one(
                con,
                f"SELECT count(*) FROM {table} WHERE {col} IS NOT NULL "
                f"AND TRY_CAST({col} AS {target_type}) IS NULL",
            )
            assert bad == 0, f"{table}.{col} has values that fail casting"


# games


def test_final_games_have_scores_and_winner(con):
    assert one(
        con,
        """
        SELECT count(*) FROM mlb_games
        WHERE coded_game_state = 'F'
          AND (away_score IS NULL OR home_score IS NULL
               OR away_is_winner IS NULL OR home_is_winner IS NULL)
        """,
    ) == 0


def test_exactly_one_winner(con):
    assert one(
        con,
        """
        SELECT count(*) FROM mlb_games
        WHERE coded_game_state = 'F' AND away_is_winner = home_is_winner
        """,
    ) == 0


def test_teams_are_the_30_mlb_teams(con):
    assert one(
        con,
        """
        SELECT count(DISTINCT team_id) FROM (
            SELECT away_team_id AS team_id FROM mlb_games
            UNION ALL SELECT home_team_id FROM mlb_games
        )
        """,
    ) == 30


# per-game data


def test_final_games_have_plays(con):
    missing = one(
        con,
        """
        SELECT count(*) FROM mlb_games g
        LEFT JOIN (SELECT DISTINCT game_pk FROM mlb_plays) p USING (game_pk)
        WHERE g.coded_game_state = 'F' AND p.game_pk IS NULL
        """,
    )
    assert missing == 0


def test_play_timestamps_near_scheduled_start(con):
    # a suspended game's plays legitimately span two days (started, rained
    # out, resumed), so the window is wide — this only catches garbage
    assert one(
        con,
        """
        SELECT count(*) FROM mlb_plays_typed p
        JOIN mlb_games_typed g USING (game_pk)
        WHERE p.start_time IS NOT NULL
          AND abs(date_diff('hour', g.game_date, p.start_time)) > 48
        """,
    ) == 0


def test_win_probabilities_in_range(con):
    assert one(
        con,
        """
        SELECT count(*) FROM mlb_win_probability
        WHERE home_wp < 0 OR home_wp > 100 OR away_wp < 0 OR away_wp > 100
           OR abs(home_wp + away_wp - 100) > 0.01
        """,
    ) == 0


# kalshi <-> mlb map


def test_map_events_are_unique(con):
    assert one(con, "SELECT count(*) FROM kalshi_mlb_map") == one(
        con, "SELECT count(DISTINCT event_ticker) FROM kalshi_mlb_map"
    )


def test_map_match_rate(con):
    # >= 99% of game events map to a game; the rest are cancelled games
    total = one(
        con,
        """
        SELECT count(DISTINCT event_ticker) FROM markets
        WHERE event_ticker LIKE 'KXMLBGAME-%'
          AND regexp_extract(ticker, '-([A-Z]+)$', 1)
              NOT IN ('ALHS', 'ALLS', 'NLHS', 'NLLS')
        """,
    )
    mapped = one(con, "SELECT count(*) FROM kalshi_mlb_map")
    assert mapped / total >= 0.99


def test_map_points_to_existing_games(con):
    assert one(
        con,
        """
        SELECT count(*) FROM kalshi_mlb_map map
        LEFT JOIN mlb_games g USING (game_pk)
        WHERE g.game_pk IS NULL
        """,
    ) == 0


def test_finalized_results_agree_with_schedule_winner(con):
    # a finalized yes/no market must name the team the schedule says won
    assert one(
        con,
        """
        SELECT count(*) FROM markets m
        JOIN kalshi_mlb_map map USING (event_ticker)
        JOIN mlb_games g USING (game_pk)
        WHERE m.status = 'finalized' AND m.result IN ('yes', 'no')
          AND g.away_is_winner IS NOT NULL AND g.home_is_winner IS NOT NULL
          AND (m.result = 'yes') != (
              CASE regexp_extract(m.ticker, '-([A-Z]+)$', 1)
                   WHEN map.away_abbr THEN map.away_team_id
                   ELSE map.home_team_id
              END = CASE WHEN g.away_is_winner
                         THEN g.away_team_id ELSE g.home_team_id END)
        """,
    ) == 0


def test_no_scalar_market_is_mapped(con):
    # cancelled games settle scalar and must never be matched to a game
    assert one(
        con,
        """
        SELECT count(*) FROM markets m
        JOIN kalshi_mlb_map map USING (event_ticker)
        WHERE m.result = 'scalar'
        """,
    ) == 0
