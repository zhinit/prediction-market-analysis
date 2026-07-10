# Data Collection Buildout Plan

Step-by-step implementation of `docs/data-collect-specs.md`.

Existing project patterns: self-contained scripts in `db/scripts/`, Pydantic
models for API responses, httpx async + tenacity retries, DuckDB TEXT storage
with typed views, pytest in `db/tests/`. Dependencies already installed:
httpx, duckdb, pydantic, tenacity, polars, pytest.

Reference implementation: poka-arb's `strategies/arbitrage/matcher/` (adapters,
core matcher, match_cli, config).

---

## Step 1: Auth utilities

**File**: `db/scripts/auth.py`

Port the auth module from poka-arb (`strategies/arbitrage/matcher/adapters/auth.py`):
- RSA-PSS signing for Kalshi (load PEM private key, sign timestamp+method+path)
- Ed25519 signing for Polymarket US (load Ed25519 private key, sign timestamp+method+path)
- Key paths read from environment variables (same vars as poka-arb)

**Dependencies to add**: `uv add cryptography PyNaCl`

**Test**: `db/tests/test_auth.py`
- Signing produces deterministic output for a known key + timestamp
- Missing env var raises clear error
- Invalid key file raises clear error

---

## Step 2: REST adapters

**File**: `db/scripts/kalshi_adapter.py`

Port from poka-arb's `adapters/kalshi.py`:
- `fetch_series()` — paginated, returns list of series with category metadata
- `fetch_events()` — paginated cursor-based, all open events
- `fetch_event_markets(event_ticker)` — sub-markets for a single event

**File**: `db/scripts/poly_adapter.py`

Port from poka-arb's `adapters/polymarket_us.py`:
- `fetch_markets()` — paginated, with `endDateMin=today` and `active=true`

Both adapters: httpx async, tenacity retries, Pydantic response models.

**Test**: `db/tests/test_adapters.py`
- Mock httpx responses to verify pagination handling (multiple pages, empty page stops)
- Verify Pydantic models parse real response fixtures (save one page of real
  API response as a JSON fixture in `db/tests/fixtures/`)
- Verify `endDateMin` is always set on Polymarket requests

---

## Step 3: Matching logic

**File**: `db/scripts/match_markets.py`

Port and simplify from poka-arb's `core/matcher.py` + `match_cli.py`:

1. **Grouping functions**:
   - `group_kalshi_events(events, series)` — attach category from series,
     extract sport sub-type from series title
   - `group_poly_markets(markets)` — group by `gameId`, pick moneyline as
     representative

2. **Pre-filters** (all four, as pure functions):
   - `categories_compatible(kalshi_cat, poly_cat) -> bool`
   - `sport_types_compatible(kalshi_sport, poly_sport) -> bool`
   - `bet_types_compatible(kalshi_type, poly_type) -> bool`
   - `dates_overlap(kalshi_date, poly_date, is_sports) -> bool`

3. **Jaccard scorer**:
   - `normalize_title(title) -> set[str]` — lowercase, strip punctuation,
     remove stop words
   - `jaccard_score(set_a, set_b) -> float`

4. **Pipeline**: `find_candidates(kalshi_events, poly_games, threshold=0.3)`
   - Apply pre-filters, score survivors, sort by score descending,
     deduplicate by Polymarket slug

5. **CLI entry point**: fetches from both APIs, runs pipeline, excludes
   known matches/rejections, fetches Kalshi sub-markets for each candidate,
   writes `candidates.json`

**Test**: `db/tests/test_matcher.py`
- `normalize_title`: strips punctuation, lowercases, removes stop words
- `jaccard_score`: known pair → expected score; identical → 1.0; disjoint → 0.0
- `categories_compatible`: sports↔sports true, sports↔politics false
- `sport_types_compatible`: mlb↔mlb true, mlb↔nba false, unknown↔unknown true
- `bet_types_compatible`: moneyline↔moneyline true, moneyline↔spread false
- `dates_overlap`: same date true, different date false (sports), missing date
  true (non-sports), missing date false (sports)
- `find_candidates`: synthetic events/games → expected candidates with correct
  ordering and deduplication
- Already-known matches excluded from output

---

## Step 4: `/matcher` command

**File**: `.claude/commands/matcher.md`

Claude command that:
1. Runs `uv run python db/scripts/match_markets.py`
2. Reads `candidates.json`
3. For each candidate, reviews against checklist:
   - Same event?
   - Same date?
   - Same bet type?
   - Correct Kalshi sub-market / ticker?
   - Direction: read Kalshi ticker suffix for YES side, read Polymarket
     `question` field for YES side. Record both in notes.
   - Not a duplicate?
4. Appends approved to `matches.json`, rejected to `rejected_matches.json`
5. Removes expired matches (event date in the past)

**Test**: manual — run `/matcher` against live APIs, verify candidates look
reasonable, approve/reject a few, confirm JSON files are well-formed.

---

## Step 5: Orderbook collector

**File**: `db/scripts/collect_orderbooks.py`

**Dependencies to add**: `uv add websockets`

1. **Load** `matches.json`
2. **Kalshi websocket**:
   - Connect to `wss://external-api-ws.kalshi.com/trade-api/ws/v2`
   - RSA-PSS auth headers
   - Subscribe to `orderbook_delta` for each matched Kalshi ticker
   - Maintain local orderbook state per ticker
   - On each delta: update state, extract best bid/ask/size, emit snapshot
   - Track sequence numbers, re-snapshot on gap
3. **Polymarket US websocket**:
   - Connect to `wss://api.polymarket.us/v1/ws/markets`
   - Ed25519 auth headers
   - Subscribe via `SUBSCRIPTION_TYPE_MARKET_DATA` for each matched slug
   - Text frames only (not binary)
   - On each message: parse `offers` (not `asks`), extract nested prices
     `px.value`, emit snapshot
4. **Snapshot writer**:
   - Batch snapshots in memory (e.g., flush every 100 or every 30 seconds)
   - Write to `orderbook_snapshots` table in `db/pma.db`
   - Create typed view on first run
5. **Reconnection**: exponential backoff, log connection state transitions
6. **Graceful shutdown**: flush pending batch on SIGINT/SIGTERM

**Test**: `db/tests/test_collector.py`
- Snapshot batching: accumulate N snapshots, flush writes correct rows to
  DuckDB
- Kalshi delta application: apply a sequence of deltas to an empty orderbook,
  verify best bid/ask extraction
- NO bid conversion: NO bid at price X → YES ask at 1−X
- Polymarket price parsing: nested `px.value` → float
- Sequence gap detection: missing sequence number triggers re-snapshot flag
- Typed view creation is idempotent

---

## Step 6: `/collect-arb-data` command

**File**: `.claude/commands/collect-arb-data.md`

Claude command that:
1. Checks `matches.json` exists and is non-empty
2. Runs `uv run python db/scripts/collect_orderbooks.py`
3. Monitors stdout for connection status lines

**Test**: manual — run command, verify both websockets connect, let it run
for a few minutes, query `orderbook_snapshots` table to confirm rows.

---

## Step 7: Data quality tests

**File**: `db/tests/test_arb_data_quality.py`

Post-collection reasonability checks (run after accumulating some data):
- Every snapshot has valid bid/ask: bid ≤ ask, both in [0, 1]
- Every snapshot `market_id` maps to a match in `matches.json`
- Every snapshot `match_id` maps to a match in `matches.json`
- No `match_id` / `market_id` mismatch (market belongs to stated match)
- Both platforms represented for each match
- No timestamp gaps longer than 10 minutes within a collection session
  (flags outages)
- Typed view returns correct numeric types

---

## Step 8: End-to-end smoke test

Run the full daily workflow once:
1. `/matcher` — verify candidates generated, approve at least 2-3 matches
2. `/collect-arb-data` — run for 5 minutes
3. `uv run pytest db/tests/` — all tests pass including data quality
4. Query `orderbook_snapshots` directly:
   - Both platforms have rows
   - Timestamps are recent
   - Prices are in reasonable range

---

## Build order

Steps 1-3 can be built and tested without live API access (mocked fixtures).
Step 4 requires live APIs but no websockets. Steps 5-6 require websocket
access. Steps 7-8 require collected data.

```
Step 1 (auth) → Step 2 (adapters) → Step 3 (matcher) → Step 4 (/matcher command)
                                                      ↘
                                          Step 5 (collector) → Step 6 (/collect-arb-data command)
                                                                              ↓
                                                              Step 7 (data quality tests) → Step 8 (smoke test)
```
