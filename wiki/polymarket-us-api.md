# Polymarket US API

Polymarket US is a CFTC-regulated prediction market platform, separate from the
international Polymarket (polymarket.com). The international version runs on
Polygon blockchain with pUSD; the US version uses USD-denominated accounts with
traditional financial infrastructure (source: polymarket-us-api-overview.md).

## Two API Tiers

The platform exposes two distinct API products (source: polymarket-us-api-overview.md):

**Exchange API** — for institutional participants (DMA, ISVs, IBs, FCMs).
Protocols: REST, gRPC, FIX. Auth: RSA/JWT via Auth0. Access requires
application, sandbox testing, and approval. FIX requires AWS PrivateLink VPC
setup (source: polymarket-us-api-environments.md).

**Retail API** — for individual users. Protocols: REST, WebSocket. Auth:
Ed25519 API key (Key ID + Secret Key) generated at polymarket.us/developer
after KYC. Self-service (source: polymarket-us-api-authentication.md).

## Base URLs

| API | URL |
|-----|-----|
| Retail (authenticated) | `https://api.polymarket.us` |
| Retail (public) | `https://gateway.polymarket.us` |
| Exchange (prod) | `https://api.prod.polymarketexchange.com` |
| Exchange (preprod) | `https://api.preprod.polymarketexchange.com` |
| Exchange (dev) | `https://api.dev01.polymarketexchange.com` |
| WebSocket (private) | `wss://api.polymarket.us/v1/ws/private` |
| WebSocket (markets) | `wss://api.polymarket.us/v1/ws/markets` |

(source: polymarket-us-api-overview.md, polymarket-us-api-environments.md)

## Authentication

Retail API requests require three headers: `X-PM-Access-Key` (UUID),
`X-PM-Timestamp` (unix ms, within 30s of server), `X-PM-Signature` (base64
Ed25519 over `timestamp + method + path`). Exchange API uses Private Key JWT
via Auth0; tokens refresh every 3 minutes (source: polymarket-us-api-authentication.md).

## Endpoint Summary

### Markets (public, no auth)
- `GET /v1/markets` — list with filtering (status, category, volume range, dates)
- `GET /v1/market/slug/{slug}` — single market
- `GET /v1/markets/{slug}/book` — full order book + stats
- `GET /v1/markets/{slug}/bbo` — best bid/offer only
- `GET /v1/markets/{slug}/settlement` — resolution price

(source: polymarket-us-api-markets.md)

### Events (public)
- `GET /v1/events` — list with filtering (status, category, dates, sports)
- `GET /v1/events/{id}` — single event

(source: polymarket-us-api-events.md)

### Orders (authenticated, 20 req/s rate limit)
- `POST /v1/orders` — create order
- `POST /v1/order/preview` — validate before submission
- `POST /v1/order/close-position` — exit position
- `GET /v1/orders/open` — list open orders
- `POST /v1/order/{id}/modify` — modify
- `POST /v1/order/{id}/cancel` — cancel
- Batch variants for up to 20 orders per request

(source: polymarket-us-api-orders.md)

### Portfolio (authenticated)
- `GET /v1/portfolio/positions` — positions by market slug
- `GET /v1/portfolio/activities` — transaction history (cursor-paginated)
- `GET /v1/account/balances` — balance, buying power, margin

(source: polymarket-us-api-portfolio.md)

## Order Mechanics

Order types: limit and market. Price always expressed as YES-side (YES + NO =
$1.00). Valid range: $0.01–$0.99. Intent can be specified as BUY_LONG,
SELL_LONG, BUY_SHORT, SELL_SHORT — or equivalently as outcomeSide + action.
TIF options: DAY, GTC, GTD, IOC, FOK. Markets define tick size and minimum
quantity (source: polymarket-us-api-orders.md).

## WebSocket

Two streams, both requiring auth. Markets stream supports full book (type 1),
lite pricing (type 2), and trade feed (type 3) — max 100 markets per
subscription. Private stream delivers order (type 1), position (type 3), and
balance (type 4) updates. Server sends heartbeats; reconnect with exponential
backoff if they stop (source: polymarket-us-api-websocket.md).

## Fees

Fee = Theta x C x p x (1 - p), symmetric around p = $0.50.

| Role | Theta | Max at p=$0.50 (per 100 contracts) |
|------|-------|------------------------------------|
| Taker | 0.05 | $1.25 |
| Maker | -0.0125 | -$0.31 (rebate) |

Maker rebate = 25% of taker fees. No fees on unfilled orders. Effective April
3, 2026 (source: polymarket-us-api-fees.md).

## Collateral Model

Fully collateralized — no leverage. Buyers pay the contract price; sellers post
$1.00 per contract. Portfolio-level margining across all positions. Trades fail
if buying power would go below zero. Settlement: winners get $1.00, losers get
$0, guaranteed by Polymarket Clearing (source: polymarket-us-api-collateral-margin.md).

## SDKs

- TypeScript: `npm install polymarket-us` (Node.js 18+)
- Python: `pip install polymarket-us` (Python 3.10+)

(source: polymarket-us-api-overview.md)

## Comparison with [[kalshi-api]]

Both are CFTC-regulated US prediction market platforms with REST + WebSocket
APIs, KYC requirements, and fully collateralized binary contracts settling at
$0/$1. Key differences in fee structure, authentication method, and institutional
API support (FIX protocol) warrant direct comparison.

## See Also

- [[polymarket-international-api]] — the crypto-based international platform
- [[polymarket-us-fees]] — detailed fee schedule
- [[prediction-market-platforms]] — platform comparison
