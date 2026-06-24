# Kalshi API Rate Limits

The API uses a token bucket model with separate read and write budgets. Both
REST and FIX requests draw from the same buckets.
(source: kalshi-api-rate-limits.md)

## How It Works

Every authenticated request costs tokens (default: 10). Your tier determines
the refill rate in tokens per second. Non-default endpoint costs are available
via `GET /account/endpoint_costs`. (source: kalshi-api-rate-limits.md)

## Buckets

- **Read**: GET endpoints and non-write operations
- **Write**: Order placement, amends, cancels, order groups, RFQ flows, block trade accepts

(source: kalshi-api-rate-limits.md)

## Tier Budgets (tokens/second, event-contract)

| Tier | Read | Write |
|------|------|-------|
| Basic | 200 | 100 |
| Advanced | 300 | 300 |
| Expert | 600 | 600 |
| Premier | 1,000 | 1,000 |
| Paragon | 2,000 | 2,000 |
| Prime | 4,000 | 4,000 |
| Prestige | 6,000 | 8,000 |

(source: kalshi-api-rate-limits.md)

## Burst Capacity

- Advanced Predictions Read, Basic+ Write: hold 2 seconds of budget
- Higher Predictions Read, Perps Read, Basic Write: hold 1 second only

(source: kalshi-api-rate-limits.md)

## Tier Qualification

Tiers are earned through trailing trading volume share, reviewed daily, with
30-day grants. Separate "Earn" and "Keep" thresholds prevent immediate
demotion. Qualification requirements were halved on June 25, 2026.
(source: kalshi-api-rate-limits.md, kalshi-api-changelog-2026.md)

## Rate Limit Response

429 Too Many Requests. No penalty — exponential backoff recommended.
(source: kalshi-api-rate-limits.md)
