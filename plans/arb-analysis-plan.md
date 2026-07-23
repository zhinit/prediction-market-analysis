# Arbitrage Analysis Plan

Cross-platform arbitrage analysis between Kalshi and Polymarket US on MLB
game winner markets. The output is a write-up similar in style to the MLB
calibration analysis.

## Phase 1: Market Matcher ✓

Build the market matching logic:

1. Pull today's MLB schedule (MLB Stats API or equivalent).
2. Fetch active MLB game winner markets from Kalshi and Polymarket US REST
   APIs.
3. Match markets across platforms using a static team name normalization
   table and exact date match. No fuzzy matching needed for MLB game winners.
4. Output: a list of matched market pairs (Kalshi ticker + Polymarket slug
   per team per game).

Test: verify matches against a manual spot-check of both platforms. Confirm
the normalization table covers all 30 MLB teams on both platforms.

**Status:** Complete. Code in `db/arbitrage/`. Tested against live APIs on
2026-07-23: 5/5 games matched, all 30 teams covered in normalization table.
Both platforms use identical team abbreviations (only exception: Kalshi
legacy "ARI" alongside "AZ" for Arizona).

**Implementation details:**
- Kalshi: `GET /trade-api/v2/events` with `series_ticker=KXMLBGAME`,
  filter by date prefix in event ticker (e.g. `KXMLBGAME-26JUL23...`).
  Two markets per event, one per team (ticker suffix = team abbr).
- Polymarket: `GET /v2/leagues/mlb/events` returns all MLB events.
  Filter for `sportsMarketType == "baseball_team_full_game_winner"`.
  One market per event with two `marketSides` (away/home).
- Match key: `frozenset({away_abbr, home_abbr})` on the same date.
- Storage: `db/arb_orderbooks.db`, table `matched_markets`.
  Idempotent per date (deletes + reinserts).

## Phase 2: Orderbook Collector ✓

Build the WebSocket-based orderbook collector:

1. Takes matched market pairs from Phase 1 as input (the matcher runs at
   startup as the first step of the collector script).
2. Connects to both platforms' WebSocket streams and subscribes to full
   orderbook data for all matched markets.
3. Logs every orderbook update with a timestamp to DuckDB.
4. Handles reconnects gracefully — log the gap and re-snapshot.

Test: connect to a small number of markets, verify messages parse correctly
and rows land in DuckDB. Confirm book state reconstruction is correct for
Kalshi (snapshot + delta model) by comparing against a REST orderbook poll.

Dependency: Polymarket US WebSocket research is complete
(wiki/polymarket-us-websocket.md). Kalshi WebSocket format is known from
prior work.

**Status:** Complete. Code in `db/arbitrage/collector.py`. Tested against
live APIs on 2026-07-23: both Kalshi and Polymarket US WebSocket connections
authenticated successfully. 5/5 matched games subscribed. 5-minute
collection run produced ~35,000 Kalshi updates and ~3,000 Polymarket
updates. Data verified: Kalshi YES prices sum to 0.99 per game (correct
complementarity), Polymarket books have no crossed spreads, prices align
across platforms.

**Implementation details:**
- Kalshi: RSA-PSS auth on WS handshake, `orderbook_delta` channel.
  Snapshot + delta model — local book state maintained per market/side,
  full book written to DB on every update.
- Polymarket: Ed25519 auth on WS handshake, `SUBSCRIPTION_TYPE_MARKET_DATA`.
  Full book on every message — written directly, no local state needed.
- Both connections run as independent asyncio tasks with exponential
  backoff reconnect (1s → 30s max). Graceful shutdown via SIGINT/SIGTERM.
- Run: `uv run python -m db.arbitrage.collector`

## Phase 3: Run Collection

Run the collector for 1–2 days (covers ~15 games/day = ~30 matched markets).
The script runs on the local machine. If it crashes, restart and note the
gap in a metadata table.

## Phase 4: Analysis

Using the collected orderbook data:

1. **Identify arbitrage opportunities.** At each timestamp, check whether
   buying YES on one platform and YES-equivalent on the other costs less
   than $1.00 after fees. Fee formulas are documented in wiki/kalshi-fees.md
   and wiki/polymarket-us-fees.md.
2. **Measure duration.** For each opportunity, how long does it persist?
   Distribution of lifetimes.
3. **Survival analysis.** What fraction of opportunities survive past 1s, 2s,
   3s, etc.? This directly addresses whether the Polymarket taker delay
   (1–3s on sports markets) would kill them.
4. **Depth at profitable levels.** When an arb exists, how many contracts are
   available? Is it actually tradable or just a phantom?
5. **Direction alignment.** Confirm which Kalshi side maps to which Polymarket
   side. Can be done in post-processing — the raw data stores platform,
   ticker, and full book.

## Phase 5: Write-Up

Style: same as the MLB calibration analysis. Quantitative, first-person,
honest about findings. Systematic dimensional breakdowns with charts.
Scope TBD after seeing the data.
