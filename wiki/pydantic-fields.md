# pydantic-fields

The `Field()` function and the `Annotated` pattern for customizing Pydantic model fields.

## Field() Function

Customizes fields with defaults, constraints, aliases, JSON Schema metadata:

```python
from pydantic import BaseModel, Field

class Model(BaseModel):
    name: str = Field(frozen=True)
    age: int = Field(default=20)
    score: float = Field(gt=0, le=100)
```

Even when `Field()` is assigned, the field is still required unless a `default` or `default_factory` is provided.
(source: pydantic-docs-fields.md)

## Annotated Pattern

Preferred approach. Attaches metadata via `Annotated` — clearer intent, reusable types:

```python
from typing import Annotated
from pydantic import BaseModel, Field

class Model(BaseModel):
    name: Annotated[str, Field(strict=True)]
    int_list: list[Annotated[int, Field(gt=0)]]
```

Benefits:
- No confusion about whether a field has a default
- Multiple metadata elements per field
- Types become reusable across models

Note: `default`, `default_factory`, and `alias` should use normal assignment (not Annotated) for type checker compatibility.
(source: pydantic-docs-fields.md)

## Default Values

```python
class User(BaseModel):
    name: str = 'John Doe'                              # literal default
    age: int = Field(default=20)                        # Field default
    id: str = Field(default_factory=lambda: uuid4().hex) # factory
```

Default factories can take validated data (v2.10+):

```python
class User(BaseModel):
    email: EmailStr
    username: str = Field(default_factory=lambda data: data['email'])
```

Only already-validated fields are available (based on field ordering).

Mutable defaults are deep-copied per instance — no shared-mutable-default bugs.

### Validate Default Values

Disabled by default. Enable with `validate_default=True` on the field or in `ConfigDict`.
(source: pydantic-docs-fields.md)

## Aliases

| Parameter | Validation | Serialization |
|-----------|-----------|---------------|
| `alias='x'` | x | x |
| `validation_alias='x'` | x | field name |
| `serialization_alias='x'` | field name | x |

```python
class User(BaseModel):
    name: str = Field(alias='username')

User(username='johndoe')                    # validation uses alias
user.model_dump(by_alias=True)              # {'username': 'johndoe'}
```

`validation_alias` overrides `alias` for validation. `serialization_alias` overrides `alias` for serialization.
(source: pydantic-docs-fields.md)

## Constraints

Numeric: `gt`, `ge`, `lt`, `le`, `multiple_of`
String: `min_length`, `max_length`, `pattern`
Decimal: `max_digits`, `decimal_places`

```python
from decimal import Decimal

class Model(BaseModel):
    positive: int = Field(gt=0)
    short: str = Field(max_length=3)
    price: Decimal = Field(max_digits=5, decimal_places=2)
```

Constraints on `int | None` automatically apply to the `int` part.
(source: pydantic-docs-fields.md)

## Strict Fields

`Field(strict=True)` — no type coercion for this field:

```python
class User(BaseModel):
    name: str = Field(strict=True)   # must be str
    age: int = Field(strict=False)   # str '42' coerced to 42 (default)
```
(source: pydantic-docs-strict-mode.md)

## Computed Fields

Include properties in serialization and JSON Schema:

```python
from pydantic import BaseModel, computed_field

class Box(BaseModel):
    width: float
    height: float

    @computed_field
    @property
    def area(self) -> float:
        return self.width * self.height

Box(width=3, height=4).model_dump()
# {'width': 3.0, 'height': 4.0, 'area': 12.0}
```

Can also use `@cached_property`. Can be deprecated. Conditional exclusion via `exclude_if` (v2.13+).
(source: pydantic-docs-fields.md)

## Excluding Fields

- `Field(exclude=True)` — permanently excluded from serialization
- `Field(exclude_if=lambda v: v == 0)` — conditionally excluded (v2.12+)

## Frozen Fields

`Field(frozen=True)` — prevent reassignment after creation.

## Deprecated Fields (v2.7+)

- `Field(deprecated=True)` — runtime deprecation warning on access
- `Field(deprecated='message')` — custom deprecation message

Sets `deprecated` keyword in JSON Schema.

## Discriminator

For unions, controls which model to validate against:

```python
pet: Cat | Dog = Field(discriminator='pet_type')
```

Or with a callable: `Field(discriminator=Discriminator(my_func))`.
(source: pydantic-docs-fields.md, pydantic-docs-unions.md)

## JSON Schema Customization

`title`, `description`, `examples`, `json_schema_extra` customize generated JSON Schema.

## Inspecting Fields

```python
Model.model_fields['name']  # FieldInfo instance
# .annotation, .alias, .metadata, .default, .is_required()
```

Only accessible from the class, not from instances (deprecated in v2.11, removed in v3).
(source: pydantic-docs-fields.md)

## See Also

- [[pydantic]] — hub page
- [[pydantic-validators]] — custom validation logic
- [[pydantic-serialization]] — serialization customization
