# Kalshi API Orders and Portfolio Endpoints

Source: https://docs.kalshi.com/api-reference/orders/create-order-v2, https://docs.kalshi.com/getting_started/quick_start_create_order, https://docs.kalshi.com/api-reference/portfolio/get-positions
Fetched: 2026-06-24

---

## POST /portfolio/events/orders (Create Order V2)

"Endpoint for submitting event-market orders using the V2 request/response shape" with single-book bid/ask pricing in fixed-point dollars. The legacy endpoint (`POST /portfolio/orders`) will be phased out no earlier than May 6, 2026.

### Request Body (CreateOrderV2Request)

**Required Fields:**
- `ticker` (string, min length 1) — market ticker
- `side` (string: "bid" or "ask") — bid = buy YES; ask = sell YES (equivalent to buy NO at 1 - price)
- `count` (FixedPointCount) — contract quantity, 0-2 decimals (e.g., "10.00")
- `price` (FixedPointDollars) — up to 6 decimals
- `time_in_force` (enum: "fill_or_kill", "good_till_canceled", "immediate_or_cancel")
- `self_trade_prevention_type` (enum: "taker_at_cross", "maker")

**Optional Fields:**
- `client_order_id` (string) — UUID for deduplication and idempotent retries
- `expiration_time` (Unix timestamp in seconds; requires "good_till_canceled")
- `post_only` (boolean, default: false)
- `cancel_order_on_pause` (boolean, default: false)
- `reduce_only` (boolean, default: false)
- `subaccount` (integer, minimum 0, default: 0)
- `order_group_id` (string)
- `exchange_index` (integer, default: 0; -1 for auto-routing)

### Example Request

```json
{
  "ticker": "HIGHNY-24JAN01-T60",
  "client_order_id": "8c35ecb3-328f-4f52-8c7c-0f4b9862f8d1",
  "side": "bid",
  "count": "10.00",
  "price": "0.5600",
  "time_in_force": "good_till_canceled",
  "self_trade_prevention_type": "taker_at_cross",
  "post_only": false,
  "cancel_order_on_pause": false,
  "reduce_only": false,
  "subaccount": 0,
  "exchange_index": 0
}
```

### Response (CreateOrderV2Response)

**Required Fields:**
- `order_id` (string)
- `fill_count` (FixedPointCount)
- `remaining_count` (FixedPointCount)
- `ts_ms` (Unix epoch milliseconds)

**Conditional Fields:**
- `client_order_id` (string, mirrors request)
- `average_fill_price` (present when fill_count > 0)
- `average_fee_paid` (present when fill_count > 0)

### Example Response

```json
{
  "order_id": "3b23c1c7-f4ef-4f0d-8b9a-9e53c61f1a0d",
  "client_order_id": "8c35ecb3-328f-4f52-8c7c-0f4b9862f8d1",
  "fill_count": "0.00",
  "remaining_count": "10.00",
  "ts_ms": 1715793600123
}
```

### HTTP Status Codes

- 201: Order created successfully
- 400: Bad request (invalid input)
- 401: Unauthorized
- 409: Conflict (duplicate client_order_id)
- 429: Rate limit exceeded (default: 10 tokens per request)
- 500: Internal server error

### Field Semantics

**BookSide**: "bid" means buy YES; "ask" means sell YES. Selling YES is economically equivalent to buying NO at (1 - price).

**FixedPointCount**: Accepts 0-2 decimals (e.g., "10", "10.0", "10.00"); responses always emit 2 decimals. Fractional contracts (e.g., "2.50") supported on enabled markets; minimum granularity is 0.01 contracts.

**SelfTradePreventionType**: "taker_at_cross" cancels taker order when trading against the same user's order (execution stops); "maker" cancels resting maker order and continues matching.

---

## Other Order Endpoints

- `GET /portfolio/events/orders` — list orders
- `GET /portfolio/events/orders/{order_id}` — get single order
- `DELETE /portfolio/events/orders/{order_id}` — cancel order
- `PATCH /portfolio/events/orders/{order_id}` — amend order
- Batch operations available for multiple orders

---

## GET /portfolio/positions

Returns market positions and event positions.

**URL**: `https://external-api.kalshi.com/trade-api/v2/portfolio/positions`

---

## GET /portfolio/balance

Returns account balance information.

---

## Order Groups

Order groups allow setting contract limits and auto-cancel functionality across related orders.

- `POST /portfolio/order-groups` — create order group
- `GET /portfolio/order-groups` — list order groups
- `GET /portfolio/order-groups/{id}` — get order group
- `GET /portfolio/order-queue-position` — get order queue position

---

## Order Lifecycle

1. Find a market via `GET /markets`
2. Place an order via `POST /portfolio/events/orders`
3. Check status via `GET /portfolio/events/orders/{order_id}`
4. Cancel via `DELETE /portfolio/events/orders/{order_id}`
5. Monitor via WebSocket `fill` and `order` channels
