# Prediction Market Analysis

Are prediction markets priced accurately?\
This project uses data analysis to search for mispricings on predictions markets platforms like Kalshi is mispriced.

Polished versions of completed analyses are published at [TODO: website URL].

## Analyses

### MLB Game Winner Calibration

Data analysis which investigates if MLB game winner markets are priced efficiently.

**Data:**
- 3,507 games
- from April 2025 through July 2026
- ~25 million Kalshi trades across 7,000+ markets from Kalshi API
- game outcomes, play-by-play, and weather from the MLB Stats API.

**Verdict:**
Kalshi's MLB game winner markets appear to be calibrated.
No apparent exploitable mispricing.

Six cuts tested:
- overall pre-game
- by inning
- home vs. away
- by team
- stability over time
- weather
Details in [`write_ups/mlb_game_winners_analysis.md`](write_ups/mlb_game_winners_analysis.md). Data pipeline methodology in [`write_ups/data_pull.md`](write_ups/data_pull.md).

## Project Structure

```
analysis/       Jupyter notebooks (the actual analyses)
db/             DuckDB database and pipeline scripts
write_ups/      Near-final write-ups, published to the website when ready
wiki/           Research wiki — primary-source reference material
docs/           Project conventions and methodology decisions
db/tests/       Data quality and pipeline tests
raw/            Immutable source documents (HTML + markdown)
```

## Data Pipeline

All data flows through a five-layer stack:

```
httpx (fetch) → tenacity (retry) → pydantic (validate) → polars (transform) → duckdb (store)
```

The pipeline scripts in `db/scripts/` are organized as pull → build → prepare:

1. **Pull** mirrors APIs faithfully (Kalshi trades, MLB schedule/games)
2. **Build** joins the mirrors (matching Kalshi events to MLB games)
3. **Prepare** builds the tables a specific analysis needs

Everything lands in a single DuckDB file (`db/pma.db`). Every table and column is documented with `COMMENT ON` so the schema is self-describing.

## Research Wiki

The `wiki/` directory is a from-scratch research wiki covering the APIs, tools, and methods used in this project. ~100 pages on Kalshi's API, the MLB Stats API, DuckDB, Polars, Pydantic, EDA methodology, and data visualization. Every claim cites a primary source archived in `raw/`.

The wiki contains reference material only — no project opinions or analysis results.

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run db/scripts/refresh.py                  # pulls Kalshi + MLB data, builds the map
uv run db/scripts/prepare_mlb_calibration.py  # builds tables for the analysis
uv run jupyter notebook analysis/mlb_calibration.ipynb
```

The pull scripts require API access to Kalshi.
