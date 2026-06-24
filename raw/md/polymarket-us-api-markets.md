# Polymarket US Markets API

Source: https://docs.polymarket.us/api-reference/market/overview
Fetched: 2026-06-24

## Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/v1/markets` | Get all markets with filtering |
| GET | `/v1/market/id/{id}` | Get market by numeric ID |
| GET | `/v1/market/slug/{slug}` | Get market by URL-friendly slug |
| GET | `/v1/markets/sides/{marketSideId}` | Get individual market outcome |
| GET | `/v1/markets/{marketId}/sides` | Get all outcomes for a market |
| GET | `/v1/markets/{slug}/book` | Full order book and stats |
| GET | `/v1/markets/{slug}/bbo` | Best bid/offer (lightweight) |
| GET | `/v1/markets/{slug}/settlement` | Settlement price after resolution |

## Market Properties

### Status
- `active` — accepts orders
- `closed` — resolved/expired
- `archived` — hidden

### States (WebSocket)
open, pre-open, suspended, halted, expired, terminated, closing-auction

### Pricing Fields
- `orderPriceMinTickSize`
- `minimumTradeQty`
- `lastTradePrice`
- `bestBid`, `bestAsk`
- `spread`
- 24h and 7d price changes

### Liquidity Metrics
- Current liquidity
- Volume totals
- Time-based volume: 24hr, 1wk, 1mo

### Sports-Specific
- Market type: moneyline, spread, total, prop
- `gameId`
- Line values

## Filtering

- Status: active, closed, archived booleans
- Categories: sports, politics, crypto, etc.
- Market types: binary, scalar
- Sports classification: moneyline, spread, total, prop
- Identifiers: market IDs, slugs, question UUIDs, game IDs
- Volume/liquidity: min/max thresholds
- Temporal: ISO 8601 date ranges for start/end dates

## Pagination

- `limit` — records per page
- `offset` — skip count
- `orderBy` — multi-field sorting
- `orderDirection` — asc/desc

## Order Book Response (`/book`)

Full bid/ask ladder with:
- Market state
- Open/high/low prices
- Shares traded
- Notional value
- Open interest

## BBO Response (`/bbo`)

Top-of-book only:
- Best bid/ask prices
- Depth levels
- Settlement data

## Settlement Response

Returns market slug and settlement value: typically `0.00` (No) or `1.00` (Yes).
