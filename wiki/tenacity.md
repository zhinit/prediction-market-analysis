# tenacity

Python retry library with exponential backoff, jitter, and async support. Handles transient API failures and rate limiting.

## Installation

```
uv add tenacity
```

## Why tenacity

API calls fail transiently — 429 rate limits, 503 service unavailable, network timeouts. Tenacity wraps any function with configurable retry logic: how long to wait, when to stop, which errors to retry.
(source: tenacity-docs.md)

## Recommended Pattern for API Rate Limits

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import httpx
import logging

logger = logging.getLogger(__name__)

@retry(
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def fetch_with_retry(client: httpx.AsyncClient, url: str, **kwargs):
    r = await client.get(url, **kwargs)
    r.raise_for_status()
    return r.json()
```

`wait_random_exponential` adds jitter to prevent thundering herd on rate-limited APIs.
(source: tenacity-docs.md)

## Stop Conditions

```python
stop=stop_after_attempt(5)              # max 5 tries
stop=stop_after_delay(30)               # max 30 seconds total
stop=(stop_after_delay(30) | stop_after_attempt(5))  # whichever first
```
(source: tenacity-docs.md)

## Wait Strategies

```python
wait=wait_fixed(2)                       # 2s between retries
wait=wait_exponential(multiplier=1, min=1, max=30)  # 1, 2, 4, 8, ...30
wait=wait_random_exponential(multiplier=1, max=60)   # exponential + jitter
wait=wait_fixed(3) + wait_random(0, 2)   # 3-5s (fixed + jitter)
```
(source: tenacity-docs.md)

## Retry Conditions

```python
retry=retry_if_exception_type(httpx.HTTPStatusError)  # only HTTP errors
retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError))
retry=retry_if_result(lambda x: x is None)  # retry on None return
```
(source: tenacity-docs.md)

## Async Support

Works natively on async functions — sleeps are async too:

```python
@retry(wait=wait_random_exponential(max=60))
async def fetch_data(client, url):
    r = await client.get(url)
    r.raise_for_status()
    return r.json()
```
(source: tenacity-docs.md)

## Code Block Retrying

For retrying arbitrary code blocks without a decorator:

```python
from tenacity import AsyncRetrying, stop_after_attempt

async for attempt in AsyncRetrying(stop=stop_after_attempt(3)):
    with attempt:
        result = await some_operation()
```
(source: tenacity-docs.md)

## Statistics

```python
fetch_with_retry.retry.statistics
# {'start_time': ..., 'attempt_number': 3, 'idle_for': 4.2, ...}
```
(source: tenacity-docs.md)

## See Also

- [[httpx]] — HTTP client that tenacity wraps
- [[kalshi-api-rate-limits]] — Kalshi token bucket rate limits
- [[data-pipeline-stack]] — how tenacity fits in the pipeline
