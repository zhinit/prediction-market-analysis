# Kalshi API

Kalshi exposes a REST API, WebSocket API, and FIX protocol for both its
event-contract (Predictions) and perpetual futures (Perps/Margin) exchanges.
(source: kalshi-api-overview-and-environments.md)

## Protocols

| Protocol  | Use case                  |
|-----------|---------------------------|
| REST      | Request/response queries and order management |
| WebSocket | Real-time streaming (orderbook, tickers, fills) |
| FIX       | Standard financial protocol for low-latency trading |

(source: kalshi-api-overview-and-environments.md)

## API Version

Current REST path prefix: `/trade-api/v2`. The V2 order endpoints use
fixed-point dollar strings for prices and fixed-point count strings for
quantities. Legacy integer-based fields are deprecated.
(source: kalshi-api-changelog-2026.md)

## Environments

See [[kalshi-api-environments]].

## Authentication

See [[kalshi-api-auth]].

## Rate Limits

See [[kalshi-api-rate-limits]].

## Key Endpoint Groups

- **Market data** (public, no auth): [[kalshi-api-market-data]]
- **Orders and portfolio** (authenticated): [[kalshi-api-orders]]
- **WebSocket streaming**: [[kalshi-api-websocket]]
- **SDKs**: [[kalshi-api-sdks]]

## Specifications

- REST OpenAPI: https://docs.kalshi.com/openapi.yaml
- WebSocket AsyncAPI: https://docs.kalshi.com/asyncapi.yaml
- Documentation index: https://docs.kalshi.com/llms.txt

(source: kalshi-api-overview-and-environments.md)

## Developer Agreement

Use of the API requires acceptance of Kalshi's Developer Agreement.
(source: kalshi-api-overview-and-environments.md)
