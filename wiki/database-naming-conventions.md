# database-naming-conventions

Consistent naming makes a database self-explanatory. Conventions for naming tables and columns in an analytical database.

## General rules

- **Lowercase snake_case everywhere.** No CamelCase, no hyphens. `market_snapshots`, not `MarketSnapshots` or `market-snapshots`.
- **American English spelling.**
- **No abbreviations** except universally understood ones: `id`, `config`, `stats`, `ref`. Document any others.
- **Avoid prepositions**: `error_reason` not `reason_for_error`.
- **Avoid postpositive adjectives**: `collected_items` not `items_collected`.
(source: database-naming-conventions-warehouse-design.md)

## Table names

**Plural nouns.** `markets`, `trades`, `teams` — not `market`, `trade`, `team`.

**Suffixes and prefixes by table type:**

| Type | Pattern | Example |
|------|---------|---------|
| Fact table | No prefix/suffix | `market_snapshots`, `trades` |
| Dimension table | `_dim` suffix | `markets_dim`, `teams_dim`, `dates_dim` |
| Reference/lookup | `ref_` prefix | `ref_market_types`, `ref_game_states` |
| Temporary pipeline | `tmp_` prefix | `tmp_daily_load` |
| Testing (with expiration management) | `test_` prefix | `test_trades` |

Fact tables are unprefixed, allowing alphabetical grouping of related tables.
(source: database-naming-conventions-warehouse-design.md)

## Column names

### Primary keys

Use `id` within the table's own definition. The name is unambiguous in context:

```sql
CREATE TABLE markets_dim (id INTEGER PRIMARY KEY, ...);
```
(source: database-naming-conventions-warehouse-design.md)

### Foreign keys

Format: `[referenced_table]_id`. Matches the referenced table name:

```sql
market_id   -- references markets_dim.id
event_id    -- references events_dim.id
date_id     -- references dates_dim.id
```

When a table has multiple foreign keys to the same table, prefix with a distinguishing name:

```sql
home_team_id    -- references teams_dim.id
away_team_id    -- references teams_dim.id
```
(source: database-naming-conventions-warehouse-design.md)

### Temporal columns

| Suffix | Meaning | Format | Example |
|--------|---------|--------|---------|
| `_time` | Point in time | UTC timestamp | `snapshot_time`, `create_time` |
| `_date` | Calendar date only | YYYY-MM-DD | `game_date`, `expiry_date` |
| `_duration` | Time span | Interval or seconds | `session_duration` |

Always store timestamps in UTC.
(source: database-naming-conventions-warehouse-design.md)

### Quantities and units

Include the unit or type in the column name:

```sql
volume_count        -- number of contracts traded
distance_miles      -- distance in miles
price               -- unitless when the unit is obvious from context
spread_cents        -- spread in cents
```

Use `_count` suffix for countable items: `trade_count`, `contract_count`.
(source: database-naming-conventions-warehouse-design.md)

### Boolean columns

Use `is_` or `has_` prefix: `is_active`, `is_settled`, `has_outcome`.

### Humanized values

Dimension tables should map codes to readable strings:

```sql
-- In a dimension table, not a fact table
payment_type     INTEGER,     -- raw code from source
payment_type_name TEXT        -- 'Credit card', 'Cash', etc.
```

Transform flags (0/1) into booleans. Transform cryptic codes into meaningful labels.
(source: database-naming-conventions-warehouse-design.md)

## Data cleaning principles

- **Eliminate NULLs** where possible — use appropriate defaults ("Unknown", 0, false).
- **Fix inconsistencies** at ingestion — standardize formats before they reach dimension tables.
- **Remove irrelevant rows** — exclude test data, fraud entries, inactive records at the staging layer.
(source: database-naming-conventions-warehouse-design.md)

Project-specific choices are recorded in `docs/project-conventions.md`.

## See also

- [[analytical-database-design]] — overall approach
- [[dimensional-modeling]] — star schema, fact and dimension tables
- [[self-documenting-database]] — COMMENT ON and metadata introspection
