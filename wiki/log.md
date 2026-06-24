# Wiki Log

## 2026-06-24

- **Source**: Polymarket US API documentation (docs.polymarket.us)
- **Pages created**: polymarket-us-api, polymarket-us-fees, polymarket-international-api
- **Raw sources archived**: polymarket-us-api-overview.md, polymarket-us-api-authentication.md, polymarket-us-api-markets.md, polymarket-us-api-events.md, polymarket-us-api-orders.md, polymarket-us-api-portfolio.md, polymarket-us-api-websocket.md, polymarket-us-api-fees.md, polymarket-us-api-collateral-margin.md, polymarket-us-api-environments.md
- **Coverage**: Full retail API surface — environments, Ed25519 authentication, markets/events/orders/portfolio endpoints, WebSocket streams, fee schedule (Theta formula), collateral model, SDKs. Exchange API architecture documented (REST/gRPC/FIX tiers, Auth0 JWT). International Polymarket documented for comparison (CLOB/Gamma/Data APIs, EIP-712 auth, Polygon settlement).

- **Source**: Kalshi API official documentation (docs.kalshi.com)
- **Pages created**: kalshi-api, kalshi-api-environments, kalshi-api-auth, kalshi-api-rate-limits, kalshi-api-market-data, kalshi-market-object, kalshi-api-orders, kalshi-api-websocket, kalshi-api-sdks, kalshi-api-pagination
- **Raw sources archived**: kalshi-api-overview-and-environments.md, kalshi-api-authentication.md, kalshi-api-rate-limits.md, kalshi-api-market-data-endpoints.md, kalshi-api-orders-and-portfolio.md, kalshi-api-websocket.md, kalshi-api-sdks.md, kalshi-api-pagination.md, kalshi-api-changelog-2026.md
- **Coverage**: Full API surface — environments, authentication (RSA-PSS signing), rate limits (7-tier token bucket), market data endpoints (public, no auth), order management (V2 fixed-point), WebSocket channels, official SDKs, pagination, and recent changelog entries through June 2026.

- **Source**: pseudo-r/Public-MLB-API (GitHub, MIT license) — https://github.com/pseudo-r/Public-MLB-API
- **Pages created**: mlb-stats-api, mlb-stats-api-schedule, mlb-stats-api-standings, mlb-stats-api-game, mlb-stats-api-people, mlb-stats-api-stats, mlb-stats-api-teams, mlb-team-ids, mlb-stats-api-venues, mlb-stats-api-draft, mlb-stats-api-transactions, mlb-stats-api-reference, mlb-stats-api-sports-leagues, mlb-stats-api-seasons, mlb-stats-api-gamepace
- **Raw sources archived**: mlb-stats-api-public-docs-readme.md, mlb-stats-api-schedule.md, mlb-stats-api-standings.md, mlb-stats-api-game.md, mlb-stats-api-people.md, mlb-stats-api-stats.md, mlb-stats-api-teams.md, mlb-stats-api-venues.md, mlb-stats-api-draft.md, mlb-stats-api-transactions.md, mlb-stats-api-reference.md, mlb-stats-api-sports-leagues.md, mlb-stats-api-seasons.md, mlb-stats-api-gamepace-highlow.md
- **Coverage**: Full API surface — base URL (`statsapi.mlb.com/api/v1/`), no-auth access, hydrate pattern, 40+ endpoints across schedule, standings, game data (live feed, boxscore, linescore, play-by-play, win probability, diffPatch polling), player profiles/stats/search, team rosters/stats/leaders, venues/field dimensions, draft results, transactions with type codes, stat leaders with all hitting/pitching categories, reference lookups, seasons, game pace, and Home Run Derby. All 30 team IDs, league IDs, and division IDs documented.

- **Source**: pybaseball Python library documentation (GitHub: jldbc/pybaseball)
- **Pages created**: pybaseball, pybaseball-statcast, pybaseball-batting-pitching, pybaseball-team-game, pybaseball-historical, pybaseball-player-lookup, pybaseball-plotting, pybaseball-draft-prospects
- **Raw sources archived**: pybaseball-readme.md, pybaseball-docs-statcast.md, pybaseball-docs-batting-pitching.md, pybaseball-docs-team-game.md, pybaseball-docs-historical.md, pybaseball-docs-misc.md
- **Coverage**: Full library reference (v2.2.7) — Statcast pitch-level data (statcast, statcast_batter/pitcher, single_game), batter/pitcher aggregate functions (exit velo, expected stats, percentile ranks, pitch arsenal, pitch movement, active spin, spin direction comparison), statcast_pitcher_spin (Magnus effect columns), fielding (OAA, directional OAA, catch probability, outfielder jump, catcher poptime, catcher framing, fielding run value), running (sprint speed, 90ft splits), utility (spray angle). FanGraphs individual and team batting/pitching/fielding stats with full parameter tables. Baseball Reference season/range stats, split stats, WAR. Game data (schedule_and_record, team_game_logs), standings (1969+), team ID cross-reference. Lahman database (25+ tables), Retrosheet (game logs, rosters, events, schedules). Player ID lookup (Chadwick Bureau, fuzzy search, batch, reverse). Plotting (stadium, spraychart, batted ball profile, team scatter, strike zone). Draft and prospect functions.

- **Source**: Kalshi API historical data documentation (docs.kalshi.com)
- **Pages created**: kalshi-api-historical
- **Pages updated**: kalshi-api-market-data (added historical cross-reference)
- **Raw sources archived**: kalshi-api-historical-data.md
- **Coverage**: Full historical data tier — live/historical partition (~3-month rolling cutoff), cutoff timestamp endpoint (market_settled_ts, trades_created_ts, orders_updated_ts), historical markets (list, single, candlesticks with OHLCV), historical trades (public, filterable by ticker/timestamp/block), historical fills (authenticated), historical orders (authenticated). Implementation pattern for merging live+historical results.
