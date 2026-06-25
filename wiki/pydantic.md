# pydantic

Data validation library using Python type hints. Validates API responses against defined schemas, catching format changes and malformed data early.

## Installation

```
uv add pydantic
```

## Why pydantic for API data

API responses are untrusted data. Pydantic validates and coerces JSON into typed Python objects, guaranteeing field types and catching missing or malformed fields before they propagate through analysis code.
(source: pydantic-getting-started.md)

## Defining Response Models

```python
from pydantic import BaseModel
from datetime import datetime

class KalshiMarket(BaseModel):
    ticker: str
    title: str
    status: str
    yes_ask: float | None = None
    yes_bid: float | None = None
    volume: int
    open_time: datetime
    close_time: datetime
    result: str | None = None

class KalshiMarketsResponse(BaseModel):
    markets: list[KalshiMarket]
    cursor: str | None = None
```
(source: pydantic-models.md)

## Validating API Responses

```python
# From JSON bytes (fastest)
response = KalshiMarketsResponse.model_validate_json(r.content)

# From dict
response = KalshiMarketsResponse.model_validate(r.json())
```

`model_validate_json()` is faster than parsing JSON then validating — it does both in one Rust-optimized pass.
(source: pydantic-models.md)

## Serialization

```python
market.model_dump()        # → dict
market.model_dump_json()   # → JSON string
```
(source: pydantic-models.md)

## Generic Models for Paginated Responses

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    cursor: str | None = None
    has_more: bool = False
```
(source: pydantic-models.md)

## Nested Models

```python
class Orderbook(BaseModel):
    yes: list[list[float]]
    no: list[list[float]]

class MarketDetail(BaseModel):
    ticker: str
    orderbook: Orderbook
```
(source: pydantic-models.md)

## Error Handling

`ValidationError` collects **all** errors, not just the first:

```python
from pydantic import ValidationError

try:
    market = KalshiMarket.model_validate(data)
except ValidationError as e:
    print(e.errors())  # list of all validation failures
```
(source: pydantic-models.md)

## Configuration

```python
from pydantic import ConfigDict

class StrictMarket(BaseModel):
    model_config = ConfigDict(
        frozen=True,          # immutable instances
        extra="forbid",       # reject unexpected fields
        str_max_length=500,
    )
    ticker: str
    title: str
```
(source: pydantic-models.md)

## See Also

- [[httpx]] — fetches the data that pydantic validates
- [[kalshi-market-object]] — Kalshi market data structure
- [[data-pipeline-stack]] — how pydantic fits in the pipeline
