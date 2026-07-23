# Polymarket US WebSocket API

Two WebSocket endpoints, both requiring Ed25519 API key authentication in the
connection handshake (source: polymarket-us-ws-overview.md).

| Endpoint | Purpose |
|---|---|
| `wss://api.polymarket.us/v1/ws/markets` | Market data, order book, trades |
| `wss://api.polymarket.us/v1/ws/private` | Orders, positions, account balances |

## Connection Handshake

Three headers are required during the WebSocket upgrade request (source:
polymarket-us-ws-overview.md):

| Header | Value |
|---|---|
| `X-PM-Access-Key` | API key identifier |
| `X-PM-Timestamp` | Current time in milliseconds |
| `X-PM-Signature` | Base64-encoded Ed25519 signature |

The signature message is `{timestamp}GET{path}`, where path is `/v1/ws/private`
or `/v1/ws/markets`. Timestamps must be within 30 seconds of server time
(source: polymarket-us-ws-authentication.md).

Python signature construction (source: polymarket-us-ws-authentication.md):

```python
import time, base64
from cryptography.hazmat.primitives.asymmetric import ed25519

private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
    base64.b64decode("YOUR_SECRET_KEY")[:32]
)

def auth_headers(method, path):
    timestamp = str(int(time.time() * 1000))
    message = f"{timestamp}{method}{path}"
    signature = base64.b64encode(private_key.sign(message.encode())).decode()
    return {
        "X-PM-Access-Key": "YOUR_KEY_ID",
        "X-PM-Timestamp": timestamp,
        "X-PM-Signature": signature,
    }
```

## Heartbeat

The server sends periodic heartbeat messages (source: polymarket-us-ws-overview.md):

```json
{"heartbeat": {}}
```

Clients should respond to heartbeats or implement their own keep-alive
mechanism.

## Markets Stream

Three subscription types on the markets endpoint (source:
polymarket-us-ws-markets-stream.md):

| Type | Key | Description |
|---|---|---|
| `SUBSCRIPTION_TYPE_MARKET_DATA` | `marketData` | Full order book + stats |
| `SUBSCRIPTION_TYPE_MARKET_DATA_LITE` | `marketDataLite` | BBO + price only |
| `SUBSCRIPTION_TYPE_TRADE` | `trade` | Trade notifications |

Maximum 100 markets per subscription; use multiple subscriptions for more
(source: polymarket-us-ws-markets-stream.md).

### Subscription Request

```json
{
  "subscribe": {
    "requestId": "md-sub-1",
    "subscriptionType": "SUBSCRIPTION_TYPE_MARKET_DATA",
    "marketSlugs": ["market-slug-1", "market-slug-2"]
  }
}
```

Optional field `"responsesDebounced": true` batches updates at regular
intervals instead of firing on every change (source:
polymarket-us-ws-markets-stream.md).

### Full Book Response (SUBSCRIPTION_TYPE_MARKET_DATA)

Every update delivers the complete order book — there is no snapshot + delta
mode. Bids are sorted highest-first; offers are sorted lowest-first (source:
polymarket-us-ws-markets-stream.md).

```json
{
  "requestId": "md-sub-1",
  "subscriptionType": "SUBSCRIPTION_TYPE_MARKET_DATA",
  "marketData": {
    "marketSlug": "market-slug-1",
    "bids": [
      {"px": {"value": "0.555", "currency": "USD"}, "qty": "0.50"},
      {"px": {"value": "0.550", "currency": "USD"}, "qty": "2.50"}
    ],
    "offers": [
      {"px": {"value": "0.560", "currency": "USD"}, "qty": "0.80"},
      {"px": {"value": "0.565", "currency": "USD"}, "qty": "1.50"}
    ],
    "state": "MARKET_STATE_OPEN",
    "stats": {
      "lastTradePx": {"value": "0.55", "currency": "USD"},
      "sharesTraded": "150000",
      "openInterest": "500000",
      "highPx": {"value": "0.58", "currency": "USD"},
      "lowPx": {"value": "0.52", "currency": "USD"}
    },
    "transactTime": "2024-01-15T10:30:00Z"
  }
}
```

Price fields use `{"value": "string", "currency": "USD"}` format. Quantity
fields (`qty`) are strings (source: polymarket-us-ws-markets-stream.md).

### Lite Response (SUBSCRIPTION_TYPE_MARKET_DATA_LITE)

```json
{
  "requestId": "mdl-sub-1",
  "subscriptionType": "SUBSCRIPTION_TYPE_MARKET_DATA_LITE",
  "marketDataLite": {
    "marketSlug": "market-slug-1",
    "currentPx": {"value": "0.55", "currency": "USD"},
    "lastTradePx": {"value": "0.55", "currency": "USD"},
    "bestBid": {"value": "0.54", "currency": "USD"},
    "bestAsk": {"value": "0.56", "currency": "USD"},
    "bidDepth": 5,
    "askDepth": 4,
    "sharesTraded": "150000",
    "openInterest": "500000"
  }
}
```

(source: polymarket-us-ws-markets-stream.md)

### Trade Response (SUBSCRIPTION_TYPE_TRADE)

```json
{
  "requestId": "trade-sub-1",
  "subscriptionType": "SUBSCRIPTION_TYPE_TRADE",
  "trade": {
    "marketSlug": "market-slug-1",
    "price": {"value": "0.555", "currency": "USD"},
    "quantity": {"value": "0.50", "currency": "USD"},
    "tradeTime": "2024-01-15T10:30:00Z",
    "maker": {
      "side": "ORDER_SIDE_BUY",
      "intent": "ORDER_INTENT_BUY_LONG"
    },
    "taker": {
      "side": "ORDER_SIDE_SELL",
      "intent": "ORDER_INTENT_SELL_LONG"
    }
  }
}
```

(source: polymarket-us-ws-markets-stream.md)

## Private Stream

Four subscription types on the private endpoint (source:
polymarket-us-ws-private-stream.md):

| Type | Description |
|---|---|
| `SUBSCRIPTION_TYPE_ORDER` | Order updates (new, filled, canceled) |
| `SUBSCRIPTION_TYPE_ORDER_SNAPSHOT` | Initial snapshot of open orders |
| `SUBSCRIPTION_TYPE_POSITION` | Position changes |
| `SUBSCRIPTION_TYPE_ACCOUNT_BALANCE` | Balance changes |

Leave `marketSlugs` empty to subscribe to all markets (source:
polymarket-us-ws-private-stream.md).

### Order Snapshot

```json
{
  "requestId": "order-sub-1",
  "subscriptionType": "SUBSCRIPTION_TYPE_ORDER",
  "orderSubscriptionSnapshot": {
    "orders": [
      {
        "id": "order-123",
        "marketSlug": "market-slug-1",
        "side": "ORDER_SIDE_BUY",
        "type": "ORDER_TYPE_LIMIT",
        "price": {"value": "0.555", "currency": "USD"},
        "quantity": 0.5,
        "leavesQuantity": 0.5,
        "state": "ORDER_STATE_PENDING_NEW",
        "intent": "ORDER_INTENT_BUY_LONG",
        "tif": "TIME_IN_FORCE_GOOD_TILL_CANCEL"
      }
    ],
    "eof": true
  }
}
```

(source: polymarket-us-ws-private-stream.md)

### Order Update (Execution)

```json
{
  "requestId": "order-sub-1",
  "subscriptionType": "SUBSCRIPTION_TYPE_ORDER",
  "orderSubscriptionUpdate": {
    "execution": {
      "id": "exec-456",
      "lastShares": "0.25",
      "lastPx": {"value": "0.555", "currency": "USD"},
      "type": "EXECUTION_TYPE_PARTIAL_FILL",
      "tradeId": "trade-789"
    }
  }
}
```

`lastShares` is a string and may contain decimals for partial-contract markets
(source: polymarket-us-ws-private-stream.md).

### Position Update

```json
{
  "requestId": "pos-sub-1",
  "subscriptionType": "SUBSCRIPTION_TYPE_POSITION",
  "positionSubscription": {
    "beforePosition": {
      "netPosition": "1",
      "netPositionDecimal": "1.0000",
      "cost": {"value": "55.00", "currency": "USD"}
    },
    "afterPosition": {
      "netPosition": "2",
      "netPositionDecimal": "1.5000",
      "cost": {"value": "82.50", "currency": "USD"}
    },
    "updateTime": "2024-01-15T10:30:00Z",
    "entryType": "LEDGER_ENTRY_TYPE_ORDER_EXECUTION",
    "tradeId": "trade-789"
  }
}
```

Additional decimal fields: `qtyBoughtDecimal`, `qtySoldDecimal`,
`bodPositionDecimal`, `qtyAvailableDecimal` (source:
polymarket-us-ws-private-stream.md).

### Account Balance

Snapshot includes `currentBalance`, `currency`, `buyingPower`. Updates include
`beforeBalance`/`afterBalance` diffs with `entryType` indicating the cause
(source: polymarket-us-ws-private-stream.md).

## Enumerations

### Market States

`MARKET_STATE_OPEN`, `MARKET_STATE_PREOPEN`, `MARKET_STATE_SUSPENDED`,
`MARKET_STATE_HALTED`, `MARKET_STATE_EXPIRED`, `MARKET_STATE_TERMINATED`,
`MARKET_STATE_MATCH_AND_CLOSE_AUCTION` (source:
polymarket-us-ws-markets-stream.md).

### Execution Types

`EXECUTION_TYPE_PARTIAL_FILL`, `EXECUTION_TYPE_FILL`,
`EXECUTION_TYPE_CANCELED`, `EXECUTION_TYPE_REPLACE`,
`EXECUTION_TYPE_REJECTED`, `EXECUTION_TYPE_EXPIRED`,
`EXECUTION_TYPE_DONE_FOR_DAY` (source: polymarket-us-ws-private-stream.md).

### Ledger Entry Types

`LEDGER_ENTRY_TYPE_ORDER_EXECUTION`, `LEDGER_ENTRY_TYPE_DEPOSIT`,
`LEDGER_ENTRY_TYPE_WITHDRAWAL`, `LEDGER_ENTRY_TYPE_RESOLUTION`,
`LEDGER_ENTRY_TYPE_COMMISSION`, `LEDGER_ENTRY_TYPE_CORRECTION`,
`LEDGER_ENTRY_TYPE_NETTING`, `LEDGER_ENTRY_TYPE_MANUAL_ADJUSTMENT`,
`LEDGER_ENTRY_TYPE_CONTRACT_EXPIRATION` (source:
polymarket-us-ws-private-stream.md).

### Order States

`ORDER_STATE_PENDING_NEW`, `ORDER_STATE_PENDING_REPLACE`,
`ORDER_STATE_PENDING_CANCEL`, `ORDER_STATE_PENDING_RISK`,
`ORDER_STATE_PARTIALLY_FILLED`, `ORDER_STATE_FILLED`,
`ORDER_STATE_CANCELED`, `ORDER_STATE_REPLACED`, `ORDER_STATE_REJECTED`,
`ORDER_STATE_EXPIRED` (source: polymarket-us-ws-private-stream.md).

### Order Intents

`ORDER_INTENT_BUY_LONG` (buy YES), `ORDER_INTENT_SELL_LONG` (sell YES),
`ORDER_INTENT_BUY_SHORT` (buy NO), `ORDER_INTENT_SELL_SHORT` (sell NO)
(source: polymarket-us-ws-markets-stream.md).

## TypeScript SDK

The SDK wraps both endpoints with typed event handlers (source:
polymarket-us-sdk-typescript-websocket.md):

```typescript
import { PolymarketUS } from 'polymarket-us';

const client = new PolymarketUS({
  keyId: process.env.POLYMARKET_KEY_ID,
  secretKey: process.env.POLYMARKET_SECRET_KEY,
});

// Markets stream
const ws = client.ws.markets();
await ws.connect();
ws.subscribeMarketData('book', ['btc-100k-2025']);
ws.subscribeMarketDataLite('prices', ['btc-100k-2025']);
ws.subscribeTrades('trades', ['btc-100k-2025']);

// Private stream
const priv = client.ws.private();
await priv.connect();
priv.subscribeOrders('my-orders');
priv.subscribePositions('my-positions');
priv.subscribeAccountBalance('my-balance');
```

SDK events: `marketData`, `marketDataLite`, `trade`, `orderSnapshot`,
`orderUpdate`, `positionSnapshot`, `positionUpdate`,
`accountBalanceSnapshot`, `accountBalanceUpdate` (source:
polymarket-us-sdk-typescript-websocket.md).

## Wire Format Note

The overview page shows `snake_case` field names with numeric subscription
types (`subscription_type: 1`), while the markets and private pages use
`camelCase` with string enum types (`subscriptionType:
"SUBSCRIPTION_TYPE_MARKET_DATA"`). The detailed per-endpoint pages and the
TypeScript SDK both use the camelCase/string-enum format (source:
polymarket-us-ws-overview.md, polymarket-us-ws-markets-stream.md).

## Comparison with [[kalshi-api-websocket]]

Kalshi uses a snapshot + delta model (`orderbook_delta` channel) where the
initial message is a full book and subsequent messages are incremental changes.
Polymarket US sends the full order book on every update with no delta mode
(source: polymarket-us-ws-markets-stream.md). Kalshi's WebSocket is
unauthenticated for market data; Polymarket US requires auth on both endpoints
(source: polymarket-us-ws-overview.md).

## Related pages

- [[polymarket-us-api]] — API overview, endpoints, authentication
- [[polymarket-us-market-object]] — market object schema, REST book/BBO
- [[kalshi-api-websocket]] — Kalshi's WebSocket (snapshot + delta model)
