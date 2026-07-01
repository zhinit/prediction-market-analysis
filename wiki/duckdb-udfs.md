# duckdb-udfs

Register Python functions as DuckDB user-defined functions (UDFs) for use in SQL queries.

## Creating a UDF

```python
import duckdb
from duckdb.sqltypes import VARCHAR

def generate_random_name():
    fake = Faker()
    return fake.name()

duckdb.create_function("random_name", generate_random_name, [], VARCHAR)
duckdb.sql("SELECT random_name()").fetchall()
```
(source: duckdb-python-udfs.md)

## create_function Parameters

| Parameter | Description |
|:--|:--|
| `name` | Function name in the catalog |
| `function` | The Python callable |
| `parameters` | List of input column types |
| `return_type` | Return type |
| `type` | `'native'` (default, row-at-a-time) or `'arrow'` (batch, much faster) |
| `null_handling` | `'default'` (NULL in → NULL out) or `'special'` (handle NULLs yourself) |
| `exception_handling` | `'default'` (re-throw) or `'return_null'` |
| `side_effects` | `True` if function uses randomness/state |

Remove with `con.remove_function(name)`.
(source: duckdb-python-udfs.md)

## Type Annotations

With annotations, parameter types and return type are inferred automatically:

```python
def my_function(x: int) -> str:
    return str(x)

duckdb.create_function("my_func", my_function)
```
(source: duckdb-python-udfs.md)

## Arrow UDFs (Batch Processing)

Much more efficient — operates on batches of up to 2048 tuples:

```python
import pyarrow as pa
from pyarrow import compute as pc

def mirror(strings: pa.Array, sep: pa.Array) -> pa.Array:
    return pc.binary_join_element_wise(strings, pc.ascii_reverse(strings), sep)

duckdb.create_function("mirror", mirror, [VARCHAR, VARCHAR],
    return_type=VARCHAR, type="arrow")
```
(source: duckdb-python-udfs.md)

## NULL Handling

Default behavior: NULL input → NULL output. Override with `null_handling="special"`:

```python
from duckdb.sqltypes import BIGINT

def handle_null(x):
    return 5

duckdb.create_function("f", handle_null, [BIGINT], BIGINT, null_handling="special")
# SELECT f(NULL) → 5
```

Always use `null_handling="special"` when your function can return NULL.
(source: duckdb-python-udfs.md)

## Side Effects

Default: DuckDB assumes pure functions (same input → same output) and may optimize accordingly. Set `side_effects=True` for stateful or random functions:

```python
def counter() -> int:
    old = counter.n
    counter.n += 1
    return old
counter.n = 0

con.create_function("counter", counter, side_effects=True)
```
(source: duckdb-python-udfs.md)

## Partial Functions

`functools.partial` is supported:

```python
import functools

con.create_function("my_logger",
    functools.partial(logger_fn, get_datetime, "prefix"))
```
(source: duckdb-python-udfs.md)

## See Also

- [[duckdb]] — hub page
- [[duckdb-result-conversion]] — type mapping between Python and DuckDB
