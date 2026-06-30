# pydantic

Data validation library using Python type hints. Validates API responses against defined schemas, catching format changes and malformed data early. V2 uses a Rust core (`pydantic-core`) for performance.

## Installation

```
uv add pydantic
```

## Why pydantic for API data

API responses are untrusted data. Pydantic validates and coerces JSON into typed Python objects, guaranteeing field types and catching missing or malformed fields before they propagate through analysis code.
(source: pydantic-docs-models.md)

## Defining Models

Models inherit from `BaseModel` and define typed fields as annotations:

```python
from pydantic import BaseModel, Field
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

Required fields have no default. Optional fields have defaults.
(source: pydantic-docs-models.md)

## Core Methods

| Method | Purpose |
|--------|---------|
| `model_validate(data)` | Validate a dict (Python mode) |
| `model_validate_json(json)` | Validate JSON string/bytes (faster — single Rust pass) |
| `model_validate_strings(data)` | Validate dict with string values |
| `model_dump()` | Serialize to dict |
| `model_dump_json()` | Serialize to JSON string |
| `model_copy(update={...})` | Copy with field updates |
| `model_json_schema()` | Generate JSON Schema |
| `model_construct(**fields)` | Create without validation (trusted data only) |
| `model_rebuild()` | Resolve forward references |

(source: pydantic-docs-models.md)

## Validation Modes

- **Python mode** (`model_validate`) — expects Python types
- **JSON mode** (`model_validate_json`) — looser rules (strings for dates, lists for tuples) because JSON lacks these types
- **Strings mode** (`model_validate_strings`) — all values are strings

`model_validate_json()` is faster than parsing JSON then validating — does both in one Rust-optimized pass.
(source: pydantic-docs-json.md)

## Fields

The `Field()` function customizes fields. See [[pydantic-fields]] for details.

```python
from pydantic import BaseModel, Field

class Model(BaseModel):
    positive: int = Field(gt=0)
    short_str: str = Field(max_length=3)
    name: str = Field(alias='username')
    frozen_field: str = Field(frozen=True)
```

The `Annotated` pattern is preferred for reusable type constraints:

```python
from typing import Annotated
PositiveInt = Annotated[int, Field(gt=0)]
```

(source: pydantic-docs-fields.md)

## Validators

Custom validation at field and model level. See [[pydantic-validators]] for details.

Four field validator types: **after** (post-Pydantic validation, type-safe), **before** (pre-validation, raw input), **plain** (replaces Pydantic validation), **wrap** (most flexible, can intercept).

```python
from typing import Annotated
from pydantic import AfterValidator, BaseModel

def is_even(v: int) -> int:
    if v % 2 == 1:
        raise ValueError(f'{v} is not even')
    return v

EvenInt = Annotated[int, AfterValidator(is_even)]

class Model(BaseModel):
    number: EvenInt
```

Model validators validate the entire model:

```python
from typing_extensions import Self
from pydantic import model_validator

@model_validator(mode='after')
def check_passwords_match(self) -> Self:
    if self.password != self.password_repeat:
        raise ValueError('Passwords do not match')
    return self
```

(source: pydantic-docs-validators.md)

## Serialization

See [[pydantic-serialization]] for details.

```python
market.model_dump()                          # → dict
market.model_dump_json()                     # → JSON string
market.model_dump(exclude={'password'})      # exclude fields
market.model_dump(by_alias=True)             # use aliases
market.model_dump(exclude_none=True)         # skip None fields
market.model_dump(exclude_unset=True)        # skip fields not explicitly set
```

Custom serializers via `@field_serializer`, `@model_serializer`, `PlainSerializer`, `WrapSerializer`.
(source: pydantic-docs-serialization.md)

## Configuration

`ConfigDict` controls model behavior. See [[pydantic-config]] for details.

```python
from pydantic import BaseModel, ConfigDict

class StrictMarket(BaseModel):
    model_config = ConfigDict(
        frozen=True,           # immutable instances
        extra='forbid',        # reject unexpected fields
        strict=True,           # no type coercion
        str_max_length=500,
        from_attributes=True,  # ORM mode
    )
    ticker: str
    title: str
```

Key options: `strict`, `extra`, `frozen`, `validate_assignment`, `from_attributes`, `str_to_lower`, `coerce_numbers_to_str`, `serialize_by_alias`.

Config is inherited by subclasses (merged). Does NOT propagate to nested Pydantic models.
(source: pydantic-docs-config.md)

## Generic Models

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    cursor: str | None = None
    has_more: bool = False
```
(source: pydantic-docs-models.md)

## Nested Models

```python
class Orderbook(BaseModel):
    yes: list[list[float]]
    no: list[list[float]]

class MarketDetail(BaseModel):
    ticker: str
    orderbook: Orderbook
```
(source: pydantic-docs-models.md)

## Discriminated Unions

For union types, discriminators select which model to validate against:

```python
from typing import Literal
from pydantic import BaseModel, Field

class Cat(BaseModel):
    pet_type: Literal['cat']
    age: int

class Dog(BaseModel):
    pet_type: Literal['dog']
    age: int

class Model(BaseModel):
    pet: Cat | Dog = Field(discriminator='pet_type')
```

More performant and predictable than untagged unions.
(source: pydantic-docs-unions.md)

## Handling Extra Data

- `extra='ignore'` (default) — extra fields silently dropped
- `extra='forbid'` — `ValidationError` on extra fields
- `extra='allow'` — extra fields stored in `__pydantic_extra__`

(source: pydantic-docs-models.md)

## Error Handling

`ValidationError` collects **all** errors, not just the first:

```python
from pydantic import ValidationError

try:
    market = KalshiMarket.model_validate(data)
except ValidationError as e:
    print(e.errors())  # list of all validation failures
```
(source: pydantic-docs-models.md)

## TypeAdapter

For validating types that aren't `BaseModel` subclasses:

```python
from pydantic import TypeAdapter

ta = TypeAdapter(list[int])
ta.validate_python(['1', '2'])  # [1, 2]
ta.validate_json(b'[1, 2]')    # [1, 2]
ta.dump_json([1, 2])            # b'[1,2]' (bytes, not str)
```

Create once and reuse — schema building has overhead.
(source: pydantic-docs-type-adapter.md)

## Partial JSON Parsing (v2.7+)

For validating incomplete JSON (useful for LLM outputs):

```python
from pydantic_core import from_json
from pydantic import BaseModel

class Dog(BaseModel):
    breed: str
    name: str
    friends: list = []

partial = '{"breed": "lab", "name": "fluffy", "friends": ["buddy"], "age'
Dog.model_validate(from_json(partial, allow_partial=True))
```

All fields should have defaults for reliable partial parsing.
(source: pydantic-docs-json.md)

## Computed Fields

Properties included in serialization:

```python
from pydantic import BaseModel, computed_field

class Box(BaseModel):
    width: float
    height: float

    @computed_field
    @property
    def area(self) -> float:
        return self.width * self.height
```
(source: pydantic-docs-fields.md)

## See Also

- [[pydantic-fields]] — Field(), constraints, aliases, computed fields, annotated pattern
- [[pydantic-validators]] — field/model validators, validation info, ordering
- [[pydantic-serialization]] — model_dump, serializers, field inclusion/exclusion, polymorphic serialization
- [[pydantic-config]] — ConfigDict reference, propagation rules
- [[httpx]] — fetches the data that pydantic validates
- [[kalshi-market-object]] — Kalshi market data structure
- [[data-pipeline-stack]] — how pydantic fits in the pipeline
