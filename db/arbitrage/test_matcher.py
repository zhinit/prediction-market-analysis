from __future__ import annotations

import json
from pathlib import Path

import pytest

from match_markets import (
    EventCandidate,
    KalshiEvent,
    PolyGame,
    bet_types_compatible,
    categories_compatible,
    dates_overlap,
    find_candidates,
    group_kalshi_events,
    group_poly_markets,
    jaccard_score,
    normalize_title,
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
        ) is True

    def test_moneyline_spread(self):
        assert bet_types_compatible(
            "KXMLBGAME", "SPORTS_MARKET_TYPE_SPREAD",
        ) is False

    def test_none_poly_type(self):
        assert bet_types_compatible("KXMLBGAME", None) is True

    def test_poly_moneyline_unknown_kalshi(self):
        assert bet_types_compatible(
            "KXSOMETHING", "SPORTS_MARKET_TYPE_MONEYLINE",
        ) is False


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
        # Two games (mlb and nba) grouped by gameId, one standalone (politics)
        slugs_by_game = {g.game_id: g for g in result if g.game_id}
        assert "mlb-tex-nyy-2026-07-10" in slugs_by_game
        assert "nba-lal-bos-2026-07-10" in slugs_by_game
        # MLB game should pick moneyline as representative
        mlb = slugs_by_game["mlb-tex-nyy-2026-07-10"]
        assert "moneyline" in mlb.slug
        # Politics is standalone
        politics = [g for g in result if g.game_id is None]
        assert len(politics) == 1
        assert "trump" in politics[0].slug


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
