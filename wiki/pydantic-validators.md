# pydantic-validators

Custom validation at the field and model level for enforcing complex constraints.

## Field Validators

Four types, usable via the Annotated pattern or `@field_validator` decorator.

### After Validators

Run after Pydantic's internal validation. Type safe — value is already the correct type.

```python
from typing import Annotated
from pydantic import AfterValidator, BaseModel

def is_even(value: int) -> int:
    if value % 2 == 1:
        raise ValueError(f'{value} is not even')
    return value

class Model(BaseModel):
    number: Annotated[int, AfterValidator(is_even)]
```

Decorator form:

```python
@field_validator('number', mode='after')  # 'after' is default
@classmethod
def is_even(cls, value: int) -> int: ...
```

### Before Validators

Run before Pydantic's parsing. Value can be any type.

```python
from typing import Annotated, Any
from pydantic import BeforeValidator

def ensure_list(value: Any) -> Any:
    if not isinstance(value, list):
        return [value]
    return value

class Model(BaseModel):
    numbers: Annotated[list[int], BeforeValidator(ensure_list)]

Model(numbers=2)  # numbers=[2]
```

Avoid mutating the value directly if raising a validation error later (the mutated value may pass to other union validators).
(source: pydantic-docs-validators.md)

### Plain Validators

Terminate validation immediately. No further validators or Pydantic internal validation runs.

```python
from typing import Annotated, Any
from pydantic import PlainValidator

def val_number(value: Any) -> Any:
    if isinstance(value, int):
        return value * 2
    return value

class Model(BaseModel):
    number: Annotated[int, PlainValidator(val_number)]
```
(source: pydantic-docs-validators.md)

### Wrap Validators

Most flexible. Mandatory `handler` parameter to delegate to Pydantic:

```python
from pydantic import WrapValidator, ValidatorFunctionWrapHandler

def truncate(value: Any, handler: ValidatorFunctionWrapHandler) -> str:
    try:
        return handler(value)
    except ValidationError as err:
        if err.errors()[0]['type'] == 'string_too_long':
            return handler(value[:5])
        raise

class Model(BaseModel):
    my_string: Annotated[str, Field(max_length=5), WrapValidator(truncate)]
```
(source: pydantic-docs-validators.md)

## Which Pattern to Use

**Annotated**: Reusable types. Clear which validators apply.

```python
EvenInt = Annotated[int, AfterValidator(is_even)]
# Reuse across models:
class Model1(BaseModel):
    x: EvenInt
class Model2(BaseModel):
    items: list[EvenInt]
```

**Decorator**: Apply one validator to multiple fields.

```python
@field_validator('f1', 'f2', mode='before')
@classmethod
def capitalize(cls, value: str) -> str:
    return value.capitalize()
```

- `'*'` applies to all fields (including subclass fields)
- `check_fields=False` skips field existence check (for base classes)
(source: pydantic-docs-validators.md)

## Model Validators

Three types via `@model_validator`:

### After

Runs after full model validation. Instance method, must return `self`:

```python
from typing_extensions import Self
from pydantic import model_validator

@model_validator(mode='after')
def check_passwords_match(self) -> Self:
    if self.password != self.password_repeat:
        raise ValueError('Passwords do not match')
    return self
```

### Before

Runs before model instantiation. Classmethod, receives raw data:

```python
@model_validator(mode='before')
@classmethod
def check_card_number_not_present(cls, data: Any) -> Any:
    if isinstance(data, dict) and 'card_number' in data:
        raise ValueError("'card_number' should not be included")
    return data
```

### Wrap

Most flexible. Takes a handler to delegate to Pydantic.
(source: pydantic-docs-validators.md)

## Raising Errors

- `ValueError` — most common
- `AssertionError` — via `assert` (skipped with `-O` flag)
- `PydanticCustomError` — custom error type, message template, context:

```python
from pydantic_core import PydanticCustomError

raise PydanticCustomError(
    'my_error_type',
    '{value} is invalid because {reason}',
    {'value': v, 'reason': 'it is too large'},
)
```
(source: pydantic-docs-validators.md)

## Validation Info

Validators can take `ValidationInfo` as an extra argument:

- `info.data` — already validated fields dict (field validators only)
- `info.context` — user-passed context
- `info.mode` — `'python'`, `'json'`, or `'strings'`
- `info.field_name` — current field name

```python
from pydantic import ValidationInfo, field_validator

@field_validator('password_repeat', mode='after')
@classmethod
def check_match(cls, value: str, info: ValidationInfo) -> str:
    if value != info.data['password']:
        raise ValueError('Passwords do not match')
    return value
```

Validated data depends on field ordering — can only access fields defined before the current one.
(source: pydantic-docs-validators.md)

## Validation Context

Pass context to validation methods:

```python
Model.model_validate(data, context={'stopwords': ['the', 'a']})
```

Access via `info.context` in validators.
(source: pydantic-docs-validators.md)

## Validator Ordering

With the Annotated pattern:
- Before and wrap validators: right to left
- After validators: left to right

```python
name: Annotated[
    str,
    AfterValidator(runs_3rd),
    AfterValidator(runs_4th),
    BeforeValidator(runs_2nd),
    WrapValidator(runs_1st),
]
```

Decorator validators are appended after existing Annotated metadata.
(source: pydantic-docs-validators.md)

## Special Types

- `InstanceOf[T]` — validate value is an instance of T
- `SkipValidation[T]` — skip validation entirely
- `ValidateAs(source, converter)` — validate as one type, convert to another
- `PydanticUseDefault` — raise to use field's default value
(source: pydantic-docs-validators.md)

## See Also

- [[pydantic]] — hub page
- [[pydantic-fields]] — Field() constraints that complement validators
- [[pydantic-serialization]] — custom serializers (analogous structure)
