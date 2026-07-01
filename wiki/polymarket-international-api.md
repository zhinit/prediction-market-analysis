# Polymarket International API

> Note: no dedicated raw source for the international Polymarket platform has
> been archived yet. Sections below without a citation are tagged as
> unverified pending /research.

The international Polymarket platform (polymarket.com) operates on the Polygon
blockchain. It is separate from [[polymarket-us-api]], which is CFTC-regulated
and USD-denominated (source: polymarket-us-api-overview.md). It reportedly
uses pUSD as collateral (unverified — no archived source; pending /research).

## Architecture

(unverified — no archived source; pending /research)

Three API services plus a bridge:

1. **Gamma API** (`https://gamma-api.polymarket.com`) — markets, events, tags,
   series, comments, sports, search, profiles. Public, no auth.

2. **Data API** (`https://data-api.polymarket.com`) — positions, trades,
   activity, holders, open interest, leaderboards, builder analytics. Public,
   no auth.

3. **CLOB API** (`https://clob.polymarket.com`) — orderbook, pricing,
   midpoints, spreads, price history, order placement/cancellation.
   Market data: public. Trading: authenticated.

4. **Bridge API** (`https://bridge.polymarket.com`) — deposits/withdrawals via
   fun.xyz proxy.

## Authentication

(unverified — no archived source; pending /research)

Two-level system:
- **L1**: EIP-712 signatures using private key to derive API credentials
- **L2**: HMAC-SHA256 for trading operations

Four wallet types: EOA (type 0), POLY_PROXY (1), GNOSIS_SAFE (2), POLY_1271 (3).
New users use deposit wallets (type 3).

## SDKs

(unverified — no archived source; pending /research)

- TypeScript: `@polymarket/clob-client-v2`
- Python: `py-clob-client-v2` (archived; migrate to `py-sdk`)
- Rust: `polymarket_client_sdk_v2`

## WebSocket Channels

(unverified — no archived source; pending /research)

- Market channel — orderbook, price, market lifecycle updates (public)
- User channel — order and trade updates (authenticated)
- Sports channel — live sports scores (public)
- RFQ/Quoter gateway — combinatorial RFQ for market makers (authenticated)

## Key Differences from [[polymarket-us-api]]

The US platform is CFTC-regulated, USD-denominated, and offers FIX and gRPC
for its Exchange API (source: polymarket-us-api-overview.md). The
international-side entries in this table are unverified — no archived source;
pending /research.

| Aspect | International | US |
|--------|--------------|-----|
| Regulator | None (crypto) | CFTC |
| Collateral | pUSD (Polygon) | USD |
| Auth | EIP-712 + HMAC | Ed25519 / RSA JWT |
| Settlement | On-chain (Polygon) | Centralized clearing |
| FIX protocol | No | Yes (institutional) |
| gRPC | No | Yes |
| Geographic | Blocked in US | US only |

## Documentation

(unverified — no archived source; pending /research)

- Docs: https://docs.polymarket.com
- LLM index: https://docs.polymarket.com/llms.txt
- OpenAPI specs available for all services

## See Also

- [[polymarket-us-api]] — the CFTC-regulated US platform
- Platform comparison: see the Key Differences table above
