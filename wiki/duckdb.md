# duckdb

In-process analytical SQL database. No server, no setup — runs inside the Python process. Designed for OLAP queries on columnar data.

## Installation

```
uv add duckdb
```

Requires Python 3.9 or newer.
(source: duckdb-python-overview.md)

## Strengths

- Directly queries Pandas DataFrames, Polars DataFrames, and Arrow tables via SQL.
- Reads and writes CSV and Parquet files natively.
- Persistent storage: a connection to a database file persists all data written to it, and the data can be reloaded by reconnecting to the same file.
(source: duckdb-python-overview.md)

Project-specific stack choices are recorded in `docs/project-conventions.md`.

## Basic Usage

```python
import duckdb

# In-memory (ephemeral)
duckdb.sql("SELECT 42").show()

# Persistent (data survives between runs)
con = duckdb.connect("analytics.db")
con.sql("CREATE TABLE IF NOT EXISTS markets (ticker TEXT, price REAL)")
con.sql("INSERT INTO markets VALUES ('KXBTC', 0.65)")
con.table("markets").show()
con.close()
```

The result of `duckdb.sql()` is a **Relation** — a symbolic representation of the query. Nothing executes until you call `.show()`, `.fetchall()`, `.df()`, `.pl()`, etc.
(source: duckdb-python-overview.md)

## Context Manager

```python
with duckdb.connect("analytics.db") as con:
    con.sql("SELECT * FROM markets WHERE price > 0.5").show()
```
(source: duckdb-python-overview.md)

## DataFrame Integration

DuckDB queries Python DataFrames directly by variable name:

```python
import polars as pl

markets_df = pl.DataFrame({"ticker": ["A", "B"], "price": [0.6, 0.8]})
duckdb.sql("SELECT * FROM markets_df WHERE price > 0.7").show()
```

Works with Polars, Pandas, and PyArrow tables.
(source: duckdb-python-overview.md)

## Result Conversion

```python
result = con.sql("SELECT * FROM markets")
result.fetchall()       # list of tuples
result.pl()             # → Polars DataFrame
result.df()             # → Pandas DataFrame
result.arrow()          # → PyArrow Table
result.fetchnumpy()     # → dict of NumPy arrays
```
(source: duckdb-python-conversion.md)

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
(source: duckdb-python-data-ingestion.md)

## Thread Safety

The global `duckdb.sql()` connection is not thread-safe. For concurrent use, create separate connections:

```python
con = duckdb.connect()  # each thread gets its own
```

`cursor()` creates another handle on the same connection, not a new connection — cursors from one connection serialize queries.
(source: duckdb-python-overview.md)

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

## Sub-pages

- [[duckdb-python-connections]] — Connection types, configuration, named in-memory, read-only, extensions
- [[duckdb-db-api]] — PEP 249 compliant API: execute(), fetchone/fetchall, prepared statements, named parameters
- [[duckdb-relational-api]] — Lazy query builder: relation creation, transformations, aggregations, output methods
- [[duckdb-data-ingestion]] — Reading CSV, Parquet, JSON; querying DataFrames; registering virtual tables
- [[duckdb-result-conversion]] — Python↔DuckDB type mapping; output to Pandas, Polars, Arrow, NumPy
- [[duckdb-udfs]] — User-defined functions: native and Arrow, type annotations, NULL/exception handling
- [[duckdb-expression-api]] — Programmatic expression building: Column, Star, Constant, Case, Function, SQL expressions
- [[duckdb-friendly-sql]] — DuckDB SQL extensions: FROM-first, GROUP BY ALL, EXCLUDE, COLUMNS(), ASOF joins

## See Also

- [[polars]] — DataFrame library that DuckDB queries directly
- [[data-pipeline-stack]] — how DuckDB fits in the pipeline
- [[analytical-database-design]] — overall database design approach
- [[dimensional-modeling]] — star schema design for analytical workloads
- [[self-documenting-database]] — COMMENT ON and metadata introspection
