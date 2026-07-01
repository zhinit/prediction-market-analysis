# polars

Fast DataFrame library written in Rust with Python bindings. Handles data transformation, aggregation, and I/O. Alternative to pandas with better performance and a more expressive API.

## Installation

```
uv add polars
```

## Why polars over pandas

- Multi-threaded by default — uses all CPU cores
- Lazy API with automatic query optimization (predicate/projection pushdown)
- Handles datasets larger than RAM
- Expression-based API — more composable than pandas method chaining
- Native Parquet support with layout that mirrors in-memory representation
(source: polars-getting-started.md, polars-lazy-api.md)

## Core Concepts

### Creating DataFrames

```python
import polars as pl

df = pl.DataFrame({
    "ticker": ["KXBTC-26JUN", "KXBTC-27JUN"],
    "yes_price": [0.65, 0.72],
    "volume": [1500, 2300],
})
```
(source: polars-getting-started.md)

### Expressions and Contexts

Four main contexts for data transformation:

```python
# select — choose/transform columns
df.select(pl.col("ticker"), pl.col("yes_price"))

# with_columns — add columns, keep existing
df.with_columns(
    no_price=1 - pl.col("yes_price"),
    spread=pl.col("yes_price") - pl.col("no_price"),
)

# filter — subset rows
df.filter(pl.col("volume") > 1000)

# group_by — aggregate
df.group_by("category").agg(
    pl.col("volume").sum(),
    pl.col("yes_price").mean(),
)
```
(source: polars-getting-started.md)

## Lazy API

The Polars docs state the lazy API should be preferred unless you need intermediate results or are doing exploratory work. It defers execution and optimizes the query plan:

```python
q = (
    pl.scan_parquet("data/markets.parquet")
    .filter(pl.col("status") == "open")
    .group_by("category")
    .agg(pl.col("volume").sum())
)
df = q.collect()  # executes the optimized plan
```

Optimizations applied automatically:
- **Predicate pushdown**: filters applied during file read
- **Projection pushdown**: only needed columns loaded
(source: polars-lazy-api.md)

## I/O

### CSV
```python
df = pl.read_csv("data.csv")           # eager
lf = pl.scan_csv("data.csv")           # lazy
df.write_csv("output.csv")
```
(source: polars-io-csv.md)

### Parquet
```python
df = pl.read_parquet("data.parquet")    # eager
lf = pl.scan_parquet("data.parquet")    # lazy
df.write_parquet("output.parquet")
```

Parquet I/O is extremely fast — columnar layout mirrors Polars' in-memory layout.
(source: polars-io-parquet.md)

### Database
```python
# Read via ConnectorX (fast, Rust-native)
df = pl.read_database_uri(query="SELECT * FROM markets", uri=uri)

# Read via SQLAlchemy
df = pl.read_database(query="SELECT * FROM markets", connection=conn)

# Write
df.write_database(table_name="markets", connection=uri)
```

`read_database_uri` with ConnectorX is faster than `read_database` with SQLAlchemy.
(source: polars-io-database.md)

## See Also

- [[duckdb]] — SQL engine that queries Polars DataFrames directly
- [[data-pipeline-stack]] — how polars fits in the pipeline
