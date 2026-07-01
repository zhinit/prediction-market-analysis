# tenacity

General-purpose retry library for Python. Apache 2.0 license. Evolved from a maintained fork of the `retrying` library.
(source: tenacity-api-reference.md, tenacity-docs.md)

## Installation

```
uv add tenacity
```

## Basic Usage

The `@retry` decorator retries a function whenever it raises an exception, indefinitely, with no wait:

```python
from tenacity import retry

@retry
def do_something_unreliable():
    if random.randint(0, 10) > 1:
        raise IOError("Broken sauce")
    return "Awesome sauce!"
```

Works on both sync and async functions — detected automatically.
(source: tenacity-docs.md)

## Stop Conditions

Control when retrying gives up.
(source: tenacity-docs.md, tenacity-source-strategies.md)

| Strategy | Behavior |
|---|---|
| `stop_after_attempt(n)` | Stop after n attempts |
| `stop_after_delay(seconds)` | Stop after total elapsed time exceeds seconds |
| `stop_before_delay(seconds)` | Stop if next sleep would push total time past seconds (stricter) |
| `stop_when_event_set(event)` | Stop when a `threading.Event` is set |
| `stop_never` | Never stop (default, singleton) |

```python
stop=stop_after_attempt(5)
stop=stop_after_delay(30)
stop=(stop_after_delay(30) | stop_after_attempt(5))  # whichever first
```

Combine with `|` (OR/any) or `&` (AND/all). `stop_any` and `stop_all` are the underlying classes.

`stop_after_delay` vs `stop_before_delay`: `stop_after_delay` checks elapsed time before each attempt but still lets the attempt run, so actual elapsed time can exceed `max_delay`. `stop_before_delay` prevents starting an attempt if the upcoming sleep would push past the deadline.
(source: tenacity-source-strategies.md)

## Wait Strategies

Control delay between retries.
(source: tenacity-docs.md, tenacity-source-strategies.md)

| Strategy | Behavior |
|---|---|
| `wait_none()` | No delay (0s) |
| `wait_fixed(seconds)` | Fixed delay |
| `wait_random(min, max)` | Random delay in [min, max] |
| `wait_incrementing(start, increment, max)` | Linear increase: `start + (attempt-1) * increment` |
| `wait_exponential(multiplier, min, max, exp_base)` | `multiplier * exp_base^(attempt-1)`, clamped to [min, max] |
| `wait_random_exponential(multiplier, max, exp_base, min)` | Full Jitter: random in [min, multiplier * exp_base^(attempt-1)], capped at max |
| `wait_exponential_jitter(initial, max, exp_base, jitter)` | Google Cloud pattern: `initial * exp_base^(attempt-1) + random(0, jitter)` |
| `wait_chain(*strategies)` | Use strategies in sequence; last one repeats forever |
| `wait_combine(*strategies)` | Sum of multiple strategies |

```python
wait=wait_fixed(2)                                    # 2s between retries
wait=wait_exponential(multiplier=1, min=1, max=30)    # 1, 2, 4, 8, ...30
wait=wait_random_exponential(multiplier=1, max=60)    # exponential + jitter (recommended for APIs)
wait=wait_fixed(3) + wait_random(0, 2)                # 3-5s (fixed + jitter)
wait=wait_chain(*[wait_fixed(3) for _ in range(3)] +
               [wait_fixed(7) for _ in range(2)] +
               [wait_fixed(9)])                        # 3s x3, 7s x2, then 9s forever
```

Combine with `+` operator (additive).

`wait_random_exponential` implements the "Full Jitter" algorithm for distributed systems — prevents thundering herd when multiple clients back off simultaneously.
(source: tenacity-source-strategies.md)

## Retry Conditions

Control which outcomes trigger a retry.
(source: tenacity-docs.md, tenacity-source-strategies.md)

### Exception-based

```python
retry=retry_if_exception_type(IOError)                        # specific type
retry=retry_if_exception_type((IOError, ConnectionError))     # multiple types
retry=retry_if_not_exception_type(ClientError)                # everything except
retry=retry_unless_exception_type(ClientError)                # retry UNTIL this type
retry=retry_if_exception(lambda e: "timeout" in str(e))       # predicate on exception
retry=retry_if_exception_cause_type(ConnectionError)          # walks __cause__ chain
retry=retry_if_exception_message(match=r"5\d\d")             # regex on message
retry=retry_if_exception_message(message="exact match")       # exact string match
```

`retry_if_exception_cause_type` recursively walks the `__cause__` chain — useful when the exception you care about is wrapped.
(source: tenacity-source-strategies.md)

### Result-based

```python
retry=retry_if_result(lambda x: x is None)       # retry on None return
retry=retry_if_not_result(lambda x: x > 0)       # retry unless positive
```
(source: tenacity-docs.md)

### Combining conditions

```python
retry=(retry_if_result(is_none) | retry_if_exception_type())  # OR
retry=(condition_a & condition_b)                              # AND
```

`|` maps to `retry_any`, `&` maps to `retry_all`.
(source: tenacity-source-strategies.md)

### Explicit retry

Raise `TryAgain` inside a retried function to force an immediate retry regardless of conditions:

```python
from tenacity import retry, TryAgain

@retry
def do_something():
    result = something_else()
    if result == 23:
        raise TryAgain
```
(source: tenacity-docs.md)

## Error Handling

When all retries are exhausted, tenacity raises `RetryError` by default. The original exception is in the middle of the stack trace.

With `reraise=True`, the original exception is re-raised directly:

```python
@retry(reraise=True, stop=stop_after_attempt(3))
def raise_my_exception():
    raise MyException("Fail")

try:
    raise_my_exception()
except MyException:
    pass  # original exception, not RetryError
```

`RetryError.last_attempt` contains the `Future` of the final attempt.
(source: tenacity-docs.md, tenacity-api-reference.md)

## Callbacks and Logging

Six callback hooks, each accepts a `RetryCallState` parameter:
(source: tenacity-docs.md, tenacity-source-callbacks.md, tenacity-api-reference.md)

| Hook | When | Built-in |
|---|---|---|
| `before` | Before each attempt | `before_log(logger, level)`, `before_nothing` |
| `after` | After each attempt | `after_log(logger, level, sec_format)`, `after_nothing` |
| `before_sleep` | Before waiting between retries | `before_sleep_log(logger, level, exc_info, sec_format)`, `before_sleep_nothing` |
| `retry_error_callback` | When all retries exhausted | (no built-in) |

### Built-in log messages

- `before_log`: `"Starting call to '{fn}', this is the {N}th time calling it."`
- `after_log`: `"Finished call to '{fn}' after {seconds}(s), this was the {N}th time calling it."`
- `before_sleep_log`: `"Retrying {fn} in {seconds} seconds as it {raised/returned} {value}."` With `exc_info=True`, appends full traceback.
(source: tenacity-source-callbacks.md)

### Usage

```python
import logging
logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    before=before_log(logger, logging.DEBUG),
    after=after_log(logger, logging.DEBUG),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def my_function():
    raise Exception("fail")
```

### Custom callbacks

Any callable accepting `RetryCallState`:

```python
def my_before_sleep(retry_state):
    if retry_state.attempt_number < 1:
        loglevel = logging.INFO
    else:
        loglevel = logging.WARNING
    logger.log(
        loglevel, 'Retrying %s: attempt %s ended with: %s',
        retry_state.fn, retry_state.attempt_number, retry_state.outcome)
```

### retry_error_callback

Called when all retries are exhausted. Return value becomes the function's return value instead of raising:

```python
def return_last_value(retry_state):
    return retry_state.outcome.result()

@retry(
    stop=stop_after_attempt(3),
    retry_error_callback=return_last_value,
    retry=retry_if_result(lambda x: x is False),
)
def eventually_return_false():
    return False
# Returns False instead of raising RetryError
```
(source: tenacity-docs.md)

### Custom strategy callbacks

Full custom strategies follow the same pattern:

| Callback type | Signature | Returns |
|---|---|---|
| `my_stop(retry_state)` | RetryCallState → bool | True to stop |
| `my_wait(retry_state)` | RetryCallState → float | Seconds to wait |
| `my_retry(retry_state)` | RetryCallState → bool | True to retry |
| `my_before(retry_state)` | RetryCallState → None | — |
| `my_after(retry_state)` | RetryCallState → None | — |
| `my_before_sleep(retry_state)` | RetryCallState → None | — |

(source: tenacity-docs.md, tenacity-api-reference.md)

## RetryCallState

Available attributes in all callbacks:
(source: tenacity-api-reference.md, tenacity-source-callbacks.md)

| Attribute | Type | Description |
|---|---|---|
| `fn` | callable | The wrapped function |
| `args` | tuple | Positional args passed to fn |
| `kwargs` | dict | Keyword args passed to fn |
| `attempt_number` | int | Current attempt count (starts at 1) |
| `outcome` | Future | Result or exception of last attempt |
| `outcome_timestamp` | float | When outcome was set |
| `start_time` | float | When first attempt began |
| `seconds_since_start` | float | Elapsed time since first attempt |
| `idle_for` | float | Total time spent sleeping |
| `next_action` | RetryAction/None | Next action (has `.sleep` attribute for wait duration) |

Methods:
- `set_result(val)` — manually set the result (needed in async context managers)
- `get_fn_name()` — get the wrapped function's name

## Statistics

Decorated functions expose retry statistics:

```python
@retry(stop=stop_after_attempt(3))
def my_function():
    raise Exception("Fail")

try:
    my_function()
except Exception:
    pass

print(my_function.retry.statistics)
# {'start_time': ..., 'attempt_number': 3, 'idle_for': 4.2, ...}
```
(source: tenacity-docs.md)

## Runtime Modification

### retry_with

Create a modified copy for a single invocation:

```python
@retry(stop=stop_after_attempt(3))
def my_function():
    raise MyException("Fail")

# One-off with different settings
my_function.retry_with(stop=stop_after_attempt(10))()

# Disable retries entirely
my_function.retry_with(retry=tenacity.retry_if_exception_type())()
```
(source: tenacity-docs.md)

### Using Retrying directly

```python
from tenacity import Retrying, stop_after_attempt

retryer = Retrying(stop=stop_after_attempt(3), reraise=True)
retryer(my_function, arg1, arg2, kwarg1="value")
```
(source: tenacity-docs.md)

## Code Block Retrying (Context Manager)

Retry arbitrary code blocks without wrapping in a function:

### Synchronous

```python
from tenacity import Retrying, RetryError, stop_after_attempt

try:
    for attempt in Retrying(stop=stop_after_attempt(3)):
        with attempt:
            raise Exception('My code is failing!')
except RetryError:
    pass
```

### Asynchronous

```python
from tenacity import AsyncRetrying, RetryError, stop_after_attempt

async def function():
    try:
        async for attempt in AsyncRetrying(stop=stop_after_attempt(3)):
            with attempt:
                raise Exception('My code is failing!')
    except RetryError:
        pass
```

### Setting results in async context managers

When using result-based retry conditions with async context managers, manually set the result:

```python
async for attempt in AsyncRetrying(retry=retry_if_result(lambda x: x < 3)):
    with attempt:
        result = 1
    if not attempt.retry_state.outcome.failed:
        attempt.retry_state.set_result(result)
return result
```
(source: tenacity-docs.md)

## Async Support

Works natively on async functions — detected automatically. Sleeps are async too:

```python
@retry
async def my_async_function(loop):
    await loop.getaddrinfo('8.8.8.8', 53)
```

For alternative event loops (Trio, curio), pass the sleep callable:

```python
@retry(sleep=trio.sleep)
async def my_async_function():
    await asks.get('https://example.org')
```
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
(source: tenacity-docs.md)

## Limitations

- Does not support generator or async generator functions. The decorator wraps the function call, not iteration. Generators passed as arguments are exhausted after the first attempt.
(source: tenacity-docs.md)

## All Importable Names

```python
from tenacity import (
    # Decorator
    retry,
    # Classes
    Retrying, AsyncRetrying, RetryCallState, RetryError, TryAgain,
    # Stop
    stop_after_attempt, stop_after_delay, stop_before_delay,
    stop_when_event_set, stop_never, stop_all, stop_any,
    # Wait
    wait_none, wait_fixed, wait_random, wait_incrementing,
    wait_exponential, wait_random_exponential, wait_exponential_jitter,
    wait_chain, wait_combine,
    # Retry conditions
    retry_if_exception, retry_if_exception_type, retry_if_not_exception_type,
    retry_unless_exception_type, retry_if_exception_cause_type,
    retry_if_exception_message, retry_if_not_exception_message,
    retry_if_result, retry_if_not_result, retry_all, retry_any,
    # Callbacks
    before_log, before_nothing, after_log, after_nothing,
    before_sleep_log, before_sleep_nothing,
)
```
(source: tenacity-api-reference.md)

## See Also

- [[httpx]] — HTTP client that tenacity wraps
- [[kalshi-api-rate-limits]] — Kalshi token bucket rate limits
- [[data-pipeline-stack]] — how tenacity fits in the pipeline
