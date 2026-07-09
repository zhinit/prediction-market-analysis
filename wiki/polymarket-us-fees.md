# Polymarket US Fees

## Formula

Fee = Theta x C x p x (1 - p)

Where C is the number of contracts, p is the trade price ($0.01–$0.99), and
Theta is the fee coefficient (source: polymarket-us-fees-july-2026.md).

## Coefficients

| Role | Theta |
|------|-------|
| Taker | 0.06 |
| Maker | -0.0125 |

Maker rebate equals 25% of taker fees (20% on Crypto markets), credited at
time of fill (source: polymarket-us-fees-july-2026.md).

## Schedule (per 1,000 contracts)

| Price | Taker Fee | Maker Rebate |
|-------|-----------|--------------|
| $0.10 | $5.40 | $1.13 |
| $0.25 | $11.25 | $2.34 |
| $0.50 | $15.00 | $3.13 |
| $0.75 | $11.25 | $2.34 |
| $0.90 | $5.40 | $1.13 |

Fees are symmetric around $0.50 and lowest near extremes. Banker's rounding
applied (source: polymarket-us-fees-july-2026.md).

## Volume-Based Taker Rebate Tiers

| Prior Calendar-Month Taker Volume | Rebate |
|-----------------------------------|--------|
| $250,000 – $999,999 | 10% |
| $1,000,000 – $4,999,999 | 25% |
| $5,000,000+ | 50% |

(source: polymarket-us-fees-july-2026.md)

## Fee History

- April 3, 2026: initial fee schedule (theta taker = 0.05, max $1.25/100 at
  p=$0.50) (source: polymarket-us-api-fees.md)
- July 1, 2026: taker theta increased to 0.06, max $1.50/100 at p=$0.50;
  volume-based taker rebate tiers added (source: polymarket-us-fees-july-2026.md)

## Key Rules

- Fees charged only on execution — no cost for canceled/expired/rejected orders
- Taker fees deducted immediately
- Maker rebates credited immediately upon fill

(source: polymarket-us-fees-july-2026.md)

## Category-Specific Rates (Unverified)

Third-party sources report category-specific max taker fees per 100 contracts
at p=$0.50: Sports $0.75, Politics/Finance/Tech $1.00, Economics/Culture/Weather
$1.25, Crypto $1.80, Geopolitics free. These figures are not confirmed by the
official fee docs, which show a uniform theta=0.06 formula. The discrepancy
may reflect different theta values per category (source:
polymarket-us-fees-july-2026.md).

## Comparison with [[kalshi-fees]]

Both platforms use price-dependent fee formulas that peak at p=$0.50 and
decline toward extremes (source: polymarket-us-fees-july-2026.md,
kalshi-fees.md).

## Related pages

- [[polymarket-us-api]] — full API reference
