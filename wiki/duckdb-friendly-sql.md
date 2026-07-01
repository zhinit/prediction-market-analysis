# duckdb-friendly-sql

DuckDB extends standard SQL with syntactic sugar that makes queries more concise. These features are unique to DuckDB or were popularized by it.

## FROM-First Syntax

Query without SELECT — implicit `SELECT *`:

```sql
FROM markets
FROM markets WHERE price > 0.5
FROM 'data/markets.parquet'
```
(source: duckdb-friendly-sql.md)

## GROUP BY ALL / ORDER BY ALL

Infer grouping or ordering columns from the SELECT list:

```sql
SELECT ticker, AVG(price) FROM markets GROUP BY ALL
SELECT * FROM markets ORDER BY ALL
```
(source: duckdb-friendly-sql.md)

## EXCLUDE and REPLACE

Remove or substitute columns from SELECT *:

```sql
SELECT * EXCLUDE (internal_id) FROM markets
SELECT * REPLACE (price * 100 AS price) FROM markets
```
(source: duckdb-friendly-sql.md)

## COLUMNS() Expression

Apply operations across multiple columns using regex, EXCLUDE, REPLACE, or lambdas:

```sql
SELECT COLUMNS('price.*') FROM markets
SELECT MIN(COLUMNS(*)), MAX(COLUMNS(*)) FROM markets
```
(source: duckdb-friendly-sql.md)

## Column Aliases in WHERE/GROUP BY/HAVING

```sql
SELECT price * 100 AS cents FROM markets WHERE cents > 50
SELECT ticker, COUNT(*) AS n FROM markets GROUP BY ticker HAVING n > 1
```
(source: duckdb-friendly-sql.md)

## Lateral Column Aliases

Reference earlier columns in the same SELECT:

```sql
SELECT price * 100 AS cents, cents / 2 AS half_cents FROM markets
```
(source: duckdb-friendly-sql.md)

## count() Shorthand

`count()` replaces `count(*)`.
(source: duckdb-friendly-sql.md)

## UNION BY NAME

Match columns by name rather than position:

```sql
SELECT ticker, price FROM markets_a
UNION BY NAME
SELECT price, ticker FROM markets_b
```
(source: duckdb-friendly-sql.md)

## Prefix Aliases

```sql
SELECT x: 42, name: 'hello'
-- equivalent to: SELECT 42 AS x, 'hello' AS name
```
(source: duckdb-friendly-sql.md)

## INSERT Variants

```sql
INSERT INTO t BY NAME SELECT ...        -- match by column name
INSERT OR IGNORE INTO t VALUES (...)    -- skip on constraint conflict
INSERT OR REPLACE INTO t VALUES (...)   -- upsert on conflict
```
(source: duckdb-friendly-sql.md)

## PIVOT / UNPIVOT

```sql
PIVOT markets ON ticker USING SUM(volume)
UNPIVOT wide_table ON col1, col2, col3 INTO NAME category VALUE amount
```
(source: duckdb-friendly-sql.md)

## Direct File Queries

```sql
SELECT * FROM 'data/markets.csv'
SELECT * FROM 'data/*.parquet'
SELECT * FROM read_csv('file.csv', header=true)
```

Glob patterns supported. Schema auto-detected for CSV.
(source: duckdb-friendly-sql.md)

## ASOF Joins

Match nearest preceding timestamp in time-series data:

```sql
SELECT * FROM trades ASOF JOIN quotes ON trades.ts >= quotes.ts
```
(source: duckdb-friendly-sql.md)

## POSITIONAL Joins

Row-by-row matching without a key:

```sql
SELECT * FROM table_a POSITIONAL JOIN table_b
```
(source: duckdb-friendly-sql.md)

## Dot Operator / Method Chaining

```sql
SELECT ('hello world').upper().split(' ')
```
(source: duckdb-friendly-sql.md)

## Numeric Separators

Underscores as digit separators:

```sql
SELECT 1_000_000
```
(source: duckdb-friendly-sql.md)

## Trailing Commas

Permitted in SELECT lists and array literals.
(source: duckdb-friendly-sql.md)

## Top-N Aggregates

Efficient per-group ranking without window functions:

```sql
SELECT arg_max(player, batting_avg, 5) FROM stats GROUP BY team
-- returns top 5 players by batting_avg per team
```

Functions: `max(arg, n)`, `min(arg, n)`, `arg_max(arg, val, n)`, `arg_min(arg, val, n)`, `max_by(arg, val, n)`, `min_by(arg, val, n)`.
(source: duckdb-friendly-sql.md)

## FILTER Clause

Conditional aggregation:

```sql
SELECT
    COUNT(*) FILTER (WHERE status = 'settled') AS settled,
    COUNT(*) FILTER (WHERE status = 'open') AS open
FROM markets
```
(source: duckdb-friendly-sql.md)

## SQL Variables

```sql
SET VARIABLE my_threshold = 0.5;
SELECT * FROM markets WHERE price > getvariable('my_threshold');
RESET VARIABLE my_threshold;
```
(source: duckdb-friendly-sql.md)

## See Also

- [[duckdb]] — hub page
- [[duckdb-relational-api]] — Python API for building queries programmatically
