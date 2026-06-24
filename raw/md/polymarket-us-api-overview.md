# Polymarket US API Overview

Source: https://docs.polymarket.us (multiple pages)
Fetched: 2026-06-24

## Platform

Polymarket US is a CFTC-regulated prediction market platform, distinct from the
international Polymarket (polymarket.com) which operates on the Polygon
blockchain. Polymarket US uses USD-denominated accounts with traditional
financial infrastructure.

## Two API Tiers

1. **Exchange API** — for professional participants (DMA Participants, ISVs,
   IBs, FCMs). Supports REST, gRPC, and FIX protocols. Uses RSA/JWT
   authentication via Auth0. Comprehensive trading, clearing, and account
   management.

2. **Retail API** — for individual app users. Supports REST and WebSocket.
   Uses Ed25519 API key authentication. Self-service, limited to personal
   accounts.

## Base URLs

### Retail API
- Authenticated API: `https://api.polymarket.us`
- Public API: `https://gateway.polymarket.us`

### Exchange API (REST/gRPC)
- Development: `https://api.dev01.polymarketexchange.com`
- Pre-Production: `https://api.preprod.polymarketexchange.com`
- Production: `https://api.prod.polymarketexchange.com`

REST endpoints follow `/v1/{service}/{operation}`.
Health check: `GET /v1/health`.

### WebSocket
- Private: `wss://api.polymarket.us/v1/ws/private`
- Markets: `wss://api.polymarket.us/v1/ws/markets`

### Auth0 Domains (Exchange API)
- Dev: `pmx-dev01.us.auth0.com`
- Preprod: `pmx-preprod.us.auth0.com`
- Prod: `pmx-prod.us.auth0.com`

## Functional Areas

1. **Trading** — order placement, modification, cancellation, execution monitoring
2. **Market Data** — real-time order books, BBO, price history
3. **Account** — balances, positions, P&L
4. **Capital Management** — deposits, withdrawals
5. **Historical** — order/trade history, compliance reporting

## Organizational Hierarchy

Clearing Member → Participant Firm → User → Trading Account

## Access Requirements

### Retail API
- Download the Polymarket US app
- Complete identity verification (KYC)
- Generate API credentials at polymarket.us/developer
- Credentials: Key ID + Secret Key

### Exchange API
- Apply for access (contact support@polymarket.us)
- Complete integration testing in sandbox
- Obtain production credentials after approval
- Comply with CFTC regulations and exchange rules

### FIX Protocol
- VPC connections required (AWS PrivateLink)
- Contact fix@polymarket.us for onboarding

## SDKs

- TypeScript: `npm install polymarket-us` (Node.js 18+)
- Python: `pip install polymarket-us` (Python 3.10+)

## Rate Limits

Orders API: 20 requests per second per key.

## Contact

- General: support@polymarket.us
- Onboarding: onboarding@polymarket.us
- FIX protocol: fix@polymarket.us

## Documentation

- Full docs: https://docs.polymarket.us
- LLM index: https://docs.polymarket.us/llms.txt
- Developer resources: https://www.polymarketexchange.com/developers.html
