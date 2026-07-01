# duckdb-python-connections

Connection types, configuration options, and threading model for the DuckDB Python API.

## Connection Types

### In-Memory (default)

```python
import duckdb

con = duckdb.connect()           # unnamed in-memory
con = duckdb.connect(":memory:") # equivalent
```

No data persists to disk. Each call to `duckdb.connect()` without a name creates a separate database instance.
(source: duckdb-python-dbapi.md)

### Named In-Memory

```python
con1 = duckdb.connect(":memory:conn3")
con2 = duckdb.connect(":memory:conn3")  # same database, shared catalogs
```

Subsequent connects with the same name share tables, views, macros.
(source: duckdb-python-dbapi.md)

### Persistent (File-Based)

```python
con = duckdb.connect("analytics.db")
```

Data survives between script runs. File extension is irrelevant (`.db`, `.duckdb`, anything).
(source: duckdb-python-dbapi.md)

### Read-Only

```python
con = duckdb.connect("analytics.db", read_only=True)
```

Required when multiple Python processes access the same database file simultaneously. If the file does not exist, it is not created.
(source: duckdb-python-dbapi.md)

### Default Connection

```python
con = duckdb.connect(":default:")
# or equivalently:
duckdb.sql("SELECT 1")
```

The `duckdb` module maintains a global unnamed in-memory database. Every method on `DuckDBPyConnection` is also available directly on the `duckdb` module. Avoid the default connection in packages — it's shared globally and can cause hard-to-debug issues.
(source: duckdb-python-overview.md)

## Configuration

Pass a `config` dictionary to `duckdb.connect()`:

```python
con = duckdb.connect(config={'threads': 1})
con = duckdb.connect(config={'storage_compatibility_version': 'latest'})
```
(source: duckdb-python-overview.md)

## Context Manager

```python
with duckdb.connect("analytics.db") as con:
    con.sql("SELECT * FROM markets").show()
    # connection closed automatically
```

Connections are also closed implicitly when they go out of scope.
(source: duckdb-python-overview.md)

## Threading

`duckdb.sql()` and `duckdb.connect(':default:')` use a shared global connection that is **not thread-safe**. Each thread needs its own connection:

```python
import duckdb

def good_use():
    con = duckdb.connect()  # new connection per thread
    con.sql("SELECT 1").fetchall()

def bad_use():
    duckdb.sql("SELECT 1").fetchall()  # shared global — not safe
```

`cursor()` creates another handle on the same connection (not a new connection). Cursors from one connection serialize queries.
(source: duckdb-python-overview.md)

## Extensions

### Community Extensions

```python
con = duckdb.connect()
con.install_extension("h3", repository="community")
con.load_extension("h3")
```

### Unsigned Extensions

```python
con = duckdb.connect(config={"allow_unsigned_extensions": "true"})
```

Only load from trusted sources. Avoid loading over HTTP.
(source: duckdb-python-overview.md)

## See Also

- [[duckdb]] — hub page
- [[duckdb-db-api]] — PEP 249 query interface
