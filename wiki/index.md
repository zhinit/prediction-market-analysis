# Wiki Index

## Polymarket US

- [[polymarket-us-api]] — CFTC-regulated US prediction market API (REST, WebSocket, gRPC, FIX)
- [[polymarket-us-fees]] — Fee formula and schedule (Theta x C x p x (1-p))
- [[polymarket-international-api]] — Crypto-based international Polymarket API (Polygon/pUSD)

## Kalshi

- [[kalshi-api]] — Overview of the Kalshi API (REST, WebSocket, FIX)
- [[kalshi-api-environments]] — Production and demo base URLs
- [[kalshi-api-auth]] — RSA-PSS authentication and request signing
- [[kalshi-api-rate-limits]] — Token bucket system, tier budgets (Basic through Prestige)
- [[kalshi-api-market-data]] — Public endpoints for markets, trades, orderbooks, candlesticks
- [[kalshi-market-object]] — Market data structure: pricing, volume, status, strike fields
- [[kalshi-api-orders]] — V2 order creation, amendment, cancellation, portfolio endpoints
- [[kalshi-api-websocket]] — Real-time channels (ticker, orderbook_delta, fill, etc.)
- [[kalshi-api-sdks]] — Official Python (sync/async) and TypeScript SDKs
- [[kalshi-api-pagination]] — Cursor-based pagination across list endpoints
- [[kalshi-api-historical]] — Historical data tier: cutoff timestamps, archived markets/trades/orders/candlesticks

## MLB Stats API

- [[mlb-stats-api]] — Overview: base URL, auth, rate limits, hydrate pattern, response structure
- [[mlb-stats-api-schedule]] — Schedule endpoint: games by date/team/league, game type codes, game states
- [[mlb-stats-api-standings]] — Standings: division standings, standings types, split records
- [[mlb-stats-api-game]] — Game data: live feed, boxscore, linescore, play-by-play, win probability, diffPatch
- [[mlb-stats-api-people]] — Players: profiles, stats, game logs, search, free agents
- [[mlb-stats-api-stats]] — Stats & leaders: leaderboards, stat aggregates, active streaks, leader categories
- [[mlb-stats-api-teams]] — Teams: listings, rosters, team stats, leaders, history, affiliates
- [[mlb-team-ids]] — All 30 MLB team IDs, league IDs, division IDs
- [[mlb-stats-api-venues]] — Venues: stadium details, field dimensions, notable venue IDs
- [[mlb-stats-api-draft]] — Draft: results by year, pick fields, live draft tracking
- [[mlb-stats-api-transactions]] — Transactions: trades, signings, IL, call-ups, transaction type codes
- [[mlb-stats-api-reference]] — Reference: positions, game types, awards, attendance, umpires
- [[mlb-stats-api-sports-leagues]] — Sports, leagues, divisions: organizational hierarchy and IDs
- [[mlb-stats-api-seasons]] — Seasons: date windows for regular season, preseason, postseason
- [[mlb-stats-api-gamepace]] — Game pace, high-low records, Home Run Derby

## pybaseball

- [[pybaseball]] — Python package for baseball data analysis (v2.2.7, Baseball Savant / FanGraphs / BRef / Lahman / Retrosheet)
- [[pybaseball-statcast]] — Statcast pitch-level data, fielding metrics, running, spin analysis
- [[pybaseball-batting-pitching]] — Individual batting and pitching stats (FanGraphs, Baseball Reference, splits, WAR)
- [[pybaseball-team-game]] — Team stats, game logs, standings, team ID cross-reference
- [[pybaseball-historical]] — Lahman database (25+ tables) and Retrosheet historical data
- [[pybaseball-player-lookup]] — Player ID lookup and Chadwick Bureau register
- [[pybaseball-plotting]] — Visualization: stadium plots, spraycharts, strike zones, team scatters
- [[pybaseball-draft-prospects]] — Amateur draft data and top prospects
