# Kalshi API Orders

Order management requires authentication. The V2 endpoints
(`/portfolio/events/orders`) are the current standard; legacy
`/portfolio/orders` endpoints are deprecated with 10x rate-limit cost
penalties. (source: kalshi-api-orders-and-portfolio.md, kalshi-api-changelog-2026.md)

## V2 Order Model

V2 uses a single-book bid/ask model with fixed-point dollar pricing:
- **bid** = buy YES
- **ask** = sell YES (economically equivalent to buying NO at 1 - price)

(source: kalshi-api-orders-and-portfolio.md)

## Create Order (POST /portfolio/events/orders)

Required fields:
- `ticker` — market ticker
- `side` — "bid" or "ask"
- `count` — FixedPointCount (e.g., "10.00")
- `price` — FixedPointDollars (e.g., "0.5600")
- `time_in_force` — fill_or_kill, good_till_canceled, or immediate_or_cancel
- `self_trade_prevention_type` — taker_at_cross or maker

Optional: `client_order_id` (UUID, enables idempotent retries),
`post_only`, `cancel_order_on_pause`, `reduce_only`, `subaccount`,
`order_group_id`, `expiration_time`, `exchange_index`.

Response includes: `order_id`, `fill_count`, `remaining_count`, `ts_ms`,
and conditionally `average_fill_price` and `average_fee_paid`.

(source: kalshi-api-orders-and-portfolio.md)

## Other Order Endpoints

- `GET /portfolio/events/orders` — list orders
- `GET /portfolio/events/orders/{order_id}` — single order
- `DELETE /portfolio/events/orders/{order_id}` — cancel
- `PATCH /portfolio/events/orders/{order_id}` — amend
- Batch operations for multiple orders

(source: kalshi-api-orders-and-portfolio.md)

## Portfolio Endpoints

- `GET /portfolio/positions` — market and event positions
- `GET /portfolio/balance` — account balance

(source: kalshi-api-orders-and-portfolio.md)

## Order Groups

Order groups set contract limits and auto-cancel across related orders.
(source: kalshi-api-orders-and-portfolio.md)

## Fractional Contracts

Markets with `fractional_trading_enabled` accept counts with up to 2 decimal
places (minimum granularity: 0.01 contracts).
(source: kalshi-api-orders-and-portfolio.md)
