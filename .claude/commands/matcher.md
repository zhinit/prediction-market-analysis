Find and verify cross-platform market matches between Kalshi and Polymarket US.

## Steps

1. Run the matcher script:
   ```
   uv run python db/scripts/match_markets.py
   ```
2. Read `db/data/candidates.json`. If empty or missing, report "no new candidates" and stop.
3. For each candidate, review against this checklist. Approve matches from ALL categories — sports (any league, any bet type), politics, crypto, entertainment, weather, anything. Only reject if it fails the checklist:
   - **Same event?** Do both sides refer to the same real-world event?
   - **Same date?** Check `strike_date` (Kalshi) vs slug/question date (Poly). For date-bucketed markets (politics, crypto "when will X happen"), match the Kalshi sub-market whose date window aligns with the Poly market's date.
   - **Same bet type?** Moneyline↔moneyline, spread↔spread, total↔total, prop↔prop, etc.
   - **Correct Kalshi sub-market / ticker?** Look at `kalshi_markets` — pick the ticker whose `yes_sub_title` matches the Polymarket YES side. For multi-outcome markets (e.g., "Person of the Year", Senate races), match each Poly market to the corresponding Kalshi sub-market by name.
   - **Direction**: Read the Kalshi ticker suffix for the YES side (e.g., `-TEX` = YES means Texas). Read the Polymarket `question` field for the YES side. Do NOT infer from the slug — fetch the market detail from the Poly API if the question is ambiguous (check `marketSides` where `long: true`). If both YES sides = same outcome → `kalshi_yes_eq_poly_yes`. If opposite → `kalshi_yes_eq_poly_no`. Record both sides in `notes`.
   - **Not a duplicate?** Check against existing entries in `db/data/matches.json`.
4. For sports games with 2 Kalshi sub-markets (one per team) and 1 Poly market, create TWO match entries — one per team. The away team (Poly YES side) gets `kalshi_yes_eq_poly_yes`, the home team gets `kalshi_yes_eq_poly_no`.
5. For each approved match, append to `db/data/matches.json`:
   ```json
   {
     "id": "<polymarket_slug>-<team_or_outcome_suffix>",
     "kalshi_ticker": "<kalshi_market_ticker>",
     "polymarket_slug": "<polymarket_slug>",
     "direction": "kalshi_yes_eq_poly_yes",
     "notes": "MLB moneyline: Kalshi YES = Rangers, Poly YES = Rangers."
   }
   ```
6. For each rejected match, append to `db/data/rejected_matches.json` with a specific reason why it failed the checklist:
   ```json
   {
     "kalshi_event_ticker": "<event_ticker>",
     "polymarket_slug": "<slug>",
     "reason": "<specific reason: different event, date mismatch, etc.>"
   }
   ```
7. Remove expired matches from `db/data/matches.json` — any match whose event date (extracted from the Kalshi ticker or Polymarket slug) is in the past.
8. Create `db/data/matches.json` and `db/data/rejected_matches.json` as empty arrays `[]` if they don't exist yet.

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
- When the Poly question is ambiguous (e.g., "Team A vs. Team B" without saying who is YES), fetch the market detail from the API to check `marketSides` where `long: true`.
- Present each candidate clearly with both sides' details before making a judgment.
