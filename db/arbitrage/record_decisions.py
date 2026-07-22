"""Record /matcher verification decisions into the match files.

The /matcher review writes its decisions — data, not code — to a JSON
file; this tool validates them, appends them to matches.json /
rejected_matches.json (skipping anything already recorded, so re-runs and
per-batch runs are safe), enforces the match-file invariants, and deletes
the consumed decisions file. Nothing here judges a candidate: approvals
and rejections are made by reading the candidates
(see .claude/commands/matcher.md).

Usage:
    uv run python -m db.arbitrage.record_decisions db/arbitrage/decisions.json

Decisions file schema:
{
  "approve": [<match entry — schema in matcher.md>, ...],
  "reject": [{"kalshi_event_ticker": "...", "polymarket_slug": "...",
              "reason": "..."}, ...]
}
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

_MATCHES_PATH = Path("db/arbitrage/matches.json")
_REJECTED_PATH = Path("db/arbitrage/rejected_matches.json")

_DIRECTIONS = frozenset({"kalshi_yes_eq_poly_yes", "kalshi_yes_eq_poly_no"})

_ENTRY_FIELDS = ("id", "kalshi_ticker", "polymarket_slug", "direction",
                 "poly_yes", "notes")
_REJECT_FIELDS = ("kalshi_event_ticker", "polymarket_slug", "reason")


def validate_entry(e: dict, i: int) -> None:
    for f in _ENTRY_FIELDS:
        if not e.get(f):
            raise SystemExit(f"approve[{i}]: missing or empty '{f}'")
    if e["direction"] not in _DIRECTIONS:
        raise SystemExit(f"approve[{i}]: bad direction '{e['direction']}'")
    if not e.get("expires") and not e.get("event_date"):
        raise SystemExit(
            f"approve[{i}] ({e['id']}): needs 'expires' or 'event_date' "
            "(expiry pruning has nothing to key on)")


def validate_reject(r: dict, i: int) -> None:
    for f in _REJECT_FIELDS:
        if not r.get(f):
            raise SystemExit(f"reject[{i}]: missing or empty '{f}'")


def check_invariants(matches: list[dict]) -> None:
    ids = [m["id"] for m in matches]
    if len(ids) != len(set(ids)):
        dupes = {i for i in ids if ids.count(i) > 1}
        raise SystemExit(f"duplicate match ids: {sorted(dupes)}")
    # One Kalshi market quoting two different Poly markets means at most
    # one pairing is the same real-world event (observed: the men's and
    # women's Hundred both matched to one Kalshi event, 2026-07-23).
    by_ticker: dict[str, set[str]] = defaultdict(set)
    for m in matches:
        by_ticker[m["kalshi_ticker"]].add(m["polymarket_slug"])
    conflicts = {t: sorted(s) for t, s in by_ticker.items() if len(s) > 1}
    if conflicts:
        raise SystemExit(
            "one Kalshi market matched to several Poly markets — at most "
            f"one pairing can be correct, re-read those candidates: "
            f"{conflicts}")


def record(
    decisions: dict,
    matches_path: Path = _MATCHES_PATH,
    rejected_path: Path = _REJECTED_PATH,
) -> dict[str, int]:
    approvals = decisions.get("approve", [])
    rejects = decisions.get("reject", [])
    for i, e in enumerate(approvals):
        validate_entry(e, i)
    for i, r in enumerate(rejects):
        validate_reject(r, i)

    matches = (json.loads(matches_path.read_text())
               if matches_path.exists() else [])
    rejected = (json.loads(rejected_path.read_text())
                if rejected_path.exists() else [])
    known_ids = {m["id"] for m in matches}
    known_rejects = {(r["kalshi_event_ticker"], r["polymarket_slug"])
                     for r in rejected}

    counts = {"approved": 0, "rejected": 0, "skipped": 0}
    for e in approvals:
        if e["id"] in known_ids:
            counts["skipped"] += 1
            continue
        matches.append(e)
        known_ids.add(e["id"])
        counts["approved"] += 1
    for r in rejects:
        key = (r["kalshi_event_ticker"], r["polymarket_slug"])
        if key in known_rejects:
            counts["skipped"] += 1
            continue
        rejected.append({f: r[f] for f in _REJECT_FIELDS})
        known_rejects.add(key)
        counts["rejected"] += 1

    check_invariants(matches)  # validate the merged result before any write

    matches_path.write_text(json.dumps(matches, indent=2))
    rejected_path.write_text(json.dumps(rejected, indent=2))
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decisions", help="path to the decisions JSON file")
    args = parser.parse_args()

    path = Path(args.decisions)
    decisions = json.loads(path.read_text())
    counts = record(decisions)
    path.unlink()  # consumed; the repo keeps no transient decision files
    print(f"approved: {counts['approved']} | rejected: {counts['rejected']} "
          f"| already recorded: {counts['skipped']} "
          f"(consumed {path})")


if __name__ == "__main__":
    main()
