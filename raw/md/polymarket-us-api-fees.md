# Polymarket US Fee Schedule

Source: https://docs.polymarket.us/fees
Fetched: 2026-06-24
Effective: April 3, 2026 (3pm ET)

## Fee Formula

Fee = Theta x C x p x (1 - p)

Where:
- C = number of contracts
- p = trade price ($0.01 to $0.99)
- Theta = fee coefficient

## Fee Coefficients

| Role | Theta | Max Fee (at p=$0.50) |
|------|-------|---------------------|
| Taker | 0.05 | $1.25 per 100 contracts |
| Maker | -0.0125 | -$0.31 per 100 contracts |

Maker rebate = 25% of taker fees at point of trade execution.

## Fee Characteristics

- Symmetric around p = $0.50
- Lowest near extreme prices (0 and 1)
- Only charged on trade execution; no fees for canceled/expired/rejected orders
- Taker fees deducted immediately
- Maker rebates credited immediately upon fill
- Banker's rounding (round half to even), rounded to nearest cent

## Fee Examples (per 1,000 contracts)

| Price | Taker Fee | Maker Rebate |
|-------|-----------|--------------|
| $0.10 | $4.50 | $1.13 |
| $0.50 | $12.50 | $3.13 |
| $0.90 | $4.50 | $1.13 |

## Promotional Rebate

Participants with over $250,000 in taker volume between May 15–June 30, 2026
receive 30% rebate on total taker fees for that period.
