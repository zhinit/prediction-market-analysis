# duckdb-db-api

PEP 249 (DB-API 2.0) compliant SQL interface, similar to the SQLite Python API.

## Querying

```python
con.execute("CREATE TABLE items (item VARCHAR, value DECIMAL(10, 2), count INTEGER)")
con.execute("INSERT INTO items VALUES ('jeans', 20.0, 1), ('hammer', 42.2, 2)")

# fetch all at once
con.execute("SELECT * FROM items")
print(con.fetchall())
# [('jeans', Decimal('20.00'), 1), ('hammer', Decimal('42.20'), 2)]

# fetch one at a time
con.execute("SELECT * FROM items")
print(con.fetchone())  # ('jeans', Decimal('20.00'), 1)
print(con.fetchone())  # ('hammer', Decimal('42.20'), 2)
print(con.fetchone())  # None — closes the transaction
```

`con.description` contains column names per the DB-API standard.
(source: duckdb-python-dbapi.md)

## Prepared Statements

Values passed as additional parameter using `?` or `$1` placeholders:

```python
# positional (?)
con.execute("INSERT INTO items VALUES (?, ?, ?)", ["laptop", 2000, 1])

# multiple rows
con.executemany("INSERT INTO items VALUES (?, ?, ?)",
    [["chainsaw", 500, 10], ["iphone", 300, 2]])

# query with parameter
con.execute("SELECT item FROM items WHERE value > ?", [400])
print(con.fetchall())  # [('laptop',), ('chainsaw',)]

# dollar notation with reuse
con.execute("SELECT $1, $1, $2", ["duck", "goose"])
print(con.fetchall())  # [('duck', 'duck', 'goose')]
```

**Do not use `executemany` for bulk inserts** — see [[duckdb-data-ingestion]] for efficient alternatives.
(source: duckdb-python-dbapi.md)

## Named Parameters

Use `$name` syntax with a dictionary:

```python
res = duckdb.execute("""
    SELECT $my_param, $other_param, $also_param
    """,
    {"my_param": 5, "other_param": "DuckDB", "also_param": [42]}
).fetchall()
# [(5, 'DuckDB', [42])]
```
(source: duckdb-python-dbapi.md)

## Performance Note

Passing parameters to `sql()`, `query()`, or `from_query()` (the relational API methods) has **significant overhead** — at least 5x processing and nearly 2x memory vs non-parameterized. Use `execute()` for parameterized queries, then feed the result into the relational API:

```python
df = conn.execute("SELECT * FROM my_table WHERE x = ?", [42]).df()
conn.sql("SELECT * FROM df WHERE y > 0").order("y").show()
```
(source: duckdb-python-known-issues.md)

## See Also

- [[duckdb]] — hub page
- [[duckdb-python-connections]] — connection types and configuration
- [[duckdb-relational-api]] — lazy query builder alternative
