# duckdb-result-conversion

Type mapping between Python and DuckDB, and output format methods.

## Python → DuckDB Type Mapping

| Python Type | DuckDB Type |
|:--|:--|
| `None` | `NULL` |
| `bool` | `BOOLEAN` |
| `int` | `BIGINT` (tries INTEGER, UBIGINT, UINTEGER, DOUBLE) |
| `float` | `DOUBLE` (tries FLOAT) |
| `str` | `VARCHAR` |
| `bytes` | `BLOB` |
| `bytearray` | `BLOB` |
| `memoryview` | `BLOB` |
| `decimal.Decimal` | `DECIMAL` / `DOUBLE` |
| `uuid.UUID` | `UUID` |
| `datetime.datetime` | `TIMESTAMP` (with tzinfo: `TIMESTAMPTZ`) |
| `datetime.date` | `DATE` |
| `datetime.time` | `TIME` (with tzinfo: `TIMETZ`) |
| `datetime.timedelta` | `INTERVAL` |
| `list` | `LIST` (most permissive child type) |
| `tuple` | `LIST` (or `STRUCT` with Value) |
| `dict` (key/value lists) | `MAP` |
| `dict` (other) | `STRUCT` |

(source: duckdb-python-conversion.md)

## DuckDB → Python Output Methods

| Method | Returns |
|:--|:--|
| `fetchall()` | List of tuples |
| `fetchone()` | Single tuple (None when exhausted) |
| `fetchmany(n)` | List of n tuples |
| `df()` / `fetchdf()` / `fetch_df()` | Pandas DataFrame |
| `fetch_df_chunk(vector_multiple)` | Chunked Pandas (2048 × vector_multiple rows) |
| `pl()` | Polars DataFrame |
| `to_arrow_table()` | Arrow Table |
| `to_arrow_reader(chunk_size)` | Arrow RecordBatchReader |
| `fetchnumpy()` | Dict of NumPy arrays |

Deprecated: `fetch_arrow_table()` → use `to_arrow_table()`. `fetch_record_batch()` → use `to_arrow_reader()`.
(source: duckdb-python-conversion.md)

## Python Built-in → DuckDB Type (for type annotations / DuckDBPyType)

| Python | DuckDB |
|:--|:--|
| `bool` | `BOOLEAN` |
| `int` | `BIGINT` |
| `float` | `DOUBLE` |
| `str` | `VARCHAR` |
| `bytes` | `BLOB` |
| `bytearray` | `BLOB` |
| `list[T]` | `LIST(T)` |
| `dict[K, V]` | `MAP(K, V)` |
| `{'a': T, ...}` (dict literal) | `STRUCT(a T, ...)` |
| `Union[T1, T2]` | `UNION(u1 T1, u2 T2)` |

(source: duckdb-python-types.md)

## Type Constants

Available in `duckdb.sqltypes`:

`BIGINT`, `BIT`, `BLOB`, `BOOLEAN`, `DATE`, `DOUBLE`, `FLOAT`, `HUGEINT`, `INTEGER`, `INTERVAL`, `SMALLINT`, `SQLNULL`, `TIME_TZ`, `TIME`, `TIMESTAMP_MS`, `TIMESTAMP_NS`, `TIMESTAMP_S`, `TIMESTAMP_TZ`, `TIMESTAMP`, `TINYINT`, `UBIGINT`, `UHUGEINT`, `UINTEGER`, `USMALLINT`, `UTINYINT`, `UUID`, `VARCHAR`

Complex type constructors: `list_type(child)`, `struct_type(fields)`, `map_type(key, value)`, `decimal_type(width, scale)`, `union_type(members)`, `string_type(collation)`.
(source: duckdb-python-types.md)

## See Also

- [[duckdb]] — hub page
- [[duckdb-data-ingestion]] — reading data in
