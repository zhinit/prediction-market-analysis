# Pulling every MLB trade from Kalshi

I wanted a local database of every trade ever made on Kalshi's MLB game markets, something I could run analysis queries against without hitting the API every time. This is the story of the pull script that builds it: what it does, the problems that came up, and what I learned fixing them.

The end result is a single script, `db/scripts/pull_kalshi_mlb.py`, that I can rerun any time. It fetches whatever is new, skips everything it already has, and lands about 25 million trades across 7,000+ markets into a DuckDB file.

## The stack

The script is one pipeline with five layers:

```
httpx (fetch) -> tenacity (retry) -> pydantic (validate) -> polars (transform) -> duckdb (store)
```

- **httpx** makes async HTTP requests. `base_url` and shared timeouts are configured once on the client.
- **tenacity** wraps the fetch function with retry logic (more on this below).
- **pydantic** validates every API response against a model before anything else touches it.
- **polars** turns the validated objects into DataFrames.
- **duckdb** stores everything in a single local file, `db/pma.db`.

## Validating at the boundary

Every response from the API goes through a pydantic model:

```python
class Trade(BaseModel):
    trade_id: str
    ticker: str
    yes_price_dollars: str
    created_time: str
    ...
```

An API response is input you don't control. If Kalshi renames a field or changes a type, I want the script to fail loudly at the fetch, with an error that says exactly which field is missing, instead of writing malformed rows and finding out weeks later in some analysis query. Validation happens once, at the boundary, and everything downstream can trust the shape of the data.

## Exponential backoff

Any script that makes thousands of requests will hit transient failures: a timeout here, a rate limit there, the occasional 500. Retrying immediately tends to make things worse, because if the server is struggling, hammering it again a millisecond later just adds load. So the fetch function retries with exponential backoff: wait a bit before the first retry, longer before the second, longer again before the third, up to a cap. The waits are also randomized (jitter), so if many requests fail at once they don't all retry in lockstep.

```python
@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, max=60),
    retry=retry_if_exception(is_retryable),
    reraise=True,
)
```

One lesson here: retry only the errors that can actually succeed on retry. The first version retried every HTTP error, which meant a 404 would burn five attempts over several minutes before failing. A 404 will be a 404 no matter how long you wait. Now the script retries timeouts, 429s (rate limits), and 5xx (server errors), and fails immediately on everything else.

Rate limits deserve a mention: Kalshi returns 429 with no penalty beyond the rejection itself, so backoff-and-retry means the script naturally settles at whatever pace the server allows.

## The historical/live split

Kalshi partitions its data into two tiers. The live API serves a rolling window of recent data, and older data moves to dedicated `/historical/...` endpoints. There's an endpoint, `GET /historical/cutoff`, that tells you exactly where the boundary sits.

The first version of the script fetched the cutoff, printed it, and then ignored it. It looped over all 7,000 markets twice, once against the historical trades endpoint and once against the live one, even though most markets could only possibly have data on one side. Using the cutoff properly means partitioning: a market whose trades all predate the cutoff only needs the historical endpoint, a market that opened after it only needs the live one, and only markets straddling the boundary need both. That roughly halved the number of requests.

## Idempotency: rerun anytime, no duplicates, no wasted work

This was the most satisfying part. The goal is a script you can run weekly (or after a crash, or twice by accident) and it always does the right thing. That took two separate properties.

**No duplicates.** Every table has a primary key (trade_id, ticker, event_ticker) and every insert is `INSERT OR REPLACE`. Refetching a trade the database already has just overwrites the row with itself. This means overlapping fetches are always safe, which turns out to unlock everything else.

**No wasted work.** Before fetching, the script reads two things from the previous run:

1. The newest stored trade per market. New trades can only exist after that timestamp, so the request includes `min_ts` and the API only returns what's new. (With a one second overlap, in case the boundary is inclusive. The primary key eats the duplicate.)
2. Which markets were already finalized. A finalized market's trade history is complete, so if its trades are stored, it gets skipped entirely. Zero requests.

The effect on a full database: the first pull touched all 7,000+ markets, and a rerun the next day touched 94. Cost now scales with what happened since the last run, instead of with the whole season.

The crash story falls out for free. If a run dies halfway, nothing is corrupted (inserts are idempotent) and nothing is lost (the next run picks up from what actually landed). No checkpoints, no state files, the database itself is the state.

## Raw data first, types later

Everything from the API lands in the database exactly as it arrived: timestamps and prices are stored as TEXT strings. That felt wrong at first, but it follows a pattern I've come around to: land the raw data faithfully, convert as a separate step.

The conversion step is a pair of SQL views, created alongside the tables:

```sql
CREATE OR REPLACE VIEW trades_typed AS
SELECT
    trade_id,
    ticker,
    CAST(yes_price_dollars AS DECIMAL(18, 6)) AS yes_price_dollars,
    CAST(created_time AS TIMESTAMP) AS created_time,
    ...
FROM trades
```

A view stores no data. It's a saved query, and the casting happens on the fly whenever an analysis reads from it. So analyses get real TIMESTAMP and DECIMAL columns, the casts live in exactly one place, and the raw tables stay byte-for-byte what the API sent. If a cast ever turns out wrong, I fix the view and every row, past and future, is instantly seen through the corrected lens. Nothing was baked in.

## Small things that bit me

**Positional inserts.** `INSERT INTO trades SELECT * FROM df` matches columns by position, which silently depends on the pydantic model, the DataFrame, and the table all agreeing on column order. Reorder one field and values land in the wrong columns without any error, since everything is TEXT. DuckDB's `INSERT ... BY NAME` matches by column name instead. Two extra words per insert, one whole category of silent corruption gone.

**Empty results crash weirdly.** `pl.DataFrame([])` has no columns at all, so inserting it fails with a confusing binder error. For trades that's handled with a simple skip (markets with zero trades are normal). For events and markets, an empty result means something is wrong (bad ticker, API change), so the script aborts early with a message that says so.

**The list endpoint doesn't return everything.** My reasonability checks found 22 markets referencing events that weren't in the events table. It turned out those events are never returned by the `/events` list endpoint, under any status filter, even though fetching them directly by ticker works fine. The fix: after pulling markets, any referenced event missing from the list gets fetched individually. I would never have found this without checking referential integrity, which brings me to the last section.

## Trust, but verify

After the pull worked end to end, I wrote a set of reasonability checks as pytest tests (`tests/test_data_quality.py`), so they're documented and rerunnable after every pull. They check things like:

- every trade's market exists, every market's event exists
- every raw string casts cleanly to its typed column
- prices are strictly between 0 and 1, and yes + no = 1 on every one of the 25 million trades
- markets close after they open, finalized markets have results
- no trades before market open, none from the future

The checks caught the missing-events bug and also surfaced a fun quirk: about 3,000 trades have timestamps up to 60 seconds after their market's official close time. Trading apparently runs slightly past the scheduled close. Harmless, but the kind of thing you want to know about your data before building analysis on top of it.

## From mirrors to analysis-ready tables

The database so far is a faithful mirror. An analysis wants one more layer: tables prepared for it specifically, so its notebook loads data with a straightforward read and does no cleaning of its own. For the MLB calibration analysis that layer is `db/scripts/prepare_mlb_calibration.py`, which builds tables namespaced `mlb_calib_*`: pre-game snapshots, entering-inning snapshots, and the full 24-hour pre-start trade window.

The script owns the dataset definition, including three cleanups that would otherwise clutter the analysis:

- **What the universe filter drops.** Only markets that settled yes or no are kept: 7,028 markets across 3,514 events. Excluded are 88 markets that had not settled at pull time, 20 that settled at an intermediate value instead of 0 or 100, and 8 All-Star markets.
- **Duplicate listings.** Seven games on 2025-04-18 were listed twice on Kalshi, so the 3,514 events cover 3,507 distinct games. The snapshot tables keep one row per game and side, last trade wins, so each real game counts once.
- **A label fix.** One market is labeled "Chicago W". The script renames it to "Chicago WS" so it groups with the rest of the White Sox markets.
- **Simultaneous trades.** The snapshot is defined as "the last trade before" some moment, but in 749 snapshots several trades share the last timestamp down to the microsecond, usually one taker order filling against several resting orders at once. In 211 of them the tied trades have different prices (one tick apart in the vast majority). There is no meaningful "last" among simultaneous trades, and letting the database pick one arbitrarily made builds nondeterministic. An earlier version re-picked on every query, so two tables in the same notebook could disagree by a few markets. The snapshot price is the average of the tied trades instead: deterministic, and at worst half a tick from any single print. The averaging sums integer cents and divides once, because averaging floats accumulates in whatever order the parallel aggregation happens to use, and that alone made rebuilds differ in the last decimal places.

Every run rebuilds from scratch, prints the accounting above, and asserts invariants: one row per game and side, prices strictly between 0 and 1, exactly 30 team labels. And one deliberate omission: the tables are never rebuilt automatically when new raw data arrives. A finished analysis's prepared tables are the exact dataset its write-up was computed from, and refreshing raw data must not silently change them. A single-row `mlb_calib_build_info` table records when the tables were built and what date range they cover, so a table frozen on old data can't be mistaken for a current one.

## Takeaways

- Validate API responses at the boundary. Errors at fetch time are cheap, errors in analysis are expensive.
- Retry with exponential backoff and jitter, and only retry errors that can actually change.
- Idempotency comes from primary keys plus upserts. Once refetching is always safe, incremental logic gets simple.
- Store raw data faithfully, convert with views. You can always fix a view; you can't un-bake a bad conversion.
- Match insert columns by name, never by position.
- Write your sanity checks as tests. They found two real issues that a working script happily hid.
