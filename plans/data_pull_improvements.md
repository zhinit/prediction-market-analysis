# Data pull improvements — `db/scripts/pull_kalshi_mlb.py`

Findings from a review of the Kalshi MLB pull script, ordered by importance.

**Status (2026-07-01): all items implemented except #5, which was skipped
(see its decision note).** For #6, the typed-views option was chosen: raw
TEXT tables remain the landing layer, with `markets_typed` and `trades_typed`
views created in `init_db`.

## Serious

### 1. `cutoff` is fetched and never used

The script fetches `/historical/cutoff`, prints it, and then iterates **all**
markets in both the historical-trades loop and the live-trades loop. Every
settled market gets a pointless `/markets/trades` call and every live market a
pointless `/historical/trades` call — roughly doubling an already long
sequential run.

- Use the cutoff (or `market.status` / `close_time`) to partition markets
  between the two loops.
- Add `.raise_for_status()` and retry to the cutoff request — it is the only
  request without either.
- Give it a leading slash (`/historical/cutoff`) for consistency with every
  other path.

### 2. No incremental logic

Every run refetches the entire trade history for every market from scratch.
Fine for the first pull; unbounded growth over a season.

- `/markets/trades` accepts `min_ts` — resume from `max(created_time)` per
  ticker.
- The existing `INSERT OR REPLACE` idempotency already makes overlapping
  re-fetches safe.

### 3. Positional `SELECT *` inserts

`INSERT OR REPLACE INTO <table> SELECT * FROM <df>` depends on three copies of
the schema staying in sync: the pydantic field order, the polars column order,
and the `CREATE TABLE` column order. Reorder one field and values silently land
in the wrong columns (everything is TEXT, so nothing errors).

- Use `INSERT OR REPLACE INTO <table> BY NAME SELECT * FROM <df>` (DuckDB
  supports this), removing the ordering dependence entirely.

## Worth improving

### 4. Retry policy retries all `HTTPStatusError`s

A 404 or 400 burns 5 attempts over up to ~4 minutes before failing.

- Retry only 429 and 5xx; fail fast on other 4xx.

### 5. Sequential trade fetching

Trades are fetched one market at a time.

- An `asyncio.Semaphore(5)` + `asyncio.gather` would cut wall time
  substantially while staying polite to rate limits.
- **Decision (2026-07-01): skipped.** After #2, a weekly incremental run only
  touches active markets (~dozens), so sequential is fast enough. Revisit if
  more series are added or reruns get slow.

### 6. Everything stored as TEXT

Timestamps, prices, and volumes are all TEXT. Defensible as a raw-fidelity
landing layer, but every analysis query will cast.

- Either type the columns (`TIMESTAMP`, `DECIMAL`) or plan a typed view on top
  of the raw tables.

### 7. Copy-paste duplication between the two trade loops

The historical-trades loop and live-trades loop have identical bodies except
for the path.

- Factor into one function with a `path` parameter.

### 8. Style: type hints, constant naming, dead code

- No type hints on `fetch_all`, `fetch`, `init_db`, `main`.
- Module-level `base_url` / `timeouts` should be `BASE_URL` / `TIMEOUTS`
  constants at the top of the file.
- Remove the commented-out debug loop after the events print.

### 9. Empty-result inserts

If a fetch returns an empty list, `pl.DataFrame([])` has no columns and the
insert fails. The trades loops guard this; the events and markets inserts do
not.

- Skip the insert (with a warning) when the list is empty.
