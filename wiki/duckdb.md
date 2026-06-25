# duckdb

In-process analytical SQL database. No server, no setup — runs inside the Python process. Designed for OLAP queries on columnar data.

## Installation

```
uv add duckdb
```

## Why DuckDB for this project

- In-process: no database server to manage. A single file in `db/` holds all data.
- Queries Polars DataFrames directly via SQL — zero-copy when possible.
- Native Parquet/CSV read and write.
- Vectorized, multi-core query execution.
- Persistent storage: data survives between script runs.
(source: duckdb-python-api.md)

## Basic Usage

```python
import duckdb

# In-memory (ephemeral)
duckdb.sql("SELECT 42").show()

# Persistent (data survives between runs)
con = duckdb.connect("db/pma.db")
con.sql("CREATE TABLE IF NOT EXISTS markets (ticker TEXT, price REAL)")
con.sql("INSERT INTO markets VALUES ('KXBTC', 0.65)")
con.table("markets").show()
con.close()
```
(source: duckdb-python-api.md)

## Context Manager

```python
with duckdb.connect("db/pma.db") as con:
    con.sql("SELECT * FROM markets WHERE price > 0.5").show()
```
(source: duckdb-python-api.md)

## DataFrame Integration

DuckDB queries Python DataFrames directly by variable name:

```python
import polars as pl

markets_df = pl.DataFrame({"ticker": ["A", "B"], "price": [0.6, 0.8]})
duckdb.sql("SELECT * FROM markets_df WHERE price > 0.7").show()
```

Works with Polars, Pandas, and PyArrow tables.
(source: duckdb-python-api.md)

## Result Conversion

```python
result = con.sql("SELECT * FROM markets")
result.fetchall()       # list of tuples
result.pl()             # → Polars DataFrame
result.df()             # → Pandas DataFrame
result.arrow()          # → PyArrow Table
```
(source: duckdb-python-api.md)

## Data Import/Export

```python
# Read files directly in SQL
con.sql("SELECT * FROM 'data/markets.parquet'")
con.sql("SELECT * FROM 'data/trades.csv'")

# Write query results to files
con.sql("SELECT * FROM markets").write_parquet("out.parquet")
con.sql("SELECT * FROM markets").write_csv("out.csv")

# Programmatic read
con.read_parquet("data/markets.parquet")
con.read_csv("data/trades.csv")
```
(source: duckdb-python-api.md)

## Thread Safety

The global `duckdb.sql()` connection is not thread-safe. For concurrent use, create separate connections:

```python
con = duckdb.connect()  # each thread gets its own
```
(source: duckdb-python-api.md)

## Schema Documentation

DuckDB supports `COMMENT ON` for embedding descriptions directly in the database. See [[self-documenting-database]] for usage patterns and [[database-naming-conventions]] for table/column naming rules.

```python
con.sql("COMMENT ON TABLE markets_dim IS 'Prediction market metadata'")
con.sql("SELECT table_name, comment FROM duckdb_tables()").show()
```
(source: duckdb-comment-on.md)

## Metadata Introspection

```python
con.sql("SELECT * FROM duckdb_tables()").show()    # all tables
con.sql("SELECT * FROM duckdb_columns()").show()   # all columns
con.sql("SELECT * FROM duckdb_constraints()").show() # keys, constraints
```
(source: duckdb-metadata-functions.md)

## See Also

- [[polars]] — DataFrame library that DuckDB queries directly
- [[data-pipeline-stack]] — how DuckDB fits in the pipeline
- [[analytical-database-design]] — overall database design approach
- [[dimensional-modeling]] — star schema design for analytical workloads
- [[self-documenting-database]] — COMMENT ON and metadata introspection
