# httpx

Modern async HTTP client for Python. Replacement for `requests` with async support, HTTP/2, and connection pooling.

## Installation

```
uv add httpx
```

## Why httpx over requests

- Async support via `AsyncClient` — concurrent API calls without threads
- Connection pooling built in — reuses TCP connections across requests
- HTTP/2 support
- Streaming responses for large payloads
- Type-annotated API
(source: httpx-quickstart.md, httpx-advanced-clients.md)

## Core Pattern: AsyncClient

Always use a client instance, never bare `httpx.get()`:

```python
async with httpx.AsyncClient(base_url="https://api.example.com") as client:
    r = await client.get("/endpoint", params={"key": "value"})
    data = r.json()
```

The `base_url` parameter eliminates repeated URL construction. One client per API.
(source: httpx-advanced-clients.md)

## Configuration

```python
timeout = httpx.Timeout(connect=2.0, read=10.0, write=10.0, pool=2.0)
limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)

async with httpx.AsyncClient(
    base_url="https://trading-api.kalshi.com",
    timeout=timeout,
    limits=limits,
    headers={"Accept": "application/json"},
) as client:
    ...
```
(source: httpx-advanced-clients.md)

## Response Handling

```python
r = await client.get("/markets")
r.raise_for_status()           # raises HTTPStatusError on 4xx/5xx
data = r.json()                # parsed JSON
r.status_code                  # int
r.headers["Content-Type"]      # case-insensitive
```
(source: httpx-quickstart.md)

## Streaming

For large responses without loading the full body into memory:

```python
async with client.stream("GET", "/large-dataset") as r:
    async for chunk in r.aiter_bytes():
        process(chunk)
```

Also available: `aiter_text()`, `aiter_lines()`, `aiter_raw()`.
(source: httpx-async-support.md)

## Redirects

httpx does **not** follow redirects by default (unlike requests):

```python
r = await client.get("/old-path", follow_redirects=True)
```
(source: httpx-quickstart.md)

## Error Handling

```python
try:
    r = await client.get("/endpoint")
    r.raise_for_status()
except httpx.HTTPStatusError as exc:
    # 4xx/5xx — has exc.response and exc.request
    ...
except httpx.RequestError as exc:
    # network error — has exc.request
    ...
```
(source: httpx-quickstart.md)

## Authentication

```python
# Basic auth
await client.get("/endpoint", auth=("user", "pass"))

# Custom auth (e.g., Kalshi RSA-PSS) — implement httpx.Auth subclass
```
(source: httpx-quickstart.md)

## See Also

- [[tenacity]] — retry failed requests with backoff
- [[kalshi-api-auth]] — Kalshi RSA-PSS authentication
- [[kalshi-api-rate-limits]] — Kalshi rate limit tiers
- [[polymarket-us-api]] — Polymarket US API
