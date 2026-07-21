from __future__ import annotations

import json
from pathlib import Path

import pytest

from datetime import date

from db.arbitrage.match_markets import (
    EventCandidate,
    KalshiEvent,
    PolyGame,
    bet_types_compatible,
    categories_compatible,
    dates_overlap,
    ensure_match_files,
    find_candidates,
    group_kalshi_events,
    group_poly_markets,
    jaccard_score,
    normalize_title,
    player_prop_teams_match,
    prune_expired_matches,
    sport_types_compatible,
)

FIXTURES = Path(__file__).parent / "fixtures"


class TestNormalizeTitle:
    def test_lowercase(self):
        assert "hello" in normalize_title("Hello")

    def test_strips_punctuation(self):
        result = normalize_title("Rangers vs. Yankees!")
        assert "rangers" in result
        assert "yankees" in result
        assert "vs" in result

    def test_removes_stop_words(self):
        result = normalize_title("Will the Rangers beat the Yankees")
        assert "the" not in result
        assert "will" not in result
        assert "rangers" in result
        assert "yankees" in result


class TestJaccardScore:
    def test_identical(self):
        s = {"a", "b", "c"}
        assert jaccard_score(s, s) == 1.0

    def test_disjoint(self):
        assert jaccard_score({"a", "b"}, {"c", "d"}) == 0.0

    def test_partial_overlap(self):
        score = jaccard_score({"a", "b", "c"}, {"b", "c", "d"})
        assert score == pytest.approx(2 / 4)

    def test_empty_sets(self):
        assert jaccard_score(set(), set()) == 0.0


class TestCategoriesCompatible:
    def test_sports_sports(self):
        assert categories_compatible("Sports", "sports") is True

    def test_sports_politics(self):
        assert categories_compatible("Sports", "politics") is False

    def test_empty_is_compatible(self):
        assert categories_compatible("", "sports") is True
        assert categories_compatible("Sports", "") is True

    def test_alias_match(self):
        assert categories_compatible("Sport", "sports") is True
        assert categories_compatible("Financial", "economics") is True


class TestSportTypesCompatible:
    def test_same_sport(self):
        assert sport_types_compatible("mlb", "mlb") is True

    def test_different_sport(self):
        assert sport_types_compatible("mlb", "nba") is False

    def test_unknown(self):
        assert sport_types_compatible(None, None) is True
        assert sport_types_compatible("mlb", None) is True
        assert sport_types_compatible(None, "nba") is True


class TestBetTypesCompatible:
    def test_moneyline_moneyline(self):
        assert bet_types_compatible(
            "KXMLBGAME", "SPORTS_MARKET_TYPE_MONEYLINE",
            "aec-mlb-tex-nyy-2026-07-10",
        ) is True

    def test_moneyline_spread(self):
        assert bet_types_compatible(
            "KXMLBGAME", "SPORTS_MARKET_TYPE_SPREAD",
            "asc-mlb-tex-nyy-2026-07-10-neg-1pt5",
        ) is False

    def test_none_poly_type_rejected(self):
        assert bet_types_compatible("KXMLBGAME", None, "some-slug") is False

    def test_unknown_kalshi_series_rejected(self):
        assert bet_types_compatible(
            "KXSOMETHING", "SPORTS_MARKET_TYPE_MONEYLINE",
            "aec-mlb-tex-nyy-2026-07-10",
        ) is False

    def test_f5_spread_not_full_game_spread(self):
        assert bet_types_compatible(
            "KXMLBF5SPREAD", "SPORTS_MARKET_TYPE_SPREAD",
            "asc-mlb-stl-laa-2026-07-21-neg-1pt5",
        ) is False

    def test_f5_total_not_full_game_total(self):
        assert bet_types_compatible(
            "KXMLBF5TOTAL", "SPORTS_MARKET_TYPE_TOTAL",
            "tsc-mlb-stl-laa-2026-07-21-8pt5",
        ) is False

    def test_games_spread_matches_gs_marker(self):
        assert bet_types_compatible(
            "KXATPGSPREAD", "SPORTS_MARKET_TYPE_SPREAD",
            "asc-atp-a-b-2026-07-22-gs-neg-2pt5",
        ) is True

    def test_set_winner_never_matches_spread(self):
        assert bet_types_compatible(
            "KXWTASETWINNER", "SPORTS_MARKET_TYPE_SPREAD",
            "asc-wta-a-b-2026-07-22-gs-neg-2pt5",
        ) is False

    def test_correct_score_never_matches_spread(self):
        assert bet_types_compatible(
            "KXMLSSCORE", "SPORTS_MARKET_TYPE_SPREAD",
            "asc-mls-sje-lag-2026-07-25-neg-2pt5",
        ) is False

    def test_f5_winner_prop(self):
        assert bet_types_compatible(
            "KXMLBF5", "SPORTS_MARKET_TYPE_PROP",
            "atc-mlb-stl-laa-2026-07-21-f5-laa",
        ) is True

    def test_extras_not_f5_winner(self):
        assert bet_types_compatible(
            "KXMLBEXTRAS", "SPORTS_MARKET_TYPE_PROP",
            "atc-mlb-stl-laa-2026-07-22-f5-laa",
        ) is False

    def test_total_bases_prop(self):
        assert bet_types_compatible(
            "KXMLBTB", "SPORTS_MARKET_TYPE_PROP",
            "astatc-mlb-nym-mil-2026-07-21-tb-fralin-gte2",
        ) is True

    def test_rays_f5_not_total_bases(self):
        # 'tb' as a team code before the date must not classify as
        # total-bases; only tail tokens after the date count.
        assert bet_types_compatible(
            "KXMLBF5", "SPORTS_MARKET_TYPE_PROP",
            "atc-mlb-tb-bal-2026-07-21-f5-tb",
        ) is True

    def test_esports_map_winner(self):
        assert bet_types_compatible(
            "KXLOLMAP", "SPORTS_MARKET_TYPE_PROP",
            "astatc-lol-khk-use-2026-07-22-game1",
        ) is True

    def test_half_spreads_never_match_full_game(self):
        # fh = first half, sh = second half; neither is the full-game spread
        for half in ("fh", "sh"):
            assert bet_types_compatible(
                "KXMLSSPREAD", "SPORTS_MARKET_TYPE_SPREAD",
                f"asc-mls-nyc-chi-2026-07-25-{half}-neg-1pt5",
            ) is False

    def test_ftts_never_matches_btts(self):
        assert bet_types_compatible(
            "KXMLSFTTS", "SPORTS_MARKET_TYPE_PROP",
            "astatc-mls-sje-lag-2026-07-25-fh-btts",
        ) is False


class TestPlayerPropTeamsMatch:
    def test_same_game(self):
        assert player_prop_teams_match(
            "KXMLBHRR-26JUL211940NYMMIL",
            "astatc-mlb-nym-mil-2026-07-21-hrr-fraalv-gte1",
        ) is True

    def test_different_game(self):
        assert player_prop_teams_match(
            "KXMLBHRR-26JUL211940SFKC",
            "astatc-mlb-nym-mil-2026-07-21-hrr-fraalv-gte1",
        ) is False

    def test_doubleheader_suffix(self):
        assert player_prop_teams_match(
            "KXMLBHRR-26JUL21BALDETG1",
            "astatc-mlb-bal-det-2026-07-21-hrr-gunhen-gte2",
        ) is True

    def test_unparseable_ticker_passes(self):
        assert player_prop_teams_match(
            "KXSOMETHING-WEIRD", "astatc-mlb-nym-mil-2026-07-21-hrr-x-gte1",
        ) is True


class TestDatesOverlap:
    def _poly(self, slug="slug", question="q"):
        return PolyGame(
            game_id=None, slug=slug, question=question,
            category="", sport_type=None, slugs=(slug,), sport=None,
        )

    def test_same_date(self):
        pg = self._poly(slug="aec-mlb-tex-nyy-2026-07-10")
        assert dates_overlap("2026-07-10", pg, is_sports=True) is True

    def test_different_date(self):
        pg = self._poly(slug="aec-mlb-tex-nyy-2026-07-11")
        assert dates_overlap("2026-07-10", pg, is_sports=True) is False

    def test_missing_date_non_sports(self):
        pg = self._poly(slug="will-trump-win")
        assert dates_overlap(None, pg, is_sports=False) is True

    def test_missing_date_sports(self):
        pg = self._poly(slug="will-team-win")
        assert dates_overlap("2026-07-10", pg, is_sports=True) is False

    def test_date_from_ticker(self):
        pg = self._poly(slug="aec-mlb-tex-nyy-2026-07-10")
        assert dates_overlap(
            None, pg, is_sports=True,
            kalshi_event_ticker="KXMLBGAME-26JUL10-TEX-NYY",
        ) is True

    def test_date_from_question(self):
        pg = self._poly(
            slug="some-slug",
            question="Will X happen on 2026-07-10?",
        )
        assert dates_overlap("2026-07-10", pg, is_sports=False) is True


class TestGrouping:
    def test_group_kalshi_events(self):
        events = json.loads((FIXTURES / "kalshi_events.json").read_text())["events"]
        series = json.loads((FIXTURES / "kalshi_series.json").read_text())
        series_map = {s["ticker"]: s for s in series}
        result = group_kalshi_events(events, series_map)
        assert len(result) == 2
        assert result[0].sport == "mlb"
        assert result[1].sport == "nba"

    def test_group_poly_markets(self):
        markets = json.loads((FIXTURES / "poly_markets.json").read_text())
        result = group_poly_markets(markets)
        # Two games (mlb and nba) grouped by gameId
        slugs_by_game = {g.game_id: g for g in result if g.game_id}
        assert "mlb-tex-nyy-2026-07-10" in slugs_by_game
        assert "nba-lal-bos-2026-07-10" in slugs_by_game
        mlb = slugs_by_game["mlb-tex-nyy-2026-07-10"]
        assert "moneyline" in mlb.slug
        assert mlb.game_start_time == "2026-07-10T23:05:00Z"
        # Standalone: politics, plus the spread (line markets never group)
        standalone = {g.slug for g in result if g.game_id is None}
        assert standalone == {
            "will-trump-win-2028",
            "aec-mlb-tex-nyy-2026-07-10-spread",
        }
        spread = next(g for g in result if "spread" in g.slug)
        assert spread.line == "-1.5"

    def test_line_markets_not_collapsed(self):
        base = {
            "question": "Will the Cardinals cover?",
            "category": "sports",
            "sportsMarketTypeV2": "SPORTS_MARKET_TYPE_SPREAD",
            "gameId": None,
            "gameStartTime": "2026-07-21T00:00:00Z",
        }
        markets = [
            {**base, "slug": "asc-mlb-stl-laa-2026-07-21-neg-1pt5", "line": "-1.5"},
            {**base, "slug": "asc-mlb-stl-laa-2026-07-21-neg-2pt5", "line": "-2.5"},
        ]
        result = group_poly_markets(markets)
        assert len(result) == 2
        assert {g.line for g in result} == {"-1.5", "-2.5"}


class TestFindCandidates:
    def _ke(self, ticker, title, series="KXMLBGAME", date="2026-07-10"):
        return KalshiEvent(
            event_ticker=ticker, series_ticker=series,
            title=title, strike_date=date,
            category="Sports", market_count=2, sport="mlb",
        )

    def _pg(self, slug, question, game_id=None):
        return PolyGame(
            game_id=game_id, slug=slug, question=question,
            category="sports",
            sport_type="SPORTS_MARKET_TYPE_MONEYLINE",
            slugs=(slug,), sport="mlb",
        )

    def test_matching_pair(self):
        ke = self._ke(
            "KXMLBGAME-26JUL10-TEX-NYY",
            "Rangers vs. Yankees: July 10",
        )
        pg = self._pg(
            "aec-mlb-tex-nyy-2026-07-10-moneyline",
            "Will the Texas Rangers beat the New York Yankees on July 10?",
        )
        results = find_candidates([ke], [pg], threshold=0.2)
        assert len(results) == 1
        assert results[0].score > 0.2

    def test_no_match_different_sport(self):
        ke = self._ke(
            "KXMLBGAME-26JUL10-TEX-NYY",
            "Rangers vs. Yankees",
        )
        pg = self._pg(
            "aec-nba-lal-bos-2026-07-10-moneyline",
            "Will the Lakers beat the Celtics?",
        )
        pg = PolyGame(
            game_id=None, slug=pg.slug, question=pg.question,
            category="sports",
            sport_type="SPORTS_MARKET_TYPE_MONEYLINE",
            slugs=(pg.slug,), sport="nba",
        )
        results = find_candidates([ke], [pg], threshold=0.2)
        assert len(results) == 0

    def test_deduplication_by_slug(self):
        ke1 = self._ke("EV1", "Rangers vs. Yankees: July 10")
        ke2 = self._ke("EV2", "Texas Rangers vs. New York Yankees July 10")
        pg = self._pg(
            "aec-mlb-tex-nyy-2026-07-10-moneyline",
            "Will the Texas Rangers beat the New York Yankees on July 10?",
        )
        results = find_candidates([ke1, ke2], [pg], threshold=0.2)
        assert len(results) == 1  # deduplicated by poly slug

    def test_ordering_by_score(self):
        ke = self._ke("EV1", "Rangers vs. Yankees")
        pg_high = self._pg(
            "slug-high",
            "Rangers vs. Yankees",
        )
        pg_low = self._pg(
            "slug-low",
            "Something completely different Rangers",
        )
        results = find_candidates([ke], [pg_high, pg_low], threshold=0.1)
        if len(results) >= 2:
            assert results[0].score >= results[1].score

    def test_non_sports_kalshi_excluded(self):
        ke = KalshiEvent(
            event_ticker="KXPRES-2028", series_ticker="KXPRES",
            title="Presidential Election Winner 2028", strike_date=None,
            category="Politics", market_count=2, sport=None,
        )
        pg = PolyGame(
            game_id=None, slug="will-trump-win-2028",
            question="Will Trump win the 2028 presidential election?",
            category="politics", sport_type=None,
            slugs=("will-trump-win-2028",), sport=None,
        )
        results = find_candidates([ke], [pg], threshold=0.1)
        assert results == []

    def test_blank_poly_category_still_matches(self):
        ke = self._ke(
            "KXMLBGAME-26JUL10-TEX-NYY",
            "Rangers vs. Yankees: July 10",
        )
        pg = PolyGame(
            game_id=None,
            slug="aec-mlb-tex-nyy-2026-07-10-moneyline",
            question="Will the Texas Rangers beat the New York Yankees on July 10?",
            category="",
            sport_type="SPORTS_MARKET_TYPE_MONEYLINE",
            slugs=("aec-mlb-tex-nyy-2026-07-10-moneyline",), sport="mlb",
        )
        results = find_candidates([ke], [pg], threshold=0.2)
        assert len(results) == 1

    def test_known_matches_excluded(self):
        # This tests the _load_known_slugs path indirectly via find_candidates
        # find_candidates itself doesn't exclude; the CLI does. This test
        # verifies find_candidates returns all matches for the CLI to filter.
        ke = self._ke("EV1", "Rangers vs. Yankees: July 10")
        pg = self._pg(
            "aec-mlb-tex-nyy-2026-07-10-moneyline",
            "Will the Texas Rangers beat the New York Yankees on July 10?",
        )
        results = find_candidates([ke], [pg], threshold=0.2)
        assert len(results) == 1


class TestMatchFileMaintenance:
    def test_ensure_match_files_creates_empty_arrays(self, tmp_path):
        matches = tmp_path / "matches.json"
        rejected = tmp_path / "rejected_matches.json"
        ensure_match_files((matches, rejected))
        assert json.loads(matches.read_text()) == []
        assert json.loads(rejected.read_text()) == []

    def test_ensure_match_files_leaves_existing(self, tmp_path):
        matches = tmp_path / "matches.json"
        matches.write_text('[{"id": "x"}]')
        ensure_match_files((matches,))
        assert json.loads(matches.read_text()) == [{"id": "x"}]

    def test_prune_expired_matches(self, tmp_path):
        path = tmp_path / "matches.json"
        path.write_text(json.dumps([
            {"id": "past", "event_date": "2026-07-10"},
            {"id": "today", "event_date": "2026-07-21"},
            {"id": "future", "event_date": "2026-07-22"},
            {"id": "undated"},
        ]))
        pruned = prune_expired_matches(date(2026, 7, 21), path)
        assert pruned == 1
        kept = {m["id"] for m in json.loads(path.read_text())}
        assert kept == {"today", "future", "undated"}


class TestIntegrationWithFixtures:
    def test_full_pipeline_with_fixtures(self):
        events_data = json.loads(
            (FIXTURES / "kalshi_events.json").read_text(),
        )["events"]
        series_data = json.loads(
            (FIXTURES / "kalshi_series.json").read_text(),
        )
        poly_data = json.loads(
            (FIXTURES / "poly_markets.json").read_text(),
        )

        series_map = {s["ticker"]: s for s in series_data}
        kalshi_events = group_kalshi_events(events_data, series_map)
        poly_games = group_poly_markets(poly_data)

        candidates = find_candidates(kalshi_events, poly_games, threshold=0.2)

        # Should match MLB game and NBA game, not cross-match
        matched_sports = set()
        for c in candidates:
            matched_sports.add((c.kalshi_event.sport, c.poly_game.sport))
        for k_sport, p_sport in matched_sports:
            assert k_sport == p_sport

        # Politics should not match sports
        poly_slugs = {c.poly_game.slug for c in candidates}
        assert "will-trump-win-2028" not in poly_slugs
