# Cross-Platform Prediction Market Arbitrage

Cross-platform arbitrage exploits pricing gaps on semantically equivalent
markets listed on different prediction market platforms. Roughly 6% of all
events are concurrently listed across platforms, exhibiting persistent
execution-aware price deviations of 2–4% on average
(source: arxiv-semantic-non-fungibility-cross-platform-spreads.md).

## Why price differences persist

The core impediment is semantic non-fungibility — economically identical
claims lack enforceable cross-platform identity. Positions cannot be netted
across venues and must be held until resolution. Capital-intensive arbitrage
requirements make short-horizon alignment unfeasible. Liquidity fragments
across platforms instead of pooling. Heterogeneous resolution semantics
create genuinely distinct payoff structures (source:
arxiv-semantic-non-fungibility-cross-platform-spreads.md).

Additional structural causes: different user bases with varying information
sources, liquidity profile variations, regulatory constraints affecting
listing speed, and fee structure differences between platforms
(source: clawarbs-kalshi-polymarket-arbitrage-guide.md).

## Magnitude and persistence

Typical deviations are 2–4% from execution-adjusted parity in actively
traded markets, with maximum deviations reaching 7%+ for sustained intervals.
A 2024 election case study showed execution-adjusted spreads averaging
approximately $0.03 and reaching up to $0.07 between Polymarket and Kalshi
(source: arxiv-semantic-non-fungibility-cross-platform-spreads.md).

Cross-platform spreads of 2–8% are detected daily by arbitrage scanning
tools. After accounting for platform fees plus capital opportunity costs,
gross spread typically becomes 1% net or negative after execution
(source: insidersignal-prediction-market-arbitrage-guide.md).

## Profitability of naive strategies

A naive, fully mechanical strategy achieved cumulative return of 1,218.66%
over 800 days across 15 completed trades. However, this required capital
commitment throughout resolution periods, making it capital-inefficient
relative to typical financial arbitrage
(source: arxiv-semantic-non-fungibility-cross-platform-spreads.md).

At the standard Kalshi fee tier (7%), only edges above ~5% survive after
fees. At the 3% tier ($250K–$1M monthly volume), a $0.03 edge yields
$0.0135 net profit per contract
(source: clawarbs-kalshi-polymarket-arbitrage-guide.md).

## Speed of arbitrage closure

Simple intra-market arbitrage windows collapsed from 12.3 seconds to 2.7
seconds over two years. Same-market arbitrage opportunities on Polymarket
averaged returns of 0.5–2%, with windows often closing within 200
milliseconds. 73% of arbitrage profits are captured by sub-100-millisecond
automated systems
(source: insidersignal-prediction-market-arbitrage-guide.md).

Automated bots detect cross-platform pricing gaps within approximately 25
milliseconds via WebSocket feeds
(source: clawarbs-kalshi-polymarket-arbitrage-guide.md).

## Scale of extraction

A Flashbots study documented approximately $40 million in arbitrage profits
extracted from Polymarket over one year (April 2024 – April 2025). The
majority came from multi-condition market rebalancing (YES/NO prices failing
to sum to 1.0 across multi-outcome markets), not cross-platform arbitrage
(source: flashbots-arbitrage-prediction-markets.md).

Profit breakdown by strategy
(source: flashbots-arbitrage-prediction-markets.md):

- Single-condition rebalancing: ~$10.6M
- Multi-condition rebalancing: ~$29.0M
- Combinatorial (cross-market logical dependencies): ~$95K

The authors acknowledge these are upper bounds on extractable profit, not
actual realized returns, since traders face opportunity costs, liquidity
constraints, and holding requirements until resolution
(source: flashbots-arbitrage-prediction-markets.md).

## Execution risks

Key risks for cross-platform arbitrage: execution risk from naked legs
(one side fills, the other does not), liquidity illusion (displayed depth
that disappears on execution), capital lockup until event resolution,
resolution disputes between platforms, and market movement speed exceeding
execution capability
(source: clawarbs-kalshi-polymarket-arbitrage-guide.md).

## Related pages

- [[polymarket-taker-delay]] — Polymarket's 1-second matching delay on sports markets
- [[cross-platform-settlement-differences]] — divergent resolution examples between platforms
- [[cross-platform-matching]] — approaches to matching markets across platforms
- [[polymarket-dynamic-fees]] — dynamic fees introduced to curb latency arbitrage
- [[prediction-market-orderbook-microstructure]] — orderbook behavior and liquidity
- [[kalshi-orderbook-reconstruction]] — reconstructing Kalshi LOBs from WebSocket streams
- [[nba-arbitrage-study]] — UCLA study on Polymarket NBA market efficiency
