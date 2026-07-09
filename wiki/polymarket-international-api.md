# Polymarket International API

The international Polymarket platform (polymarket.com) operates on the Polygon
blockchain. It is separate from [[polymarket-us-api]], which is CFTC-regulated
and USD-denominated. Collateral is pUSD on Polygon (source:
polymarket-international-api-parlay-guide.md).

## Architecture

Three API services plus a bridge (source: polymarket-international-docs-intro.md,
polymarket-international-api-parlay-guide.md):

1. **Gamma API** (`https://gamma-api.polymarket.com`) — markets, events, tags,
   series, comments, sports, search, profiles. Public, no auth.

2. **Data API** (`https://data-api.polymarket.com`) — positions, trades,
   activity, holders, open interest, leaderboards, builder analytics. Public,
   no auth.

3. **CLOB API** (`https://clob.polymarket.com`) — orderbook, pricing,
   midpoints, spreads, price history, order placement/cancellation.
   Market data: public. Trading: authenticated.

4. **Bridge API** (`https://bridge.polymarket.com`) — deposits/withdrawals via
   fun.xyz proxy (source: polymarket-international-docs-intro.md).

## Data Model

Events contain multiple Markets, each with YES/NO tokens. Each token has a
unique `asset_id`. Orderbook operates at the token level. Every market includes
a `condition_id` (on-chain identifier) and `neg_risk` flag that determines
which signing contract to use (source: polymarket-international-api-parlay-guide.md).

## Authentication

Two-level system (source: polymarket-international-api-parlay-guide.md):

**L1 (one-time):** EIP-712 signature via wallet derives `apiKey`, `secret`,
`passphrase` using `ClobAuthDomain` (always `version: "1"`, even post-V2).

**L2 (per-request):** HMAC-SHA256 signs
`timestamp_seconds + METHOD + path + body` using derived secret.

Five headers on authenticated requests: `POLY_ADDRESS`, `POLY_API_KEY`,
`POLY_PASSPHRASE`, `POLY_TIMESTAMP`, `POLY_SIGNATURE`.

Four wallet types: EOA (type 0), POLY_PROXY (1), GNOSIS_SAFE (2),
deposit wallet (3). New users use type 3.

## Key Endpoints

### Discovery (Gamma, no auth)
- `GET /markets/keyset` — cursor-paginated market list (max 100)
- `GET /markets/slug/{slug}` — single market
- `GET /public-search` — text search

### Pricing (CLOB, no auth)
- `GET /book?token_id=...` — full orderbook
- `GET /price`, `/midpoint`, `/spread`
- `GET /prices-history` — historical series

### Trading (CLOB, L2 auth)
- `POST /order` — single order
- `POST /orders` — batch (max 15)
- `DELETE /order` — cancel by ID
- `DELETE /cancel-all` — cancel all

### Analytics (Data, no auth)
- `GET /positions?user=0x...` — open positions
- `GET /trades?user=0x...` — fill history
- `GET /leaderboard` — global rankings

(source: polymarket-international-api-parlay-guide.md)

## Order Types

| Type | Behavior |
|------|----------|
| GTC | Rests on book until matched or canceled |
| FOK | Fill entire size immediately or cancel |
| GTD | Rests until `expiration` timestamp |
| FAK | Fill available, cancel remainder |

(source: polymarket-international-api-parlay-guide.md)

## Rate Limits

Global: 15,000 requests per 10-second window. No tier system (source:
polymarket-international-api-parlay-guide.md).

| Endpoint | Limit (per 10s) |
|----------|----------------|
| Gamma `/markets` | 300 |
| CLOB `/book` | 1,500 |
| Trading `POST /order` | 5,000 burst; 48,000/10-min sustained |

Cloudflare returns 429 with no `Retry-After` header (source:
polymarket-international-api-parlay-guide.md).

## Pagination

Keyset endpoints use cursor-based pagination: `limit` (max 100),
`after_cursor`. Do not pass `offset` to keyset endpoints (returns 422)
(source: polymarket-international-api-parlay-guide.md).

## WebSocket

URL: `wss://ws-subscriptions-clob.polymarket.com` (source:
polymarket-international-api-parlay-guide.md)

**Market channel** (public): subscribe with `{"assets_ids": [...], "type": "market"}`.
Events: `book`, `price_change`, `last_trade_price`, `tick_size_change`.
Client heartbeat every 10 seconds.

**User channel** (L2 auth): subscribe includes `auth: {apiKey, secret, passphrase}`.
Events: `order`, `trade`. Same heartbeat.

## Geographic Restrictions

Read endpoints are not geo-blocked. Trading is restricted by tier (source:
polymarket-international-geoblock.md):

- **Complete block** (OFAC-sanctioned): Iran, Syria, Cuba, North Korea, Crimea,
  Donetsk, Luhansk
- **Close-only (API + frontend)**: US, UK, France, Germany, Belgium, Australia,
  Brazil, Canada (some provinces), Russia, Singapore, Taiwan, Thailand, 20+ others
- **Close-only (frontend only)**: Japan, Netherlands, Malta (sports only) — API
  still permits new orders

See [[polymarket-us-geographic-restrictions]] for US state-level details.

## SDKs

- Python: `polymarket-client` via `py-sdk` (beta, replaces archived `py-clob-client`)
  (source: polymarket-py-sdk.md)
- TypeScript: `@polymarket/clob-client-v2`

(source: polymarket-international-docs-intro.md, polymarket-py-sdk.md)

## Key Differences from [[polymarket-us-api]]

| Aspect | International | US |
|--------|--------------|-----|
| Regulator | None (crypto) | CFTC |
| Collateral | pUSD (Polygon) | USD |
| Auth | EIP-712 + HMAC | Ed25519 / RSA JWT |
| Settlement | On-chain (Polygon) | Centralized clearing |
| FIX protocol | No | Yes (institutional) |
| gRPC | No | Yes |
| Geographic | Blocked in US for trading | US only |

(source: polymarket-us-api-overview.md, polymarket-international-api-parlay-guide.md)

## Related pages

- [[polymarket-us-api]] — the CFTC-regulated US platform
- [[polymarket-us-geographic-restrictions]] — US state-level access
