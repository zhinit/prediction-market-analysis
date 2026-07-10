"""Unit tests for the pure functions in build_kalshi_mlb_map.py.

Run with: uv run pytest db/game_winners/
"""

from datetime import date, datetime, timezone

from datetime import timedelta

from build_kalshi_mlb_map import (
    KALSHI_TO_MLB_TEAM_ID,
    GameRow,
    parse_event_ticker,
    pick_game,
    settled_on,
    split_pair,
)

# ticker parsing


def test_parse_known_ticker():
    # verified against the schedule: gamePk 823391, 2026-04-30T16:35Z
    t = parse_event_ticker("KXMLBGAME-26APR301235STLPIT")
    assert t is not None
    assert t.start_utc == datetime(2026, 4, 30, 16, 35, tzinfo=timezone.utc)
    assert t.et_date == date(2026, 4, 30)
    assert t.pair == "STLPIT"


def test_parse_handles_dst():
    # July is EDT (UTC-4), December is EST (UTC-5)
    summer = parse_event_ticker("KXMLBGAME-25JUL041910WSHBOS")
    winter = parse_event_ticker("KXMLBGAME-25DEC011910WSHBOS")
    assert summer.start_utc.hour == 23
    assert winter.start_utc.hour == 0 and winter.start_utc.day == 2


def test_parse_2025_format_no_time():
    t = parse_event_ticker("KXMLBGAME-25SEP24KCLAA")
    assert t is not None
    assert t.start_utc is None
    assert t.et_date == date(2025, 9, 24)
    assert t.pair == "KCLAA"
    assert t.game_number is None


def test_parse_2025_doubleheader_suffix():
    t = parse_event_ticker("KXMLBGAME-25APR26BALDETG1")
    assert t is not None
    assert t.pair == "BALDET"
    assert t.game_number == 1


def test_parse_2025_doubleheader_suffix_without_g():
    t = parse_event_ticker("KXMLBGAME-25APR18MIAPHI2")
    assert t is not None
    assert t.pair == "MIAPHI"
    assert t.game_number == 2


def test_parse_2026_format_has_no_game_number():
    t = parse_event_ticker("KXMLBGAME-26APR301235STLPIT")
    assert t.game_number is None


def test_parse_rejects_malformed():
    assert parse_event_ticker("KXMLBGAME-26XXX301235STLPIT") is None  # bad month
    assert parse_event_ticker("KXMLBGAME-26APR351235STLPIT") is None  # bad day
    assert parse_event_ticker("KXNFLGAME-26APR301235STLPIT") is None  # wrong series


# pair splitting


def test_split_pair_both_orders():
    assert split_pair("STLPIT", {"STL", "PIT"}) == ("STL", "PIT")
    assert split_pair("PITSTL", {"STL", "PIT"}) == ("PIT", "STL")


def test_split_pair_variable_length_abbrs():
    assert split_pair("AZSTL", {"AZ", "STL"}) == ("AZ", "STL")
    assert split_pair("CLECWS", {"CLE", "CWS"}) == ("CLE", "CWS")


def test_split_pair_rejects_mismatch():
    assert split_pair("STLPIT", {"STL", "BOS"}) is None
    assert split_pair("STLPIT", {"STL"}) is None
    assert split_pair("STLPIT", {"STL", "PIT", "BOS"}) is None


# team abbreviation mapping


def test_team_map_covers_all_30_teams():
    assert len(set(KALSHI_TO_MLB_TEAM_ID.values())) == 30


def test_arizona_has_both_abbrs():
    assert KALSHI_TO_MLB_TEAM_ID["ARI"] == KALSHI_TO_MLB_TEAM_ID["AZ"] == 109


# game selection


def _game(
    pk: int, when: datetime, game_number: int = 1, lasts_hours: float = 3
) -> GameRow:
    return GameRow(
        game_pk=pk,
        game_date=when,
        official_date=when.date(),
        away_team_id=138,
        home_team_id=134,
        game_number=game_number,
        actual_end=when + timedelta(hours=lasts_hours),
    )


def test_pick_game_single_candidate():
    t = parse_event_ticker("KXMLBGAME-26APR301235STLPIT")
    g = _game(1, datetime(2026, 4, 30, 16, 35, tzinfo=timezone.utc))
    assert pick_game([g], t) is g


def test_pick_game_doubleheader_nearest_start():
    t = parse_event_ticker("KXMLBGAME-26APR301235STLPIT")
    game1 = _game(1, datetime(2026, 4, 30, 16, 35, tzinfo=timezone.utc))
    game2 = _game(2, datetime(2026, 4, 30, 22, 10, tzinfo=timezone.utc))
    assert pick_game([game1, game2], t) is game1
    t_night = parse_event_ticker("KXMLBGAME-26APR301810STLPIT")
    assert pick_game([game1, game2], t_night) is game2


def test_pick_game_rejects_out_of_tolerance():
    t = parse_event_ticker("KXMLBGAME-26APR301235STLPIT")
    far = _game(1, datetime(2026, 5, 1, 16, 35, tzinfo=timezone.utc))
    assert pick_game([far], t) is None


def test_pick_game_2025_single_candidate_no_time():
    t = parse_event_ticker("KXMLBGAME-25SEP24KCLAA")
    g = _game(1, datetime(2025, 9, 24, 23, 40, tzinfo=timezone.utc))
    assert pick_game([g], t) is g


def test_pick_game_2025_doubleheader_by_game_number():
    game1 = _game(1, datetime(2025, 4, 26, 17, 0, tzinfo=timezone.utc), 1)
    game2 = _game(2, datetime(2025, 4, 26, 22, 0, tzinfo=timezone.utc), 2)
    t1 = parse_event_ticker("KXMLBGAME-25APR26BALDETG1")
    t2 = parse_event_ticker("KXMLBGAME-25APR26BALDETG2")
    assert pick_game([game1, game2], t1) is game1
    assert pick_game([game1, game2], t2) is game2


def test_pick_game_2025_doubleheader_without_suffix_is_ambiguous():
    game1 = _game(1, datetime(2025, 4, 26, 17, 0, tzinfo=timezone.utc), 1)
    game2 = _game(2, datetime(2025, 4, 26, 22, 0, tzinfo=timezone.utc), 2)
    t = parse_event_ticker("KXMLBGAME-25APR26BALDET")
    assert pick_game([game1, game2], t) is None


def test_pick_game_empty():
    t = parse_event_ticker("KXMLBGAME-26APR301235STLPIT")
    assert pick_game([], t) is None


def test_pick_game_single_candidate_wrong_game_number_rejected():
    # ticker says G2 but the only game that day is game 1: the real game 2
    # was moved to another day (e.g. KXMLBGAME-25AUG18MILCHCG2)
    t = parse_event_ticker("KXMLBGAME-25AUG18MILCHCG2")
    game1 = _game(1, datetime(2025, 8, 18, 18, 20, tzinfo=timezone.utc), 1)
    assert pick_game([game1], t) is None


def test_pick_game_traditional_dh_resolved_by_settlement():
    # traditional doubleheader: scheduled starts 5 minutes apart, so start
    # proximity is meaningless; the market settled right after game 1 ended
    # (e.g. KXMLBGAME-26APR051340CHCCLE)
    t = parse_event_ticker("KXMLBGAME-26APR051340CHCCLE")
    game1 = _game(1, datetime(2026, 4, 5, 17, 10, tzinfo=timezone.utc), 1, 2.5)
    game2 = _game(2, datetime(2026, 4, 5, 17, 15, tzinfo=timezone.utc), 2, 6.5)
    settle = datetime(2026, 4, 5, 19, 55, tzinfo=timezone.utc)
    assert pick_game([game1, game2], t, settle) is game1
    settle_late = datetime(2026, 4, 6, 0, 5, tzinfo=timezone.utc)
    assert pick_game([game1, game2], t, settle_late) is game2


# settlement fallback (postponed games)


def test_settlement_picks_game_that_ended_before_settling():
    # postponed into a split doubleheader; event settled after the night game
    game1 = _game(1, datetime(2026, 4, 30, 16, 35, tzinfo=timezone.utc), 1)
    game2 = _game(2, datetime(2026, 4, 30, 21, 35, tzinfo=timezone.utc), 2)
    settle = datetime(2026, 5, 1, 1, 24, tzinfo=timezone.utc)
    assert settled_on([game1, game2], settle) is game2


def test_settlement_rejects_settlement_long_after_game():
    # zombie market settled months later must not match
    g = _game(1, datetime(2025, 4, 18, 23, 5, tzinfo=timezone.utc))
    settle = datetime(2026, 3, 25, 17, 33, tzinfo=timezone.utc)
    assert settled_on([g], settle) is None


def test_settlement_rejects_game_ending_after_settlement():
    g = _game(1, datetime(2026, 5, 2, 16, 35, tzinfo=timezone.utc))
    settle = datetime(2026, 5, 1, 1, 24, tzinfo=timezone.utc)
    assert settled_on([g], settle) is None
