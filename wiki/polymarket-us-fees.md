# Polymarket US Fees

## Formula

Fee = Theta x C x p x (1 - p)

Where C is the number of contracts, p is the trade price ($0.01–$0.99), and
Theta is the fee coefficient (source: polymarket-us-api-fees.md).

## Coefficients

| Role | Theta |
|------|-------|
| Taker | 0.05 |
| Maker | -0.0125 |

Maker rebate equals 25% of taker fees, credited at time of fill (source:
polymarket-us-api-fees.md).

## Schedule (per 1,000 contracts)

| Price | Taker Fee | Maker Rebate |
|-------|-----------|--------------|
| $0.10 | $4.50 | $1.13 |
| $0.25 | $9.38 | $2.34 |
| $0.50 | $12.50 | $3.13 |
| $0.75 | $9.38 | $2.34 |
| $0.90 | $4.50 | $1.13 |

Fees are symmetric around $0.50 and lowest near extremes. Banker's rounding
applied (source: polymarket-us-api-fees.md).

## Promotions

Through June 30, 2026: participants with over $250,000 in taker volume (since
May 15) receive 30% rebate on total taker fees (source: polymarket-us-api-fees.md).

## Key Rules

- Fees charged only on execution — no cost for canceled/expired/rejected orders
- Taker fees deducted immediately
- Maker rebates credited immediately upon fill

Effective April 3, 2026, 3pm ET (source: polymarket-us-api-fees.md).

## Comparison with [[kalshi-api]] Fees

Both platforms use price-dependent fee formulas that peak at p=$0.50 and
decline toward extremes. Direct coefficient comparison is relevant for
mispricing analysis.

## See Also

- [[polymarket-us-api]] — full API reference
