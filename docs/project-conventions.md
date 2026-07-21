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
`wiki/database-naming-conventions.md`, `wiki/self-documenting-database.md`.

- Raw pulls live in `db/pma.db`; each analysis freezes its own prepared
  database (e.g. `db/arbitrage/arb_data.db`) so finished numbers cannot
  silently move.
- Prices and quantities are stored as TEXT exactly as the API returned
  them, with typed views for reading. Casts are explicit and testable.
- Analysis-specific prepared tables are namespaced by analysis
  (`arb_*`, `mlb_calib_*`).
- Important tables get `COMMENT ON` documentation-as-code.

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
