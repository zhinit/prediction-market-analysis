# NBA Arbitrage Study

A UCLA study (Cheng, Yang, and Zou, May 2026) examined market efficiency in
Polymarket's NBA prediction markets, analyzing over 75 million limit order
book snapshots across 173 games from February–March 2026
(source: arxiv-arbitrage-polymarket-nba-markets.md).

## Single-market arbitrage

Only 7 executable arbitrage episodes were identified across 3,042 markets,
indicating "profound microstructural efficiency." These episodes persisted
for a median of 3.6 seconds before correction. Theoretical profit potential
was $4,418.44, but actual capped profit (limited to $100 per episode) was
$210.19 (source: arxiv-arbitrage-polymarket-nba-markets.md).

## Combinatorial arbitrage

290 active episodes were found between Moneyline and Spread markets,
concentrated in final game minutes. Median return was 101 basis points.
76.9% of opportunities were constrained to executable sizes averaging 14.8
shares due to shallow order book depth
(source: arxiv-arbitrage-polymarket-nba-markets.md).

## Central finding

Shallow liquidity — not pricing inefficiency — is the binding constraint on
arbitrage extraction. Even identifiable mispricings cannot be corrected at
institutional scale due to execution frictions. Residual inefficiencies are
"structurally confined to the retail tier"
(source: arxiv-arbitrage-polymarket-nba-markets.md).

## Methodology

High-resolution order book snapshots with 3.6–5.5 second polling intervals.
Strict deduplication and post-game exclusion filters to mitigate phantom
signals (source: arxiv-arbitrage-polymarket-nba-markets.md).

## Related pages

- [[cross-platform-arbitrage]] — cross-platform arbitrage overview
- [[prediction-market-orderbook-microstructure]] — orderbook behavior on Polymarket
