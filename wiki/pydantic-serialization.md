# pydantic-serialization

Serialization (dumping) of Pydantic models to dicts and JSON.

## Core Methods

```python
m.model_dump()                   # → dict (Python mode)
m.model_dump(mode='json')        # → dict with JSON-compatible types (tuple→list)
m.model_dump_json()              # → JSON string
m.model_dump_json(indent=2)      # → pretty-printed JSON string
m.model_dump(by_alias=True)      # use serialization aliases
```

`TypeAdapter` equivalents return `bytes`, not `str`:
```python
ta.dump_python(obj)              # → dict
ta.dump_json(obj)                # → bytes
```
(source: pydantic-docs-serialization.md)

## Field Inclusion and Exclusion

### At the field level

```python
from pydantic import BaseModel, Field

class Transaction(BaseModel):
    id: int
    private_id: int = Field(exclude=True)
    value: int = Field(ge=0, exclude_if=lambda v: v == 0)  # v2.12+
```

### At serialization time

```python
# Exclude specific fields
m.model_dump(exclude={'user', 'value'})

# Nested exclusion
m.model_dump(exclude={'user': {'username', 'password'}})

# Include specific fields
m.model_dump(include={'id': True, 'user': {'id'}})

# Apply to all items in a list/dict
m.model_dump(exclude={'hobbies': {'__all__': {'info'}}})
```

### Value-based exclusion

```python
m.model_dump(exclude_defaults=True)   # skip fields equal to default
m.model_dump(exclude_none=True)       # skip None fields
m.model_dump(exclude_unset=True)      # skip fields not explicitly set
```

`model_fields_set` tracks which fields were explicitly provided:

```python
user = User(name='John')
user.model_fields_set          # {'name'}
user.model_dump(exclude_unset=True)  # {'name': 'John'} — age omitted
```
(source: pydantic-docs-serialization.md)

## Custom Field Serializers

Only ONE serializer per field. Cannot combine plain and wrap.

### Plain Serializer

Bypasses Pydantic's built-in serialization:

```python
from typing import Annotated
from pydantic import BaseModel, PlainSerializer

DoubleInt = Annotated[int, PlainSerializer(lambda v: v * 2)]

class Model(BaseModel):
    number: DoubleInt
```

Decorator form:

```python
@field_serializer('number', mode='plain')
def ser_number(self, value: Any) -> Any:
    return value * 2
```

### Wrap Serializer

Runs code before/after Pydantic serialization via a handler:

```python
from pydantic import WrapSerializer, SerializerFunctionWrapHandler

def add_one(value: Any, handler: SerializerFunctionWrapHandler) -> int:
    return handler(value) + 1

class Model(BaseModel):
    number: Annotated[int, WrapSerializer(add_one)]
```

### Decorator Pattern

- Apply to multiple fields: `@field_serializer('f1', 'f2')`
- Apply to all fields: `@field_serializer('*')`
- Instance methods (not classmethods, unlike validators)
(source: pydantic-docs-serialization.md)

## Custom Model Serializers

### Plain Model Serializer

```python
from pydantic import model_serializer

@model_serializer(mode='plain')
def serialize_model(self) -> str:
    return f'{self.username} - {self.password}'
```

### Wrap Model Serializer

```python
@model_serializer(mode='wrap')
def serialize_model(self, handler: SerializerFunctionWrapHandler) -> dict:
    result = handler(self)
    result['fields'] = list(result)
    return result
```
(source: pydantic-docs-serialization.md)

## Serialization Info

Serializer callables can take an `info` argument:
- `info.mode` — `'python'` or `'json'`
- `info.context` — user-defined context
- `info.exclude_unset`, `info.serialize_as_any` — current parameters
- `info.field_name` — for field serializers

### Serialization Context

```python
model.model_dump(context={'format': 'api_v2'})
```
(source: pydantic-docs-serialization.md)

## Subclass Serialization

Default: only base class fields are included when a subclass instance fills a base-typed field.

### Polymorphic Serialization (v2.13+)

Serializes all subclass fields:

```python
from pydantic import BaseModel, ConfigDict

class User(BaseModel):
    model_config = ConfigDict(polymorphic_serialization=True)
    name: str

class UserLogin(User):
    password: str
```

Or at runtime: `m.model_dump(polymorphic_serialization=True)`.

### SerializeAsAny

Per-field duck-typing serialization:

```python
from pydantic import SerializeAsAny

class OuterModel(BaseModel):
    user: SerializeAsAny[User]  # always serializes all fields
```

Or at runtime: `m.model_dump(serialize_as_any=True)`.
(source: pydantic-docs-serialization.md)

## Iterating Over Models

```python
for name, value in model:
    print(f'{name}: {value}')
# Sub-models are NOT converted to dicts when iterating
```
(source: pydantic-docs-serialization.md)

## See Also

- [[pydantic]] — hub page
- [[pydantic-fields]] — Field(exclude=True), computed_field
- [[pydantic-validators]] — custom validators (analogous structure)
