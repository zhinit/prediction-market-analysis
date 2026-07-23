# Arbitrage Orderbook Collector — Technical Spec

## Overview

A Python script that connects to Kalshi and Polymarket US WebSocket streams,
subscribes to MLB game winner orderbooks, and logs every update to DuckDB.

## Status

Complete. All components implemented and verified against live APIs on
2026-07-23. Run: `uv run python -m db.arbitrage.collector`.

## Market Matching ✓

The matcher runs as the first step of the collector script at startup.
It is not a separate tool — it discovers today's markets, matches them,
writes the pairs to the matched_markets table, then hands the tickers/slugs
to the WebSocket subscriber.

### Approach

MLB game winners only. Both platforms use the same team abbreviations
(ATL, NYY, SD, etc.) — matching is by `frozenset({away, home})` on the
same date. No fuzzy matching needed.

### Market Discovery

- Kalshi: `GET /trade-api/v2/events` with `series_ticker=KXMLBGAME`,
  filtered to today by date prefix in event ticker. Then
  `GET /trade-api/v2/markets` per event to get individual market tickers
  (one per team, suffix is the team abbreviation).
- Polymarket US: `GET /v2/leagues/mlb/events` (public, no auth). Filter
  markets by `sportsMarketType == "baseball_team_full_game_winner"`.
  Slug format: `aec-mlb-{away}-{home}-{YYYY-MM-DD}`.

### Kalshi market structure

Each Kalshi event has **two markets** — one per team. Example:
- `KXMLBGAME-26JUL231840KCDET-KC` (YES = KC wins)
- `KXMLBGAME-26JUL231840KCDET-DET` (YES = DET wins)

These are complements: YES on KC ≈ NO on DET. The collector subscribes to
both because the `orderbook_delta` channel delivers updates per market ticker.

### Polymarket market structure

Each Polymarket event has **one moneyline market** with two `marketSides`.
Each side has a `team` object with `abbreviation`, `displayAbbreviation`,
`ordering` (away/home). The market slug is used for WebSocket subscription.

### Direction Alignment

Deferred to the analysis phase. The collector stores platform, market
identifier, and full book — enough to reconstruct direction later.

### Implementation

Code: `db/arbitrage/matcher.py`, `db/arbitrage/teams.py`,
`db/arbitrage/models.py`.

Run standalone: `uv run python -m db.arbitrage.matcher`.

## WebSocket Connections

### Kalshi

- Endpoint: `wss://external-api-ws.kalshi.com/trade-api/ws/v2`
- Auth: RSA-PSS signature over `{timestamp}GET/trade-api/ws/v2`, passed as
  `KALSHI-ACCESS-*` headers on handshake.
- Channel: `orderbook_delta` (requires auth).
- Subscribe: `{"id": 1, "cmd": "subscribe", "params": {"channels": ["orderbook_delta"], "market_tickers": ["TICKER1", "TICKER2"]}}`
- Initial message: `orderbook_snapshot` with full book.
  ```json
  {"type": "orderbook_snapshot", "msg": {
    "market_ticker": "...",
    "yes_dollars_fp": [["price", "qty"], ...],
    "no_dollars_fp": [["price", "qty"], ...]
  }}
  ```
- Subsequent messages: `orderbook_delta` with one level change.
  ```json
  {"type": "orderbook_delta", "msg": {
    "market_ticker": "...",
    "side": "yes"|"no",
    "price_dollars": "0.55",
    "delta_fp": "10.00"
  }}
  ```
- Local state: maintain a dict per market, apply deltas. On reconnect,
  re-snapshot replaces local state.
- Rate limits: 200 read tokens/s at Basic tier (10 tokens/request).
  WebSocket subscriptions don't count against REST rate limits.

### Polymarket US

- Endpoint: `wss://api.polymarket.us/v1/ws/markets`
- Auth: Ed25519 signature over `{timestamp}GET/v1/ws/markets`, passed as
  `X-PM-Access-Key`, `X-PM-Timestamp`, `X-PM-Signature` headers.
- Subscribe:
  ```json
  {"subscribe": {
    "requestId": "mlb-books",
    "subscriptionType": "SUBSCRIPTION_TYPE_MARKET_DATA",
    "marketSlugs": ["slug-1", "slug-2"]
  }}
  ```
- Every update delivers the full book (no delta mode):
  ```json
  {"requestId": "mlb-books",
   "subscriptionType": "SUBSCRIPTION_TYPE_MARKET_DATA",
   "marketData": {
     "marketSlug": "slug-1",
     "bids": [{"px": {"value": "0.55", "currency": "USD"}, "qty": "2.50"}, ...],
     "offers": [{"px": {"value": "0.56", "currency": "USD"}, "qty": "0.80"}, ...],
     "state": "MARKET_STATE_OPEN",
     "stats": {"lastTradePx": {...}, "sharesTraded": "...", "openInterest": "..."},
     "transactTime": "2024-01-15T10:30:00Z"
   }}
  ```
- No local state management needed — each message is self-contained.
- Max 100 markets per subscription. MLB daily volume (~30 markets) is well
  within this.
- Heartbeats: server sends `{"heartbeat": {}}` periodically.

## Auth

- Kalshi: RSA private key at `keys/hookline_kalshi_api_key.pem`.
  Key ID in `.env` as `KALSHI_API_KEY_ID`.
  Signing code: `db/shared/auth.py` (`load_rsa_key`, `sign_rsa`).
- Polymarket: Ed25519 key in `.env` as `POLYMARKET_US_PRIVATE_KEY` (base64).
  Key ID in `.env` as `POLYMARKET_US_API_KEY_ID`.
  Signing code: `db/shared/auth.py` (`load_ed25519_key`, `sign_ed25519`).

## Storage

DuckDB at `db/arb_orderbooks.db`. Schema code: `db/arbitrage/storage.py`.

### Table: matched_markets ✓

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment PK |
| game_date | DATE | MLB game date |
| away_team | VARCHAR | Normalized team abbreviation |
| home_team | VARCHAR | Normalized team abbreviation |
| kalshi_ticker_away | VARCHAR | Kalshi market ticker for away team |
| kalshi_ticker_home | VARCHAR | Kalshi market ticker for home team |
| poly_slug | VARCHAR | Polymarket moneyline market slug |
| kalshi_event_ticker | VARCHAR | Kalshi event ticker |
| poly_event_slug | VARCHAR | Polymarket event slug |

Note: the spec originally had `poly_slug_away` and `poly_slug_home` as
separate columns. Polymarket has one slug per moneyline market (with two
sides), so this was simplified to a single `poly_slug` column.

### Table: orderbook_snapshots

Each row is one full book state at a point in time.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment PK |
| timestamp | TIMESTAMP | When the update was received (local clock) |
| platform | VARCHAR | 'kalshi' or 'polymarket' |
| market_id | VARCHAR | Market ticker (Kalshi) or slug (Polymarket) |
| side | VARCHAR | 'yes' or 'no' (Kalshi) / 'bids' or 'offers' (Polymarket) |
| book_json | JSON | Full price-level array: [[price, qty], ...] |
| source_timestamp | VARCHAR | Platform-provided timestamp if available |

On every Kalshi delta: apply to local state, then write the full current
book for that market+side. On every Polymarket update: write the book
directly from the message.

This means every row is a complete book snapshot, making analysis queries
simple (no need to replay deltas).

### Table: collection_metadata

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment PK |
| event | VARCHAR | 'start', 'stop', 'reconnect', 'error' |
| platform | VARCHAR | 'kalshi' or 'polymarket' |
| timestamp | TIMESTAMP | When the event occurred |
| details | VARCHAR | Error message, gap duration, etc. |

## Python Stack

Per wiki/data-pipeline-stack.md: httpx for REST calls, pydantic for message
validation, DuckDB for storage. WebSocket library: `websockets` (asyncio).
All execution via `uv run`.

## Reconnect Strategy

On disconnect from either platform:
1. Log the disconnect event to collection_metadata.
2. Exponential backoff: 1s, 2s, 4s, 8s, max 30s.
3. On reconnect, re-subscribe. Kalshi sends a fresh snapshot automatically.
   Polymarket sends full books on every message so no state is stale.
4. Log the reconnect event with the gap duration.

## Testing

- **Matcher** ✓: run against live APIs, spot-check output against both
  platforms. Confirm all games with markets on both platforms are matched.
- **WebSocket parsing** ✓: both platforms connect, authenticate, and stream
  data. Kalshi snapshots + deltas parse correctly. Polymarket full-book
  messages parse correctly.
- **Kalshi book reconstruction** ✓: after 5 minutes of deltas, YES prices
  per game sum to 0.99 (correct complementarity across both markets).
- **Storage** ✓: DuckDB rows present with well-formed book_json. ~35k
  Kalshi + ~3k Polymarket rows in 5 minutes across 5 games.
- **Reconnect**: kill and restart the script, verify it logs the gap and
  resumes cleanly. (exponential backoff implemented, not yet stress-tested)

## Resolved Questions

- **Kalshi series ticker:** `KXMLBGAME`. Event ticker format:
  `KXMLBGAME-{YY}{MON}{DD}{HHMM}{AWAY}{HOME}`. Market ticker:
  `{event_ticker}-{TEAM}`.
- **Polymarket event/market pattern:** Events via `/v2/leagues/mlb/events`.
  Moneyline slug: `aec-mlb-{away}-{home}-{YYYY-MM-DD}`.
  Filter: `sportsMarketType == "baseball_team_full_game_winner"`.
- **Polymarket slug consistency:** The slug from the REST events endpoint
  is the same identifier used for WebSocket `marketSlugs` subscriptions.
- **Team normalization:** Both platforms use the same uppercase abbreviations
  for all 30 MLB teams. Kalshi also accepts "ARI" (legacy) for Arizona
  alongside "AZ". Table in `db/arbitrage/teams.py`.
