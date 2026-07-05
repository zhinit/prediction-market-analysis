# Pulling every MLB trade from Kalshi (and every game from MLB)

I wanted a local database I could run analysis queries against without hitting an API every time.
For the MLB calibration analysis that means two sources:

- Kalshi: every trade ever made on their MLB game winner markets
- MLB Stats API: the schedule, play-by-play, win probability, and weather for every game

Everything lands in a single DuckDB file, `db/pma.db`.
About 25 million trades across 7,000+ markets, plus every MLB game since Kalshi's markets started trading.

## Three layers

The scripts in `db/scripts/` are organized pull -> build -> prepare.

1. **pull** - `pull_kalshi_mlb.py` and `pull_mlb_stats.py` mirror the two APIs. Faithful copies, no opinions.
2. **build** - `build_kalshi_mlb_map.py` joins the mirrors, matching each Kalshi event to an MLB gamePk.
3. **prepare** - `prepare_mlb_calibration.py` builds the exact tables one analysis reads.

`refresh.py` runs the pulls and the build in order. The prepare layer runs manually, on purpose (more on that at the end).

## The stack

Both pull scripts are the same pipeline with five layers:

```
httpx (fetch) -> tenacity (retry) -> pydantic (validate) -> polars (transform) -> duckdb (store)
```

- **httpx** makes async HTTP requests
- **tenacity** wraps the fetch with retry logic
- **pydantic** validates every response before anything else touches it
- **polars** turns the validated objects into DataFrames
- **duckdb** stores everything locally

## Validate at the boundary

Every response from an API goes through a pydantic model:

```python
class Trade(BaseModel):
    trade_id: str
    ticker: str
    yes_price_dollars: str
    created_time: str
    ...
```

An API response is input you don't control.
If Kalshi renames a field or changes a type, I want the script to fail loudly at the fetch, with an error naming the exact field, instead of writing malformed rows and finding out weeks later in some analysis query.
Validation happens once, at the boundary. Everything downstream can trust the shape.

## Exponential backoff

Thousands of requests means transient failures. A timeout here, a rate limit there, the occasional 500.
Retrying immediately makes things worse. If the server is struggling you're just adding load.
So retries wait longer each time, with jitter so failed requests don't all retry in lockstep.

```python
@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, max=60),
    retry=retry_if_exception(is_retryable),
    reraise=True,
)
```

One lesson here: only retry errors that can actually succeed on retry.
The first version retried every HTTP error, so a 404 burned five attempts over several minutes before failing.
A 404 will be a 404 no matter how long you wait.
Now the scripts retry timeouts, 429s, and 5xx, and fail immediately on everything else.

Kalshi's rate limiting plays nice with this: a 429 costs nothing beyond the rejection, so backoff-and-retry settles at whatever pace the server allows.

## The historical/live split

Kalshi partitions its data into two tiers. The live API serves a rolling window of recent data, older data moves to dedicated `/historical/...` endpoints, and `GET /historical/cutoff` tells you exactly where the boundary sits.

The first version of the script fetched the cutoff, printed it, and then ignored it.
It looped over all 7,000 markets twice, once per endpoint, even though most markets could only possibly have data on one side.
Using the cutoff properly means partitioning: a market whose trades all predate the cutoff only needs the historical endpoint, a market that opened after it only needs the live one, and only markets straddling the boundary need both.
That roughly halved the number of requests.

## Idempotency - rerun anytime, no duplicates, no wasted work

The goal is a script you can run weekly, or after a crash, or twice by accident, and it always does the right thing. Two properties.

**No duplicates.** Every table has a primary key and every insert is `INSERT OR REPLACE`.
Refetching a trade the database already has just overwrites the row with itself.
Overlapping fetches are always safe, and that unlocks everything else.

**No wasted work.** Before fetching, the script reads its own previous state out of the database:

1. The newest stored trade per market. New trades can only exist after that timestamp, so the request includes `min_ts` and the API only returns what's new. (With a one second overlap in case the boundary is inclusive. The primary key eats the duplicate.)
2. `kalshi_trade_pulls`, a bookkeeping table of markets whose trade history is complete. A market gets a row only if it was finalized and only after both trade phases of a run finish, so a crash mid-run can never mark a market done. Fully pulled markets get zero requests.

The effect on a full database: the first pull touched all 7,000+ markets, a rerun the next day touched 94.
Cost scales with what happened since the last run, not with the whole season.

Crashes fall out for free. If a run dies halfway, nothing is corrupted (inserts are idempotent) and nothing is lost (the next run picks up from what actually landed).
No checkpoints, no state files. The database is the state.

The MLB pull has the same shape, with its own bookkeeping table (`mlb_game_pulls`) plus one wrinkle: some games 404 because MLB publishes the data late.
Those are recorded and retried on later runs until the game is two weeks old, then permanently skipped.

## Raw data first, types later

Everything from the APIs lands in the database exactly as it arrived. Timestamps and prices are stored as TEXT strings.
That felt wrong at first, but the pattern is: land the raw data faithfully, convert as a separate step.

The conversion step is a set of SQL views, created alongside the tables:

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

A view stores no data. It's a saved query, and the casting happens on the fly whenever an analysis reads from it.
So analyses get real TIMESTAMP and DECIMAL columns, the casts live in exactly one place, and the raw tables stay byte-for-byte what the API sent.
If a cast ever turns out wrong, I fix the view and every row, past and future, is instantly seen through the corrected lens. Nothing was baked in.

## The MLB side

Kalshi tells you the price. The score, the innings, and the weather come from the MLB Stats API (free, no key).
`pull_mlb_stats.py` mirrors four things:

- **mlb_games** - the schedule from April 16 2025 (the first day of Kalshi MLB data) through 10 days out, so markets already listed for upcoming games can be mapped. Regular season and postseason only. No spring training, no exhibitions, no All-Star game.
- **mlb_plays** - play-by-play for every finalized game, with wall clock start/end times per at-bat. This is what lets the analysis line trades up against innings.
- **mlb_win_probability** - MLB's own per-play win probability, a ready-made model to compare market prices against later.
- **mlb_weather** - condition, temperature, and wind at game time.

The three per-game endpoints are fetched concurrently per game, five games in flight at once.

Note
- a rescheduled game appears on two schedule dates with the same gamePk, so games are deduped by gamePk
- the live feed response is enormous and only the weather is needed, so a `fields` parameter cuts the response down to just that

## Matching Kalshi markets to MLB games

The two mirrors don't share a key. Kalshi has event tickers, MLB has gamePks.
`build_kalshi_mlb_map.py` builds the join table, and this turned out to be the trickiest part of the whole pull.

The event ticker encodes the game. Two formats:

- 2025: `KXMLBGAME-25SEP24KCLAA` = date + team pair, with an optional G1/G2 suffix for doubleheaders
- 2026: `KXMLBGAME-26APR301235STLPIT` = date + start time (US/Eastern) + team pair

The team pair is away team then home team, concatenated.
Splitting it isn't trivial because abbreviations vary in length (is `AZSTL` AZ+STL or AZS+TL?), so the split uses the event's two market ticker suffixes, which name the teams individually.
A hand-verified map then takes each abbreviation to an MLB team id.
Arizona shows up as ARI in 2025 and AZ in 2026, because of course it does.

Most events match on date + team pair and that's that. The rest:

- **Doubleheaders.** Two games, same day, same teams. Resolved by the G1/G2 suffix (2025 format), or by which game ended just before the market settled, or by scheduled start proximity, in that order. The order matters: a traditional doubleheader's two scheduled starts can be minutes apart, which makes start proximity meaningless.
- **Postponed games.** The ticker names a date with no game on it. A market settles within about a day of its game actually ending, so the fallback finds the makeup game whose end the settlement follows. The makeup can be months later, whenever the opponent visits next.
- **Cancelled games.** These settle scalar instead of yes/no and are never matched to a game.

The script fails loudly if the match rate drops below 99% and asserts the away-then-home convention holds on every date match.
Then the check that makes me trust the whole thing: every finalized yes/no market's result must agree with the schedule's winner, compared by team id rather than home/away slot since a makeup game can swap venues.
Across every checkable market: zero disagreements.

## Small things that bit me

**Positional inserts.** `INSERT INTO trades SELECT * FROM df` matches columns by position, which silently depends on the pydantic model, the DataFrame, and the table all agreeing on column order. Reorder one field and values land in the wrong columns without any error, since everything is TEXT. DuckDB's `INSERT ... BY NAME` matches by column name instead. Two extra words per insert, one whole category of silent corruption gone.

**Empty results crash weirdly.** `pl.DataFrame([])` has no columns at all, so inserting it fails with a confusing binder error. For trades that's handled with a simple skip (markets with zero trades are normal). For events and markets, an empty result means something is wrong (bad ticker, API change), so the script aborts early with a message that says so.

**The list endpoint doesn't return everything.** My reasonability checks found 22 markets referencing events that weren't in the events table. Those events are never returned by the `/events` list endpoint, under any status filter, even though fetching them directly by ticker works fine. The fix: after pulling markets, any referenced event missing from the list gets fetched individually. I would never have found this without checking referential integrity, which brings me to the tests.

## Trust, but verify

After the pull worked end to end, I wrote the reasonability checks as pytest tests in `tests/`, so they're documented and rerunnable after every pull. Three files:

- `test_data_quality.py` - the Kalshi tables. Every trade's market exists and every market's event exists, every raw string casts cleanly, prices are strictly between 0 and 1 and yes + no = 1 on every one of the 25 million trades, markets close after they open, no trades before market open or from the future.
- `test_mlb_data_quality.py` - the MLB tables and the map. Finalized games have scores and exactly one winner, exactly 30 teams appear, win probabilities sum to 100, the map covers 99%+ of game events, and the market-result-vs-schedule-winner agreement check.
- `test_kalshi_mlb_map.py` - unit tests for the ticker parsing and game picking. The DST cases, both doubleheader formats, the postponed-game settlement fallback, and the zombie market that settled months after its game (it must not match).

The checks caught the missing-events bug and also surfaced a fun quirk: about 3,000 trades have timestamps up to 60 seconds after their market's official close time.
Trading apparently runs slightly past the scheduled close.
Harmless, but the kind of thing you want to know about your data before building analysis on top of it.

## From mirrors to analysis-ready tables

The database so far is a faithful mirror. An analysis wants one more layer: tables prepared for it specifically, so its notebook loads data with a straightforward read and does no cleaning of its own.
For the MLB calibration analysis that layer is `prepare_mlb_calibration.py`, which builds tables namespaced `mlb_calib_*`: pre-game snapshots, entering-inning snapshots, and the full 24-hour pre-start trade window.

The script owns the dataset definition, including the cleanups that would otherwise clutter the analysis:

- **What the universe filter drops.** Only markets that settled yes or no are kept: 7,028 markets across 3,514 events. Excluded are 88 markets that had not settled at pull time, 20 that settled at an intermediate value instead of 0 or 100, and 8 All-Star markets.
- **Duplicate listings.** Seven games on 2025-04-18 were listed twice on Kalshi, so the 3,514 events cover 3,507 distinct games. The snapshot tables keep one row per game and side, last trade wins, so each real game counts once.
- **A label fix.** One market is labeled "Chicago W". The script renames it to "Chicago WS" so it groups with the rest of the White Sox markets.
- **Simultaneous trades.** The snapshot is defined as "the last trade before" some moment, but in 749 snapshots several trades share the last timestamp down to the microsecond, usually one taker order filling against several resting orders at once. There is no meaningful "last" among simultaneous trades, and letting the database pick one arbitrarily made builds nondeterministic. So the snapshot price is the average of the tied trades: deterministic, and at worst half a tick from any single print. The averaging sums integer cents and divides once, because averaging floats accumulates in whatever order the parallel aggregation happens to run, and that alone made rebuilds differ in the last decimal places.

Every run rebuilds from scratch, prints the accounting above, and asserts invariants: one row per game and side, prices strictly between 0 and 1, exactly 30 team labels.

And one deliberate omission: `refresh.py` never runs this script.
A finished analysis's prepared tables are the exact dataset its write-up was computed from, and refreshing raw data must not silently change them.
A single-row `mlb_calib_build_info` table records when the tables were built and what date range they cover, so a table frozen on old data can't be mistaken for a current one.

## Takeaways

- Validate API responses at the boundary. Errors at fetch time are cheap, errors in analysis are expensive.
- Retry with exponential backoff and jitter, and only retry errors that can actually change.
- Idempotency comes from primary keys plus upserts. Once refetching is always safe, incremental logic gets simple.
- Store raw data faithfully, convert with views. You can always fix a view. You can't un-bake a bad conversion.
- Match insert columns by name, never by position.
- When joining two independent data sources, find a semantic cross-check. Market results vs schedule winners is what makes me trust the map, not the match rate.
- Write your sanity checks as tests. They found real issues that a working script happily hid.
