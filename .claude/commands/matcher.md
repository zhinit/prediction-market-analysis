Find and verify cross-platform market matches between Kalshi and Polymarket US.

## Steps

1. Run the matcher script as a module from the repo root (it also creates `matches.json` / `rejected_matches.json` if missing and prunes matches whose `event_date` is past):
   ```
   uv run python -m db.arbitrage.match_markets
   ```
2. Read `db/arbitrage/candidates.json`. If empty or missing, report "no new candidates" and stop.
3. For each candidate, review against this checklist. Scope is sports only (project decision, 2026-07-21) — any league, any bet type. Reject non-sports candidates as out of scope; reject sports candidates only if they fail the checklist:
   - **Same event?** Do both sides refer to the same real-world event?
   - **Same date?** Check `strike_date` (Kalshi) vs slug/question date (Poly). Must match exactly.
   - **Same bet type?** Moneyline↔moneyline, spread↔spread, total↔total, prop↔prop, etc.
   - **Correct Kalshi sub-market / ticker?** Look at `kalshi_markets` — pick the ticker whose `yes_sub_title` matches the Polymarket YES side. For multi-outcome markets (e.g., "Person of the Year", Senate races), match each Poly market to the corresponding Kalshi sub-market by name.
   - **Direction**: follow the Direction section below — never inferred from slugs, home/away, or question wording alone.
4. For sports games with 2 Kalshi sub-markets (one per team) and 1 Poly market, create TWO match entries — one per team. The sub-market naming the Poly YES side (see Direction) gets `kalshi_yes_eq_poly_yes`; the other gets `kalshi_yes_eq_poly_no`. Each pair must have one of each direction — two identical directions on a pair is always a bug.
5. For each approved match, append to `db/arbitrage/matches.json`:
   ```json
   {
     "id": "<polymarket_slug>-<team_or_outcome_suffix>",
     "kalshi_ticker": "<kalshi_market_ticker>",
     "polymarket_slug": "<polymarket_slug>",
     "direction": "kalshi_yes_eq_poly_yes",
     "poly_yes": "Texas Rangers",
     "event_date": "2026-07-10",
     "notes": "MLB moneyline: Kalshi YES = Rangers, Poly YES = Rangers."
   }
   ```
   `event_date` is the date of the real-world event (the matched date from the checklist); the matcher script uses it to prune expired matches automatically.
6. For each rejected match, append to `db/arbitrage/rejected_matches.json` with a specific reason why it failed the checklist:
   ```json
   {
     "kalshi_event_ticker": "<event_ticker>",
     "polymarket_slug": "<slug>",
     "reason": "<specific reason: different event, date mismatch, etc.>"
   }
   ```

## What to reject

Only reject a candidate if it is out of scope or genuinely fails the checklist:
- Non-sports (out of scope — project scope is sports only)
- Different real-world events (false positive from similar titles)
- Date mismatch (must be exact)
- Bet type mismatch (moneyline matched to spread, etc.)
- Cannot determine direction with confidence

Do NOT reject based on:
- League (NPB, esports, WNBA, cricket are all valid)
- Bet type (F5, map winner, exact score, spread, total, props are all valid if both sides have the same type)
- Liquidity concerns (that's for analysis, not matching)

## Direction

Direction is the most dangerous part — poka-arb had a $68 bug from getting it wrong. One procedure, every sport, no shortcuts:

1. Fetch the Poly YES side: `uv run python -m db.arbitrage.fetch_poly_sides --from-candidates` (or pass specific slugs as arguments). The YES side — the outcome the orderbook quotes — is the `marketSides` entry with `"long": true`; its `team.name` names the outcome (`description` when there is no team object).
2. Read the Kalshi YES side from the sub-market ticker suffix and `yes_sub_title` (e.g., `-TEX` = YES means Texas).
3. Match the two by full name, accounting for name variants (e.g. "Facundo Acosta" = "Facundo Diaz Acosta"). Same outcome → `kalshi_yes_eq_poly_yes`; opposite → `kalshi_yes_eq_poly_no`.
   - Some markets (observed on esports, 2026-07-21) have no team object and the lookup returns `description: "Yes"` — there the YES outcome is the one the question asks ("Will All Gamers win Map 1 vs Dragon Ranger Gaming?" → YES = All Gamers), and that name is what goes in `poly_yes`.
4. Record the Poly YES-side name in the entry's `poly_yes` field exactly as `fetch_poly_sides` returned it.

Never infer the Poly YES side from anything else:

- Not from slug order or home/away (`team.ordering`). On 2026-07-21 all 54 live MLB moneylines had YES = away = first slug team, but the convention does not hold across sports — tennis and NPB were verified inconsistent on 2026-07-11. Treat the MLB pattern as coincidence, not a rule.
- Not from Kalshi ticker suffix vs Poly `team.abbreviation` string-equality. For MLB they happen to align (`SF` = `sf`); for tennis and NPB the Poly "abbreviation" is a slug code (`martop`, `trge`) that never equals the Kalshi suffix, and the platforms often list the two sides in opposite order.
- Not from the Poly `question` text alone when it is ambiguous ("Team A vs. Team B" without naming YES).

## Important

- For totals and spreads, the line must match exactly (Kalshi "Over 16.5" ≠ Poly 17.5) — the Poly line is in the candidate's `polymarket.line`; reject if no Kalshi sub-market has that line.
- Present each candidate clearly with both sides' details before making a judgment.
