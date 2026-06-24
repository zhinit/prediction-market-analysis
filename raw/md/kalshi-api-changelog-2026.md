# Kalshi API Changelog (2026)

Source: https://docs.kalshi.com/changelog
Fetched: 2026-06-24

---

RSS feed available at: https://docs.kalshi.com/changelog/rss.xml

Covers all three API surfaces (REST, WebSocket, FIX) across both exchange types (Predictions and Margin/Perps).

## June 2026

- **June 25**: API usage tier qualification requirements for all tiers halved
- **June 24**: FIX RFQ Quote creation now supports post-only behavior via `ExecInst=6`
- **June 23**: GET Quote rate-limit cost reduced to 2 tokens
- **June 20**: RFQ quote market/event filters removed from search functionality
- **June 19**: Communications RFQ/quote retention window reduced from 14 to 7 days
- **June 18**: Events API now returns `settlement_sources` for each event

## WebSocket Enhancements (recent)

- `market_lifecycle_v2` channel now includes `strike_type` and `cap_strike` in metadata updates
- FIX market data incremental refreshes include trade entries
- Sanity limits enforced: max 500k market subscriptions and 10k/s command rate

## Order System Modernization

- Legacy `/portfolio/orders` endpoints deprecated; V2 `/portfolio/events/orders` endpoints recommended
- V2 endpoints feature bid/ask single-book shape with fixed-point dollar prices
- Rate-limit costs increasing on legacy endpoints to encourage migration (10x cost effective June 11, 2026)

## Fixed-Point Migration

- Comprehensive shift from integer representations to fixed-point string fields
- New `_fp` suffix for contract quantities; `_dollars` for price/cost fields
- Legacy fields scheduled for removal March 12, 2026

## Rate Limiting System Overhaul

- Token-cost model replacing per-second scheme
- Separate read/write budgets with new Paragon tier
- Automated tier advancement based on trading volume
- Burst capacity for write endpoints

## Historical Data Split (February 19, 2026)

- Recent data at regular endpoints
- Settled or aged market data at dedicated `/historical/` endpoints

## Batched Orderbook (March 2026)

- Batched orderbook fetch endpoint supporting up to 100 tickers in one call

## FIX Protocol

Updates through versions v1.0.16 to v1.0.31 documented.
