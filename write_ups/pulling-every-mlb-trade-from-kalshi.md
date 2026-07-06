---
title: Pulling every MLB Game Winner trade from Kalshi 
date: 2026-07-06
description: Building an idempotent pipeline that lands 25 million Kalshi trades and every MLB game into DuckDB — validation at the boundary, exponential backoff, rerun-anytime incremental fetches, and matching two data sources that don't share a key.
---

I wanted to search for mispricings on prediction markets to see if there are any profitable opporunities. To do this you must analyze available data and to analyze available data you must pull in and clean the available data. 

Any one who has spent significant time doing data analysis or predictive modeling has heard "garbage in, garbage out" and understands the importance of pulling and cleaning your data propperly.

*For those who have not heard "garbage in, garbage out" before, it means that if you put garbage into your analysis/model, it doesnt matter how good your model/analysis are, you will get garbage output.*

This article describes my process for pulling data from the Kalshi and MLB stats API's for the purposes of this analysis, and general advice/methodology for anyone looking to do similar data pulls for predictive markets analysis. A write up for the subsequent analysis can be found <link goes here>

## What we're pulling and where it goes

We join two data sources into one database. The Kalshi API has the prediction market data (orderbook, trades, etc), and the MLB Stats API has detailed MLB data for each game (play-by-play, weather, etc) for every game played.

Everything lands in a single DuckDB file. I chose DuckDB because it's an embedded analytical database that runs in-process with no server to manage. You `uv add duckdb`, point it at a file, and you have a full SQL engine. For a project like this where you're one person running queries on a laptop, it's exactly right.

The pipeline is three scripts run in sequence: pull Kalshi data, pull MLB data, then join them together. A fourth script prepares tables for a specific analysis, but that one runs separately (more on why later).

## The Kalshi pull

Kalshi organizes their data into a hierarchy: a **series** (like KXMLBGAME, which covers all MLB Game Winner markets) contains **events** (one per game), each event has **markets** (typically two — one for each team), and each market has **trades**.

The pull starts at the top and works down. Fetch all events in the KXMLBGAME series, fetch all markets for those events, then fetch every trade for every market. The trades are the expensive part — there are millions of them, and you have to page through them one market at a time.

### Storing text, casting later

Every field from the API comes in as TEXT. Timestamps, dollar amounts, volumes — all stored as strings in the raw tables. Typed views sit on top and cast everything into proper types (TIMESTAMP, DECIMAL, etc.) for queries downstream.

This sounds unnecessarily cautious but it solves a real problem. If Kalshi changes the precision of a dollar field or tweaks the timezone format on a timestamp, you dont want your pull to crash on a cast error halfway through ingesting 25 million trades. The raw data lands safely regardless. If a cast fails, you find out when you query the view, not when you're three hours into a pull.

### Validation at the boundary

Every API response gets validated through a Pydantic model before anything touches the database. The models define the exact shape of what Kalshi returns — which fields exist, which are optional, what types they should be. If the API returns something unexpected, it fails immediately with a clear error instead of silently inserting garbage.

This is where "garbage in, garbage out" becomes practical. You can't validate data you've already stored. Catching bad data at the point of entry means the database is always clean, and you never have to wonder whether that weird outlier in your analysis is a real signal or a parsing bug.

### Exponential backoff

The Kalshi API rate limits aggressively. Any serious pull is going to hit 429s. The fetch function retries on 429s and 5xx errors with randomized exponential backoff — first retry after ~1 second, second after ~2-4 seconds, scaling up to a max of 60 seconds, with jitter so you dont accidentally synchronize retries. Non-retryable errors (bad request, unauthorized, etc.) fail immediately. All the requests are idempotent GETs, so retrying is always safe.

### Making it rerunnable

The first time you run this script, it takes hours. You do not want to start from scratch if something goes wrong in the middle, and you do not want to re-pull trades you already have when you come back a week later for new data.

Two mechanisms handle this. First, trades are keyed by `trade_id` and inserted with `INSERT OR REPLACE`, so re-pulling a trade you already have is a no-op instead of a duplicate. Second, a bookkeeping table (`kalshi_trade_pulls`) tracks which markets have been fully pulled. On the next run, those markets are skipped entirely.

There's also the question of which endpoint to use. Kalshi splits their trade data between a historical endpoint (for trades before a rolling cutoff date) and a live endpoint (for trades after it). The script checks the cutoff, figures out which markets need historical trades, which need live trades, and which need both, then pulls from the right endpoint accordingly. Markets that straddle the cutoff get pulled from both — deduplicated on insert.

The result is that you can run the script every day and it finishes in minutes, only pulling new trades. Or you can blow away the database and rebuild from scratch. Same script, same command, different runtime.

## The MLB pull

The MLB Stats API is a completely different beast. It's free, has generous rate limits, and is deeply nested JSON. No API key required.

The pull happens in two phases. First, the schedule: every game from opening day through 10 days into the future, chunked by month. This gives you game IDs, teams, scores, venues, and game status. Second, per-game detail: play-by-play, win probability, and weather for every finalized game.

The per-game pulls run concurrently (five at a time, controlled by a semaphore) since each game is independent. A bookkeeping table tracks which games have been fully pulled, same pattern as the Kalshi side.

One wrinkle: some games return 404 on the play-by-play or win probability endpoints. This is normal — the data might not be published yet, especially for recent games. The script records the 404 and retries on subsequent runs for up to 14 days. After that it gives up and marks the game as permanently missing.

## Matching two data sources that don't share a key

This is where the interesting engineering problem lives. Kalshi and MLB have no shared identifier. There's no field in a Kalshi event that says "this is MLB game 748291." You have to figure it out from the event ticker string.

### Parsing the ticker

Kalshi event tickers follow a naming convention that encodes the game date and the two teams. But the convention changed between 2025 and 2026:

- **2025 format:** `KXMLBGAME-25SEP24KCLAA` — year, month, day, two team abbreviations concatenated. Doubleheaders get a G1/G2 suffix.
- **2026 format:** `KXMLBGAME-26APR301235STLPIT` — year, month, day, start time in Eastern, two team abbreviations. Doubleheaders are disambiguated by their different start times, no suffix needed.

A regex parses both formats into a structured object: date, optional start time, team pair, optional game number. The team pair is the tricky part — it's two abbreviations smashed together with no delimiter. `STLPIT` is St. Louis and Pittsburgh. `KCLAA` is Kansas City and Los Angeles Angels. The script figures out where to split by looking at which abbreviations appear as suffixes in the event's market tickers.

### The team abbreviation problem

Kalshi uses their own team abbreviations, which mostly but not perfectly match what you'd expect. Arizona is `ARI` in 2025 data and `AZ` in 2026 data. The Chicago White Sox are `CWS`. Oakland (now Sacramento) is `ATH`. A lookup table maps every Kalshi abbreviation to the MLB Stats API's numeric team ID.

### Doubleheaders and postponements

Single games on a given date between two specific teams match trivially. Doubleheaders are harder. In the 2025 data, the G1/G2 suffix tells you which game. In the 2026 data, the start time embedded in the ticker handles it — pick the game whose scheduled start is closest.

But traditional doubleheaders (where both games are scheduled minutes apart) break start-time matching because the times are essentially identical. For those, the script falls back to settlement timing: Kalshi settles a market shortly after the game ends, so the market that settled around 7pm belongs to the game that ended around 7pm.

Postponed games are the worst case. A game gets rained out, the Kalshi event has a date with no corresponding MLB game, and the makeup happens weeks or months later on a completely different date. The script handles this by searching forward up to 200 days for a game between the same two teams whose ending aligns with when the Kalshi market settled.

### Verification

After matching, the script runs a battery of checks. The overall match rate must exceed 99%. Every date-matched event must have the away team first in the ticker (this verifies the parsing convention). And a semantic spot check: for every finalized market that resolved yes or no, verify that the market's result agrees with the MLB schedule's recorded winner. Zero disagreements allowed.

These checks are assertions, not warnings. If matching quality degrades — say Kalshi changes their ticker format, or a new edge case appears — the script crashes instead of writing bad data.

## Preparing data for analysis

The three scripts above (pull Kalshi, pull MLB, match) run together via a single `refresh.py` and can safely be re-run anytime. They maintain a mirror of the raw data.

The analysis prep script is deliberately separate. It transforms the mirrored data into tables shaped for a specific analysis — in this case, a calibration study asking "when Kalshi says a team has a 70% chance of winning, do they actually win 70% of the time?"

The prep script builds snapshot tables: for each game and each side (home team market, away team market), it finds the last trade before the scheduled start time and records that price as the market's pre-game probability. It does the same thing at each inning boundary for in-game calibration. Deduplication, tie-breaking, weather parsing, and dataset filtering all happen here.

Why keep this separate from refresh? Because a finished analysis's numbers should be reproducible. If the prep script ran automatically on every refresh, new data would silently change the dataset underneath a published write-up. By running it manually, the prepared tables are a frozen snapshot of the exact dataset the analysis was computed from. The prep script even writes a `build_info` row recording when it ran and what data range it covers.

## General advice

A few things I'd do the same way on any similar project:

**Store raw, cast later.** You will encounter weird data. Storing everything as text and casting in views means your pull never crashes on unexpected formats, and you can fix casting issues without re-pulling.

**Validate at entry, not at query time.** If you catch bad data when it enters the database, you never have to wonder whether a downstream anomaly is real or an artifact. Pydantic models are great for this.

**Make every run incremental.** A pull that takes hours the first time should take minutes on subsequent runs. Bookkeeping tables that track what's been fully pulled are simple and reliable. Key everything on natural IDs and use INSERT OR REPLACE so re-processing is always safe.

**Separate your mirror from your analysis prep.** The mirror is a faithful copy of the source data and should stay current. Analysis-specific transformations should be a separate, manually-triggered step so your results are reproducible.

**Test your data, not just your code.** Referential integrity checks, range validation, cast-ability tests, cross-source agreement checks — these catch real problems that unit tests on your pull logic never will. Run them after every pull.
