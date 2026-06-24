# Kalshi API WebSocket

Real-time streaming via WebSocket. Requires authentication at connection
time using the same RSA-PSS signing as REST.
(source: kalshi-api-websocket.md)

## Connection

- Production: `wss://external-api-ws.kalshi.com/trade-api/ws/v2`
- Demo: `wss://external-api-ws.demo.kalshi.co/trade-api/ws/v2`

Sign: `timestamp + "GET" + "/trade-api/ws/v2"` and pass the three
`KALSHI-ACCESS-*` headers during the handshake.
(source: kalshi-api-websocket.md)

## Channels

### Public (no per-channel auth)

| Channel | Description |
|---------|-------------|
| `ticker` | Real-time ticker updates |
| `trade` | Trade notifications |
| `market_lifecycle_v2` | Market status changes (includes strike_type, cap_strike) |
| `multivariate_market_lifecycle` | Multivariate market changes |
| `multivariate` | Multivariate event data |

### Private (require per-channel auth)

| Channel | Description |
|---------|-------------|
| `orderbook_delta` | Incremental orderbook changes |
| `fill` | User fill notifications |
| `market_positions` | Position changes |
| `communications` | RFQ activity |
| `order_group_updates` | Order group changes |

(source: kalshi-api-websocket.md)

## Subscription Format

```json
{
  "id": 1,
  "cmd": "subscribe",
  "params": {
    "channels": ["ticker", "orderbook_delta"],
    "market_tickers": ["HIGHNY-24JAN01-T60"]
  }
}
```

## Message Types

`ticker`, `orderbook_snapshot`, `orderbook_delta`, `error`.
The `orderbook_delta` type includes an optional `client_order_id` field
indicating user-caused changes. (source: kalshi-api-websocket.md)

## Limits

- Max 500,000 market subscriptions
- Max 10,000 commands per second

(source: kalshi-api-websocket.md)
