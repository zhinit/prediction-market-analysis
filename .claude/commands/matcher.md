Find and verify cross-platform market matches between Kalshi and Polymarket US.

Matching is two stages: a mechanical candidate generator, then YOUR
verification pass. You are the verifier — every approval is your judgment,
made by READING the settlement texts both platforms publish. Fail-safe
rule: anything you cannot decide with confidence is rejected with a
reason, never approved.

NEVER write a script that decides approvals or rejections — no per-family
rules, no keyword matching, no regex classification. Rule-based
verification was tried and retired (2026-07-22, see
docs/market-matching.md): it silently approved a CS2 event against a
Valorant market and confused the men's and women's Hundred. Your output
is data — a decisions file — recorded by the committed
`record_decisions` tool. Do not write any other script. If you notice
yourself writing `if`/regex logic over candidate fields, stop: that is
the deleted verifier being reinvented.

## Steps

1. Run the candidate generator as a module from the repo root (it also
   creates `matches.json` / `rejected_matches.json` if missing and moves
   expired matches to `matches_archive.json`):
   ```
   uv run python -m db.arbitrage.match_markets
   ```
2. Read `db/arbitrage/candidates.json`. If empty or missing, report
   "no new candidates" and stop.
3. Verify every candidate against the checklist below — by reading, in
   batches. Group candidates that share one game (a spread event with
   many lines shares one pair of settlement texts): decide same-event
   once per game, then pick each sub-market and direction. Each candidate
   carries the evidence inline:
   - `kalshi_event.title`, `strike_date`; per sub-market: `title`,
     `rules` (Kalshi's settlement rules text), `expires`
   - `polymarket.question`, `description` (Poly's settlement text),
     `line`, `game_start_time`
   - `polymarket.yes_side` — the mechanically fetched Poly YES side
     (the `marketSides` entry with `long: true`)
4. Write your decisions for the batch to `db/arbitrage/decisions.json`:
   ```json
   {
     "approve": [<match entry — schema below>, ...],
     "reject": [<rejection — schema below>, ...]
   }
   ```
   Then record them:
   ```
   uv run python -m db.arbitrage.record_decisions db/arbitrage/decisions.json
   ```
   The tool validates the schemas, appends (skipping anything already
   recorded, so one file per batch is fine), enforces the match-file
   invariants, and deletes the consumed decisions file. If it exits with
   "one Kalshi market matched to several Poly markets", at most one of
   those pairings is the same real-world event — re-read those
   candidates' settlement texts and keep at most one.
5. Repeat 3–4 until every candidate is decided, then report the totals.

## Checklist

Scope is sports only (project decision, 2026-07-21) — any league, any bet
type. Reject non-sports candidates as out of scope; reject sports
candidates only if they fail the checklist:

- **Same event? Read the settlement texts, not just the titles.** The
  Kalshi `rules` and the Poly `description` must describe the same
  real-world event: same competition, same gender ("The Hundred" and
  "The Hundred Women" are different events with identical team names —
  observed wrong match 2026-07-23), same opponent, and the same start
  time when both texts state one. Titles and questions alone are not
  enough: right-team-wrong-game candidates score well on titles.
- **Same date?** `strike_date` (Kalshi) vs slug/question date (Poly).
  Must match exactly.
- **Same bet type?** Moneyline↔moneyline, spread↔spread, total↔total,
  first-5-innings↔F5, map winner↔map winner, prop↔prop. The Kalshi
  `rules` text states the bet type precisely.
- **Exact line** for spreads and totals: the Poly line is in
  `polymarket.line`; the Kalshi line is in the sub-market `title` and
  `rules`. Kalshi "Over 16.5" ≠ Poly 17.5 — reject if no sub-market has
  the exact line.
- **Correct Kalshi sub-market?** Pick the ticker whose title/rules names
  the Poly YES outcome (and line, for spreads/totals).
- **Settlement terms equal?** If Kalshi settles on regulation time and
  the Poly description does not state regulation (or vice versa), the
  contracts are different — reject.
- **Direction**: follow the Direction section below — never inferred from
  slugs, home/away, or question wording alone.

For games with exactly 2 Kalshi sub-markets (one per team) and 1 Poly
market, create TWO match entries — one per team. The sub-market naming the
Poly YES side gets `kalshi_yes_eq_poly_yes`; the other gets
`kalshi_yes_eq_poly_no`. Each pair must have one of each direction — two
identical directions on a pair is always a bug. When a Tie/Draw
third-outcome sub-market exists, or the Poly market's `sport_type` is
`SPORTS_MARKET_TYPE_DRAWABLE_OUTCOME`, create only the YES-side entry:
the other team's sub-market is not the complement of the Poly market.

Approved match schema (`db/arbitrage/matches.json`):
```json
{
  "id": "<polymarket_slug>--<kalshi_ticker_suffix>",
  "kalshi_ticker": "<kalshi_market_ticker>",
  "polymarket_slug": "<polymarket_slug>",
  "direction": "kalshi_yes_eq_poly_yes",
  "poly_yes": "Texas Rangers",
  "event_date": "2026-07-10",
  "expires": "2026-07-11T03:00:00Z",
  "notes": "MLB moneyline: Kalshi YES = Rangers, Poly YES = Rangers."
}
```
`expires` is the sub-market's `expires` (Kalshi's
`expected_expiration_time`) and drives expiry pruning; `event_date` is the
event date from the slug and is the fallback when `expires` is absent.

Rejection schema (`db/arbitrage/rejected_matches.json`) — always include a
specific reason:
```json
{
  "kalshi_event_ticker": "<event_ticker>",
  "polymarket_slug": "<slug>",
  "reason": "<specific reason: different event, date mismatch, etc.>"
}
```
Rejected slugs are never re-scored (the generator treats them as known),
so a rejection is permanent — reject on evidence, not on missing evidence
you could fetch.

## What to reject

- Non-sports (out of scope)
- Different real-world events (competition, gender, opponent, or start
  time disagree between the two settlement texts)
- Date mismatch (must be exact)
- Bet type mismatch (moneyline matched to spread, etc.)
- Line mismatch (no Kalshi sub-market at the Poly line)
- Settlement terms differ (regulation time vs full match)
- `yes_side` is null or `yes_side_error` is present and re-fetching
  (`uv run python -m db.arbitrage.fetch_poly_sides <slug>`) still fails —
  reason "cannot determine direction"

Do NOT reject based on:
- League (NPB, esports, WNBA, cricket are all valid)
- Bet type (F5, map winner, exact score, spread, total, props are all
  valid if both sides have the same type)
- Liquidity concerns (that's for analysis, not matching)

## Direction

Direction is the most dangerous part — poka-arb had a $68 bug from getting
it wrong. One procedure, every sport, no shortcuts:

1. The Poly YES side is `polymarket.yes_side` in the candidate — fetched
   mechanically from the market detail endpoint (the `marketSides` entry
   with `"long": true`). Its `name` names the outcome (`description` when
   there is no team object). To re-fetch:
   `uv run python -m db.arbitrage.fetch_poly_sides <slug>`.
   - Some markets (observed on esports, 2026-07-21) have no team object
     and `description: "Yes"` — there the YES outcome is the one the
     question asks ("Will All Gamers win Map 1 vs Dragon Ranger Gaming?"
     → YES = All Gamers), and that name is what goes in `poly_yes`.
2. Read the Kalshi YES side from the sub-market ticker suffix and title
   (e.g., `-TEX` = YES means Texas).
3. Match the two by full name, accounting for name variants ("Facundo
   Acosta" = "Facundo Diaz Acosta" — but "M8" vs "M8 GC" is a DIFFERENT
   team, the Game Changers roster; when in doubt the settlement texts
   decide). Same outcome → `kalshi_yes_eq_poly_yes`; opposite →
   `kalshi_yes_eq_poly_no`.
4. Record the Poly YES-side name in `poly_yes` exactly as fetched.

Never infer the Poly YES side from anything else:

- Not from slug order or home/away (`team.ordering`). On 2026-07-21 all 54
  live MLB moneylines had YES = away = first slug team, but the convention
  does not hold across sports — tennis and NPB were verified inconsistent
  on 2026-07-11. Treat the MLB pattern as coincidence, not a rule.
- Not from Kalshi ticker suffix vs Poly `team.abbreviation`
  string-equality. For MLB they happen to align (`SF` = `sf`); for tennis
  and NPB the Poly "abbreviation" is a slug code (`martop`, `trge`) that
  never equals the Kalshi suffix, and the platforms often list the two
  sides in opposite order.
- Not from the Poly `question` text alone when it is ambiguous
  ("Team A vs. Team B" without naming YES).
