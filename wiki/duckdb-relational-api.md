# duckdb-relational-api

Lazy query builder centered around `DuckDBPyRelation` nodes. Relations are symbolic representations of SQL queries — nothing executes until an output method is called.

## Lazy Evaluation

```python
import duckdb

con = duckdb.connect()
rel = con.sql("FROM range(1_000_000_000)")  # no data loaded yet
rel.show()  # first 10K rows fetched on demand
```
(source: duckdb-python-relational-api.md)

## Creating Relations

| Method | Description |
|:--|:--|
| `sql(query)` | From a SQL SELECT statement |
| `table(name)` | From an existing table |
| `view(name)` | From an existing view |
| `from_df(df)` | From a Pandas DataFrame |
| `from_arrow(obj)` | From an Arrow table/batch |
| `read_csv(path)` | From CSV file(s) |
| `read_parquet(path)` | From Parquet file(s) |
| `read_json(path)` | From JSON file(s) |
| `values(values)` | From literal values |
| `table_function(name, params)` | From a table function |

```python
rel = con.sql("SELECT * FROM markets WHERE price > 0.5")
rel = con.table("markets")
rel = con.read_parquet("data/*.parquet")
rel = con.values([["A", 1], ["B", 2]])
```
(source: duckdb-python-relational-api.md)

## Relation Metadata

| Method | Returns |
|:--|:--|
| `rel.columns` | Column names |
| `rel.dtypes` | Column types |
| `rel.types` | Column types (alias) |
| `rel.shape` | (rows, cols) tuple |
| `rel.alias` | Relation alias |
| `rel.description` | Column descriptions |
| `rel.explain()` | Query plan |
| `rel.sql_query()` | Generated SQL |
| `rel.describe()` | Statistical summary |

(source: duckdb-python-relational-api.md)

## Transformations

All transformations return new relations (lazy — not executed until output is called).

| Method | SQL Equivalent |
|:--|:--|
| `rel.filter(condition)` | WHERE |
| `rel.select(*cols)` / `rel.project(*cols)` | SELECT |
| `rel.order(*cols)` / `rel.sort(*cols)` | ORDER BY |
| `rel.limit(n, offset)` | LIMIT / OFFSET |
| `rel.aggregate(aggr_expr, group_expr)` | GROUP BY + aggregates |
| `rel.distinct()` | SELECT DISTINCT |
| `rel.join(other, condition, how)` | JOIN |
| `rel.cross(other)` | CROSS JOIN |
| `rel.union(other)` | UNION ALL |
| `rel.except_(other)` | EXCEPT |
| `rel.intersect(other)` | INTERSECT |
| `rel.insert(values)` | INSERT VALUES |
| `rel.insert_into(table)` | INSERT INTO |
| `rel.update(set, condition)` | UPDATE |

```python
rel = con.table("markets")
result = (rel
    .filter("price > 0.5")
    .select("ticker", "price")
    .order("price DESC")
    .limit(10))
result.show()
```
(source: duckdb-python-relational-api.md)

## Aggregate Functions

Available directly on relations:

`any_value`, `arg_max`, `arg_min`, `avg`, `bit_and`, `bit_or`, `bit_xor`, `bitstring_agg`, `bool_and`, `bool_or`, `count`, `cume_dist`, `dense_rank`, `favg`, `first`, `first_value`, `fsum`, `geomean`, `histogram`, `lag`, `last`, `last_value`, `lead`, `list`, `max`, `mean`, `median`, `min`, `mode`, `n_tile`, `nth_value`, `percent_rank`, `product`, `quantile`, `quantile_cont`, `quantile_disc`, `rank`, `rank_dense`, `row_number`, `std`, `stddev`, `stddev_pop`, `stddev_samp`, `string_agg`, `sum`, `unique`, `value_counts`, `var`, `var_samp`, `variance`

```python
rel = con.table("markets")
rel.avg("price").show()
rel.value_counts("ticker").show()
```
(source: duckdb-python-relational-api.md)

## Type Selection

```python
rel.select_dtypes(["INTEGER", "DOUBLE"])  # by type name
rel.select_types([duckdb.INTEGER, duckdb.DOUBLE])  # by type object
```
(source: duckdb-python-relational-api.md)

## Output Methods

These trigger execution and materialize results:

| Method | Returns |
|:--|:--|
| `rel.show()` | Print to screen |
| `rel.fetchall()` | List of tuples |
| `rel.fetchone()` | Single tuple |
| `rel.fetchmany(n)` | List of n tuples |
| `rel.df()` / `rel.fetchdf()` / `rel.to_df()` | Pandas DataFrame |
| `rel.pl()` | Polars DataFrame |
| `rel.arrow()` / `rel.to_arrow_table()` | Arrow Table |
| `rel.to_arrow_reader(chunk_size)` | Arrow RecordBatchReader |
| `rel.fetchnumpy()` | Dict of NumPy arrays |
| `rel.fetch_df_chunk(vector_multiple)` | Chunked Pandas DataFrame |
| `rel.tf()` | TensorFlow dataset |
| `rel.torch()` | PyTorch tensors |

### Writing to Storage

| Method | Description |
|:--|:--|
| `rel.to_table(name)` | Create/insert into table |
| `rel.create(name)` | Create new table |
| `rel.create_view(name)` | Create view |
| `rel.to_view(name)` | Create view (alias) |
| `rel.to_csv(path)` / `rel.write_csv(path)` | Write CSV |
| `rel.to_parquet(path)` / `rel.write_parquet(path)` | Write Parquet |

```python
rel = con.sql("SELECT * FROM markets")
rel.to_parquet("output/markets.parquet")
rel.to_table("markets_archive")
```
(source: duckdb-python-relational-api.md)

## See Also

- [[duckdb]] — hub page
- [[duckdb-db-api]] — PEP 249 alternative
- [[duckdb-expression-api]] — programmatic expression building for use with transformations
