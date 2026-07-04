# Kalshi Fees

Kalshi charges trading fees per contract using a probability-weighted
formula. Taker fee per contract is 7¢ × C × (1 − C), where C is the
contract price between $0.01 and $0.99 (source: kalshi-fees.md). Maker
fee is 25% of the taker fee, i.e. 1.75¢ × C × (1 − C) per contract
(source: kalshi-fee-schedule-2026-detailed.md).

## Fee formula and properties

The taker fee peaks at the 50c price point — 7¢ × 0.5 × 0.5 = 1.75¢ per
contract — and falls toward the extremes: 0.63¢ at 10c or 90c. Fees never
exceed $0.02 per contract (source: kalshi-fees.md). The fee is symmetric
around 50c: prices equally distant from 50c pay the same fee. The fee is
charged on the "expected earnings on the contract" (source:
kalshi-fees.md).

There are no fees for canceling resting orders; maker fees apply only
when resting orders execute (source: kalshi-fees.md).

## Fee schedule by price point

| Contract price | Taker fee | Maker fee | Fee as % of cost |
|---|---|---|---|
| 5¢ | 0.33¢ | 0.08¢ | 6.65% |
| 10¢ | 0.63¢ | 0.16¢ | 6.30% |
| 20¢ | 1.12¢ | 0.28¢ | 5.60% |
| 30¢ | 1.47¢ | 0.37¢ | 4.90% |
| 40¢ | 1.68¢ | 0.42¢ | 4.20% |
| 50¢ | 1.75¢ | 0.44¢ | 3.50% |
| 60¢ | 1.68¢ | 0.42¢ | 2.80% |
| 70¢ | 1.47¢ | 0.37¢ | 2.10% |
| 80¢ | 1.12¢ | 0.28¢ | 1.40% |
| 90¢ | 0.63¢ | 0.16¢ | 0.70% |
| 95¢ | 0.33¢ | 0.08¢ | 0.35% |

(source: kalshi-fee-schedule-2026-detailed.md)

Because the fee scales with C × (1 − C) while the cost of a contract
scales with C, the fee as a share of capital is highest for cheap
contracts (6.65% at 5c) and lowest for expensive ones (0.35% at 95c)
(source: kalshi-fee-schedule-2026-detailed.md).

## Per-market variation

Some markets have different fee schedules — elections and major sporting
events are the named examples (source: kalshi-fees.md). The 2026 fee
schedule states there are no volume discounts or tiered pricing and no
settlement fees, and describes the structure as stable as of March 2026
(source: kalshi-fee-schedule-2026-detailed.md). The two sources are not
fully aligned: the earlier capture also mentions Volume Incentive and
Liquidity Incentive Programs (source: kalshi-fees.md), which the 2026
schedule does not list. Whether a specific market series (e.g. MLB game
markets) uses the standard formula is not settled by these sources.

## Deposit and withdrawal fees

ACH bank transfers are free in both directions (1–3 business days). Wire
transfers cost $25 each way (same day). Debit card deposits cost ~2%
(instant) (source: kalshi-fee-schedule-2026-detailed.md).

## Related pages

- [[kalshi-api]]
- [[kalshi-api-orders]]
- [[kalshi-market-object]]
