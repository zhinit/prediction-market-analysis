# Kalshi API Market Data Endpoints

Source: https://docs.kalshi.com/api-reference/market/get-markets, https://docs.kalshi.com/api-reference/market/get-market, https://docs.kalshi.com/api-reference/market/get-trades, https://docs.kalshi.com/getting_started/quick_start_market_data
Fetched: 2026-06-24

---

## Public Market Data (No Auth Required)

"No authentication headers are required for the endpoints in this guide. You can start making requests immediately!"

Despite the "elections" naming, the API provides "access to ALL Kalshi markets - not just election-related ones" including economics, climate, and entertainment.

---

## GET /markets

Returns a paginated list of markets.

**URL**: `https://external-api.kalshi.com/trade-api/v2/markets`

### Query Parameters

| Parameter | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| limit | integer | Results per page | Default: 100, Max: 1000 |
| cursor | string | Pagination cursor from previous response | Optional |
| event_ticker | string | Filter by event ticker (single) | Optional |
| series_ticker | string | Filter by series ticker | Optional |
| min_created_ts | integer | Created after this Unix timestamp | Optional |
| max_created_ts | integer | Created before this Unix timestamp | Optional |
| min_updated_ts | integer | Metadata updated after this Unix timestamp | Optional |
| max_close_ts | integer | Closes before this Unix timestamp | Optional |
| min_close_ts | integer | Closes after this Unix timestamp | Optional |
| min_settled_ts | integer | Settled after this Unix timestamp | Optional |
| max_settled_ts | integer | Settled before this Unix timestamp | Optional |
| status | string | Filter by status: unopened, open, paused, closed, settled | Optional |
| tickers | string | Comma-separated list of market tickers | Optional |
| mve_filter | string | "only" or "exclude" multivariate events | Optional |

### Filter Compatibility Matrix

| Timestamp Filters | Compatible Status | Notes |
|-------------------|-------------------|-------|
| min/max_created_ts | unopened, open, empty | Standard filtering |
| min/max_close_ts | closed, empty | Closing time range |
| min/max_settled_ts | settled, empty | Settlement time range |
| min_updated_ts | empty only | Incompatible with all filters besides mve_filter=exclude |

### Response

```json
{
  "markets": [Market],
  "cursor": "string"
}
```

---

## GET /markets/{ticker}

Returns a single market by ticker.

**URL**: `https://external-api.kalshi.com/trade-api/v2/markets/{ticker}`

### Path Parameters

- **ticker** (required, string): Market ticker identifier

### Response

```json
{
  "market": Market
}
```

---

## Market Object

### Required Fields

- `ticker` (string)
- `event_ticker` (string)
- `market_type` (enum: binary, scalar)
- `yes_sub_title`, `no_sub_title` (strings)
- `created_time`, `updated_time`, `open_time`, `close_time`, `latest_expiration_time` (date-time)
- `settlement_timer_seconds` (integer)
- `status` (enum: initialized, inactive, active, closed, determined, disputed, amended, finalized)
- `notional_value_dollars` (FixedPointDollars)
- `yes_bid_dollars`, `yes_ask_dollars`, `no_bid_dollars`, `no_ask_dollars` (FixedPointDollars)
- `yes_bid_size_fp`, `yes_ask_size_fp` (FixedPointCount)
- `last_price_dollars`, `previous_yes_bid_dollars`, `previous_yes_ask_dollars`, `previous_price_dollars` (FixedPointDollars)
- `volume_fp`, `volume_24h_fp`, `open_interest_fp` (FixedPointCount)
- `liquidity_dollars` (FixedPointDollars, deprecated)
- `result` (enum: yes, no, scalar, empty string)
- `can_close_early`, `fractional_trading_enabled` (boolean)
- `expiration_value` (string)
- `rules_primary`, `rules_secondary` (strings)
- `price_level_structure` (string)
- `price_ranges` (array of PriceRange objects)

### Optional Fields

- `title`, `subtitle` (deprecated)
- `expected_expiration_time` (date-time, nullable)
- `settlement_value_dollars` (FixedPointDollars, nullable — only post-determination)
- `settlement_ts` (date-time, nullable)
- `occurrence_datetime` (date-time, nullable)
- `fee_waiver_expiration_time` (date-time, nullable)
- `early_close_condition` (string, nullable)
- `strike_type` (enum: greater, greater_or_equal, less, less_or_equal, between, functional, custom, structured)
- `floor_strike`, `cap_strike` (number)
- `functional_strike`, `custom_strike` (objects)
- `mve_collection_ticker` (string)
- `mve_selected_legs` (array of MveSelectedLeg objects)
- `primary_participant_key` (string, nullable)
- `is_provisional` (boolean)
- `exchange_index` (integer)

### Data Types

- **FixedPointDollars**: "US dollar amount as a fixed-point decimal string with up to 6 decimal places of precision."
- **FixedPointCount**: "Fixed-point contract count string (2 decimals). Responses always emit 2 decimals."

---

## GET /markets/trades

Returns all trades across markets.

**URL**: `https://external-api.kalshi.com/trade-api/v2/markets/trades`

"A trade represents a completed transaction between two users on a specific market." Block trades are included by default and filterable.

### Query Parameters

| Parameter | Type | Description | Constraints |
|-----------|------|-------------|-------------|
| limit | integer | Results per page | Default: 100, Max: 1000 |
| cursor | string | Pagination cursor | Optional |
| ticker | string | Filter by market ticker | Optional |
| min_ts | integer | After this Unix timestamp | Optional |
| max_ts | integer | Before this Unix timestamp | Optional |
| is_block_trade | boolean | Filter block/non-block trades | Optional |

### Trade Object

- `trade_id` (string)
- `ticker` (string)
- `count_fp` (FixedPointCount) — contract quantity
- `yes_price_dollars` (FixedPointDollars)
- `no_price_dollars` (FixedPointDollars)
- `taker_side` (enum: yes/no) — deprecated
- `taker_outcome_side` (enum: yes/no)
- `taker_book_side` (enum: bid/ask)
- `created_time` (date-time)
- `is_block_trade` (boolean)

---

## GET /markets/{ticker}/orderbook

Returns the current orderbook for a market. Returns bids only — in binary markets, bid/ask are reciprocal (YES bid at 60c = NO ask at 40c).

---

## Accessing Series, Events, and Markets

The hierarchy is: Series → Events → Markets.

Example flow:
1. `GET /series/KXHIGHNY` — get series info (title, frequency, category)
2. `GET /markets?series_ticker=KXHIGHNY&status=open` — list active markets in the series
3. `GET /events/{event_ticker}` — get event details
4. `GET /markets/{market_ticker}/orderbook` — current orderbook

---

## Historical Data

Markets settled before the historical cutoff are accessed via `GET /historical/markets`. Starting February 19, 2026, Kalshi split data into a live tier and a historical tier, with recent data at regular endpoints and settled or aged market data at dedicated historical endpoints.

---

## Candlestick Data

Available via `GET /events/{event_ticker}/candlesticks` with 1-minute, hourly, and daily granularity.
