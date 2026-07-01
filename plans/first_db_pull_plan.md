# First Data Pull: Kalshi MLB Markets

Goal: pull all Kalshi MLB market data (catalog + trade history + outcomes)
into `db/pma.db` (DuckDB).

---

## Step 0: Setup

- [x] Create `db/` directory
- [x] `uv add httpx tenacity pydantic duckdb polars`
- [x] Verify connectivity: hit `GET /exchange/status` (public, no auth)
- [x] Base URL: `https://external-api.kalshi.com/trade-api/v2`

No auth needed for the entire pull — all market data, trade, and event
endpoints are public (wiki: [[kalshi-api-market-data]]).

## Step 1: Build the HTTP client ✅ DONE

Use `httpx.AsyncClient` with connection pooling. Wrap fetch calls with
tenacity for automatic 429 retry with exponential backoff + jitter
(wiki: [[data-pipeline-stack]], [[httpx]], [[tenacity]]).

```python
import httpx
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type

@retry(
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
    reraise=True,
)
async def fetch(client: httpx.AsyncClient, path: str, **params) -> bytes:
    r = await client.get(path, params=params)
    r.raise_for_status()
    return r.content

client = httpx.AsyncClient(
    base_url="https://external-api.kalshi.com/trade-api/v2",
    timeout=httpx.Timeout(connect=2.0, read=10.0),
)
```

## Step 2: Define Pydantic models ✅ DONE

Validate API responses before they reach the database
(wiki: [[pydantic]], [[kalshi-market-object]]).

```python
from pydantic import BaseModel

class Event(BaseModel):
    event_ticker: str
    series_ticker: str
    title: str
    category: str
    sub_title: str | None = None

class EventResponse(BaseModel):
    events: list[Event]
    cursor: str | None = None

class Market(BaseModel):
    ticker: str
    event_ticker: str
    market_type: str
    yes_sub_title: str | None = None
    no_sub_title: str | None = None
    status: str
    result: str | None = None
    open_time: str | None = None
    close_time: str | None = None
    settlement_ts: str | None = None
    settlement_value_dollars: str | None = None
    volume_fp: str | None = None
    open_interest_fp: str | None = None
    rules_primary: str | None = None

class MarketResponse(BaseModel):
    markets: list[Market]
    cursor: str | None = None

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

class TradeResponse(BaseModel):
    trades: list[Trade]
    cursor: str | None = None
```

## Step 3: Build the paginator ✅ DONE

Cursor-based pagination, max 1000 per page (wiki: [[kalshi-api-pagination]]).

```python
async def fetch_all(
    client: httpx.AsyncClient,
    path: str,
    response_model: type[BaseModel],
    result_key: str,
    **params,
) -> list:
    results = []
    cursor = None
    while True:
        p = {**params, "limit": 1000}
        if cursor:
            p["cursor"] = cursor
        raw = await fetch(client, path, **p)
        response = response_model.model_validate_json(raw)
        results.extend(getattr(response, result_key))
        cursor = response.cursor
        if not cursor:
            break
    return results
```

## Step 4: Find the MLB series/events ✅ DONE

Events and series stay on live endpoints regardless of age — no historical
split applies to them (wiki: [[kalshi-api-historical]]).

```
GET /events?series_ticker=MLB  (try this first)
GET /events?status=open        (browse if the series ticker is wrong)
```

Look for the series_ticker that covers MLB game outcomes. Save it once
found — you'll filter everything else by it.

## Step 5: Pull all MLB markets (live + historical) ✅ DONE

The live/historical split applies to markets
(wiki: [[kalshi-api-historical]]).

**5a.** Get the cutoff — public, no auth:
```
GET /historical/cutoff
```
Note `market_settled_ts` — markets settled before this need the historical
endpoint.

**5b.** Pull historical markets:
```
GET /historical/markets?series_ticker=<MLB_TICKER>
```
Filters include `series_ticker`, `event_ticker`, `tickers`
(mutually exclusive).

**5c.** Pull live markets:
```
GET /markets?series_ticker=<MLB_TICKER>
```

**5d.** Merge and deduplicate by `ticker` in memory before inserting.

## Step 6: Pull all MLB trades (live + historical) ✅ DONE

Biggest pull. Same two-tier pattern. `trades_created_ts` from the cutoff
response determines the boundary.

**6a.** Pull historical trades:
```
GET /historical/trades?ticker=<MARKET_TICKER>&limit=1000
```
Supports `min_ts`, `max_ts` for timestamp range filtering. Pull per
market ticker — safer than pulling everything and filtering client-side.

**6b.** Pull live trades:
```
GET /markets/trades?ticker=<MARKET_TICKER>&limit=1000
```

**6c.** Merge and deduplicate by `trade_id` in memory.

## Step 7: Load into DuckDB ✅ DONE (pulled forward into step 6)

Store in `db/pma.db` — the single project database
(wiki: [[duckdb]]).

```sql
CREATE TABLE IF NOT EXISTS events (
    event_ticker TEXT PRIMARY KEY,
    series_ticker TEXT NOT NULL,
    title TEXT,
    category TEXT,
    sub_title TEXT
);

CREATE TABLE IF NOT EXISTS markets (
    ticker TEXT PRIMARY KEY,
    event_ticker TEXT NOT NULL REFERENCES events(event_ticker),
    market_type TEXT,
    yes_sub_title TEXT,
    no_sub_title TEXT,
    status TEXT NOT NULL,
    result TEXT,
    open_time TIMESTAMPTZ,
    close_time TIMESTAMPTZ,
    settlement_ts TIMESTAMPTZ,
    settlement_value_dollars DECIMAL(10,6),
    volume_fp TEXT,
    open_interest_fp TEXT,
    rules_primary TEXT
);

CREATE TABLE IF NOT EXISTS trades (
    trade_id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL REFERENCES markets(ticker),
    count_fp TEXT,
    yes_price_dollars DECIMAL(10,6),
    no_price_dollars DECIMAL(10,6),
    taker_outcome_side TEXT,
    taker_book_side TEXT,
    created_time TIMESTAMPTZ NOT NULL,
    is_block_trade BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_markets_event_ticker ON markets(event_ticker);
CREATE INDEX IF NOT EXISTS idx_trades_ticker ON trades(ticker);
CREATE INDEX IF NOT EXISTS idx_trades_created_time ON trades(created_time);
```

Load from Polars DataFrames:

```python
import polars as pl
import duckdb

events_df = pl.DataFrame([e.model_dump() for e in events])
markets_df = pl.DataFrame([m.model_dump() for m in markets])
trades_df = pl.DataFrame([t.model_dump() for t in trades])

with duckdb.connect("db/pma.db") as con:
    con.sql("INSERT INTO events SELECT * FROM events_df")
    # etc.
```

## Step 8: Sanity checks ⬅️ START HERE

```sql
-- Row counts
SELECT 'events' AS tbl, count(*) FROM events
UNION ALL SELECT 'markets', count(*) FROM markets
UNION ALL SELECT 'trades', count(*) FROM trades;

-- Settled markets should have a result
SELECT result, count(*) FROM markets
WHERE status = 'finalized' GROUP BY result;

-- Trade volume distribution
SELECT ticker, count(*) AS n_trades
FROM trades GROUP BY ticker ORDER BY n_trades DESC LIMIT 20;

-- Referential integrity
SELECT ticker FROM trades t
LEFT JOIN markets m ON t.ticker = m.ticker
WHERE m.ticker IS NULL;

-- No dupes
SELECT trade_id, count(*) FROM trades
GROUP BY trade_id HAVING count(*) > 1;
```

## Rate limit awareness

Basic tier: 200 read tokens/sec, 10 tokens per request = ~20 req/sec
(wiki: [[kalshi-api-rate-limits]]). Tenacity handles 429s automatically
with exponential backoff + jitter. No manual sleep needed.

## File structure when done

```
db/
  pma.db                 -- DuckDB database
scripts/
  pull_kalshi_mlb.py     -- the pull script
```
