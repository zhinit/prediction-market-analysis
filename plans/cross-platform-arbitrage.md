# Cross-Platform Arbitrage Analysis: Kalshi vs Polymarket US

## Context

The poka-arb project built an arbitrage bot between Kalshi and Polymarket US and found structural 2-4% spreads on sports markets — but they're uncapturable at retail latency due to Polymarket's taker delay. This analysis takes that finding and turns it into a clean, presentable portfolio piece: pull the data from scratch, quantify the opportunities, and show what the arbitrage landscape actually looks like.

Two write-ups already exist in this project (MLB data pull, MLB calibration). This one follows the same format and conventions.

## Open question

**Polymarket US historical trades**: We need to confirm whether Poly US has a public historical trades endpoint or Time & Sales CSVs. poka-arb references Time & Sales CSVs at `polymarketexchange.com/time-and-sales.html`. Step 1 resolves this before any code is written. If no historical trade data is available, we pivot to live BBO polling as the primary data source (and the timeline extends by however many days we collect).

---

## Steps

### Step 1: Research — confirm Poly US trade data access
- `/research` the Polymarket US API for historical trade data (Time & Sales CSVs, trades endpoint, or other)
- `/research` the Polymarket US market object schema (what fields come back from `/v1/markets`)
- Document findings in wiki pages
- **Output**: confirmed data access path, documented schemas
- **Depends on**: nothing

### Step 2: Pull market/event metadata from both platforms
- Create `db/scripts/pull_kalshi_sports.py` — pull all sports events and markets from Kalshi (not just MLB)
- Create `db/scripts/pull_poly_us_sports.py` — pull all sports events and markets from Polymarket US
- Follow existing patterns: httpx async, tenacity retries, pydantic models, polars→DuckDB, TEXT storage + typed views, resume bookkeeping
- **New tables**: `kalshi_sports_events`, `kalshi_sports_markets`, `poly_events`, `poly_markets` (plus typed views and pull-tracking tables)
- **Output**: metadata for all sports markets on both platforms in DuckDB
- **Depends on**: Step 1 (schemas)

### Step 3: Build cross-platform market matching
- Create `db/scripts/build_cross_platform_map.py`
- Rebuild matching from scratch (informed by poka-arb, not copied):
  1. Pre-filters: sport type, bet type (moneyline only initially), date overlap
  2. Try deterministic join first: Poly markets carry `gameId`/`sportradarGameId` — if these map to known IDs, skip fuzzy matching
  3. Fuzzy fallback: Jaccard similarity on normalized titles (threshold 0.4)
  4. Direction alignment: determine whether Kalshi YES = Poly YES or Poly NO, store as boolean
- **New table**: `cross_platform_matches` (kalshi_event_ticker, poly_slug, sport, direction, match_score, match_method)
- **Output**: matched market pairs with direction alignment
- **Depends on**: Step 2

### Step 4: Pull historical trades for matched markets
- **Kalshi side**: Extend or adapt existing trade pull logic to cover all sports series (not just `KXMLBGAME`). MLB trades already exist (25.7M) — reuse them, only pull new series.
- **Poly side**: Create `db/scripts/pull_poly_us_trades.py` using whatever data source Step 1 confirms (Time & Sales CSVs, trades endpoint, etc.)
- **New tables**: `poly_trades` (+ typed view), `poly_trade_pulls` (resume bookkeeping). Kalshi trades may go into existing `trades` table or a new `kalshi_sports_trades` table depending on schema compatibility.
- **Output**: trade-level price data for both sides of every matched market
- **Depends on**: Step 3

### Step 5: Build analysis-ready tables
- Create `db/scripts/prepare_arb_analysis.py`
- Join trades from both platforms on match table
- Align direction (flip Poly price to `1 - price` when Kalshi YES = Poly NO)
- Compute: raw spread, fee-adjusted spread (Kalshi taker 7%, Poly taker 5%), spread as % of price
- Time-bucket into snapshots (e.g. 5-minute intervals) for time-series analysis
- **New tables**: `arb_price_series`, `arb_snapshots`, `arb_build_info`
- **Output**: analysis-ready tables the notebook queries directly
- **Depends on**: Step 4

### Step 6: Analysis notebook
- Create `analysis/cross_platform_arb.ipynb`
- Sections:
  1. Universe: how many markets matched, by sport, date range
  2. Spread distribution: histogram of raw and fee-adjusted spreads
  3. Frequency: how often do spreads exceed X%
  4. Persistence: how long do above-threshold spreads last
  5. Patterns: by sport, time of day, market liquidity, days before event
  6. Case studies: largest spreads, what happened
  7. Conclusion: opportunities exist but uncapturable (Poly taker delay)
- **Output**: completed notebook with charts
- **Depends on**: Step 5

### Step 7: Data quality tests
- Create `db/tests/test_arb_data_quality.py`
- Same pattern as existing tests: module-scoped DuckDB fixture, skip if tables missing
- Test: tables/views exist, not empty, referential integrity, typed views cast cleanly, prices in (0,1), timestamps not from future, every match has trades on both sides
- **Output**: passing test suite
- **Depends on**: Step 5

### Step 8: Write-up
- Create `write_ups/cross-platform-arbitrage-kalshi-polymarket.md`
- YAML frontmatter, same blog-post format as existing write-ups
- Three parts: (1) data pull & matching methodology, (2) what the analysis found, (3) why it's uncapturable in practice
- **Output**: portfolio-ready write-up
- **Depends on**: Step 6

### Step 9 (optional): Live BBO polling
- Create `db/scripts/poll_live_bbo.py`
- Poll BBO/orderbook endpoints on both platforms every 30-60s for active matched markets over 3-5 days
- **New table**: `live_bbo_snapshots` (timestamp, kalshi_ticker, poly_slug, kalshi_bid, kalshi_ask, poly_bid, poly_ask)
- Richer than trade data since it gives bid/ask, not just last trade
- Can run independently once Step 3 is done
- **Depends on**: Step 3

---

## Conventions
- All scripts in `db/scripts/`, tests in `db/tests/`, analysis in `analysis/`, write-ups in `write_ups/`
- Python with `uv` only — `uv run`, `uv add`
- Self-contained scripts, no shared utility modules (matches existing pattern)
- DuckDB TEXT storage + typed views
- Pydantic for API response validation
- httpx async + tenacity retries

## Verification
- `uv run pytest db/tests/` passes after each step that adds tables
- Notebook runs end-to-end: `uv run jupyter nbconvert --execute analysis/cross_platform_arb.ipynb`
- Manual review of match quality (print unmatched events, spot-check matches)
