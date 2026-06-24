# Kalshi API Historical Data

Kalshi partitions exchange data into live and historical tiers. The live API
serves a rolling ~3-month window; older data moves to dedicated historical
endpoints. Events and Series are unaffected — they remain on the live
endpoints regardless of age. (source: kalshi-api-historical-data.md)

## Cutoff Timestamps

`GET /historical/cutoff` — public, no auth required.
(source: kalshi-api-historical-data.md)

Returns three ISO 8601 timestamps:

| Field | Determines access to |
|-------|---------------------|
| `market_settled_ts` | Markets and candlesticks settled before this → `GET /historical/markets` |
| `trades_created_ts` | Trades/fills created before this → `GET /historical/trades` or `GET /historical/fills` |
| `orders_updated_ts` | Orders canceled/executed before this → `GET /historical/orders` |

Resting (active) orders always remain on `GET /portfolio/orders` regardless of
cutoff. (source: kalshi-api-historical-data.md)

## Historical Endpoints

All historical endpoints use cursor-based pagination (same as live). See
[[kalshi-api-pagination]]. (source: kalshi-api-historical-data.md)

### GET /historical/markets

Archived settled markets. Returns the same [[kalshi-market-object]] schema as
the live endpoint, including `result`, `settlement_value_dollars`, and
`settlement_ts`. (source: kalshi-api-historical-data.md)

Filters (mutually exclusive):
- `tickers` — comma-separated list
- `event_ticker` — single event
- `series_ticker` — series filter
- `mve_filter` — "exclude" to omit multivariate/combo markets
- `limit` (default 100, max 1000), `cursor`

No authentication required. (source: kalshi-api-historical-data.md)

### GET /historical/markets/{ticker}

Single historical market by ticker. Same schema.
(source: kalshi-api-historical-data.md)

### GET /historical/markets/{ticker}/candlesticks

OHLCV candlesticks for archived markets. (source: kalshi-api-historical-data.md)

Required parameters:
- `start_ts`, `end_ts` — Unix timestamps
- `period_interval` — 1 (minute), 60 (hour), or 1440 (day)

Each candlestick contains:
- `yes_bid`, `yes_ask` — OHLC in dollars
- `price` — OHLC plus `mean` (VWAP) and `previous` (prior close)
- `volume`, `open_interest` — FixedPointCount strings

### GET /historical/trades

All historical trades across all markets. Public, no auth.
(source: kalshi-api-historical-data.md)

Parameters:
- `ticker` — filter by market
- `min_ts`, `max_ts` — Unix timestamp range
- `is_block_trade` — boolean filter (omit for all)
- `limit` (default 100, max 1000), `cursor`

Trade object fields:
- `trade_id`, `ticker`
- `count_fp` — contract count (FixedPointCount, e.g. "10.00")
- `yes_price_dollars`, `no_price_dollars` — up to 6 decimal places
- `taker_outcome_side` — "yes" or "no"
- `taker_book_side` — "bid" or "ask"
- `created_time` — ISO 8601
- `is_block_trade` — boolean
- `taker_side` — DEPRECATED, use `taker_outcome_side`/`taker_book_side`

### GET /historical/fills

User-specific historical fills. Requires authentication. Same concept as
trades but scoped to the authenticated user. (source: kalshi-api-historical-data.md)

### GET /historical/orders

Archived canceled or fully executed orders. Requires authentication.
(source: kalshi-api-historical-data.md)

Parameters:
- `ticker`, `max_ts`, `limit`, `cursor`

Order object includes: order_id, ticker, outcome_side, book_side, type
(limit|market), status (resting|canceled|executed), price fields, count
fields, fee fields, timestamps.

## Live Endpoints Affected

Six live endpoints stop returning data older than their respective cutoffs:
(source: kalshi-api-historical-data.md)

1. `GET /markets` and `GET /markets/{ticker}` — see [[kalshi-api-market-data]]
2. `GET /events/{event_ticker}` (nested markets only)
3. `GET /markets/trades` and `GET /markets/{ticker}/trades`
4. `GET /portfolio/fills`
5. `GET /portfolio/orders` (completed only)
6. `GET /markets/{ticker}/candlesticks`

## Implementation Pattern

To get complete data across the live/historical boundary:
(source: kalshi-api-historical-data.md)

1. Call `GET /historical/cutoff` to get current timestamps
2. If target data predates the relevant cutoff, use the `GET /historical/...` endpoint
3. Merge results from both live and historical endpoints when spanning the boundary
4. Both tiers use identical cursor-based pagination
