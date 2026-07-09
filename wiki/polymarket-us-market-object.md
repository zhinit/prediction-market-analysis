# Polymarket US Market Object

The market object is returned by `GET /v1/markets`, `GET /v1/market/id/{id}`,
and `GET /v1/market/slug/{slug}` on the public gateway
(`gateway.polymarket.us`, no auth) (source: polymarket-us-api-market-object.md).

## Identity & Display

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Unique identifier |
| `slug` | string? | URL-friendly identifier |
| `question` | string? | Market question text |
| `title` | string? | Market title |
| `titleShort` | string? | Compact title (e.g. "DET -5.5 F5") |
| `subtitle` | string? | Subtitle |
| `description` | string? | Detailed explanation |
| `image` | string? | Image URL |
| `color` | string? | Display color |
| `darkColor` | string? | Dark mode color |
| `rulesDisclaimer` | string? | Rules disclaimer |
| `rulesDisclaimerPopup` | boolean? | Show as popup |

(source: polymarket-us-api-market-object.md)

## Classification

| Field | Type | Notes |
|-------|------|-------|
| `category` | string? | Category |
| `subcategory` | string? | Secondary classification |
| `tags` | Tag[] | Associated tags |
| `sportsMarketType` | string? | Sports type |
| `sportsMarketTypeV2` | enum (deprecated) | MONEYLINE, SPREAD, TOTAL, PROP, FUTURE, DRAWABLE_OUTCOME |
| `marketType` | string? (deprecated) | moneyline, spreads, totals |
| `sortOrder` | integer? | Order within event |

(source: polymarket-us-api-market-object.md)

## Status

| Field | Type | Notes |
|-------|------|-------|
| `active` | boolean? | Accepting orders |
| `closed` | boolean? | Market concluded |
| `hidden` | boolean? | Hidden from listings |
| `archived` | boolean? (deprecated) | Legacy visibility flag |
| `ep3Status` | string? | EP3 system status |
| `manualActivation` | boolean? (deprecated) | Manual activation |
| `comboEnabled` | boolean? | Combo trading enabled |

(source: polymarket-us-api-market-object.md)

## Timestamps

| Field | Type | Notes |
|-------|------|-------|
| `startDate` | string? | Market start |
| `endDate` | string? | Market end / expiration |
| `createdAt` | string? | Creation time |
| `updatedAt` | string? | Last update |
| `gameStartTime` | string? (deprecated) | Game start |
| `ep3SyncedAt` | string? | Last EP3 sync |

(source: polymarket-us-api-market-object.md)

## Pricing

| Field | Type | Notes |
|-------|------|-------|
| `orderPriceMinTickSize` | decimal? | Min price increment |
| `minimumTradeQty` | decimal? | Min order size (contracts) |
| `lastTradePrice` | number | Last execution price |
| `bestBid` | number | Highest buy |
| `bestAsk` | number | Lowest sell |
| `bestBidQuote` | Amount | Bid as {value, currency} |
| `bestAskQuote` | Amount | Ask as {value, currency} |
| `spread` | number | Bid-ask differential |
| `oneDayPriceChange` | number | 24h change |
| `oneWeekPriceChange` | number | 7d change |
| `feeCoefficient` | decimal? | Market-specific fee coefficient |

Always read `orderPriceMinTickSize` and `minimumTradeQty` from the market
object before placing orders — do not infer from slug or type (source:
polymarket-us-api-market-object.md).

## Volume & Liquidity

| Field | Type | Notes |
|-------|------|-------|
| `liquidity` | string | Current liquidity |
| `liquidityNum` | number | Numeric liquidity |
| `volume` | decimal? | Lifetime volume (shares) |
| `volumeNum` | number | Numeric total volume |
| `volume24hr` | decimal? | 24h volume |
| `volume1wk` | decimal? | 7d volume |
| `volume1mo` | decimal? | 30d volume |
| `volume1yr` | decimal? | 1y volume |

(source: polymarket-us-api-market-object.md)

## Sports-Specific

| Field | Type | Notes |
|-------|------|-------|
| `gameId` | string | Provider game ID |
| `line` | decimal? | Spread or total value |
| `spreadTotalSuffix` | string? | UI suffix (points, goals) |
| `subjectId` | integer? | Subject ID |
| `subject` | Subject | Subject object (name, image, etc.) |

(source: polymarket-us-api-market-object.md)

## Market Sides

Each market has a `marketSides` array. Each side represents an outcome
(source: polymarket-us-api-market-object.md):

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Side ID |
| `marketSideType` | enum | ERC1155 or INSTRUMENT |
| `identifier` | string? | Side identifier |
| `description` | string? | Outcome description |
| `price` | string? | Current price |
| `marketId` | integer | Parent market ID |
| `long` | boolean? | Long side flag |
| `tradable` | boolean? | Whether tradable |
| `quote` | Amount | Quote {value, currency} |
| `teamId` | integer? | Team ID |

## Order Book (GET /v1/markets/{slug}/book)

Returns `marketData` with `bids[]`, `offers[]` (each with `px` Amount and
`qty`), `state` enum, and `stats` including `lastTradePx`, `openPx`, `highPx`,
`lowPx`, `closePx`, `settlementPx`, `currentPx`, `indicativeOpenPx` (all
Amount), `sharesTraded`, `notionalTraded`, `lastTradeQty`, `openInterest`
(source: polymarket-us-api-market-object.md).

Market states: OPEN, PREOPEN, SUSPENDED, HALTED, EXPIRED, TERMINATED,
MATCH_AND_CLOSE_AUCTION (source: polymarket-us-api-market-object.md).

## BBO (GET /v1/markets/{slug}/bbo)

Lightweight: `currentPx`, `lastTradePx`, `bestBid`, `bestAsk` (Amount),
`bidDepth`, `askDepth` (integer), `sharesTraded`, `openInterest`,
`settlementPx` (source: polymarket-us-api-market-object.md).

## Settlement (GET /v1/markets/{slug}/settlement)

Returns `{slug, settlement}` — 0.00 (No) or 1.00 (Yes) (source:
polymarket-us-api-market-object.md).

## Query Parameters for GET /v1/markets

Pagination: `limit`, `offset`, `orderBy` (multi-field), `orderDirection`.
Status: `active`, `closed`, `archived`. Categories: `categories[]`,
`marketTypes[]`, `sportsMarketTypes[]`, `tagId`, `relatedTags`, `includeTag`,
`cyom`. IDs: `id[]`, `slug[]`, `questionIds[]`, `gameId`. Volume:
`volumeNumMin/Max`, `liquidityNumMin/Max`, `rewardsMinSize`. Dates (ISO 8601):
`startDateMin/Max`, `endDateMin/Max` (source: polymarket-us-api-market-object.md).

## Events → Markets

Events contain a `markets` array of Market objects. An event is the container;
markets are the individual tradeable contracts within it (source:
polymarket-us-api-events-overview.md).

## Comparison with [[kalshi-market-object]]

Both return binary contract metadata with pricing, volume, and status fields
(source: polymarket-us-api-market-object.md, kalshi-api-market-data-endpoints.md).
Polymarket US uses `slug` as the primary human-readable key (source:
polymarket-us-api-market-object.md); Kalshi uses `ticker` (source:
kalshi-api-market-data-endpoints.md). Polymarket US has `marketSides` for
outcome representation (source: polymarket-us-api-market-object.md); Kalshi
uses `yes_sub_title`/`no_sub_title` (source:
kalshi-api-market-data-endpoints.md). Polymarket US includes sports-specific
fields (`gameId`, `line`, `sportsMarketType`) (source:
polymarket-us-api-market-object.md) that Kalshi does not.

## Related pages

- [[polymarket-us-api]] — full API reference
- [[polymarket-us-historical-data]] — trade history endpoints
