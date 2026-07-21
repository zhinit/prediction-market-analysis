from __future__ import annotations

import json

from db.arbitrage.verify_candidates import (
    Decision,
    append_results,
    names_match,
    team_score,
    verify_candidate,
)


def _cand(series, event_ticker, title, markets, slug, line=None):
    return {
        "kalshi_event": {
            "event_ticker": event_ticker,
            "series_ticker": series,
            "title": title,
            "category": "Sports",
            "strike_date": None,
        },
        "kalshi_markets": [
            {"ticker": t, "title": mt} for t, mt in markets
        ],
        "polymarket": {"slug": slug, "line": line},
    }


def _side(slug, question, name=None, description=None):
    return {
        "slug": slug,
        "question": question,
        "yes_side": {"name": name, "abbreviation": None,
                     "description": description or name or "Yes"},
    }


class TestNames:
    def test_variant_subset(self):
        assert names_match("Facundo Acosta", "Facundo Diaz Acosta")

    def test_partial_overlap_is_not_match(self):
        assert not names_match("Joao Lucas Da Silva", "Lucas Andrade Da Silva")

    def test_team_score_city_letter(self):
        assert team_score("Los Angeles A", "Los Angeles Angels") == 2
        assert team_score("New York M wins by over 1.5 runs",
                          "Milwaukee Brewers") == 0

    def test_team_score_letters_only(self):
        assert team_score("A's", "Athletics") == 1


class TestMoneyline:
    def _c(self):
        return _cand(
            "KXWTAMATCH", "KXWTAMATCH-26JUL22BONNOH", "Bondar vs Noha Akugue",
            [("KXWTAMATCH-26JUL22BONNOH-BON", "Anna Bondar"),
             ("KXWTAMATCH-26JUL22BONNOH-NOH", "Noma Noha Akugue")],
            "aec-wta-annbon-nomaku-2026-07-22",
        )

    def test_two_entries_opposite_directions(self):
        d = verify_candidate(self._c(), _side(
            "aec-wta-annbon-nomaku-2026-07-22",
            "Anna Bondar vs. Noma Noha Akugue", name="Anna Bondar"))
        assert d.kind == "approve"
        assert len(d.entries) == 2
        assert {e["direction"] for e in d.entries} == {
            "kalshi_yes_eq_poly_yes", "kalshi_yes_eq_poly_no"}
        yes = next(e for e in d.entries
                   if e["direction"] == "kalshi_yes_eq_poly_yes")
        assert yes["kalshi_ticker"].endswith("-BON")
        assert yes["event_date"] == "2026-07-22"

    def test_unknown_player_rejected(self):
        d = verify_candidate(self._c(), _side(
            "aec-wta-annbon-nomaku-2026-07-22",
            "Someone Else vs. Another Person", name="Someone Else"))
        assert d.kind == "reject"
        assert "different event" in d.reason

    def test_tie_market_single_entry(self):
        c = _cand(
            "KXMLSGAME", "KXMLSGAME-26JUL25NYCCHI", "New York City vs Chicago Fire",
            [("KXMLSGAME-26JUL25NYCCHI-NYC", "New York City"),
             ("KXMLSGAME-26JUL25NYCCHI-CHI", "Chicago Fire"),
             ("KXMLSGAME-26JUL25NYCCHI-TIE", "Tie")],
            "atc-mls-nyc-chi-2026-07-25-nyc",
        )
        d = verify_candidate(c, _side(
            "atc-mls-nyc-chi-2026-07-25-nyc",
            "Will New York City FC win against Chicago Fire FC in the MLS "
            "match scheduled for Jul 25?", name="New York City FC"))
        assert d.kind == "approve"
        assert len(d.entries) == 1
        assert d.entries[0]["direction"] == "kalshi_yes_eq_poly_yes"


class TestRegulationTime:
    def test_reg_time_rejected(self):
        c = _cand(
            "KXUECLGAME", "KXUECLGAME-26JUL22VARRFC", "FK Vardar Skopje vs Riga FC",
            [("KXUECLGAME-26JUL22VARRFC-VAR", "Reg Time: FK Vardar Skopje"),
             ("KXUECLGAME-26JUL22VARRFC-TIE", "Reg Time: Tie"),
             ("KXUECLGAME-26JUL22VARRFC-RFC", "Reg Time: Riga FC")],
            "atc-uecl-var-rfi-2026-07-22-var",
        )
        d = verify_candidate(c, _side(
            "atc-uecl-var-rfi-2026-07-22-var",
            "Will FK Vardar Skopje win against Riga FC in the UECL match?",
            name="FK Vardar Skopje"))
        assert d.kind == "reject"
        assert "regulation" in d.reason


class TestF5:
    def test_city_truncation(self):
        c = _cand(
            "KXMLBF5", "KXMLBF5-26JUL212138STLLAA",
            "St. Louis vs Los Angeles A: First 5 Innings",
            [("KXMLBF5-26JUL212138STLLAA-STL", "St. Louis wins first 5 innings"),
             ("KXMLBF5-26JUL212138STLLAA-TIE", "Tie"),
             ("KXMLBF5-26JUL212138STLLAA-LAA", "Los Angeles A wins first 5 innings")],
            "atc-mlb-stl-laa-2026-07-21-f5-laa",
        )
        d = verify_candidate(c, _side(
            "atc-mlb-stl-laa-2026-07-21-f5-laa",
            "Will the Los Angeles Angels win the first 5 innings vs the "
            "St. Louis Cardinals?"))
        assert d.kind == "approve"
        assert len(d.entries) == 1  # tie exists: no complement entry
        assert d.entries[0]["kalshi_ticker"].endswith("-LAA")


class TestSpread:
    def _c(self, line):
        return _cand(
            "KXMLBSPREAD", "KXMLBSPREAD-26JUL211940NYMMIL",
            "New York M vs Milwaukee: Spread",
            [("KXMLBSPREAD-26JUL211940NYMMIL-NYM2", "New York M wins by over 1.5 runs"),
             ("KXMLBSPREAD-26JUL211940NYMMIL-MIL2", "Milwaukee wins by over 1.5 runs")],
            f"asc-mlb-nym-mil-2026-07-21-{'neg' if line < 0 else 'pos'}-1pt5",
            line=line,
        )

    def test_negative_line_yes(self):
        d = verify_candidate(self._c(-1.5), _side(
            "asc-mlb-nym-mil-2026-07-21-neg-1pt5",
            "Will the New York Mets cover -1.5 vs the Milwaukee Brewers in "
            "NYM vs MIL?", name="New York Mets"))
        assert d.kind == "approve"
        assert d.entries[0]["direction"] == "kalshi_yes_eq_poly_yes"
        assert d.entries[0]["kalshi_ticker"].endswith("-NYM2")

    def test_positive_line_is_opponent_no(self):
        d = verify_candidate(self._c(1.5), _side(
            "asc-mlb-nym-mil-2026-07-21-pos-1pt5",
            "Will the New York Mets cover 1.5 vs the Milwaukee Brewers in "
            "NYM vs MIL?", name="New York Mets"))
        assert d.kind == "approve"
        assert d.entries[0]["direction"] == "kalshi_yes_eq_poly_no"
        assert d.entries[0]["kalshi_ticker"].endswith("-MIL2")

    def test_missing_line_rejected(self):
        c = self._c(-2.5)
        c["polymarket"]["slug"] = "asc-mlb-nym-mil-2026-07-21-neg-2pt5"
        d = verify_candidate(c, _side(
            "asc-mlb-nym-mil-2026-07-21-neg-2pt5",
            "Will the New York Mets cover -2.5 vs the Milwaukee Brewers in "
            "NYM vs MIL?", name="New York Mets"))
        assert d.kind == "reject"
        assert "no Kalshi sub-market at line" in d.reason


class TestTotal:
    def test_line_match(self):
        c = _cand(
            "KXMLBTOTAL", "KXMLBTOTAL-26JUL212138STLLAA",
            "St. Louis vs Los Angeles A: Total Runs",
            [("KXMLBTOTAL-26JUL212138STLLAA-8", "Over 7.5 runs scored"),
             ("KXMLBTOTAL-26JUL212138STLLAA-9", "Over 8.5 runs scored")],
            "tsc-mlb-stl-laa-2026-07-21-8pt5", line=8.5,
        )
        d = verify_candidate(c, _side(
            "tsc-mlb-stl-laa-2026-07-21-8pt5",
            "Will the total in St. Louis Cardinals vs Los Angeles Angels be "
            "more than 8.5?", description="Over"))
        assert d.kind == "approve"
        assert d.entries[0]["kalshi_ticker"].endswith("-9")


class TestMapWinner:
    def test_map_number_mismatch_rejected(self):
        c = _cand(
            "KXCS2MAP", "KXCS2MAP-26JUL221330100TFAL-1",
            "100 Thieves vs. Team Falcons: Map 1",
            [("KXCS2MAP-26JUL221330100TFAL-1-100T", "100 Thieves"),
             ("KXCS2MAP-26JUL221330100TFAL-1-FAL", "Team Falcons")],
            "astatc-cs2-fal-100t-2026-07-22-map2",
        )
        d = verify_candidate(c, _side(
            "astatc-cs2-fal-100t-2026-07-22-map2",
            "Will Team Falcons win Map 2 vs 100 Thieves?"))
        assert d.kind == "reject"
        assert "number mismatch" in d.reason

    def test_map_pair(self):
        c = _cand(
            "KXCS2MAP", "KXCS2MAP-26JUL221330100TFAL-1",
            "100 Thieves vs. Team Falcons: Map 1",
            [("KXCS2MAP-26JUL221330100TFAL-1-100T", "100 Thieves"),
             ("KXCS2MAP-26JUL221330100TFAL-1-FAL", "Team Falcons")],
            "astatc-cs2-fal-100t-2026-07-22-map1",
        )
        d = verify_candidate(c, _side(
            "astatc-cs2-fal-100t-2026-07-22-map1",
            "Will Team Falcons win Map 1 vs 100 Thieves?"))
        assert d.kind == "approve"
        assert len(d.entries) == 2


class TestPlayerProp:
    def test_threshold_and_name(self):
        c = _cand(
            "KXMLBHRR", "KXMLBHRR-26JUL212140CINSEA",
            "Cincinnati vs Seattle: Hits + Runs + RBIs",
            [("KXMLBHRR-26JUL212140CINSEA-RA2", "Randy Arozarena: 2+"),
             ("KXMLBHRR-26JUL212140CINSEA-RA4", "Randy Arozarena: 4+")],
            "astatc-mlb-cin-sea-2026-07-21-hrr-ranaro-gte2", line=2.0,
        )
        d = verify_candidate(c, _side(
            "astatc-mlb-cin-sea-2026-07-21-hrr-ranaro-gte2",
            "Will Randy Arozarena record at least 2 hits + runs + RBIs in "
            "CIN vs SEA?"))
        assert d.kind == "approve"
        assert d.entries[0]["kalshi_ticker"].endswith("-RA2")

    def test_missing_threshold_rejected(self):
        c = _cand(
            "KXMLBHRR", "KXMLBHRR-26JUL212140CINSEA",
            "Cincinnati vs Seattle: Hits + Runs + RBIs",
            [("KXMLBHRR-26JUL212140CINSEA-RA2", "Randy Arozarena: 2+")],
            "astatc-mlb-cin-sea-2026-07-21-hrr-ranaro-gte1", line=1.0,
        )
        d = verify_candidate(c, _side(
            "astatc-mlb-cin-sea-2026-07-21-hrr-ranaro-gte1",
            "Will Randy Arozarena record at least 1 hits + runs + RBIs in "
            "CIN vs SEA?"))
        assert d.kind == "reject"


class TestUnknownType:
    def test_flagged_not_approved(self):
        c = _cand("KXWCHOST", "KXWCHOST-30", "World Cup Host",
                  [("KXWCHOST-30-USA", "USA")], "some-slug-2026-07-21")
        d = verify_candidate(c, _side("some-slug-2026-07-21", "Who hosts?"))
        assert d.kind == "flag"


class TestAppendResults:
    def test_append_and_dedupe(self, tmp_path):
        matches = tmp_path / "matches.json"
        rejected = tmp_path / "rejected.json"
        flagged = tmp_path / "flagged.json"
        cand = _cand(
            "KXWTAMATCH", "EV1", "A vs B",
            [("EV1-A", "Player A")], "slug-a-2026-07-22")
        entry = {
            "id": "slug-a-2026-07-22--A", "kalshi_ticker": "EV1-A",
            "polymarket_slug": "slug-a-2026-07-22",
            "direction": "kalshi_yes_eq_poly_yes", "poly_yes": "Player A",
            "event_date": "2026-07-22", "notes": "n",
        }
        decisions = [(cand, Decision("approve", [entry]))]
        counts = append_results(decisions, matches, rejected, flagged)
        assert counts["approved"] == 1
        # second run: same entry skipped
        counts = append_results(decisions, matches, rejected, flagged)
        assert counts["approved"] == 0
        assert counts["skipped"] == 1
        assert len(json.loads(matches.read_text())) == 1
