# MLB Stats API — Draft

MLB Draft results and live draft tracking.

## Endpoints

| Endpoint | Status | Description |
|----------|--------|-------------|
| `GET /draft/{year}` | verified | Full draft results |
| `GET /draft/{year}/latest` | unverified | Latest pick during active draft |

Parameters for `/draft/{year}`: `teamId`, `round`, `limit`, `fields`.

(source: mlb-stats-api-draft.md)

## Examples

```bash
# 2024 full draft
curl "https://statsapi.mlb.com/api/v1/draft/2024"

# First round only
curl "https://statsapi.mlb.com/api/v1/draft/2024?round=1"

# Team-specific picks
curl "https://statsapi.mlb.com/api/v1/draft/2024?teamId=119"
```

## Pick Fields

| Field | Description |
|-------|-------------|
| `pickRound` | Round number |
| `pickNumber` | Overall pick number |
| `roundPickNumber` | Pick within round |
| `rank` | Pre-draft ranking |
| `pickType` | "Competitive", "Compensatory", etc. |
| `team` | `{ id, name }` |
| `person` | `{ id, fullName }` |
| `school` | `{ name, schoolType, country }` |
| `position` | `{ code, name, abbreviation }` |
| `signingBonus` | USD amount |
| `headshotLink` | URL to headshot |
| `isPass` | Boolean — team passed |

(source: mlb-stats-api-draft.md)

See also: [[mlb-stats-api]]
