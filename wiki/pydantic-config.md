# pydantic-config

`ConfigDict` controls Pydantic model behavior: validation strictness, extra field handling, serialization defaults, and more.

## Setting Configuration

### model_config attribute (most common)

```python
from pydantic import BaseModel, ConfigDict

class Model(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    name: str
```

### Class arguments

```python
class Model(BaseModel, frozen=True):
    name: str
```

Type checkers recognize class arguments (unlike `model_config`).

### On dataclasses

```python
from pydantic.dataclasses import dataclass

@dataclass(config=ConfigDict(str_max_length=10))
class User:
    name: str
```

### On TypeAdapter

```python
from pydantic import TypeAdapter, ConfigDict

ta = TypeAdapter(list[str], config=ConfigDict(coerce_numbers_to_str=True))
```
(source: pydantic-docs-config.md)

## Key Options Reference

### Validation

| Option | Default | Effect |
|--------|---------|--------|
| `strict` | `False` | Disable type coercion |
| `extra` | `'ignore'` | `'ignore'`, `'forbid'`, `'allow'` for extra fields |
| `validate_default` | `False` | Validate default values |
| `validate_assignment` | `False` | Validate on attribute assignment |
| `validate_by_name` | `False` | Allow field names alongside aliases |
| `validate_by_alias` | `True` | Allow aliases during validation |
| `from_attributes` | `False` | ORM mode — read from object attributes |
| `coerce_numbers_to_str` | `False` | Coerce numbers to strings |
| `use_enum_values` | `False` | Use enum values instead of instances |
| `arbitrary_types_allowed` | `False` | Allow types without Pydantic validation support |
| `revalidate_instances` | `'never'` | Revalidate existing model instances |

### String

| Option | Default | Effect |
|--------|---------|--------|
| `str_to_lower` | `False` | Lowercase all strings |
| `str_to_upper` | `False` | Uppercase all strings |
| `str_strip_whitespace` | `False` | Strip whitespace |
| `str_max_length` | `None` | Max string length |
| `str_min_length` | `None` | Min string length |

### Serialization

| Option | Default | Effect |
|--------|---------|--------|
| `serialize_by_alias` | `False` | Use aliases by default |
| `polymorphic_serialization` | `False` | Serialize subclass fields (v2.13+) |

### Model

| Option | Default | Effect |
|--------|---------|--------|
| `frozen` | `False` | Make instances immutable |
| `title` | `None` | Model title in JSON Schema |
| `json_schema_extra` | `None` | Extra JSON Schema data |

(source: pydantic-docs-config.md)

## Inheritance and Merging

Configuration inherits from parent classes and merges:

```python
class Parent(BaseModel):
    model_config = ConfigDict(extra='allow', str_to_lower=False)

class Child(Parent):
    model_config = ConfigDict(str_to_lower=True)

# Child.model_config == {'extra': 'allow', 'str_to_lower': True}
```

Warning: does NOT follow MRO for multiple inheritance.
(source: pydantic-docs-config.md)

## Propagation Rules

- **Pydantic models/dataclasses**: config does NOT propagate to nested models. Each model has its own configuration boundary.
- **Stdlib dataclasses/TypedDict**: config DOES propagate, unless the type has its own config.

```python
class Inner(BaseModel):
    name: str

class Outer(BaseModel):
    model_config = ConfigDict(str_to_lower=True)
    inner: Inner

Outer(inner={'name': 'JOHN'})
# inner.name == 'JOHN' — str_to_lower did NOT propagate
```
(source: pydantic-docs-config.md)

## Strict Mode Details

Three ways to enable:
1. `ConfigDict(strict=True)` — model-wide
2. `Field(strict=True)` — per-field
3. `model_validate(data, strict=True)` — per-call

JSON validation is looser even in strict mode (strings for dates, lists for tuples) because JSON lacks those types.
(source: pydantic-docs-strict-mode.md)

## For Other Types

Stdlib dataclasses and TypedDict:

```python
from dataclasses import dataclass
from pydantic import ConfigDict

@dataclass
class User:
    __pydantic_config__ = ConfigDict(strict=True)
    id: int
```

Or `@with_config` decorator (avoids TypedDict type checker issues):

```python
from pydantic import with_config

@with_config(ConfigDict(str_to_lower=True))
class Model(TypedDict):
    x: str
```
(source: pydantic-docs-config.md)

## See Also

- [[pydantic]] — hub page
- [[pydantic-fields]] — Field() options that complement config
