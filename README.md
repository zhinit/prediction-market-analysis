# pma — Prediction Market Analysis

> Work in progress.

Investigating whether anything on prediction markets (Kalshi, Polymarket) is mispriced. Pure analysis — no bots, no trading infrastructure. The end product is a presentable, portfolio-ready body of work.

## Status

**Research phase.** Building a knowledge base of platform APIs, data sources, and analytical methods before pulling data and running analyses.

Done so far:
- Research wiki with 69 pages covering Kalshi API, Polymarket API, MLB Stats API, pybaseball, EDA methodology, database design patterns, and the data pipeline stack
- Plan for first data pull (Kalshi MLB markets, trades, and outcomes into DuckDB)

Next up:
- Execute the first data pull
- Exploratory data analysis on MLB market pricing

## Structure

```
analysis/       Notebooks and scripts for EDA, pricing studies, statistical tests
db/             DuckDB database and loading scripts
docs/           Project conclusions, methodology, decisions
wiki/           Research wiki (primary source research only)
raw/            Immutable source documents (not tracked in git)
plans/          Implementation plans
```
