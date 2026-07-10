# Data Collection Specs

Two commands that together produce a continuously growing orderbook dataset
for cross-platform arbitrage analysis between Kalshi and Polymarket US.

---

## `/matcher`

Finds and verifies market matches across platforms.

### Script: `db/arbitrage/match_markets.py`

1. **Fetch active events** from both platforms via REST API.
   - Kalshi: fetch all open **events** (not individual markets — ~2K events vs
     ~455K markets). Fetch series list first for category metadata.
   - Polymarket US: fetch all active markets with `endDateMin=today`
     (without this filter the API returns stale Oct 2025–Jan 2026 data).
2. **Group markets.**
   - Kalshi: attach category from series, extract sport sub-type from series
     title.
   - Polymarket: group by `gameId`. Multiple markets exist per game
     (moneyline, spread, total) — pick moneyline as representative to avoid
     duplicate candidates.
3. **Pre-filter** with four structural checks before any text comparison:
   - **Category compatibility**: normalized categories must match
     (sports↔sports, politics↔politics, etc.).
   - **Sport sub-type**: when both sides have a sport, they must match
     (MLB↔MLB, not MLB↔NBA).
   - **Bet type**: moneyline↔moneyline, spread↔spread, etc. Incompatible
     types rejected.
   - **Date overlap**: exact date match for sports; permissive when one side
     lacks a date (politics, crypto).
4. **Jaccard similarity** on normalized title tokens (lowercase, strip
   punctuation, remove stop words), threshold 0.3. Deduplicate by Polymarket
   slug (highest score wins).
5. **Exclude** candidates already in `matches.json` or `rejected_matches.json`.
6. **Fetch Kalshi sub-markets** for each candidate's event to identify which
   ticker suffix corresponds to which team/outcome.
7. **Output** `candidates.json`.

### Claude command: `.claude/commands/matcher.md`

1. Runs `match_markets.py`.
2. Reviews each candidate against a checklist:
   - Same event?
   - Same date?
   - Same bet type?
   - Correct Kalshi sub-market / ticker?
   - Correct direction? (see direction rules below)
   - Not a duplicate of an existing match?
3. Approved matches → appended to `matches.json`.
   Rejected matches → appended to `rejected_matches.json` with reason.
4. Runs expired-match cleanup: removes matches whose event date has passed.

### Direction rules

Direction is the most dangerous part of matching — poka-arb had a $68 bug
from getting it wrong on esports markets.

To determine direction:
- **Kalshi YES side**: read the ticker suffix (e.g., `-TEX` = YES means Texas).
- **Polymarket YES side**: read the `question` field text. Do NOT infer from
  the slug — slug ordering does not reliably indicate YES side.

If both YES sides = same outcome: `kalshi_yes_eq_poly_yes`.
If opposite: `kalshi_yes_eq_poly_no`.

Record both teams' YES sides in `notes` for auditability.

### Output: `matches.json`

```json
[
  {
    "id": "<polymarket_slug>",
    "kalshi_ticker": "<kalshi_market_ticker>",
    "polymarket_slug": "<polymarket_slug>",
    "direction": "kalshi_yes_eq_poly_yes",
    "notes": "MLB moneyline: Kalshi YES = Rangers, Poly YES = Rangers."
  }
]
```

`rejected_matches.json`:

```json
[
  {
    "kalshi_event_ticker": "<event_ticker>",
    "polymarket_slug": "<slug>",
    "reason": "Different cities"
  }
]
```

---

## `/collect-arb-data`

Collects live orderbook snapshots from both platforms for all matched markets.

### Script: `db/arbitrage/collect_orderbooks.py`

1. **Load** `matches.json` to get the list of market IDs to subscribe to.
2. **Connect** to both websockets:
   - Kalshi: `orderbook_delta` channel (not `ticker` — that's last-trade
     only). RSA-PSS auth. Sends an initial snapshot then incremental deltas
     with sequence numbers. Track sequences and re-snapshot on gaps.
   - Polymarket US: `SUBSCRIPTION_TYPE_MARKET_DATA`, Ed25519 auth. Sends
     full orderbook snapshot on every update (~1–1.5 msg/sec on active
     markets). Must send text frames, not binary.
3. **Platform-specific parsing**:
   - Kalshi: apply deltas to local orderbook state. Convert NO bids to YES
     asks (YES ask price = 1 − NO bid price).
   - Polymarket: field is `offers`, not `asks`. Prices are nested:
     `{"px": {"value": "0.423", "currency": "USD"}}`.
4. **On each orderbook update**, record a snapshot:
   - timestamp, platform, market_id, match_id, best_bid, best_ask,
     bid_size, ask_size, mid_price.
5. **Write** snapshots to DuckDB table `orderbook_snapshots` in `db/pma.db`,
   batched.
6. **Reconnect** with exponential backoff on disconnect.
7. **Resumable** — appends to the same table. Safe to stop and restart.

### Claude command: `.claude/commands/collect-arb-data.md`

Runs `collect_orderbooks.py` and monitors output for connection status.

### Table: `orderbook_snapshots`

| Column     | Type | Notes |
|------------|------|-------|
| timestamp  | TEXT |       |
| platform   | TEXT | `kalshi` or `polymarket` |
| market_id  | TEXT | ticker (Kalshi) or slug (Poly) |
| match_id   | TEXT | foreign key to matches.json `id` |
| best_bid   | TEXT |       |
| best_ask   | TEXT |       |
| bid_size   | TEXT |       |
| ask_size   | TEXT |       |
| mid_price  | TEXT |       |

Plus a typed view casting TEXT columns to appropriate numeric types.

---

## Daily workflow

1. Run `/matcher` to pick up new markets and review candidates.
2. Run `/collect-arb-data` and let it run for the day.
3. Repeat.
