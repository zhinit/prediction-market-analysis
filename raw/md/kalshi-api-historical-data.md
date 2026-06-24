# Kalshi API Historical Data Documentation

Source: https://docs.kalshi.com/getting_started/historical_data and related API reference pages
Accessed: 2026-06-24

---

## Overview

Kalshi separates exchange data into live and historical tiers. As activity increases, older data moves from live endpoints to dedicated historical endpoints. This maintains API performance by partitioning data for markets, market candlesticks, trades, and orders. Events and Series remain universally accessible (no historical partition).

The system targets a ~3-month window for live data, with cutoffs regularly advancing.

## Cutoff Timestamps

`GET /trade-api/v2/historical/cutoff`

No authentication required. No parameters.

Returns three cutoff timestamps (ISO 8601 date-time strings):

- **market_settled_ts** — Markets and their candlesticks that settled before this timestamp must be accessed via `GET /historical/markets` and `GET /historical/markets/{ticker}/candlesticks`
- **trades_created_ts** — Fills that occurred before this timestamp must be accessed via `GET /historical/fills` (user fills) and `GET /historical/trades` (all trades)
- **orders_updated_ts** — Orders canceled or fully executed before this timestamp must be accessed via `GET /historical/orders`. Resting (active) orders always remain in `GET /portfolio/orders` regardless of cutoff.

## Historical Endpoints

### GET /historical/markets

Archived settled markets. Filters are mutually exclusive.

Query parameters:
- limit (int, default 100, max 1000)
- cursor (string)
- tickers (string, comma-separated list)
- event_ticker (string, single event)
- series_ticker (string)
- mve_filter (string, enum: "exclude")

Returns same Market schema as live endpoint, including: ticker, event_ticker, market_type (binary|scalar), status (initialized|inactive|active|closed|determined|disputed|amended|finalized), result (yes|no|scalar|""), settlement_value_dollars, settlement_ts, volume_fp, open_interest_fp, rules_primary, rules_secondary, strike fields, price fields, etc.

### GET /historical/markets/{ticker}

Single historical market by ticker. Same response schema as above.

### GET /historical/markets/{ticker}/candlesticks

Historical candlestick data for archived markets.

Path parameters:
- ticker (string, required)

Query parameters:
- start_ts (int64, required) — Unix timestamp, candlesticks ending on or after this time
- end_ts (int64, required) — Unix timestamp, candlesticks ending on or before this time
- period_interval (int, required) — minutes per candlestick: 1, 60, or 1440

Response contains:
- ticker (string)
- candlesticks (array of MarketCandlestickHistorical):
  - end_period_ts (int64) — Unix timestamp for end of period
  - yes_bid — OHLC for YES buy offers (open, low, high, close in FixedPointDollars)
  - yes_ask — OHLC for YES sell offers
  - price — OHLC plus mean (VWAP) and previous (prior close) for trade prices
  - volume (FixedPointCount)
  - open_interest (FixedPointCount)

### GET /historical/trades

All historical trades across all markets. No authentication required.

Query parameters:
- ticker (string, optional) — filter by market
- min_ts (int64, optional) — trades after this Unix timestamp
- max_ts (int64, optional) — trades before this Unix timestamp
- limit (int64, default 100, max 1000)
- cursor (string)
- is_block_trade (boolean, optional) — filter block trades; omit for all

Response trade object fields:
- trade_id (string)
- ticker (string)
- count_fp (string, FixedPointCount) — contract quantity, 2 decimals (e.g. "10.00")
- yes_price_dollars (string, FixedPointDollars) — up to 6 decimals (e.g. "0.5600")
- no_price_dollars (string, FixedPointDollars)
- taker_outcome_side ("yes" or "no")
- taker_book_side ("bid" or "ask")
- created_time (ISO 8601)
- is_block_trade (boolean)
- taker_side (DEPRECATED — use taker_outcome_side or taker_book_side)

### GET /historical/fills

User-specific historical fills. Requires authentication. Same concept as trades but scoped to the authenticated user's fills.

### GET /historical/orders

Archived canceled or fully executed orders. Requires authentication (KALSHI-ACCESS-KEY, KALSHI-ACCESS-SIGNATURE, KALSHI-ACCESS-TIMESTAMP headers).

Query parameters:
- ticker (string, optional)
- max_ts (int64, optional)
- limit (int64, default 100, max 1000)
- cursor (string)

Response order object fields:
- order_id, user_id, client_order_id, ticker
- side, action, outcome_side ("yes"|"no"), book_side ("bid"|"ask")
- type ("limit"|"market")
- status ("resting"|"canceled"|"executed")
- yes_price_dollars, no_price_dollars (FixedPointDollars)
- fill_count_fp, remaining_count_fp, initial_count_fp (FixedPointCount)
- taker_fees_dollars, maker_fees_dollars
- taker_fill_cost_dollars, maker_fill_cost_dollars
- expiration_time, created_time, last_update_time

## Live Endpoints Affected

Six live endpoints no longer return data beyond their cutoffs:
- GET /markets (and GET /markets/{ticker})
- GET /events/{event_ticker} with nested markets
- GET /markets/trades and GET /markets/{ticker}/trades
- GET /portfolio/fills
- GET /portfolio/orders (completed only; resting orders always available)
- GET /markets/{ticker}/candlesticks

## Implementation Pattern

1. Retrieve current cutoffs via GET /historical/cutoff
2. Route queries based on data age — if target timestamp < cutoff, use historical endpoint
3. Combine results from both live and historical endpoints for comprehensive datasets
4. Historical endpoints support same cursor-based pagination as live counterparts
