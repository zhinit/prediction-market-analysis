# Polymarket US WebSocket API

Source: https://docs.polymarket.us/api-reference/websocket/overview,
       https://docs.polymarket.us/api-reference/websocket/markets
Fetched: 2026-06-24

## Endpoints

- Private: `wss://api.polymarket.us/v1/ws/private`
  - Orders, positions, account balance updates
- Markets: `wss://api.polymarket.us/v1/ws/markets`
  - Market data, order book, trades

## Authentication

Both endpoints require API key authentication in the connection handshake.

Headers:
- `X-PM-Access-Key` — API key ID
- `X-PM-Timestamp` — current time in milliseconds
- `X-PM-Signature` — base64 Ed25519 signature of `timestamp + "GET" + path`

## Message Format

JSON with snake_case fields. Requests include a unique request ID, subscription
type number, and optional market identifiers.

## Private Stream Subscriptions

| Type | Number | Data |
|------|--------|------|
| Orders | 1 | Order notifications |
| Positions | 3 | Position changes |
| Balances | 4 | Balance modifications |

## Markets Stream Subscriptions

| Type | Number | Data |
|------|--------|------|
| Full market data | 1 | Complete order book + stats |
| Lite market data | 2 | Simplified pricing |
| Trades | 3 | Real-time trade executions |

## Full Market Data (Type 1)

- Bid/ask levels with price and quantity
- Market state
- Last trade price
- Volume traded
- Open interest
- Daily high/low

## Lite Market Data (Type 2)

- Current price
- Best bid/ask
- Depth indicators
- Volume
- Open interest

## Trade Stream (Type 3)

Per-trade messages:
- Market identifier
- Execution price and quantity
- Timestamp
- Maker/taker details (order side: buy/sell, intent: long/short)

## Limits

Maximum 100 markets per subscription.

## Optional Features

- Debouncing: batch updates at regular intervals instead of on every change

## Heartbeats

Server sends periodic heartbeat messages. Reconnect if heartbeats stop.

## Best Practices

- Use unique request IDs to track subscriptions
- Implement automatic reconnection with exponential backoff
- Process messages sequentially
- Monitor heartbeats
- Subscribe selectively to needed markets only
