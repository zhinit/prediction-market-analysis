# database-maintenance

Practices for keeping an analytical database reliable, understandable, and trustworthy over time.

## Schema evolution

Add tables and columns as analytical needs emerge ([[dimensional-modeling]] — just-in-time modeling). When adding:

1. Follow [[database-naming-conventions]] exactly.
2. Add `COMMENT ON` for every new table and non-obvious column ([[self-documenting-database]]).
3. Add constraints (NOT NULL, primary keys, foreign keys) to enforce data integrity.
4. Update dimension tables before loading new facts that reference them.
(source: holistics-kimball-dimensional-modeling.md)

## Data quality checks

Run checks after each data load:

- **Uniqueness**: No duplicate rows at the declared grain. `SELECT count(*), count(DISTINCT key) FROM table` should match.
- **Referential integrity**: Every foreign key in a fact table has a matching row in its dimension table.
- **Null checks**: Columns declared NOT NULL shouldn't have NULLs (enforced by the constraint, but verify after bulk inserts).
- **Range checks**: Prices between 0 and 1, volumes non-negative, dates within expected windows.
- **Row counts**: Track expected row counts over time. A sudden drop or spike signals a pipeline problem.
(source: python-duckdb-data-engineering-workflow.md)

```sql
-- Referential integrity check
SELECT f.market_id
FROM market_snapshots f
LEFT JOIN markets_dim d ON f.market_id = d.id
WHERE d.id IS NULL;

-- Uniqueness check
SELECT market_id, snapshot_time, count(*)
FROM market_snapshots
GROUP BY market_id, snapshot_time
HAVING count(*) > 1;
```

## Deduplication

Deduplicate at ingestion, not at query time. The staging layer (temporary pipeline tables) is where duplicates are detected and removed before data moves into fact and dimension tables.
(source: database-naming-conventions-warehouse-design.md)

## Dimension management

When dimension attributes change (a market's title is updated, a team changes division):

- **Type 1 (overwrite)** replaces the old value — simplest, but breaks historical reporting.
- If historical tracking matters, take periodic snapshots of the dimension table.
- Don't implement complex SCD logic unless there's a concrete analytical need for it — snapshots of entire dimension tables prove more efficient.
(source: holistics-kimball-dimensional-modeling.md)

See [[dimensional-modeling]] for the full Type 1/2/3 taxonomy.

## Backups

A persistent DuckDB database lives in a single file: data written to a connection is persisted and can be reloaded by reconnecting to the same file (source: duckdb-python-overview.md). Backing up is copying the file. Do this before destructive schema changes (dropping tables, altering columns).

## Metadata hygiene

Periodically verify that:
- Every table has a `COMMENT ON` description.
- Every non-trivial column has a comment.
- No orphaned staging tables remain.
- Naming conventions are consistently applied.

```sql
-- Find tables without comments
SELECT table_name
FROM duckdb_tables()
WHERE schema_name = 'main'
  AND internal = false
  AND comment IS NULL;

-- Find columns without comments (excluding standard patterns)
SELECT table_name, column_name
FROM duckdb_columns()
WHERE comment IS NULL
  AND column_name NOT IN ('id')
  AND column_name NOT LIKE '%_id';
```

Project-specific choices are recorded in `docs/project-conventions.md`.

## See also

- [[analytical-database-design]] — overall approach
- [[self-documenting-database]] — COMMENT ON and metadata introspection
- [[dimensional-modeling]] — schema design
- [[data-pipeline-stack]] — how data flows into the database
