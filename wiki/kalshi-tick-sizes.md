# Kalshi Tick Sizes

Kalshi uses per-market tick sizes controlled by the `price_level_structure`
field on Market objects. The tick size determines the minimum price increment
at which orders can be placed. (source: kalshi-fixed-point-migration.md)

## Price Level Structures

Three original structures exist since the fixed-point migration
(source: kalshi-fixed-point-migration.md):

| Structure | Edge tick ($0-0.10, $0.90-1.00) | Center tick ($0.10-0.90) |
|---|---|---|
| `linear_cent` | 1¢ | 1¢ |
| `tapered_deci_cent` | 0.1¢ | 1¢ |
| `deci_cent` | 0.1¢ | 0.1¢ |

Seven additional structures were announced July 23, 2026, using a
`center_{center}_edge_{edge}_cent` naming convention where whole = 1¢,
half = 0.5¢, quint = 0.2¢, and deci = 0.1¢
(source: kalshi-changelog-tick-sizes-2026.md):

| Structure | Edge tick | Center tick |
|---|---|---|
| `center_whole_edge_half_cent` | 0.5¢ | 1¢ |
| `center_whole_edge_quint_cent` | 0.2¢ | 1¢ |
| `center_half_edge_half_cent` | 0.5¢ | 0.5¢ |
| `center_half_edge_quint_cent` | 0.2¢ | 0.5¢ |
| `center_half_edge_deci_cent` | 0.1¢ | 0.5¢ |
| `center_quint_edge_quint_cent` | 0.2¢ | 0.2¢ |
| `center_quint_edge_deci_cent` | 0.1¢ | 0.2¢ |

Edge bands are $0.00-$0.10 and $0.90-$1.00. The center band is $0.10-$0.90.
(source: kalshi-changelog-tick-sizes-2026.md)

## Per-Market Assignment

Each market has its own `price_level_structure` field. The field was moved
from event-level to market-level in October 2025.
(source: kalshi-changelog-tick-sizes-2026.md)

The `price_ranges` array on the Market object provides the exact valid price
intervals as `{ start, end, step }` bands in fixed-point dollars. This is the
canonical source of truth for a market's valid prices, not the structure label.
(source: kalshi-fixed-point-migration.md)

## MLB Markets

MLB markets use `linear_cent`, meaning 1¢ ticks across the entire $0.00-$1.00
range. At extreme prices (e.g. 99¢), this creates a minimum 1¢ gap between
price levels, while Polymarket can express half-cent prices (e.g. 99.5¢). This
tick-size asymmetry is structural and produces apparent sub-cent arbitrage
opportunities that cannot be closed on the Kalshi side without finer ticks.
(source: kalshi-changelog-tick-sizes-2026.md)

## Rollout Timeline

Subpenny pricing launched on 2 markets March 9, 2026: KXGREENLAND-29
(`deci_cent`) and KXGDPNOM-RUS26 (`tapered_deci_cent`).
(source: kalshi-changelog-tick-sizes-2026.md)

The seven new structures began rolling out on pilot markets the week of
July 27, 2026, with expansion to higher-volume markets the week of
August 3, 2026. When a market moves to a finer tick, resting orders are
preserved and carried over to the new grid.
(source: kalshi-changelog-tick-sizes-2026.md)

## Structure Changes via WebSocket

The `market_lifecycle_v2` WebSocket channel emits a
`price_level_structure_updated` event when a market's tick size changes. Since
July 2, 2026, this event also includes the updated `price_ranges` array, so
consumers can read the new price grid without a REST call.
(source: kalshi-changelog-tick-sizes-2026.md)

## Related pages

- [[kalshi-fractional-contracts]] -- fixed-point migration, subpenny pricing, fractional contracts
- [[kalshi-fees]] -- fee formula applies to subpenny prices
- [[cross-platform-arbitrage]] -- tick-size asymmetry as source of apparent arbs
