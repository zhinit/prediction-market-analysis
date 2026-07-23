# Cross-Platform Settlement Differences

Kalshi and Polymarket use fundamentally different resolution mechanisms, and
have resolved identical events differently on multiple occasions
(source: settlement-differences-defirate.md).

## Resolution mechanisms

### Kalshi (centralized)

Internal markets team makes final determination. Named "Source Agencies"
per market category: NFL/NBA governing leagues, AP, ESPN for sports;
CF Benchmarks for crypto; BLS, Federal Reserve for economics; NOAA for
weather. Source agencies are filed with CFTC as part of exchange
self-certification. Settlement typically within hours after resolution
(source: settlement-differences-defirate.md).

No formal arbitration for traders. "Request to Settle" is a suggestion
only, not binding. Outcome Review Committee (board committee) can make
binding determinations. No independent appeal mechanism
(source: settlement-differences-defirate.md).

### Polymarket (decentralized)

International platform uses UMA's Optimistic Oracle with five-tier
escalation: proposal ($750 USDC bond), two-hour challenge period, first
dispute auto-reset, second dispute triggers UMA DVM, DVM vote by token
holders (48–96 hours). ~98.5% of markets resolve at the Optimistic Oracle
layer without DVM escalation
(source: settlement-differences-defirate.md).

Polymarket US uses its Markets Team to resolve directly
(source: settlement-differences-defirate.md).

## Divergent resolution examples

### Cardi B Super Bowl Halftime (Feb 2026)

Cardi B appeared on stage, danced, and mouthed lyrics during Bad Bunny's
halftime show. Kalshi invoked Rule 6.3(c), settling at last traded price
($0.26 YES, $0.74 NO) on $47.3M volume. Polymarket resolved YES at $1.00
payout on $10M+ volume. Root cause: different interpretation standards —
Kalshi distinguished between "performing" vs "dancing in background,"
Polymarket relied on media consensus
(source: settlement-differences-defirate.md).

### Documented Kalshi resolution errors

NFL season win totals (Jan 2026): refunded stakes but not winnings initially,
reversed only after 1M+ social media views. Oscars viewership (2025): paid
wrong side with no reversal. Soccer match with no tie option (2025): market
resolved against both sides (source: settlement-differences-defirate.md).

### Documented Polymarket disputes

Ukraine mineral deal (Mar 2025, $7M+): UMA whale cast 5M tokens (~25% of
vote), resolved YES despite no confirmed deal. Polymarket's UMA governance
risk: market cap ~$44M vs TVL ~$330M, a 15:1 ratio
(source: settlement-differences-defirate.md).

## Implications for cross-platform arbitrage

Settlement differences create genuine payoff divergence on semantically
equivalent markets. A position that wins on one platform may lose on
another for the same real-world event. This makes cross-platform arbitrage
riskier than pure price arbitrage — the assumption that both sides resolve
identically is not guaranteed
(source: settlement-differences-defirate.md).

## Related pages

- [[cross-platform-arbitrage]] — cross-platform arbitrage overview
- [[kalshi-fees]] — Kalshi fee structure
- [[polymarket-us-fees]] — Polymarket US fee structure
