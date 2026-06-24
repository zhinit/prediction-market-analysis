# Polymarket US Portfolio API

Source: https://docs.polymarket.us/api-reference/portfolio/overview
Fetched: 2026-06-24

## Base URL

`https://api.polymarket.us`

All endpoints require API key authentication.

## Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/v1/portfolio/positions` | Trading positions by market slug |
| GET | `/v1/portfolio/activities` | Transaction history |
| GET | `/v1/account/balances` | Current account balances |

## Positions

Returned as a map keyed by market slug (not a list).

### Position Fields

- `netPositionDecimal` — current position size
- `qtyBoughtDecimal` — total bought
- `qtySoldDecimal` — total sold
- Cost basis
- Realized P&L
- Unrealized value
- Expiration status

Note: integer versions of quantity fields are deprecated; use `*Decimal`
variants.

## Activities

Paginated array of typed events.

### Activity Types

- `ACTIVITY_TYPE_TRADE` — trade executions with price, quantity, P&L
- Position resolutions at market settlement
- Account balance changes: deposits, withdrawals, transfers, bonuses

## Account Balances

- Current fiat balance
- Buying power (unencumbered capital available for trading)
- Notional asset values
- Margin requirements

## Pagination

Cursor-based using `nextCursor`. The `eof` boolean indicates completion.

## Real-Time Alternative

WebSocket subscriptions recommended over polling:
- `SUBSCRIPTION_TYPE_POSITION` — position updates
- `SUBSCRIPTION_TYPE_ACCOUNT_BALANCE` — balance updates
