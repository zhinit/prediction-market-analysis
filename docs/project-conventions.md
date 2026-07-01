# Project Conventions

Project-specific decisions moved out of the wiki during the 2026-07-01 lint
pass (the wiki stays neutral reference material; these are our choices).
Each section links the wiki page that covers the general topic.

## Data pipeline

General reference: `wiki/data-pipeline-stack.md`.

- The five-layer stack (httpx → tenacity → pydantic → polars → duckdb) is
  the stack for pulling prediction market and sports data into this project.
- One httpx client per API (Kalshi, Polymarket, MLB).
- Persistent analytical database in `db/pma.db`.
- The tenacity retry layer handles 429 responses automatically, but for
  sustained high-volume pulls, track the `X-RateLimit-Remaining` header and
  throttle proactively rather than relying solely on retries.
- Parquet is the default storage format for intermediate data (columnar,
  compressed, faster than CSV in Polars). Use CSV only for
  human-inspectable exports.
- DuckDB was chosen as the analytical store: in-process, no database server
  to manage, a single file in `db/` holds all data.

## Database

General references: `wiki/analytical-database-design.md`,
`wiki/database-naming-conventions.md`, `wiki/database-maintenance.md`,
`wiki/self-documenting-database.md`, `wiki/dimensional-modeling.md`.

### Structure

The database lives in `db/pma.db`. Tables follow this organization:

- **Fact tables**: no prefix, named after the business process they
  measure. Examples: `market_snapshots`, `trades`, `game_outcomes`.
- **Dimension tables**: `_dim` suffix. Examples: `markets_dim`,
  `teams_dim`, `events_dim`, `dates_dim`.
- **Reference tables**: `ref_` prefix, small lookup tables. Examples:
  `ref_market_types`, `ref_game_states`.
- **Staging/temp tables**: `stg_` prefix, intermediate pipeline outputs,
  not for direct analysis. Examples: `stg_kalshi_raw`,
  `stg_polymarket_raw`. Note: this is our convention; the warehouse-design
  source the wiki cites prescribes `tmp_`/`test_` prefixes instead.

### Star schema

Grain: one row per market per snapshot timestamp. Dimensions for a market
snapshot: which market, which event category, what date, which platform.
Facts: price, volume, open interest, spread.

```
                    ┌──────────────┐
                    │  markets_dim │
                    │──────────────│
                    │ market_id    │
                    │ ticker       │
                    │ title        │
                    │ platform     │
                    │ category     │
                    └──────┬───────┘
                           │
┌──────────────┐    ┌──────┴───────────────┐    ┌──────────────┐
│  dates_dim   │    │  market_snapshots     │    │  events_dim  │
│──────────────│    │──────────────────────│    │──────────────│
│ date_id      ├────┤ date_id (FK)         ├────┤ event_id     │
│ date         │    │ market_id (FK)       │    │ event_name   │
│ day_of_week  │    │ event_id (FK)        │    │ event_type   │
│ month        │    │ snapshot_time        │    │ start_date   │
│ quarter      │    │ price                │    │ end_date     │
│ year         │    │ volume               │    └──────────────┘
│ is_weekend   │    │ open_interest        │
└──────────────┘    │ spread               │
                    └──────────────────────┘
```

Surrogate keys via DuckDB sequences:

```sql
CREATE SEQUENCE market_id_seq START 1;
CREATE TABLE markets_dim (
    market_id INTEGER PRIMARY KEY DEFAULT nextval('market_id_seq'),
    ticker TEXT NOT NULL,
    title TEXT,
    platform TEXT,
    category TEXT
);
```

### Slowly changing dimensions

Type 1 (overwrite) is the default: most dimension attributes (e.g. a
market's title or category) reflect current state. This is a deliberate
choice over the periodic-snapshot approach described in
`wiki/dimensional-modeling.md` — our dimensions are small and their history
is not analytically interesting; where history matters it lives in the
fact tables.

### Deduplication and comments

The staging layer (`stg_` tables) is where duplicates are detected and
removed before data moves into fact and dimension tables.

Every table and column gets a `COMMENT ON`, e.g.:

```sql
COMMENT ON TABLE market_snapshots IS
    'Point-in-time price and volume captures for prediction market contracts. One row per market per snapshot.';

COMMENT ON COLUMN market_snapshots.price IS
    'Last traded price as a probability (0.00 to 1.00)';

COMMENT ON COLUMN market_snapshots.snapshot_time IS
    'UTC timestamp when the snapshot was captured';
```

Anyone should be able to connect to `db/pma.db`, run a few metadata
queries, and understand every table and column without reading a separate
document.

## Notebooks

General reference: `wiki/notebook-presentation.md`.

Checklist for this project's analysis notebooks:

- [ ] Clear title and one-sentence summary at the top
- [ ] Problem statement before any code
- [ ] One step per cell with markdown transitions
- [ ] Parameters and configuration in the first code cell
- [ ] Dependencies listed (requirements.txt or inline)
- [ ] Every chart has a title, labeled axes, and a one-sentence interpretation
- [ ] Conclusions section at the end restating key findings
- [ ] Runs top-to-bottom without error (restart kernel and run all)

## Portfolio structure

General reference: `wiki/portfolio-presentation.md`.

pma is a portfolio-ready analysis project; each analysis follows this
template and lives in `analysis/` as a self-contained notebook (or set of
notebooks) that runs top-to-bottom:

```
Title: [What we investigated]
Question: [The specific question, stated plainly]
Data: [Source, size, time range, any cleaning notes]
Method: [What we did, briefly]
Key Findings: [2-3 bullet points with supporting charts]
Limitations: [What the data can't tell us]
```

## Analysis directions

General references: `wiki/polymarket-us-fees.md`, `wiki/polymarket-us-api.md`.

- Direct fee-coefficient comparison between Kalshi and Polymarket US is
  relevant for mispricing analysis.
- Differences in fee structure, authentication method, and institutional
  API support (FIX protocol) between the two platforms warrant direct
  comparison.
