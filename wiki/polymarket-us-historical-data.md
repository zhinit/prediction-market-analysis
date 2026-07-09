# Polymarket US Historical Data

Polymarket US has no public market-wide trade tape. All trade history endpoints
are account-scoped and authenticated (source:
polymarket-us-api-market-data-guide.md).

## Retail API

### Activities Endpoint

`GET /v1/portfolio/activities` — paginated trade history for the authenticated
user (source: polymarket-us-api-portfolio-overview.md).

Parameters: `limit`, `cursor`, `types` (filter by activity type), `marketSlug`,
`sortOrder` (ascending or descending by time).

Trade fields: `id`, `marketSlug`, `price`, `qtyDecimal`, `isAggressor`
(taker flag), `realizedPnl`. Activity types include ACTIVITY_TYPE_TRADE,
ACTIVITY_TYPE_POSITION_RESOLUTION, ACTIVITY_TYPE_TAKER_FEE_REBATE,
ACTIVITY_TYPE_LIQUIDITY_PROGRAM, plus deposits/withdrawals/transfers (source:
polymarket-us-api-portfolio-overview.md).

### Historical Positions

`GET /v1/portfolio/positions` with `as_of_time` or `as_of_date` parameters
queries positions at any historical point. Added January 2026 (source:
polymarket-us-api-changelog-data.md).

## Institutional (Exchange) API

### Report Endpoints

Account-scoped search and download for orders, executions, and trades (source:
polymarket-us-api-institutional-overview.md):

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/report/orders/search` | POST | Search historical orders |
| `/v1/report/orders/{order_id}` | GET | Get single order |
| `/v1/report/executions/search` | POST | Search historical executions |
| `/v1/report/executions/{exec_id}` | GET | Get single execution |
| `/v1/report/trades/csv` | POST | Download trades as CSV stream |

The trades CSV endpoint accepts `startTime`, `endTime` (RFC3339), and
`accounts` array. Response streams CSV in `filechunk` strings (source:
polymarket-us-api-report-trades-csv.md).

Execution responses include `commissionNotionalCollected`,
`commissionSpreadPx`, and `transactTradeDate` (added May 2026) (source:
polymarket-us-api-changelog-data.md).

### Ledger Endpoints (Added May 26, 2026)

Position and balance change logs with CSV download (source:
polymarket-us-api-positions-risk.md):

| Endpoint | Method | Content |
|----------|--------|---------|
| `/v1/positions/ledger` | GET | Paginated position changes |
| `/v1/positions/ledger/download` | GET | Position ledger CSV |
| `/v1/funding/balance-ledger` | GET | Paginated balance changes |
| `/v1/funding/balance-ledger/download` | GET | Balance ledger CSV |

Position ledger returns every position change with deltas and cumulative state
(quantity, cost, realized P&L). Balance ledger tracks all cash changes with
before/after values (deposits, withdrawals, fills, fees).

**Hard historical floor: May 1, 2026** (source:
polymarket-us-api-changelog-data.md).

### gRPC DropCopy Streams

Real-time account-scoped streams, not historical, but relevant for building
a local trade database (source: polymarket-us-api-grpc-overview.md):

- `CreateDropCopySubscription` — execution reports (fills, cancels, rejects)
- `CreateTradeCaptureReportSubscription` — completed trade records with
  aggressor/passive details
- `CreatePositionChangeSubscription` — position updates

All support resume tokens for gap-free reconnection.

## Public Market Data (No Trade Tape)

BBO (`/v1/orderbook/{symbol}/bbo`) and L2 order book
(`/v1/orderbook/{symbol}`) are public. There is no public Time & Sales or
market-wide trade history endpoint (source:
polymarket-us-api-market-data-guide.md).

## Comparison with [[kalshi-api]]

Kalshi provides a public `GET /trade-api/v2/markets/trades` endpoint returning
market-wide trade history without authentication (source:
kalshi-api-market-data-endpoints.md). Polymarket US does not have an
equivalent — all trade data is account-scoped (source:
polymarket-us-api-market-data-guide.md).

## Related pages

- [[polymarket-us-api]] — full API reference
- [[polymarket-international-api]] — the international platform's Data API
  (`GET /trades?user=0x...`) is also user-scoped (source:
  polymarket-international-api-parlay-guide.md)
