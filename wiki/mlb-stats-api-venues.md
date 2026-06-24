# MLB Stats API — Venues

Stadium details including location, field dimensions, and capacity.

## Endpoints

| Endpoint | Status | Description |
|----------|--------|-------------|
| `GET /venues` | verified | All venues |
| `GET /venues/{venueId}` | verified | Single venue |

Parameters: `sportId`, `season`, `hydrate` (`location`, `fieldInfo`,
`timezone`), `fields`.

(source: mlb-stats-api-venues.md)

## Examples

```bash
# All MLB venues
curl "https://statsapi.mlb.com/api/v1/venues?sportId=1"

# Dodger Stadium with location and field info
curl "https://statsapi.mlb.com/api/v1/venues/22?hydrate=location,fieldInfo,timezone"
```

## Key Fields

| Field | Description |
|-------|-------------|
| `id` | Venue ID |
| `name` | Venue name |
| `active` | Boolean |
| `location.city` | City |
| `location.state` | State |
| `location.latitude` / `longitude` | Coordinates |
| `timeZone.id` | IANA timezone |
| `fieldInfo.capacity` | Seating capacity |
| `fieldInfo.turfType` | `Grass` or `ArtificialTurf` |
| `fieldInfo.roofType` | `Open`, `Indoor`, `Retractable` |
| `fieldInfo.leftLine` | Left field line (ft) |
| `fieldInfo.leftCenter` | Left-center (ft) |
| `fieldInfo.center` | Center field (ft) |
| `fieldInfo.rightCenter` | Right-center (ft) |
| `fieldInfo.rightLine` | Right field line (ft) |

(source: mlb-stats-api-venues.md)

## Notable Venue IDs

| ID | Venue | Team |
|----|-------|------|
| 22 | Dodger Stadium | LAD |
| 3313 | Yankee Stadium | NYY |
| 3289 | Fenway Park | BOS |
| 2395 | Oracle Park | SF |
| 4705 | Globe Life Field | TEX |
| 680 | Wrigley Field | CHC |
| 4169 | Truist Park | ATL |
| 2392 | Petco Park | SD |
| 2394 | T-Mobile Park | SEA |
| 4140 | loanDepot park | MIA |

(source: mlb-stats-api-venues.md)

See also: [[mlb-stats-api]]
