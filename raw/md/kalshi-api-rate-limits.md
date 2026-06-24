# Kalshi API Rate Limits and Tiers

Source: https://docs.kalshi.com/getting_started/rate_limits
Fetched: 2026-06-24

---

## Token-Based System

The Kalshi API uses a token bucket model. "Every authenticated request costs tokens." Most operations consume 10 tokens by default. Your tier determines your refill rate (tokens per second), with sustained capacity calculated as budget divided by cost.

Non-default endpoint costs can be checked via `GET /account/endpoint_costs`.

## Separate Read and Write Buckets

Two independent token budgets exist:
- **Read**: GET endpoints and non-Write operations
- **Write**: Order placement, amends, cancels, order groups, RFQ flows, and block trade accepts

Both REST and FIX requests draw from identical buckets.

## Burst Capacity

- **Advanced Predictions Read, Basic+ Write**: Hold 2 seconds of budget (burst up to 2x per-second rate)
- **Higher Predictions Read, Perps Read, Basic Write**: Hold 1 second of budget (no idle accumulation)

## Rate Limiting Response

When exceeded: "A rate-limited request returns `429 Too Many Requests`" with error body. No penalty exists; exponential backoff is recommended.

## Event-Contract Tier Budgets (tokens/second)

| Tier      | Read  | Write |
|-----------|-------|-------|
| Basic     | 200   | 100   |
| Advanced  | 300   | 300   |
| Expert    | 600   | 600   |
| Premier   | 1,000 | 1,000 |
| Paragon   | 2,000 | 2,000 |
| Prime     | 4,000 | 4,000 |
| Prestige  | 6,000 | 8,000 |

## Volume-Based Tier Qualification

Tiers are earned through trading volume share thresholds reviewed daily, with 30-day grants that renew continuously while qualifying. Separate "Earn" and "Keep" thresholds prevent immediate demotion from temporary dips.

Premier, Paragon, and Prime tiers are earned automatically from trailing trading volume (and can still be granted manually), each tier backed by a grant viewable in the new grants array of `GET /trade-api/v2/account/limits`.

## Recent Changes

- June 25, 2026: API usage tier qualification requirements for all tiers halved
- Legacy `/portfolio/orders` mutation and batch endpoint rate-limit token costs will be 10x the corresponding V2 `/portfolio/events/orders` endpoint costs (effective June 11, 2026)
- Write endpoints now allow brief bursts above per-second budget — unused capacity accumulates
