# Kalshi API Market Data

All market data endpoints are public and require no authentication.
(source: kalshi-api-market-data-endpoints.md)

## Data Hierarchy

Series → Events → Markets. A series is a recurring category (e.g., "Highest
temperature in NYC"). An event is one instance of a series. A market is a
specific binary or scalar outcome within an event.
(source: kalshi-api-market-data-endpoints.md)

## Key Endpoints

### GET /markets

Paginated list of markets with filters for event_ticker, series_ticker,
status, timestamps, and tickers (comma-separated). Default limit: 100,
max: 1000. (source: kalshi-api-market-data-endpoints.md)

### GET /markets/{ticker}

Single market by ticker. Returns the full [[kalshi-market-object]].
(source: kalshi-api-market-data-endpoints.md)

### GET /markets/trades

All trades across markets. Filterable by ticker, timestamp range, and
block trade status. Returns trade_id, ticker, count_fp, yes_price_dollars,
no_price_dollars, taker_outcome_side, taker_book_side, created_time.
(source: kalshi-api-market-data-endpoints.md)

### GET /markets/{ticker}/orderbook

Current orderbook. Returns bids only — in binary markets, a YES bid at 60c
is equivalent to a NO ask at 40c. (source: kalshi-api-market-data-endpoints.md)

### GET /events/{event_ticker}/candlesticks

OHLCV data at 1-minute, hourly, or daily granularity.
(source: kalshi-api-market-data-endpoints.md)

### GET /events, GET /events/{event_ticker}

Event listing and detail. Events now include `settlement_sources` (as of
June 18, 2026). (source: kalshi-api-changelog-2026.md)

### GET /series/{series_ticker}

Series metadata including title, frequency, and category.
(source: kalshi-api-market-data-endpoints.md)

## Batched Orderbook

As of March 2026, a batched orderbook fetch endpoint supports up to 100
tickers in one call. (source: kalshi-api-changelog-2026.md)

## Historical Data

Markets settled before a cutoff date are served from `GET /historical/markets`
instead of the regular endpoints. This split took effect February 19, 2026.
The live API serves a rolling ~3-month window; older trades, markets, and
candlesticks require the historical endpoints. See [[kalshi-api-historical]]
for the full historical API reference.
(source: kalshi-api-market-data-endpoints.md, kalshi-api-changelog-2026.md,
kalshi-api-historical-data.md)

## Pagination

Cursor-based. Response includes a `cursor` field; pass it as a query parameter
for the next page. `null` cursor means no more pages. See [[kalshi-api-pagination]].
(source: kalshi-api-pagination.md)
