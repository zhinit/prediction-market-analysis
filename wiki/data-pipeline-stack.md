# Data Pipeline Stack

The recommended stack for pulling prediction market and sports data into this project. Five layers, each with a single responsibility.

```
httpx (fetch) → tenacity (retry) → pydantic (validate) → polars (transform) → duckdb (store)
```

## Layer 1: Fetch — [[httpx]]

`httpx.AsyncClient` makes HTTP requests with connection pooling. One client per API (Kalshi, Polymarket, MLB). `base_url` eliminates repeated URL construction.

```python
async with httpx.AsyncClient(
    base_url="https://trading-api.kalshi.com/trade-api/v2",
    timeout=httpx.Timeout(connect=2.0, read=10.0),
) as kalshi:
    ...
```
(source: httpx-quickstart.md, httpx-advanced-clients.md)

## Layer 2: Retry — [[tenacity]]

Wraps fetch calls with exponential backoff + jitter. Handles 429 rate limits and transient failures without manual retry loops.

```python
@retry(
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
    reraise=True,
)
async def fetch(client, path, **params):
    r = await client.get(path, params=params)
    r.raise_for_status()
    return r.content
```
(source: tenacity-docs.md)

## Layer 3: Validate — [[pydantic]]

Parses API JSON into typed Python objects. Catches schema changes, missing fields, and type mismatches before they reach analysis code.

```python
class Market(BaseModel):
    ticker: str
    yes_bid: float | None
    volume: int

response = MarketResponse.model_validate_json(raw_bytes)
```
(source: pydantic-models.md)

## Layer 4: Transform — [[polars]]

Converts validated objects to DataFrames. Expression API for filtering, aggregation, and derived columns. Lazy mode for optimized queries on large datasets.

```python
df = pl.DataFrame([m.model_dump() for m in response.markets])
result = (
    df.lazy()
    .filter(pl.col("volume") > 100)
    .with_columns(spread=pl.col("yes_ask") - pl.col("yes_bid"))
    .collect()
)
```
(source: polars-getting-started.md, polars-lazy-api.md)

## Layer 5: Store — [[duckdb]]

Persistent analytical database in `db/pma.db`. Queries Polars DataFrames directly. Data survives between runs.

```python
with duckdb.connect("db/pma.db") as con:
    con.sql("CREATE TABLE IF NOT EXISTS markets AS SELECT * FROM df")
    # Or append
    con.sql("INSERT INTO markets SELECT * FROM df")
```
(source: duckdb-python-api.md)

## Pagination Pattern

Most APIs return paginated results. The cursor loop lives between fetch and validate:

```python
async def fetch_all_markets(client: httpx.AsyncClient) -> list[Market]:
    markets = []
    cursor = None
    while True:
        params = {"limit": 100}
        if cursor:
            params["cursor"] = cursor
        raw = await fetch(client, "/markets", **params)
        response = MarketResponse.model_validate_json(raw)
        markets.extend(response.markets)
        if not response.cursor:
            break
        cursor = response.cursor
    return markets
```

Kalshi uses cursor-based pagination (source: [[kalshi-api-pagination]]). Polymarket US uses similar patterns.

## Rate Limit Awareness

Kalshi's token bucket system has per-tier budgets (source: [[kalshi-api-rate-limits]]). The tenacity retry layer handles 429 responses automatically, but for sustained high-volume pulls, track the `X-RateLimit-Remaining` header and throttle proactively rather than relying solely on retries.

## File Format Choice

Parquet is the default storage format for intermediate data. It is columnar, compressed, and Polars reads/writes it faster than CSV. Use CSV only for human-inspectable exports.
(source: polars-io-parquet.md)

## See Also

- [[kalshi-api]] — Kalshi API overview
- [[polymarket-us-api]] — Polymarket US API overview
- [[mlb-stats-api]] — MLB Stats API overview
