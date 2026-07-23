# Polymarket Dynamic Fees

Polymarket implemented a dynamic taker-fee model for its 15-minute crypto
markets to neutralize latency-based arbitrage strategies that exploited the
platform's previous zero-fee structure
(source: financemagnates-polymarket-dynamic-fees-latency-arbitrage.md).

## How the arbitrage operated

Automated bots capitalized on pricing delays between Polymarket's internal
odds and spot prices on major crypto exchanges. These strategies entered
trades near 50/50 odds and exited moments later when prices converged,
capturing small consistent gains without directional risk exposure. On-chain
analysis revealed at least one wallet converting $313 into $414,000 in a
single month through repeated execution
(source: financemagnates-polymarket-dynamic-fees-latency-arbitrage.md).

## Fee mechanics

The dynamic taker fee peaks at approximately 3.15% on 50-cent contracts
where odds approach 50/50 — precisely where latency strategies operated
most effectively. The fee applies only to takers executing against existing
liquidity on short-term markets. Most other Polymarket markets remain
fee-free (source: financemagnates-polymarket-dynamic-fees-latency-arbitrage.md).

Dynamic taker fees fund the Maker Rebates Program, with daily
redistribution to liquidity providers incentivizing deeper order books and
tighter spreads
(source: financemagnates-polymarket-dynamic-fees-latency-arbitrage.md).

## Related pages

- [[polymarket-us-fees]] — current fee schedule for Polymarket US
- [[cross-platform-arbitrage]] — cross-platform arbitrage overview
- [[polymarket-taker-delay]] — separate mechanism (matching delay) also limiting arb
