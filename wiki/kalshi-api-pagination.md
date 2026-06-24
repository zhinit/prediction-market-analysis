# Kalshi API Pagination

Cursor-based pagination across list endpoints.
(source: kalshi-api-pagination.md)

## Mechanism

1. Initial request: no cursor parameter
2. Response includes `cursor` string for next page
3. Pass `cursor` as query parameter in next request
4. `null` cursor = no more pages

## Parameters

- `cursor` (string) — from previous response
- `limit` (integer) — page size; default 100, max 1000 on some endpoints

## Supported Endpoints

Markets, events, series, trades, portfolio history, fills, orders.
(source: kalshi-api-pagination.md)
