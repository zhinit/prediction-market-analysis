---
title: Pulling every MLB Game Winner trade from Kalshi 
date: 2026-07-06
description: Prediction markets data pipeline best practices. How I pulled 25.7 million prediction market trades from Kalshi and matched them to MLB game results to check if the prices accurately represent game winning probabilities.
---

I wanted to search for mispricings on prediction markets to see if there are any profitable opportunities. To do this you must analyze available data and to analyze available data you must pull in and clean the available data. 

Anyone who has spent significant time doing data analysis or predictive modeling has heard "garbage in, garbage out" and understands the importance of pulling and cleaning your data properly.

*For those who have not heard "garbage in, garbage out" before, it means that if you put garbage into your analysis/model, it doesn't matter how good your model/analysis are, you will get garbage output.*

This article describes my process for pulling data from the Kalshi and MLB Stats APIs for the purposes of this analysis, and general advice/methodology for anyone looking to do similar data pulls for prediction markets analysis.

A write up for the subsequent analysis can be found [here](https://www.zhinit.dev/blog/kalshi-mlb-game-winner-calibration) and the project code is on [GitHub](https://github.com/zhinit/prediction-market-analysis).

## What I'm pulling and why

Kalshi lists a "Game Winner" market for every MLB game. Each game gets two binary contracts, one per team. You buy YES on the team you think will win, and the contract settles at \$1 or \$0 after the game ends. If a YES contract is trading at 45 cents, the market is saying that team has a 45% chance of winning.

I want to know whether those prices are any good i.e. is a team priced at 45 cents actually winning 45% of the time? And if not, is the gap big enough to trade profitably after fees?

To answer that I need two things
- Trades on every Game Winner market (from Kalshi)
- The actual game outcomes (from MLB)

The Kalshi data tells me what the expected probability determined by the free world. The MLB data tells me the actual empirical probability. Match them up and you can check across 3,500+ games.

The final dataset lives in a DuckDB database. 25.7 million trades, 3,507 games with full play-by-play. 

*Note that "empirical" is just a fancy word to say that the probability came from observed data.*

## The APIs

### Kalshi

Kalshi's REST API is public and well-documented. The base URL is `https://external-api.kalshi.com/trade-api/v2` and everything comes back as JSON. 

The data model has three levels
- series: groups related markets
    - eg: Game Winner, Spread, Home Runs, etc
    - all MLB Game Winner markets share the series ticker `KXMLBGAME`
- event: one game (two teams, two contracts)
- market: is one side of that event
    - eg: YES on the Red Sox, YES on the Yankees
    - Trades happen on markets.

Kalshi splits its trade data across two endpoints. Trades older than a cutoff date live at `/historical/trades` and newer trades live at `/markets/trades`. The cutoff date is available at `/historical/cutoff` and moves forward over time.

This means a single market's trades can span both endpoints. The pull script hits both, deduplicates by trade ID, and moves on.

Small quirk: some events are missing from the events endpoint but are still referenced by markets. The script detects those and fetches them individually so no market ends up without its event metadata.

### MLB Stats

The MLB Stats API is free, public, unauthenticated, and completely undocumented by MLB. No API key, no rate limit headers, no official docs. Everything known about it comes from community reverse-engineering and a GitHub repo by pseudo-r.

The base URL is `https://statsapi.mlb.com/api/v1`. It powers MLB.com and the official app, so the data is authoritative.

Our pull grabs the following:

1. **Schedule**: every game from April 16, 2025 onward (the first day Kalshi listed MLB markets), filtered to regular season and postseason game types. This gives you teams, scores, venue, day/night, and the winner.
2. **Play-by-play**: every at-bat, with inning, half-inning, timestamps, and running score. This is what lets us look at prices entering each inning, not just pre-game.
3. **Weather**: condition, temperature, wind speed. Pulled from the live game feed.

The schedule is fetched in month-sized chunks because the API chokes on ranges longer than about 30 days. Games are deduplicated by `game_pk` since a rescheduled game can appear on two calendar dates.

*Note game_pk is game primary key*

## Making it reliable

When you're pulling 25 million trades across thousands of markets, the pull will take several hours. Things will go wrong i.e. servers will hiccup, connections will drop, and rate limits will kick in.

### Pagination

A single MLB Game Winner market can have thousands of trades. Sending all of them in one HTTP response would be slow and fragile. So like most APIs, Kalshi's API paginates. You request a page, get back a chunk of results and a cursor string, pass the cursor to get the next page, and repeat until the cursor comes back null.

Kalshi uses cursor-based pagination specifically, as opposed to offset-based (page 1, page 2, page 3). Cursor-based is better for large, changing datasets because it doesn't break when rows are inserted or deleted between requests. But it means you can't parallelize the fetch for a single resource. You have to walk the pages sequentially. For 25 million trades across thousands of markets, that takes several hours. Thus, when you kick off the script, you will want to go take a walk in the park or work on something else.

### Retries with exponential backoff

When you're making thousands of sequential API calls, some will fail. The server might be momentarily overloaded, you might hit a rate limit, or the connection might drop. You don't want the entire pull to die because of one pesky request.

Both scripts use tenacity to retry failed requests. Every HTTP call goes through a single `fetch` function decorated with the retry logic:

```python
@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, max=60),
    retry=retry_if_exception(is_retryable),
    reraise=True,
)
async def fetch(client, path, params):
    r = await client.get(path, params=params)
    r.raise_for_status()
    return r.content
```

Not every error is worth retrying. A 404 means the resource doesn't exist and asking again won't change that. A 400 means you sent a bad request. But a 429 (rate limited), a 500+ (server error), or a network-level failure (DNS, timeout, connection reset) are all transient. Those get retried. Everything else fails immediately.

The backoff is exponential and randomized. The first retry waits roughly a second, then exponentially longer, up to a 60 second cap. The randomization prevents a thundering herd, where many requests fail at the same time, all wait the same duration, then all retry simultaneously and fail again. After five total attempts, if it's still failing, the original exception is raised so the calling code can handle it.

### Concurrency

The MLB script needs to fetch data for thousands of games. It could send all those requests at once, but that would likely get you blocked. A semaphore limits how many requests can be in flight at the same time. Here it's set to five. Five games fetch simultaneously, the rest wait their turn. This is a bit conservative, but the MLB doesn't publish rate limits and hammering an undocumented API felt like asking for trouble.

### Resumability

The full trade pull takes a long time. If it crashes halfway through, you don't want to start over.

The Kalshi script tracks which finalized markets have been fully pulled in a `kalshi_trade_pulls` table. On the next run, those markets are skipped entirely. For markets that aren't fully pulled yet, it looks up the most recent trade timestamp and passes that as `min_ts` to the API, so it only fetches new trades. Everything is upserted into DuckDB as it comes in, so even a partial run saves its progress.

*Note min_ts is minimum timestamp. Upsert means insert if the row doesn't exist, update if it does.*

### Idempotency

Resumability handles crashes within a run. Idempotency handles re-running the script on a different day. The MLB season runs from April through October, and I didn't want to wait until the season ended to start analyzing data. I wanted to run the pull scripts periodically to add new games and trades to the database without redoing work that was already done.

Because everything is upserted by a unique key, running the script twice with the same data doesn't create duplicates. And because the script checks what's already in the database before fetching, it skips markets and games that are already fully pulled and only requests new data for everything else. Run it today, run it tommorow, runit again next week, run it before you walk your dog, run it whenever you want and it just fills in the gap without doing repeated work.

### 404 handling

Some finalized MLB games return 404. The data might not be published yet, or the game might have been irregular (suspended, shortened). The script records these in a `not_found` column and retries them on future runs for up to 14 days, then permanently skips them.

## Making it correct

### Validating responses with pydantic

APIs return JSON. We love Jason, but JSON is untyped. A field you expect to be a string might come back as null, missing, or a number. If you just dump raw JSON into your database and something is malformed, you might not find out until weeks later when an analysis produces nonsensical results and you have to trace it back to a bad response you fetched a month ago.

That's why I validated every API response through pydantic models before anything touched the database. Each endpoint has a corresponding model that specifies exactly what fields are expected and what types they should be.

For Kalshi, the models are straightforward because the API returns snake_case keys that match Python conventions directly:

```python
class Trade(BaseModel):
    trade_id: str
    ticker: str
    count_fp: str
    yes_price_dollars: str
    no_price_dollars: str
    taker_outcome_side: str
    taker_book_side: str
    created_time: str
    is_block_trade: bool
```

For MLB, the API returns deeply nested camelCase JSON. Pydantic's `Field(alias=...)` handles the translation:

```python
class ScheduleGame(BaseModel):
    game_pk: int = Field(alias="gamePk")
    game_type: str = Field(alias="gameType")
    game_date: str = Field(alias="gameDate")
    status: GameStatus
    teams: ScheduleTeams
    venue: Venue
    double_header: str = Field(alias="doubleHeader")
    day_night: str | None = Field(alias="dayNight")
```

When a response comes in, `model_validate_json` parses the raw bytes directly into these typed objects. If a field is missing, has the wrong type, or the structure doesn't match, pydantic raises a validation error right there and the bad data never makes it to the database.

This caught several issues during development. Fields that were documented as always present turned out to be null for certain game types. Scores that should have been integers occasionally came back as strings. Finding these at parse time is much easier than tracing them downstream in an analysis.

### Storing everything as text

The Kalshi API returns prices and quantities as strings ("0.45", "10.00") rather than numbers. The database stores them exactly as they arrive, as text. A database view is used to address this. The database view is essentially a saved query that converts text to numbers on the fly, without modifying the raw data. This handles the conversion whenever you read from it.

It might seem wasteful to cast whenever you read from the raw database but it avoids a class of bugs. If the API changes its precision or format, the raw data is still intact. The casts are explicit and testable. And if a cast fails, you find out in the view, not when you're halfway through an analysis wondering why your numbers are wrong.

### Data quality tests

The test suite checks the properties you'd want to verify before running any analysis on this data:

- Every trade has a parent market, every market has a parent event
- Prices are valid probabilities (between 0 and 1, YES + NO = 1.00)
- Trade counts are positive
- Markets close after they open
- No trades happen before market open or more than 5 minutes after close
- No trades from the future
- Finalized markets have a result
- All market statuses are from the known set

If the pull scripts introduce bad data, the tests catch it before any analysis code touches it.

## The tricky part: joining two datasets that don't know about each other

Kalshi doesn't include MLB game IDs in its data. MLB doesn't know anything about Kalshi. The join has to be reconstructed from the ticker format and the schedule.

### Parsing the ticker

Kalshi event tickers encode the game date and team pair. Two formats exist:

- **2025**: `KXMLBGAME-25SEP24KCLAA`
    - date + two team abbreviations + (optional) doubleheader suffix
    - date: 25SEP24 -> September 24th 2025
    - team abbreviations: KC -> Kansas City Royals, LAA -> Los Angeles Angels
    - Doubleheaders get a G1/G2 suffix: `KXMLBGAME-25APR26BALDETG1`.
- **2026**: `KXMLBGAME-26APR301235STLPIT`
    - adds the scheduled start time in Eastern: 12:35 ET 

The team pair is the two market-ticker suffixes concatenated with the away team first. So `STLPIT` means St. Louis (away) at Pittsburgh (home). The pair order was verified empirically across every date-matched event and holds without exception.

A regex parses both formats and team abbreviations are mapped to MLB team IDs via a lookup table.


### Matching to the schedule

The parsed ticker gives a date, a team pair, and sometimes a start time.\
The MLB schedule gives a `game_pk`, teams, and the scheduled start.

Thus, this is the match logic I used

1. Find schedule games on the ticker's date with the same two teams
2. If there's one candidate, done
3. If there are multiple (doubleheader), disambiguate by the G1/G2 suffix (2025), by start-time proximity (2026), or by settlement time

#### Doubleheaders
Traditional doubleheaders schedule both games minutes apart, so start-time proximity is useless. For those, the script looks at when the Kalshi market actually settled and matches it to whichever game ended just before that settlement. This works because Kalshi settles markets shortly after the game ends.

#### Postponed games

A postponed game's event stays on the original date, but the game gets rescheduled, sometimes months later. The ticker date won't match any schedule entry.

For these, the script falls back to settlement-based matching. It searches forward up to 200 days from the ticker date for a game between the same two teams whose ending aligns with the settlement time. The 200-day window is generous because a rain-postponed April game can be made up in September when the opponent next visits.

Cancelled games resolve as "scalar" on Kalshi, which is their way of saying the contract was voided. These are excluded from the analysis.

### Validation

The mapping script runs three checks after building the join:

1. **Match rate**: 99.6% of game events matched (3,558 of 3,572). The 14 unmatched are cancelled games (scalar results) and a handful of postponed games whose makeups haven't been played yet.
2. **Orientation**: every date-matched event has away-first ticker order, confirming the concatenation convention.
3. **Result agreement**: for every finalized market that resolved YES or NO, the Kalshi result matches the MLB schedule's winner. Zero disagreements across 7,000+ markets.

## The prepared tables

A separate preparation script sits between the joined data and the analysis notebook. This is an intentional separation of concerns. The analysis is able to focus soley on analysis, and all data preparation happens in the dabase scripts.

The raw database has 25.7 million trades, but the analysis doesn't want all of them. Two trades on the same game 1 millisecond apart are highly correlated. Using both would inflate sample sizes and make results look more confident than they actually are.

What the analysis needs is one price per game (or inning) that represents the market's best estimate at that point in time. So the preparation script takes the last trade before each game starts, and the last trade before each inning starts.

A few data cleaning decisions are baked into this step. For example, when multiple trades share the same timestamp, the price is taken as the average of the prices. This is a reasonable decision because the median spread on these markets is 1 cent and the 90th percentile is 2 cents, so the averaging is at most shifting the price by about half a cent. It's also deterministic which is better than picking one of the tied trades arbitrarily because results will never change depending on the order the database happens to return rows.

## Key takeaways

- Validate data as it arrives, not after. Pydantic models on every API response mean you find problems at fetch time instead of weeks later in an analysis.
- Retry selectively. Not every error is transient. Retrying a 404 is pointless, but giving up on a 429 is wasteful.
- Exponential backoff with jitter keeps you from making things worse.
- Store raw data raw. Cast and transform in views or preparation scripts, not on the way in. You can always re-derive a cleaner format from the original, but you can't recover precision you threw away.
- Make your pipeline resumable and idempotent. A multi-hour pull that can't survive a crash is a multi-hour pull you'll end up running twice. And if you can't re-run it safely to pick up new data, you're stuck doing manual bookkeeping instead of letting the script figure out what's new.
- Separate concerns. The pull scripts get data in. The preparation script gets data ready. The analysis notebook answers questions. None of them do the other's job.

I hope you found this useful, learned something, and make lots of money.
