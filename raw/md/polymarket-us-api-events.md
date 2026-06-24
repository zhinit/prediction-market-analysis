# Polymarket US Events API

Source: https://docs.polymarket.us/api-reference/events/overview
Fetched: 2026-06-24

## Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/v1/events` | Get all events with filtering |
| GET | `/v1/events/{id}` | Get event by ID |
| GET | `/v1/events/slug/{slug}` | Get event by slug |
| GET | `/v1/partners/{partnerKey}/events/{externalId}` | Partner-specific events |

## Event Attributes

- `id`, `slug`, `title`, `description`
- `category`, `subcategory`
- Status flags: `active`, `closed`, `archived`

### Sports-Specific
- `gameId`, `sportradarGameId`
- `score`, `period`
- `live`, `ended`
- `eventState`
- `participants`

### Trading Metrics
- `liquidity`
- `volume`, `volume24hr`, `volume1wk`, `volume1mo`

## Filtering

- Status: active, closed, archived, featured, ended, live
- Categories: array of category strings
- Series: `seriesId` array
- Game: `gameId` integer
- Temporal: `startDateMin`, `startDateMax`, `startTimeMin`, `startTimeMax`, `eventDate`, `eventWeek`

## Example

```
GET /v1/events?active=true&categories=sports&limit=50
```
