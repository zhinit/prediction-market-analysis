Find and verify cross-platform market matches between Kalshi and Polymarket US.

## Steps

1. Run the matcher script as a module from the repo root:
   ```
   uv run python -m db.arbitrage.match_markets
   ```
2. Read `db/arbitrage/candidates.json`. If empty or missing, report "no new candidates" and stop.
3. For each candidate, review against this checklist. Approve matches from ALL categories — sports (any league, any bet type), politics, crypto, entertainment, weather, anything. Only reject if it fails the checklist:
   - **Same event?** Do both sides refer to the same real-world event?
   - **Same date?** Check `strike_date` (Kalshi) vs slug/question date (Poly). For date-bucketed markets (politics, crypto "when will X happen"), match the Kalshi sub-market whose date window aligns with the Poly market's date.
   - **Same bet type?** Moneyline↔moneyline, spread↔spread, total↔total, prop↔prop, etc.
   - **Correct Kalshi sub-market / ticker?** Look at `kalshi_markets` — pick the ticker whose `yes_sub_title` matches the Polymarket YES side. For multi-outcome markets (e.g., "Person of the Year", Senate races), match each Poly market to the corresponding Kalshi sub-market by name.
   - **Direction**: Read the Kalshi ticker suffix for the YES side (e.g., `-TEX` = YES means Texas). Read the Polymarket `question` field for the YES side. Do NOT infer from the slug — fetch the market detail from the Poly API if the question is ambiguous (check `marketSides` where `long: true`). If both YES sides = same outcome → `kalshi_yes_eq_poly_yes`. If opposite → `kalshi_yes_eq_poly_no`. Record both sides in `notes`.
   - **Not a duplicate?** Check against existing entries in `db/arbitrage/matches.json`.
4. For sports games with 2 Kalshi sub-markets (one per team) and 1 Poly market, create TWO match entries — one per team. The away team (Poly YES side) gets `kalshi_yes_eq_poly_yes`, the home team gets `kalshi_yes_eq_poly_no`.
5. For each approved match, append to `db/arbitrage/matches.json`:
   ```json
   {
     "id": "<polymarket_slug>-<team_or_outcome_suffix>",
     "kalshi_ticker": "<kalshi_market_ticker>",
     "polymarket_slug": "<polymarket_slug>",
     "direction": "kalshi_yes_eq_poly_yes",
     "notes": "MLB moneyline: Kalshi YES = Rangers, Poly YES = Rangers."
   }
   ```
6. For each rejected match, append to `db/arbitrage/rejected_matches.json` with a specific reason why it failed the checklist:
   ```json
   {
     "kalshi_event_ticker": "<event_ticker>",
     "polymarket_slug": "<slug>",
     "reason": "<specific reason: different event, date mismatch, etc.>"
   }
   ```
7. Remove expired matches from `db/arbitrage/matches.json` — any match whose event date (extracted from the Kalshi ticker or Polymarket slug) is in the past.
8. Create `db/arbitrage/matches.json` and `db/arbitrage/rejected_matches.json` as empty arrays `[]` if they don't exist yet.

## What to reject

Only reject a candidate if it genuinely fails the checklist:
- Different real-world events (false positive from similar titles)
- Date mismatch (sports: must be exact; non-sports: date window must align)
- Bet type mismatch (moneyline matched to spread, etc.)
- Cannot determine direction with confidence
- Duplicate of an existing match

Do NOT reject based on:
- Category (politics, crypto, entertainment are all valid)
- League (NPB, esports, WNBA, cricket are all valid)
- Bet type (F5, spread, total, props are all valid if both sides have the same type)
- Liquidity concerns (that's for analysis, not matching)

## Important

- Direction is the most dangerous part — poka-arb had a $68 bug from getting it wrong. Always verify by reading the actual ticker suffix and question text.
- When the Poly question is ambiguous (e.g., "Team A vs. Team B" without saying who is YES), fetch the market detail from the API to check `marketSides` where `long: true`. Endpoint (no auth needed): `GET https://gateway.polymarket.us/v1/market/slug/{slug}` — the YES side is `response["market"]["marketSides"]` entry with `"long": true`; its `team.name` / `team.abbreviation` names the outcome. Batch these lookups with a throwaway script rather than one curl per market.
- Do NOT determine direction by comparing Kalshi ticker suffixes to Poly `team.abbreviation` string-equality. For MLB they happen to align (`SF` = `sf`), but for tennis and NPB the Poly "abbreviation" is a slug code (`martop`, `trge`) that never equals the Kalshi suffix, and Kalshi/Poly often list the two sides in opposite order. Match by full name (`team.name` vs the Kalshi sub-market title), accounting for name variants (e.g. "Facundo Acosta" = "Facundo Diaz Acosta").
- For totals and spreads, the line must match exactly (Kalshi "Over 16.5" ≠ Poly 17.5) — reject if no Kalshi sub-market has the Poly line.
- Present each candidate clearly with both sides' details before making a judgment.
