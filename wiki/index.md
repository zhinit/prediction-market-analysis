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

## Claude Skills

- [[claude-skills]] — What skills are, structure, where they live, progressive disclosure, lifecycle
- [[claude-skills-writing-guide]] — Description field, instruction writing, 5 skill patterns, common mistakes
- [[claude-skills-frontmatter]] — Complete frontmatter reference: all fields, substitutions, invocation control
- [[claude-skills-testing]] — Testing, skill-creator plugin, evaluation loop, iteration signals, debug tips

## Claude for Learning

- [[claude-learning-mode]] — Built-in Socratic tutoring mode: guided questions, study/career/research projects, retention evidence
- [[claude-as-teacher]] — Techniques for using Claude to learn: tutor vs Socratic roles, 9 prompt patterns, question framing
- [[claude-code-learning-style]] — Claude Code's Learning output style: TODO(human) markers, learn-by-doing coding

## Exploratory Data Analysis

- [[exploratory-data-analysis]] — Philosophy, history (Tukey 1977), EDA vs classical vs Bayesian, seven objectives
- [[eda-four-rs]] — Four principles: Revelation, Resistance, Reexpression, Residuals
- [[eda-assumptions]] — Four underlying assumptions of measurement processes and the 4-Plot diagnostic
- [[eda-techniques]] — Catalog of 33 graphical techniques and quantitative methods
- [[eda-workflow]] — Practical process: profiling vs discovery, the analysis cycle, common challenges
- [[anscombes-quartet]] — Classic demonstration: identical statistics, completely different structures

## Analytical Database Design

- [[analytical-database-design]] — Hub: how to build a structured, self-documenting, presentable analytical database
- [[dimensional-modeling]] — Star schema, Kimball's four-step process, fact vs dimension tables, SCDs
- [[database-naming-conventions]] — Table and column naming rules: snake_case, suffixes, foreign keys, temporals
- [[self-documenting-database]] — DuckDB COMMENT ON, metadata introspection, documentation-as-code
- [[database-maintenance]] — Data quality checks, schema evolution, deduplication, metadata hygiene

## Data Pipeline Stack

- [[data-pipeline-stack]] — End-to-end pattern: httpx → tenacity → pydantic → polars → duckdb
- [[httpx]] — Async HTTP client with connection pooling (replaces requests)
- [[tenacity]] — Retry with exponential backoff and jitter for rate-limited APIs
- [[pydantic]] — Data validation for API responses using type hints (hub page)
- [[pydantic-fields]] — Field(), constraints, aliases, computed fields, annotated pattern
- [[pydantic-validators]] — Field/model validators (after, before, plain, wrap), validation info, ordering
- [[pydantic-serialization]] — model_dump, serializers, field inclusion/exclusion, polymorphic serialization
- [[pydantic-config]] — ConfigDict reference: strict mode, extra fields, propagation rules
- [[polars]] — Fast DataFrame library (Rust-based, lazy API with query optimization)
- [[duckdb]] — In-process analytical SQL database (persistent storage in db/)
- [[duckdb-python-connections]] — Connection types: in-memory, named, persistent, read-only, config, threading
- [[duckdb-db-api]] — PEP 249 API: execute, fetch, prepared statements, named parameters
- [[duckdb-relational-api]] — Lazy query builder: creation, transformation, aggregation, output methods
- [[duckdb-data-ingestion]] — Reading CSV/Parquet/JSON, querying DataFrames, registering virtual tables
- [[duckdb-result-conversion]] — Python↔DuckDB type mapping, output to Pandas/Polars/Arrow/NumPy
- [[duckdb-udfs]] — User-defined functions: native and Arrow, type annotations, NULL handling
- [[duckdb-expression-api]] — Programmatic expression building: Column, Star, Case, Function, SQL
- [[duckdb-friendly-sql]] — DuckDB SQL extensions: FROM-first, GROUP BY ALL, EXCLUDE, ASOF joins

## Presentable Data Analysis

- [[presentable-data-analysis]] — Hub: making analysis portfolio-ready (five principles, core loop)
- [[data-visualization-principles]] — Tufte + Knaflic + JHU: data-ink ratio, chartjunk, preattentive attributes, color palettes
- [[chart-selection]] — Question-driven chart picking: 9 question types → chart types (Tableau framework)
- [[notebook-presentation]] — PLOS ten rules for notebook structure, reproducibility checklist, output formats
- [[data-storytelling]] — Narrative structure, text's role in visualization, audience awareness, message dimensions
- [[portfolio-presentation]] — Portfolio design patterns, anti-patterns, project template

## pybaseball

- [[pybaseball]] — Python package for baseball data analysis (v2.2.7, Baseball Savant / FanGraphs / BRef / Lahman / Retrosheet)
- [[pybaseball-statcast]] — Statcast pitch-level data, fielding metrics, running, spin analysis
- [[pybaseball-batting-pitching]] — Individual batting and pitching stats (FanGraphs, Baseball Reference, splits, WAR)
- [[pybaseball-team-game]] — Team stats, game logs, standings, team ID cross-reference
- [[pybaseball-historical]] — Lahman database (25+ tables) and Retrosheet historical data
- [[pybaseball-player-lookup]] — Player ID lookup and Chadwick Bureau register
- [[pybaseball-plotting]] — Visualization: stadium plots, spraycharts, strike zones, team scatters
- [[pybaseball-draft-prospects]] — Amateur draft data and top prospects
