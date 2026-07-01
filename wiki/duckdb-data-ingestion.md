# duckdb-data-ingestion

Reading data into DuckDB from files and Python objects.

## CSV

```python
import duckdb

duckdb.read_csv("example.csv")                         # auto-detect settings
duckdb.read_csv("folder/*.csv")                        # glob multiple files
duckdb.read_csv("example.csv", header=False, sep=",")  # explicit options
duckdb.read_csv("example.csv", dtype=["int", "varchar"])  # override column types

duckdb.sql("SELECT * FROM 'example.csv'")              # direct query
duckdb.sql("SELECT * FROM read_csv('example.csv')")    # explicit function
```

Key `read_csv` parameters: `header`, `sep`/`delimiter`, `dtype`, `na_values`, `skiprows`, `quotechar`, `encoding`, `parallel`, `date_format`, `timestamp_format`, `sample_size`, `all_varchar`, `normalize_names`, `names`, `columns`.
(source: duckdb-python-data-ingestion.md)

## Parquet

```python
duckdb.read_parquet("example.parquet")
duckdb.read_parquet("folder/*.parquet")                           # glob
duckdb.read_parquet("https://some.url/some_file.parquet")         # remote
duckdb.read_parquet(["file1.parquet", "file2.parquet"])            # list

duckdb.sql("SELECT * FROM 'example.parquet'")
```
(source: duckdb-python-data-ingestion.md)

## JSON

Auto-detects newline-delimited vs regular JSON and infers schema.

```python
duckdb.read_json("example.json")
duckdb.read_json("folder/*.json")
duckdb.sql("SELECT * FROM 'example.json'")
```
(source: duckdb-python-data-ingestion.md)

## Querying Python Objects

DuckDB queries Python variables directly by name via replacement scans. Supported types:

- Pandas DataFrame
- Polars DataFrame / LazyFrame
- NumPy arrays
- PyArrow tables, datasets, RecordBatchReaders, scanners
- DuckDB relations

```python
import polars as pl

markets = pl.DataFrame({"ticker": ["A", "B"], "price": [0.6, 0.8]})
duckdb.sql("SELECT * FROM markets WHERE price > 0.7").show()
```

Only variables visible at the call site of `sql()` / `execute()` can be used. To disable: `SET python_enable_replacements = false;`
(source: duckdb-python-data-ingestion.md)

## Registering Virtual Tables

For DataFrames stored in dicts, class attributes, etc.:

```python
my_dict = {"df": pd.DataFrame({"a": [1, 2, 3]})}
duckdb.register("my_view", my_dict["df"])
duckdb.sql("SELECT * FROM my_view").show()
```

Name resolution order:
1. Explicitly registered via `register()`
2. Native DuckDB tables and views
3. Replacement scans (variable name lookup)
(source: duckdb-python-data-ingestion.md)

## Creating Persistent Tables from DataFrames

```python
con.execute("CREATE TABLE my_table AS SELECT * FROM df")
con.execute("INSERT INTO my_table SELECT * FROM df")
```
(source: duckdb-python-data-ingestion.md)

## Pandas object Column Caveat

Columns with `object` dtype are analyzed (default sample: 1000 rows) to determine the target type. If conversion fails, increase the sample:

```python
duckdb.execute("SET GLOBAL pandas_analyze_sample = 100_000")
```
(source: duckdb-python-data-ingestion.md)

## See Also

- [[duckdb]] — hub page
- [[duckdb-result-conversion]] — converting results back to Python types
