# Polymarket US Contract Sizing

## User-Facing Policy: Whole Contracts Only

Polymarket US states that only whole contracts are purchased and no fractional
amounts are created. When purchasing with a dollar amount, the platform buys as
many whole contracts as the amount can afford at the current price. Any
remainder is returned to the cash balance.
(source: polymarket-us-fractional-contracts.md)

Example from the docs: $100 at $0.65 per contract buys 153 whole contracts for
$99.45, with $0.55 returned. (source: polymarket-us-fractional-contracts.md)

## Order Book Data: Fractional Quantities Appear

Despite the whole-contract user-facing policy, the [[polymarket-us-websocket]]
market data stream delivers fractional `qty` values. Example payloads from the
docs show quantities like `"0.50"`, `"2.50"`, `"0.80"`, and `"1.50"`.
(source: polymarket-us-markets-websocket.md)

The docs describe the `qty` field as: "Total quantity at this price. May
contain decimals for partial-contract markets."
(source: polymarket-us-markets-websocket.md)

The private stream's `lastShares` field in execution reports is also described
as potentially containing decimals "for partial-contract markets."
(source: polymarket-us-markets-websocket.md)

## Polymarket International Order Book

The international (non-US) Polymarket CLOB shows order sizes as decimal strings
with values like `"93442.27"` and `"2116131.59"`. The `minOrderSize` constraint
is typically `"5"`. (source: polymarket-orderbook.md)

These large decimal values likely reflect USDC-denominated quantities on the
crypto-based international platform, distinct from the CFTC-regulated US
platform's contract-based sizing.

## Contradiction

The user-facing docs say no fractional contracts. The API docs show fractional
quantities in the order book and describe them as valid for "partial-contract
markets." This suggests either:

- The retail purchase UI rounds to whole contracts while the underlying CLOB
  accepts fractional resting orders (e.g., from API/market-maker participants)
- Some market types ("partial-contract markets") allow fractional quantities
  while standard event contracts do not
- Fractional quantities result from partial fills of resting orders

The sources do not resolve which explanation is correct.

## Related pages

- [[polymarket-us-websocket]] — WebSocket format showing fractional qty values
- [[polymarket-us-fees]] — fee formula applied per contract
- [[kalshi-fractional-contracts]] — Kalshi's explicit fractional contract support
