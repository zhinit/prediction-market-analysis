# self-documenting-database

A database where the schema itself explains the data — no external documentation needed. Achieved through naming conventions, embedded comments, and metadata introspection.

## Why it matters

External documentation (READMEs, wikis, spreadsheets) drifts from reality. The schema is always current. If the documentation lives inside the database, it stays synchronized with the data by construction.

Anyone should be able to connect to the database, run a few metadata queries, and understand every table and column without reading a separate document.
(source: techwriter-self-documenting-databases.md)

## DuckDB's COMMENT ON

DuckDB supports PostgreSQL-style comments on database objects:

```sql
COMMENT ON TABLE orders IS
    'One row per customer order placed through the storefront.';

COMMENT ON COLUMN orders.total_amount IS
    'Order total in USD, including tax';

COMMENT ON COLUMN orders.create_time IS
    'UTC timestamp when the order was placed';
```

Supported object types: TABLE, COLUMN, VIEW, INDEX, SEQUENCE, TYPE, MACRO.

To remove a comment:

```sql
COMMENT ON TABLE orders IS NULL;
```
(source: duckdb-comment-on.md)

## Reading comments back

Comments are queryable through DuckDB's metadata functions:

```sql
-- All tables with their comments
SELECT table_name, comment
FROM duckdb_tables()
WHERE schema_name = 'main';

-- All columns for a specific table
SELECT column_name, data_type, comment
FROM duckdb_columns()
WHERE table_name = 'orders';

-- Full schema catalog
SELECT t.table_name, t.comment AS table_comment, c.column_name, c.data_type, c.comment AS column_comment
FROM duckdb_tables() t
JOIN duckdb_columns() c ON t.table_name = c.table_name
WHERE t.schema_name = 'main'
ORDER BY t.table_name, c.column_index;
```
(source: duckdb-metadata-functions.md)

## What to comment

**Every table**: One sentence describing what it holds and its grain (what one row represents).

**Every non-obvious column**: Columns whose meaning isn't clear from the name alone. Skip comments on `id`, `create_time`, or foreign keys that follow the `[table]_id` convention — the naming convention already documents those.

**Views**: What question does this view answer? What is it for?

Keep comments concise. One or two sentences maximum.
(source: techwriter-self-documenting-databases.md)

## Metadata introspection

Beyond comments, DuckDB's metadata functions provide full schema introspection:

| Function | Returns |
|----------|---------|
| `duckdb_tables()` | Table names, schemas, column counts, comments |
| `duckdb_columns()` | Column names, types, nullability, defaults, comments |
| `duckdb_views()` | View definitions and comments |
| `duckdb_constraints()` | Primary keys, foreign keys, check constraints |
| `duckdb_indexes()` | Index definitions |
| `duckdb_sequences()` | Sequence current values |

```sql
-- Quick schema overview
SELECT table_name, column_count, comment
FROM duckdb_tables()
WHERE schema_name = 'main'
  AND internal = false;
```
(source: duckdb-metadata-functions.md)

## Current limitations

DuckDB's COMMENT ON cannot attach comments to schemas or databases — only to objects within them.
(source: duckdb-comment-on.md)

Project-specific choices are recorded in `docs/project-conventions.md`.

## See also

- [[analytical-database-design]] — overall approach
- [[database-naming-conventions]] — naming rules that reduce the need for comments
- [[duckdb]] — the database engine and its Python API
