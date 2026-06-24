# Kalshi API WebSocket

Source: https://docs.kalshi.com/getting_started/quick_start_websockets, https://docs.kalshi.com/websockets, https://docs.kalshi.com/websockets/websocket-connection
Fetched: 2026-06-24

---

## Connection URLs

**Production**: `wss://external-api-ws.kalshi.com/trade-api/ws/v2`
**Demo**: `wss://external-api-ws.demo.kalshi.co/trade-api/ws/v2`

## Authentication

Connections require three header parameters during handshake:
- `KALSHI-ACCESS-KEY`: API key identifier
- `KALSHI-ACCESS-SIGNATURE`: Request signature
- `KALSHI-ACCESS-TIMESTAMP`: Unix timestamp in milliseconds

The signature follows REST API patterns, combining timestamp + "GET" + "/trade-api/ws/v2" using RSA-PSS signing with SHA256 hashing.

## Channels

### Public Channels (no additional auth required)
- `ticker` — real-time ticker updates
- `trade` — trade notifications
- `market_lifecycle_v2` — market status changes (includes `strike_type` and `cap_strike`)
- `multivariate_market_lifecycle` — multivariate market changes
- `multivariate` — multivariate event data

### Private Channels (require per-channel authorization)
- `orderbook_delta` — orderbook incremental changes
- `fill` — user fill notifications
- `market_positions` — position changes
- `communications` — RFQ activity
- `order_group_updates` — order group changes

## Subscription Commands

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

Incoming messages include:
- `ticker` — ticker updates
- `orderbook_snapshot` — full orderbook state
- `orderbook_delta` — incremental orderbook changes (includes optional `client_order_id` field indicating user-caused changes)
- `error` — error notifications

## Error Codes

25 error codes documented:
- Code 1: Malformed JSON
- Code 10: Server-side issue (contact support)
- Code 17: Server-side issue (contact support)
- Code 18: Command timeout
- Code 25: Buffer overflow
- Most others are user errors

## Sanity Limits

- Max 500,000 market subscriptions
- Max 10,000 commands per second

## Implementation Notes

The Python `websockets` library handles keepalive automatically. Reconnection logic with exponential backoff is recommended.
