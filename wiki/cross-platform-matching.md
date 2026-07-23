# Cross-Platform Market Matching

Matching semantically equivalent markets across Kalshi and Polymarket
requires reconciling different ticker formats, team codes, and market
structures (source: speedyhughes-matching-logic.md).

## Kalshi ticker format

Kalshi event tickers encode league, date, and team codes in structured
strings. Two documented formats
(source: speedyhughes-matching-logic.md):

- Format 1: `KXEPLGAME-25DEC27CFCAVL` (date + teams combined)
- Format 2: `KXNCAAFGAME-25DEC27M-OHFRES` (date separate from teams with M delimiter)

Parsed into structured data: date, team1, team2. Team code splitting uses
heuristics based on string length (2 chars → 1+1 split, 4 chars → 2+2,
6 chars → 3+3, etc.)
(source: speedyhughes-matching-logic.md).

Kalshi API docs explicitly warn: "do not parse ticker strings to infer
relationships" (source: speedyhughes-matching-logic.md).

## Polymarket slug construction

Polymarket slugs can be constructed from parsed Kalshi data:
`{poly_prefix}-{team1}-{team2}-{date}`, with market-type-specific suffixes
for spread, total, or BTTS markets
(source: speedyhughes-matching-logic.md).

## Team code mapping

Platform-specific team abbreviations differ (e.g., `epl:che` on Polymarket
→ `cfc` on Kalshi). The speedyhughes bot uses a bidirectional `TeamCache`
mapping between platform codes, persisted to `kalshi_team_cache.json`.
No hardcoded mappings — populated dynamically via API discovery
(source: speedyhughes-matching-logic.md).

## Polymarket sports API

Polymarket US provides sports-specific endpoints
(source: polymarket-us-sports-api.md):

- `GET /v2/leagues/{slug}/events` — events for a specific league (NFL, NBA, MLB)
- `GET /v2/sports/{slug}/events` — events across all leagues within a sport

For matching purposes, the Markets API with `gameId` grouping may be more
useful than the Sports API, since it returns the full market object with
all pricing and classification fields
(source: polymarket-us-sports-api.md).

## Limitations

Ticker parsing only works for sports markets with standardized team codes.
Fragile to slug format changes on either platform. Does not handle
non-sports markets (source: speedyhughes-matching-logic.md).

## Related pages

- [[cross-platform-arbitrage]] — cross-platform arbitrage overview
- [[kalshi-api-market-data]] — Kalshi market data endpoints
- [[polymarket-us-api]] — Polymarket US API reference
