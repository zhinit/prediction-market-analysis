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

Project-specific choices are recorded in `docs/project-conventions.md`.

## What makes it presentable

A self-documenting database embeds documentation in the schema itself, using built-in commenting mechanisms that remain maintainable as the structure evolves: table comments describe the real-world objects a table represents, view comments explain the questions those stored queries answer, and column comments describe the properties they store. Consistent naming conventions promote readability, and a defined primary key on every table is "key to understanding the data model." Because the documentation lives inside the database, it stays synchronized with the active database rather than drifting in a separate document.
(source: techwriter-self-documenting-databases.md)

## See also

- [[dimensional-modeling]] — fact tables, dimension tables, star schema, Kimball's process
- [[database-naming-conventions]] — complete naming rules
- [[self-documenting-database]] — COMMENT ON, metadata introspection
- [[database-maintenance]] — keeping the database healthy over time
- [[duckdb]] — the database engine
- [[data-pipeline-stack]] — how data flows into the database
