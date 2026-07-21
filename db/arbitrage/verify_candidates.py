"""Stage-2 verification of matcher candidates (see docs/market-matching.md).

Applies the mechanical parts of the /matcher checklist to every candidate in
candidates.json: same event (by name/team-code), exact line, correct Kalshi
sub-market, and direction from the Poly YES side (fetched via
fetch_poly_sides). Each candidate is approved (match entries appended to
matches.json), rejected with a reason (appended to rejected_matches.json), or
flagged for human review (written to flagged_candidates.json).

Fail-safe rule: anything that does not parse or match cleanly is flagged or
rejected, never approved. New market types and wording changes surface as
flags, not as wrong matches.

Usage:
    uv run python -m db.arbitrage.verify_candidates
    uv run python -m db.arbitrage.verify_candidates --yes-sides sides.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from db.arbitrage.fetch_poly_sides import fetch_sides
from db.arbitrage.match_markets import _extract_kalshi_bet_type

_CANDIDATES_PATH = Path("db/arbitrage/candidates.json")
_MATCHES_PATH = Path("db/arbitrage/matches.json")
_REJECTED_PATH = Path("db/arbitrage/rejected_matches.json")
_FLAGGED_PATH = Path("db/arbitrage/flagged_candidates.json")

_YES = "kalshi_yes_eq_poly_yes"
_NO = "kalshi_yes_eq_poly_no"

# ---- name matching ----

_DROP_TOKENS = frozenset({
    "fc", "cf", "sc", "afc", "sk", "is", "club", "kf", "nk",
    "cd", "ca", "if", "bk", "ac", "the",
})


def norm_tokens(name: str) -> frozenset[str]:
    s = unicodedata.normalize("NFKD", name or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return frozenset(t for t in s.split() if t not in _DROP_TOKENS)


def names_match(a: str, b: str) -> bool:
    """Same name allowing variants: equal token sets or one a subset of the
    other ("Facundo Acosta" = "Facundo Diaz Acosta"). Partial overlap is NOT a
    match — shared tokens across different people caused false candidates."""
    ta, tb = norm_tokens(a), norm_tokens(b)
    if not ta or not tb:
        return False
    return ta == tb or ta <= tb or tb <= ta


def team_score(kalshi_team: str, full_name: str) -> int:
    """Graded match for Kalshi's truncated team labels against a full name.
    3 = name match; 2 = city words subset plus any single-letter
    disambiguator prefixing the nickname ("Los Angeles A" = Angels);
    1 = letters only ("A's" = Athletics); 0 = no match."""
    if names_match(kalshi_team, full_name):
        return 3
    kt, pt = norm_tokens(kalshi_team), norm_tokens(full_name)
    letters = {t for t in kt if len(t) == 1 and t != "s"}
    words = kt - letters - {"s"}
    if words and words <= pt and all(
            any(p.startswith(letter) for p in pt - words) for letter in letters):
        return 2
    if not words and letters and all(
            any(p.startswith(letter) for p in pt) for letter in letters):
        return 1
    return 0


# ---- parsing ----

_SPREAD_TITLE = re.compile(
    r"^(?:Goal Diff Reg Time: )?(.+?)(?: wins by (?:over|more than) | -)"
    r"(\d+(?:\.\d+)?)"
)
_TOTAL_TITLE = re.compile(r"Over (\d+(?:\.\d+)?)")
_PLAYER_TITLE = re.compile(r"^(.+?): (\d+)\+$")
_Q_TEAM_WIN = re.compile(r"^Will (?:the )?(.+?) (?:win|record)", re.IGNORECASE)
_Q_MAP = re.compile(
    r"^Will (?:the )?(.+?) win (?:Map|Game) (\d+) vs (?:the )?(.+?)\?",
    re.IGNORECASE,
)
_Q_PLAYER = re.compile(r"^Will (.+?) record at least (\d+)", re.IGNORECASE)
_Q_OTHER_TEAM = re.compile(r" vs\.? (?:the )?(.+?) in ")
_Q_CODES = re.compile(r" in ([A-Za-z]{2,5}) vs\.? ([A-Za-z]{2,5})\b")
_SLUG_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
_MAP_NO = re.compile(r"(?:Map|Game)\s*(\d+)", re.IGNORECASE)
_REG_TIME = re.compile(r"reg(?:ulation)? time", re.IGNORECASE)


# ---- decisions ----

@dataclass
class Decision:
    kind: str  # "approve" | "reject" | "flag"
    entries: list[dict[str, Any]] = field(default_factory=list)
    reason: str = ""


def _entry(cand: dict, kalshi_ticker: str, direction: str,
           poly_yes: str, notes: str) -> dict[str, Any]:
    slug = cand["polymarket"]["slug"]
    dm = _SLUG_DATE.search(slug)
    return {
        "id": f"{slug}--{kalshi_ticker.rsplit('-', 1)[-1]}",
        "kalshi_ticker": kalshi_ticker,
        "polymarket_slug": slug,
        "direction": direction,
        "poly_yes": poly_yes,
        "event_date": dm.group(1) if dm else "",
        "notes": notes,
    }


def _approve(cand, ticker, direction, poly_yes, notes) -> Decision:
    return Decision("approve", [_entry(cand, ticker, direction, poly_yes, notes)])


def _reject(reason: str) -> Decision:
    return Decision("reject", reason=reason)


def _flag(reason: str) -> Decision:
    return Decision("flag", reason=reason)


def _pair(cand, series, kind, strong, team_subs, tie_subs, pname) -> Decision:
    """One entry per Kalshi sub-market: yes on the matched side, plus the
    complement side only for two-outcome events (a tie outcome breaks
    complementarity)."""
    d = _approve(
        cand, strong["ticker"], _YES, pname,
        f"{series} {kind}: Kalshi YES = {strong['title']}, Poly YES = {pname}.",
    )
    if len(team_subs) == 2 and not tie_subs:
        other = next(m for m in team_subs if m is not strong)
        d.entries.append(_entry(
            cand, other["ticker"], _NO, pname,
            f"{series} {kind}: Kalshi YES = {other['title']}, "
            f"Poly YES = {pname} (opposite side).",
        ))
    return d


# ---- per-type verification ----

def verify_candidate(cand: dict, side: dict) -> Decision:
    series = cand["kalshi_event"]["series_ticker"]
    ktype = _extract_kalshi_bet_type(series)
    slug = cand["polymarket"]["slug"]
    yes = side.get("yes_side") or {}
    question = side.get("question") or ""
    kms = cand["kalshi_markets"]
    line = cand["polymarket"]["line"]

    if "error" in side:
        return _flag(f"yes-side fetch error: {side['error']}")

    ktext = cand["kalshi_event"]["title"] + " " + " ".join(
        m["title"] for m in kms)
    if _REG_TIME.search(ktext) and "regulation" not in question.lower():
        return _reject(
            "Kalshi settles on regulation time; Poly question does not state "
            "regulation — cannot verify resolution equivalence")

    tie_subs = [m for m in kms if "tie" in m["title"].lower()]
    team_subs = [m for m in kms if m not in tie_subs]

    if ktype == "moneyline":
        pname = yes.get("name") or ""
        if not pname:
            return _flag("moneyline without Poly team name")
        strong = [m for m in team_subs if names_match(pname, m["title"])]
        if len(strong) != 1:
            return _reject(f"different event: Poly YES '{pname}' matches no "
                           "Kalshi sub-market by name")
        return _pair(cand, series, "moneyline", strong[0], team_subs,
                     tie_subs, pname)

    if ktype == "f5_moneyline":
        qm = _Q_TEAM_WIN.match(question)
        if not qm:
            return _flag("cannot parse F5 question")
        pname = qm.group(1)
        scored = [
            (team_score(re.split(r" wins first 5", m["title"])[0], pname), m)
            for m in team_subs
        ]
        best = max(s for s, _ in scored)
        strong = [m for s, m in scored if s == best and s > 0]
        if len(strong) != 1:
            return _flag(f"F5 team '{pname}' not uniquely matched")
        return _approve(
            cand, strong[0]["ticker"], _YES, pname,
            f"MLB F5 winner: Kalshi YES = {strong[0]['title']}, Poly YES = "
            f"{pname} wins F5. Tie outcome exists; single entry only.")

    if ktype in ("spread", "game_spread", "f5_spread"):
        return _verify_spread(cand, series, yes, question, team_subs, line)

    if ktype in ("total", "game_total", "f5_total"):
        if line is None:
            return _flag("total missing line")
        desc = (yes.get("description") or "").lower()
        if desc != "over" and "more than" not in question.lower():
            return _flag("total YES side is not clearly Over")
        hits = [m for m in kms
                if (tm := _TOTAL_TITLE.search(m["title"]))
                and float(tm.group(1)) == float(line)]
        if len(hits) == 1:
            return _approve(cand, hits[0]["ticker"], _YES, "Over",
                            f"{series} total {line}: both YES = Over {line}.")
        if not hits:
            return _reject(f"no Kalshi sub-market at total line {line}")
        return _flag("multiple total sub-markets at line")

    if ktype == "map_winner":
        qm = _Q_MAP.match(question)
        if not qm:
            return _flag("cannot parse map/game question")
        pname, mapno = qm.group(1), qm.group(2)
        k_no = _MAP_NO.search(cand["kalshi_event"]["title"])
        s_no = re.search(r"(?:map|game)(\d+)", slug)
        if not k_no or not s_no or not (k_no.group(1) == s_no.group(1) == mapno):
            return _reject("map/game number mismatch between Kalshi event "
                           "and Poly slug")
        strong = [m for m in team_subs if names_match(pname, m["title"])]
        if len(strong) != 1:
            return _reject(f"different event: map team '{pname}' matches no "
                           "Kalshi sub-market")
        return _pair(cand, series, f"map {mapno}", strong[0], team_subs,
                     tie_subs, pname)

    if ktype in ("player_hrr", "player_tb"):
        qm = _Q_PLAYER.match(question)
        if not qm or line is None:
            return _flag("cannot parse player-prop question")
        player, n = qm.group(1), int(qm.group(2))
        if n != int(float(line)):
            return _flag(f"threshold mismatch: question={n} line={line}")
        hits = [m for m in kms
                if (hm := _PLAYER_TITLE.match(m["title"]))
                and int(hm.group(2)) == n and names_match(player, hm.group(1))]
        if len(hits) == 1:
            stat = "H+R+RBI" if ktype == "player_hrr" else "total bases"
            return _approve(cand, hits[0]["ticker"], _YES, player,
                            f"{series}: both YES = {player} {n}+ ({stat}).")
        if not hits:
            return _reject(f"no Kalshi sub-market for {player} at {n}+")
        return _flag("multiple player sub-markets matched")

    return _flag(f"unhandled bet type: {ktype}")


def _verify_spread(cand, series, yes, question, team_subs, line) -> Decision:
    pname = yes.get("name") or ""
    if not pname or line is None:
        return _flag("spread missing Poly team or line")
    pline = float(line)
    qm_other = _Q_OTHER_TEAM.search(question)
    other_name = qm_other.group(1) if qm_other else ""

    subs = []
    for m in team_subs:
        sm = _SPREAD_TITLE.match(m["title"])
        if sm:
            alpha = re.match(r"[A-Z]+", m["ticker"].rsplit("-", 1)[-1])
            subs.append((m, sm.group(1), float(sm.group(2)),
                         alpha.group(0) if alpha else ""))

    # A negative line belongs to the Poly YES team's own sub-market
    # (yes = yes); a positive line is the complement of the opponent's
    # negative line at the same number (yes = no). Selection prefers the
    # team codes in the question tail ("in ATH vs AZ") when they align
    # with Kalshi ticker suffixes; otherwise graded name matching.
    target_is_yes = pline < 0
    want_line = abs(pline)
    qm_codes = _Q_CODES.search(question)
    codes_ok = bool(qm_codes) and {
        qm_codes.group(1).upper(), qm_codes.group(2).upper(),
    } <= {a for _, _, _, a in subs} | {""}

    if codes_ok:
        target_code = (qm_codes.group(1) if target_is_yes
                       else qm_codes.group(2)).upper()
        hits = [m for m, _, ln, a in subs
                if ln == want_line and a == target_code]
    else:
        target = pname if target_is_yes else other_name
        nontarget = other_name if target_is_yes else pname
        hits = [m for m, t, ln, _ in subs
                if ln == want_line
                and team_score(t, target) > team_score(t, nontarget)]

    if len(hits) == 1:
        if target_is_yes:
            return _approve(cand, hits[0]["ticker"], _YES, pname,
                            f"{series} {pline}: Kalshi YES = "
                            f"{hits[0]['title']}, Poly YES = {pname} covers "
                            f"{pline}.")
        return _approve(cand, hits[0]["ticker"], _NO, pname,
                        f"{series} +{pline}: Poly YES = {pname} covers "
                        f"+{pline} = NO on Kalshi {hits[0]['title']}.")
    if not hits:
        side_name = pname if target_is_yes else "opponent"
        return _reject(f"no Kalshi sub-market at line -{want_line} "
                       f"for {side_name}")
    return _flag("spread pairing unclear")


# ---- persistence ----

def append_results(
    decisions: list[tuple[dict, Decision]],
    matches_path: Path = _MATCHES_PATH,
    rejected_path: Path = _REJECTED_PATH,
    flagged_path: Path = _FLAGGED_PATH,
) -> dict[str, int]:
    matches = json.loads(matches_path.read_text()) if matches_path.exists() else []
    rejected = json.loads(rejected_path.read_text()) if rejected_path.exists() else []
    known_ids = {m["id"] for m in matches}
    known_rejects = {(r["kalshi_event_ticker"], r["polymarket_slug"])
                     for r in rejected}

    flagged: list[dict] = []
    counts = {"approved": 0, "rejected": 0, "flagged": 0, "skipped": 0}
    for cand, d in decisions:
        if d.kind == "approve":
            fresh = [e for e in d.entries if e["id"] not in known_ids]
            if not fresh:
                counts["skipped"] += 1
                continue
            matches.extend(fresh)
            known_ids.update(e["id"] for e in fresh)
            counts["approved"] += len(fresh)
        elif d.kind == "reject":
            key = (cand["kalshi_event"]["event_ticker"],
                   cand["polymarket"]["slug"])
            if key in known_rejects:
                counts["skipped"] += 1
                continue
            rejected.append({
                "kalshi_event_ticker": key[0],
                "polymarket_slug": key[1],
                "reason": d.reason,
            })
            known_rejects.add(key)
            counts["rejected"] += 1
        else:
            flagged.append({
                "reason": d.reason,
                "kalshi_event_ticker": cand["kalshi_event"]["event_ticker"],
                "polymarket_slug": cand["polymarket"]["slug"],
            })
            counts["flagged"] += 1

    matches_path.write_text(json.dumps(matches, indent=2))
    rejected_path.write_text(json.dumps(rejected, indent=2))
    flagged_path.write_text(json.dumps(flagged, indent=2))
    return counts


# ---- CLI ----

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--yes-sides",
        help="path to pre-fetched fetch_poly_sides output (default: fetch)",
    )
    args = parser.parse_args()

    cands = json.loads(_CANDIDATES_PATH.read_text())
    if not cands:
        print("no candidates")
        return

    if args.yes_sides:
        sides_list = json.loads(Path(args.yes_sides).read_text())
    else:
        slugs = list({c["polymarket"]["slug"] for c in cands})
        print(f"Fetching YES sides for {len(slugs)} slugs...", flush=True)
        sides_list = asyncio.run(fetch_sides(slugs))
    sides = {s["slug"]: s for s in sides_list}

    decisions = [
        (c, verify_candidate(c, sides.get(c["polymarket"]["slug"], {"error": "no yes-side data"})))
        for c in cands
    ]
    counts = append_results(decisions)
    print(f"approved: {counts['approved']} entries | "
          f"rejected: {counts['rejected']} | flagged: {counts['flagged']} "
          f"(see {_FLAGGED_PATH}) | already known: {counts['skipped']}")


if __name__ == "__main__":
    main()
