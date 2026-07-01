# duckdb-expression-api

Programmatic expression building for dynamically constructing queries without SQL strings.

## Expression Types

### ColumnExpression

References a column by name:

```python
import duckdb

col = duckdb.ColumnExpression('price')
rel.select(col).show()

# with operations
rel.select(
    duckdb.ColumnExpression('price') * 100,
    duckdb.ColumnExpression('name').isnull()
).show()
```
(source: duckdb-python-expression.md)

### StarExpression

Selects all columns, with optional exclusions:

```python
star = duckdb.StarExpression(exclude=['internal_id'])
rel.select(star).show()
```
(source: duckdb-python-expression.md)

### ConstantExpression

A literal value:

```python
const = duckdb.ConstantExpression(42)
rel.select(const).show()
```
(source: duckdb-python-expression.md)

### CaseExpression

CASE WHEN ... THEN ... ELSE ... END:

```python
from duckdb import CaseExpression, ColumnExpression, ConstantExpression

case = (CaseExpression(
    condition=ColumnExpression('status') == 'active',
    value=ConstantExpression('yes'))
    .otherwise(ConstantExpression('no')))
```

Add more WHEN blocks with `.when(condition=..., value=...)`.
(source: duckdb-python-expression.md)

### FunctionExpression

Call any DuckDB function:

```python
from duckdb import FunctionExpression, ColumnExpression, ConstantExpression

upper = FunctionExpression('upper', ColumnExpression('name'))
```
(source: duckdb-python-expression.md)

### SQLExpression

Embed arbitrary SQL:

```python
from duckdb import SQLExpression

rel.filter(SQLExpression("price > 0.5")).select(
    SQLExpression("ticker").alias("symbol"),
    SQLExpression("price * 100").alias("cents")
).show()
```
(source: duckdb-python-expression.md)

## Common Operations

| Operation | Description |
|:--|:--|
| `.alias(name)` | Apply an alias |
| `.cast(type)` | Cast to a DuckDB type |
| `.isin(*exprs)` | IN expression |
| `.isnotin(*exprs)` | NOT IN expression |
| `.isnull()` | Check if NULL |
| `.isnotnull()` | Check if not NULL |

## Ordering

For use with `rel.order()`:

| Operation | Description |
|:--|:--|
| `.asc()` | Ascending |
| `.desc()` | Descending |
| `.nulls_first()` | NULLs before non-nulls |
| `.nulls_last()` | NULLs after non-nulls |

```python
rel.order(duckdb.ColumnExpression('price').desc().nulls_last())
```
(source: duckdb-python-expression.md)

## See Also

- [[duckdb]] — hub page
- [[duckdb-relational-api]] — transformations that use expressions
