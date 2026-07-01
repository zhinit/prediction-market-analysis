# dimensional-modeling

Organizing analytical data into fact tables (measurements) and dimension tables (context) so that queries are fast and intuitive. The dominant pattern is the **star schema**.

## Star schema

A central fact table connects to multiple dimension tables via foreign keys. The shape resembles a star: fact in the center, dimensions radiating outward.

**Fact tables** hold numeric measures and foreign keys. They grow over time as events accumulate. Every row represents one measurement at a specific grain.

**Dimension tables** hold descriptive attributes that answer who, what, where, when, why. They are denormalized — all attributes for a concept live in one table, not split across normalized lookups. They change slowly relative to facts.
(source: motherduck-star-schema-guide.md)

## Kimball's four-step process

Ralph Kimball's methodology for designing a dimensional model:

1. **Select the business process.** What are you measuring? Start with the questions analysts want to ask, not the entity structure.

2. **Establish the grain.** Define the most atomic level of data. For retail, this means line items rather than orders. Always go as granular as possible — you can aggregate up but can't disaggregate down, and detailed queries later won't require re-architecting.

3. **Choose dimensions.** Ask "how do business people describe this data?" Each answer becomes a dimension table. A date dimension, for example, captures business concepts like fiscal years and selling seasons absent from standard date fields.

4. **Identify facts.** Select numeric measures answerable to key business questions. Facts must align with the established grain.

The philosophy: "do the hard work now, to make it easy to query later."
(source: holistics-kimball-dimensional-modeling.md)

## Example: online sales star schema

The MotherDuck guide's example models online sales. A central **FactSales** table contains the foreign keys `DateKey`, `CustomerKey`, `ProductKey`, `StoreKey` and the measures `QuantitySold`, `UnitPrice`, `TotalAmount`. Four dimensions radiate from it:

- **DimDate** — temporal attributes (day of week, month, quarter, fiscal periods)
- **DimCustomer** — purchaser information (name, location, segment)
- **DimProduct** — merchandise details (category, brand, color, size)
- **DimStore** — location context (city, region, store type)

(source: motherduck-star-schema-guide.md)

## Date dimension

A dedicated, pre-populated date dimension table is standard practice. It holds pre-calculated attributes (day of week, month name, quarter, fiscal period, is_weekend) so queries filter on readable fields instead of date functions.

```sql
WHERE dd.year = 2026 AND dd.quarter = 2
```

instead of:

```sql
WHERE EXTRACT(YEAR FROM snapshot_time) = 2026
  AND EXTRACT(QUARTER FROM snapshot_time) = 2
```
(source: motherduck-star-schema-guide.md)

## DuckDB implementation notes

DuckDB uses sequences for auto-incrementing keys (no `AUTOINCREMENT` keyword):

```sql
CREATE SEQUENCE sequence_name START 1;
-- then, in the table definition:
column_name INTEGER PRIMARY KEY DEFAULT nextval('sequence_name')
```
(source: motherduck-star-schema-guide.md)

## Slowly changing dimensions

When dimension attributes change over time:

- **Type 1 (overwrite)**: Replace the old value. Simple but loses history.
- **Type 2 (new row)**: Add a new row with a surrogate key, preserving the old version. Maintains full history.
- **Type 3 (new column)**: Add a column for the previous value. Limited history depth.

Modern practice: take periodic snapshots of the entire dimension table rather than implementing complex SCD logic. "Compute is cheap. Storage is cheap. Engineering time is expensive."
(source: holistics-kimball-dimensional-modeling.md)

## Star vs. snowflake

A snowflake schema normalizes dimension tables further (e.g., storing category in a separate `DimCategory` rather than in `DimProduct`). This reduces redundancy but adds joins and complexity. Star schemas typically outperform for analytical workloads and are easier to understand.
(source: motherduck-star-schema-guide.md)

## Trade-offs

- **Storage**: Denormalization means some data is repeated across dimension rows. Acceptable for analytical databases where read performance matters more than storage efficiency.
- **Write complexity**: Updates to dimension attributes touch more rows. Mitigated by the fact that dimensions change slowly.
- **Not for OLTP**: Star schemas optimize reads, not writes. They complement transactional systems, not replace them.
(source: motherduck-star-schema-guide.md)

Project-specific choices are recorded in `docs/project-conventions.md`.

## See also

- [[analytical-database-design]] — overall approach
- [[database-naming-conventions]] — how to name tables and columns
- [[duckdb]] — the database engine
- [[data-pipeline-stack]] — how data reaches the database
