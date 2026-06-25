# analytical-database-design

How to build an analytical database that is structured for querying, self-documenting, and presentable to someone who didn't build it.

## The core idea

An analytical database exists to answer questions, not to record transactions. Every design decision follows from that: denormalize for read performance, organize by business concepts, embed documentation in the schema itself.

## Three pillars

### 1. Dimensional modeling

Separate data into **fact tables** (numeric measurements — prices, volumes, counts) and **dimension tables** (descriptive context — markets, teams, dates, events). This is the [[dimensional-modeling]] pattern (star schema). It makes queries intuitive: join a fact to its dimensions, filter, aggregate.
(source: motherduck-star-schema-guide.md, holistics-kimball-dimensional-modeling.md)

### 2. Self-documenting schema

Use [[database-naming-conventions]] so column names explain themselves. Use DuckDB's `COMMENT ON` to embed descriptions directly in the database. Anyone can run `SELECT * FROM duckdb_columns() WHERE table_name = 'markets'` and see what every column means. See [[self-documenting-database]].
(source: techwriter-self-documenting-databases.md, duckdb-comment-on.md)

### 3. Incremental, just-in-time design

Don't model everything upfront. Start with raw data, build dimensional models as analytical questions demand them. Kimball's methodology is valuable for its concepts (grain, conformed dimensions), but modern practice builds incrementally rather than waterfall.
(source: holistics-kimball-dimensional-modeling.md)

## Practical structure for this project

The database lives in `db/pma.db`. Tables follow this organization:

- **Fact tables**: No prefix. Named after the business process they measure. Examples: `market_snapshots`, `trades`, `game_outcomes`.
- **Dimension tables**: `_dim` suffix. Examples: `markets_dim`, `teams_dim`, `events_dim`, `dates_dim`.
- **Reference tables**: `ref_` prefix. Small lookup tables. Examples: `ref_market_types`, `ref_game_states`.
- **Staging/temp tables**: `stg_` prefix. Intermediate pipeline outputs, not for direct analysis.

See [[database-naming-conventions]] for column-level rules.

## What makes it presentable

A database is presentable when someone unfamiliar with it can:

1. List all tables and understand what each one holds (via table comments)
2. Look at any table's columns and understand what each means (via column comments and naming)
3. Write a query without consulting external documentation (via consistent naming and intuitive joins)
4. Trust the data (via constraints, deduplication, and documented grain)

This is achieved through structure and naming, not through a separate document that inevitably drifts from reality.

## See also

- [[dimensional-modeling]] — fact tables, dimension tables, star schema, Kimball's process
- [[database-naming-conventions]] — complete naming rules
- [[self-documenting-database]] — COMMENT ON, metadata introspection
- [[database-maintenance]] — keeping the database healthy over time
- [[duckdb]] — the database engine
- [[data-pipeline-stack]] — how data flows into the database
