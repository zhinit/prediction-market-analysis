# Polymarket International API

The international Polymarket platform (polymarket.com) is the original
crypto-based prediction market. It operates on the Polygon blockchain using
pUSD as collateral. It is separate from [[polymarket-us-api]], which is
CFTC-regulated and USD-denominated (source: polymarket-us-api-overview.md).

## Architecture

Three API services (source: polymarket-us-api-overview.md):

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

Two-level system:
- **L1**: EIP-712 signatures using private key to derive API credentials
- **L2**: HMAC-SHA256 for trading operations

Four wallet types: EOA (type 0), POLY_PROXY (1), GNOSIS_SAFE (2), POLY_1271 (3).
New users use deposit wallets (type 3).

## SDKs

- TypeScript: `@polymarket/clob-client-v2`
- Python: `py-clob-client-v2` (archived; migrate to `py-sdk`)
- Rust: `polymarket_client_sdk_v2`

## WebSocket Channels

- Market channel — orderbook, price, market lifecycle updates (public)
- User channel — order and trade updates (authenticated)
- Sports channel — live sports scores (public)
- RFQ/Quoter gateway — combinatorial RFQ for market makers (authenticated)

## Key Differences from [[polymarket-us-api]]

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

- Docs: https://docs.polymarket.com
- LLM index: https://docs.polymarket.com/llms.txt
- OpenAPI specs available for all services

## See Also

- [[polymarket-us-api]] — the CFTC-regulated US platform
- [[prediction-market-platforms]] — platform comparison
