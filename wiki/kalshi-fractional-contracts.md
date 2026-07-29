# Kalshi Fractional Contracts

Kalshi supports fractional contract sizes with a minimum granularity of 0.01
contracts. This was introduced as part of the fixed-point migration, which
also added subpenny pricing. (source: kalshi-fixed-point-migration.md)

## Quantity Representation

Contract count fields use fixed-point strings with the `_fp` suffix.
(source: kalshi-fixed-point-migration.md)

```json
{
  "count_fp": "10.00"
}
```

- `*_fp` fields are strings
- Accept 0-2 decimal places on input; responses always emit 2 decimals
- Minimum granularity is 0.01 contracts
- In requests where both integer and `_fp` fields are provided, they must match
(source: kalshi-fixed-point-migration.md)

Even without placing fractional orders, fractional values appear elsewhere in
the API (for example, fills). The docs suggest multiplying `_fp` values by 100
and casting to integers for easier arithmetic — e.g., treating `"1.55"` as 155
units. (source: kalshi-fixed-point-migration.md)

## Subpenny Pricing

Prices use fixed-point dollar strings with the `_dollars` suffix, supporting up
to 4 decimal places. Three pricing tiers exist:
(source: kalshi-fixed-point-migration.md)

| Structure           | Ranges         | Tick Size |
|---------------------|----------------|-----------|
| `linear_cent`       | $0.00 – $1.00 | $0.01     |
| `tapered_deci_cent` | $0.00 – $0.10 | $0.001    |
|                     | $0.10 – $0.90 | $0.01     |
|                     | $0.90 – $1.00 | $0.001    |
| `deci_cent`         | $0.00 – $1.00 | $0.001    |

`tapered_deci_cent` provides finer precision at the tails of the probability
range, where small absolute price differences represent large relative changes
in implied probability. (source: kalshi-fixed-point-migration.md)

## Precision

When fractional contracts and subpenny pricing combine, intermediate
calculations may reach 6 decimal places. The exchange applies rounding fees
when balance changes exceed applicable precision, with a fee accumulator
providing rebates to prevent systematic overpayment.
(source: kalshi-fixed-point-migration.md)

## Impact on Order Book Data

The [[kalshi-api-websocket]] `orderbook_delta` channel uses `_fp` fields for
quantities. A delta with `"delta_fp": "0.09"` means 0.09 contracts were added
or removed at that price level. These fractional resting quantities appear in
reconstructed order book snapshots.

## Related pages

- [[kalshi-tick-sizes]] -- per-market tick size structures and rollout timeline
- [[kalshi-api-websocket]] -- WebSocket channels including orderbook_delta
- [[kalshi-fees]] -- fee formula (fees on fractional quantities use rounding)
- [[polymarket-us-contract-sizing]] -- Polymarket US contract sizing for comparison
