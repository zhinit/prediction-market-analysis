# Polymarket US Collateral and Margin

Source: https://docs.polymarket.us/market-structure/collateral-and-margin
Fetched: 2026-06-24

## Model

Fully-collateralized contracts. Sufficient funds required to cover maximum
payout upfront. No leverage.

## Buyer

- Pays the contract price
- No additional margin required
- Maximum loss = purchase cost
- Maximum gain = $1.00 - price paid

## Seller

- Receives sale proceeds
- Must post $1.00 margin per contract (full payout value)
- Buying power decreases by ($1.00 - sale price)

### Example at $0.40

- Buyer: loses $0.40 buying power
- Seller: gains $0.40 fiat, loses $0.60 buying power (net $0.40 decrease)

## Portfolio-Level Margining

Margin requirements consider the entire set of open positions across markets
simultaneously.

## Shorting

Selling YES contracts without ownership.

- Seller immediately receives proceeds
- Cannot access $1.00 per contract in margin
- Close by repurchasing contracts (releases proportional margin)

## Settlement

- Winners receive $1.00 per contract
- Losers receive $0
- Polymarket Clearing guarantees payout from locked seller margin
- No margin calls or reconciliations post-settlement

## Risk Control

Trades automatically fail if buying power would fall below zero.
