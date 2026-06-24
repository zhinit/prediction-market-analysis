# Kalshi API Environments

Kalshi maintains separate production and demo environments. Credentials are
not shared between them — demo API keys only work against demo endpoints.
(source: kalshi-api-overview-and-environments.md)

## REST Base URLs

| Environment | URL |
|-------------|-----|
| Production (primary) | `https://external-api.kalshi.com/trade-api/v2` |
| Production (alt) | `https://api.elections.kalshi.com/trade-api/v2` |
| Demo (primary) | `https://external-api.demo.kalshi.co/trade-api/v2` |
| Demo (alt) | `https://demo-api.kalshi.co/trade-api/v2` |

The `external-api` hosts are recommended for API traders and are dedicated to
the Trade API. (source: kalshi-api-overview-and-environments.md)

## WebSocket URLs

| Environment | URL |
|-------------|-----|
| Production | `wss://external-api-ws.kalshi.com/trade-api/ws/v2` |
| Demo | `wss://external-api-ws.demo.kalshi.co/trade-api/ws/v2` |

(source: kalshi-api-websocket.md)

## Signing Path

When signing requests, use only the path portion excluding hostname and query
parameters. Sign `/trade-api/v2/portfolio/orders` regardless of which host is
used. (source: kalshi-api-overview-and-environments.md)
