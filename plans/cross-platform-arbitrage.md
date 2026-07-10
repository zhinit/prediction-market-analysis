# Cross-Platform Arbitrage Analysis: Kalshi vs Polymarket US

## Context

The poka-arb project built an arbitrage bot between Kalshi and Polymarket US and found structural 2-4% spreads on sports markets — but they're uncapturable at retail latency due to Polymarket's taker delay. This analysis takes that finding and turns it into a clean, presentable portfolio piece: collect real-time orderbook data, quantify the opportunities, and show what the arbitrage landscape actually looks like.

Two write-ups already exist in this project (MLB data pull, MLB calibration). This one follows the same format and conventions.

## Key decision: live data, not historical

Historical market metadata (titles, settlement prices) is useful for matching but not for measuring arbitrage. A single `last_price_dollars` snapshot per market tells you nothing about how spreads evolve. Real arbitrage analysis needs orderbook data at high frequency — best bid/ask on both platforms at the same moment, many times per day, over multiple days.

Both platforms offer websocket streams:
- **Kalshi**: `ticker` channel (public), streams orderbook updates. RSA-PSS auth at connection time. Up to 500K subscriptions. (wiki: [[kalshi-api-websocket]])
- **Poly US**: `SUBSCRIPTION_TYPE_MARKET_DATA` streams full orderbook snapshots on every update (~1-1.5 msg/sec on active markets). Ed25519 auth. Max 100 markets per subscription. (poka-arb wiki: polymarket-us-websocket)

---

## Status (as of 2026-07-09)

### Completed
- **Research**: Poly US API schemas documented in wiki. Websocket capabilities documented in poka-arb wiki.
- **Event metadata pulled**: Kalshi 455K events (all categories) in `kalshi_events`. Poly US 28K events in `poly_events`.
- **Table rename**: `kalshi_sports_events` → `kalshi_events`, `kalshi_sports_markets` → `kalshi_markets`. Old scripts deleted.
- **Existing matcher**: `build_cross_platform_map.py` does sports-specific team-name matching (3,978 matches). Will be replaced by Jaccard matcher.

### Next
Step 1 below.

---

## Steps

### Step 1: Match active markets across platforms

Modeled on poka-arb's `strategies/arbitrage/matcher/` and its `/arb_match` command.

**Script**: `db/scripts/match_markets.py`
- Fetch all **open/active** events from both platforms via REST (no need for the full historical catalog)
- Pre-filter by normalized category (sports↔sports, politics↔politics, etc.)
- Jaccard similarity on normalized titles, threshold 0.3 (poka-arb uses 0.4)
- Additional filters: date overlap, sport compatibility, bet type compatibility
- Output `candidates.json` for LLM review
- Skip candidates already in `matches.json` or `rejected_matches.json`

**Command**: `.claude/commands/arb_match.md` — runs the matcher, presents candidates for review with direction checklist, writes approved matches to `matches.json`

**Direction alignment** (critical — poka-arb had a $68 bug from getting this wrong):
- For each candidate, determine which team/outcome Kalshi YES represents vs Poly YES
- Set `kalshi_yes_eq_poly_yes` or `kalshi_yes_eq_poly_no`
- Both teams' YES sides recorded in notes for auditability

**Output**: `matches.json` with confirmed match pairs + direction

### Step 2: Collect live orderbook data via websockets

**Script**: `db/scripts/collect_orderbooks.py`
- Connect to both Kalshi and Poly US websockets
- Subscribe to all matched markets from `matches.json`
- On each orderbook update, save a snapshot: timestamp, market ID, best bid, best ask, bid size, ask size, mid price
- Write to DuckDB table `orderbook_snapshots` in batches
- Handle reconnection with exponential backoff
- Log connection status so you can verify it's running

**Auth**: API keys for both platforms (already set up in poka-arb, move to this project)

**Table**: `orderbook_snapshots`
| Column | Type |
|--------|------|
| timestamp | TEXT |
| platform | TEXT |
| market_id | TEXT |
| best_bid | TEXT |
| best_ask | TEXT |
| bid_size | TEXT |
| ask_size | TEXT |
| mid_price | TEXT |

Plus typed view.

**Run for 3-7 days**. Kick off each morning, let it run all day. Resumable — appends to the same table.

### Step 3: Build analysis-ready tables

**Script**: `db/scripts/prepare_arb_analysis.py`
- Join orderbook snapshots from both platforms on match table + closest timestamp
- Align direction (flip Poly price to `1 - price` when `kalshi_yes_eq_poly_no`)
- Compute: raw spread, fee-adjusted spread (Kalshi taker fee, Poly taker fee per wiki), spread as % of mid
- **Output**: `arb_spreads` table with paired snapshots and computed spreads

### Step 4: Analysis notebook

**Notebook**: `analysis/cross_platform_arb.ipynb`

Sections:
1. **Universe**: how many markets matched, by category, sport
2. **Spread distribution**: histogram of raw and fee-adjusted spreads
3. **Frequency**: how often do spreads exceed X% (e.g., 1%, 2%, 5%)
4. **Persistence**: when a spread opens, how long does it last before closing
5. **Patterns**: by category, time of day, market liquidity, days before event
6. **Case studies**: largest/most persistent spreads, what happened
7. **Conclusion**: do capturable opportunities exist after fees and latency

### Step 5: Data quality tests

**Tests**: `db/tests/test_arb_data_quality.py`
- Every snapshot has valid bid/ask (bid < ask, both in [0, 1])
- Every snapshot market_id maps to a match in matches.json
- No timestamp gaps longer than expected (flag collection outages)
- Paired snapshots have consistent direction alignment

### Step 6: Write-up

**File**: `write_ups/cross-platform-arbitrage-kalshi-polymarket.md`
- YAML frontmatter, same blog-post format as existing write-ups
- Portfolio-ready

---

## Daily workflow

1. Run `/arb_match` to pick up any new markets and review candidates
2. Start `uv run python db/scripts/collect_orderbooks.py` and let it run
3. After 3-7 days of collection, run Steps 3-6

---

## Conventions
- All scripts in `db/scripts/`, tests in `db/tests/`, analysis in `analysis/`, write-ups in `write_ups/`
- Python with `uv` only — `uv run`, `uv add`
- Self-contained scripts, no shared utility modules (matches existing pattern)
- DuckDB TEXT storage + typed views
- Pydantic for API response validation
- httpx async + tenacity retries for REST; websockets library for streaming

## Auth requirements
- **Kalshi**: RSA-PSS key pair (same as poka-arb). Needed for websocket connection.
- **Poly US**: Ed25519 API key (same as poka-arb). Needed for websocket connection.
- Keys stored outside repo (same pattern as poka-arb `keys/` directory).

## Verification
- `uv run pytest db/tests/` passes after each step
- Notebook runs end-to-end: `uv run jupyter nbconvert --execute analysis/cross_platform_arb.ipynb`
- Manual review of match quality via `/arb_match` command
