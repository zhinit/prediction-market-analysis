# Prediction Market Orderbook Microstructure

A study of 30 billion order-book events across 600 Polymarket markets over
52 days (Feb 21 – Apr 15, 2026) characterizes liquidity provision, trading
costs, and market dynamics in decentralized binary prediction markets
(source: arxiv-polymarket-microstructure-orderbook.md).

## Spread behavior

Quoted half-spreads display an inverse relationship with probability.
Markets trading below 10% probability show median spreads of 1,300–1,800
basis points, compared to ~400 bps in the 40–60% range. Sports markets
show median effective half-spreads of 0.75 basis points, while crypto
markets average -3.93 basis points
(source: arxiv-polymarket-microstructure-orderbook.md).

Polymarket spreads (~200 bps median quoted half-spread) are approximately
100x wider than US equities post-decimalization
(source: arxiv-polymarket-microstructure-orderbook.md).

## Depth structure

The depth-concentration ratio (top-of-book share of top-10 depth) averages
0.137, approximating a uniform geometric grid rather than the top-heavy
structure typical of traditional markets. Liquidity is layered throughout
the order book rather than clustered at best prices
(source: arxiv-polymarket-microstructure-orderbook.md).

Log mean depth declines with log seconds-to-close (slope 0.55, t=3.85),
implying ~6% less depth per 10x reduction in time-to-close. Liquidity
providers gradually reduce inventory exposure as resolution approaches
(source: arxiv-polymarket-microstructure-orderbook.md).

## Maker concentration

Maker-address Herfindahl indices average 0.031, implying ~32 effective
makers per market. Most markets have decentralized liquidity provision,
though some niche markets concentrate on 1–3 wallets
(source: arxiv-polymarket-microstructure-orderbook.md).

## Trade-direction inference problem

The WebSocket feed broadcasts the `change_side` field, which identifies
which orderbook side moved, not which counterparty initiated the trade.
Feed-inferred trade direction matches on-chain ground truth on only ~59%
of comparable buckets, barely exceeding the 50% random baseline. Any
Polymarket microstructure analysis depending on trade direction requires
sourcing aggressor identity from on-chain OrderFilled events
(source: arxiv-polymarket-microstructure-orderbook.md).

## Related pages

- [[cross-platform-arbitrage]] — cross-platform arbitrage overview
- [[nba-arbitrage-study]] — UCLA study finding shallow liquidity as binding constraint
- [[kalshi-orderbook-reconstruction]] — reconstructing Kalshi LOBs from WebSocket streams
