# Kalshi Market Object

The Market object is the core data structure returned by GET /markets and
GET /markets/{ticker}. (source: kalshi-api-market-data-endpoints.md)

## Pricing Fields (FixedPointDollars)

All prices are US dollar amounts as fixed-point decimal strings with up to
6 decimal places. (source: kalshi-api-market-data-endpoints.md)

| Field | Description |
|-------|-------------|
| `notional_value_dollars` | Contract notional value |
| `yes_bid_dollars` | Best YES bid price |
| `yes_ask_dollars` | Best YES ask price |
| `no_bid_dollars` | Best NO bid price |
| `no_ask_dollars` | Best NO ask price |
| `last_price_dollars` | Last trade price |
| `previous_yes_bid_dollars` | Previous YES bid |
| `previous_yes_ask_dollars` | Previous YES ask |
| `previous_price_dollars` | Previous last trade price |

## Volume Fields (FixedPointCount)

Contract counts as fixed-point strings with 2 decimal places.

| Field | Description |
|-------|-------------|
| `volume_fp` | Total volume |
| `volume_24h_fp` | 24-hour volume |
| `open_interest_fp` | Open interest |
| `yes_bid_size_fp` | Size at best YES bid |
| `yes_ask_size_fp` | Size at best YES ask |

## Identity and Status

| Field | Type |
|-------|------|
| `ticker` | string |
| `event_ticker` | string |
| `market_type` | binary or scalar |
| `status` | initialized, inactive, active, closed, determined, disputed, amended, finalized |
| `result` | yes, no, scalar, or empty string |

## Timing

`created_time`, `updated_time`, `open_time`, `close_time`,
`latest_expiration_time`, `settlement_timer_seconds`. Optional:
`expected_expiration_time`, `settlement_ts`, `occurrence_datetime`.

## Strike Information

`strike_type`: greater, greater_or_equal, less, less_or_equal, between,
functional, custom, structured. Optional: `floor_strike`, `cap_strike`,
`functional_strike`, `custom_strike`.

## Other Fields

- `rules_primary`, `rules_secondary` — resolution rules
- `can_close_early`, `fractional_trading_enabled` — booleans
- `price_level_structure`, `price_ranges` — valid order price constraints
- `mve_collection_ticker`, `mve_selected_legs` — multivariate event references
- `settlement_value_dollars` — only available post-determination
- `liquidity_dollars` — deprecated

(source: kalshi-api-market-data-endpoints.md)
