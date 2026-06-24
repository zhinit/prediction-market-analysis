# Polymarket US Orders API

Source: https://docs.polymarket.us/api-reference/orders/overview,
       https://docs.polymarket.us/api-reference/orders/create-order
Fetched: 2026-06-24

## Base URL

`https://api.polymarket.us`

All endpoints require API key authentication. Rate limit: 20 requests/second/key.

## Endpoints

### Order Entry
| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/v1/orders` | Create single order |
| POST | `/v1/order/preview` | Validate before submission |
| POST | `/v1/order/close-position` | Exit existing position |

### Query
| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/v1/orders/open` | All active orders |
| GET | `/v1/order/{orderId}` | Specific order details |

### Management
| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/v1/order/{orderId}/modify` | Update existing order |
| POST | `/v1/order/{orderId}/cancel` | Cancel single order |
| POST | `/v1/orders/open/cancel` | Cancel all open orders |

### Batch (up to 20 orders)
| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/v1/orders/batched` | Submit multiple orders |
| POST | `/v1/orders/batched/cancel` | Cancel by ID |
| POST | `/v1/orders/batched/modify` | Modify via cancel-replace |

## Order Types

- `ORDER_TYPE_LIMIT` — fixed-price execution
- `ORDER_TYPE_MARKET` — best-available execution

## Order Intent

- `ORDER_INTENT_BUY_LONG` — purchase YES contracts
- `ORDER_INTENT_SELL_LONG` — liquidate YES positions
- `ORDER_INTENT_BUY_SHORT` — purchase NO contracts
- `ORDER_INTENT_SELL_SHORT` — liquidate NO positions

Alternative: specify `outcomeSide` (`OUTCOME_SIDE_YES`/`OUTCOME_SIDE_NO`) +
`action` (`ORDER_ACTION_BUY`/`ORDER_ACTION_SELL`).

## Time-in-Force

- `TIME_IN_FORCE_DAY` — expires end-of-session
- `TIME_IN_FORCE_GOOD_TILL_CANCEL` — persists indefinitely
- `TIME_IN_FORCE_GOOD_TILL_DATE` — expires at timestamp
- `TIME_IN_FORCE_IMMEDIATE_OR_CANCEL` — partial fills OK
- `TIME_IN_FORCE_FILL_OR_KILL` — all-or-nothing

## Price Mechanics

`price.value` always represents YES-side pricing regardless of order direction.
YES + NO prices sum to $1.00. Buying NO at $0.83 requires `price.value: "0.17"`.
Valid range: $0.01–$0.99.

Markets define `orderPriceMinTickSize` and `minimumTradeQty`.

## Amount Object

```json
{
  "value": "0.55",
  "currency": "USD"
}
```

## Required Parameters

- `marketSlug` — target market
- `type` — order type
- `price` — amount object (required for limit orders)
- `quantity` — contract count (supports decimals)
- `tif` — time-in-force
- `intent` OR (`outcomeSide` + `action`)
- `manualOrderIndicator` — `MANUAL_ORDER_INDICATOR_MANUAL` or `MANUAL_ORDER_INDICATOR_AUTOMATIC`

## Optional Parameters

- `participateDontInitiate` — maker-only, rejects immediate matches
- `goodTillTime` — expiration for GTD orders
- `cashOrderQty` — dollar amount for market orders instead of shares
- `synchronousExecution` — blocks until filled/rejected/canceled
- `maxBlockTime` — seconds to wait if synchronous
- `slippageTolerance` — price reference with bips or ticks tolerance

## Order States

```
PENDING_NEW → NEW → PARTIALLY_FILLED → FILLED
                ↓
        CANCELED / REJECTED / EXPIRED
```

Full list: PENDING_NEW, NEW, PENDING_REPLACE, PENDING_CANCEL, PENDING_RISK,
PARTIALLY_FILLED, FILLED, CANCELED, REPLACED, REJECTED, EXPIRED.

## Execution Types

- `EXECUTION_TYPE_NEW`
- `EXECUTION_TYPE_PARTIAL_FILL`
- `EXECUTION_TYPE_FILL`
- `EXECUTION_TYPE_REJECTED`

## Rejection Reasons

Exchange option, unknown market, exchange closed, incorrect quantity, invalid
price increment, incorrect order type, price out of bounds, no liquidity.

## Response Format

```json
{
  "id": "exchange-assigned-order-id",
  "executions": [
    {
      "id": "execution-id",
      "order": {},
      "lastShares": "quantity-string",
      "lastPx": {"value": "0.55", "currency": "USD"},
      "type": "EXECUTION_TYPE_FILL",
      "transactTime": "ISO-8601-datetime"
    }
  ]
}
```

## Batch Limitations

Batch responses echo submitted IDs without confirming per-entry outcomes.
Use WebSocket private stream for real-time status.
