# MLB Stats API

Free, public, unauthenticated JSON API that powers MLB.com and the MLB app.
Community-documented; MLB provides no official public docs.

## Base URL

```
https://statsapi.mlb.com/api/v1/
```

Only `/api/v1/` is active. v2 and v3 return 404. (source: mlb-stats-api-public-docs-readme.md)

## Authentication

None. No API key, token, or header required for any endpoint.
(source: mlb-stats-api-public-docs-readme.md)

## Rate Limits

No official rate limits are published. The docs recommend implementing caching
and backoff strategies. CORS is not enforced, so browser requests work without
a proxy. (source: mlb-stats-api-public-docs-readme.md)

## Endpoint Categories

| Category | Endpoint(s) | Details |
|----------|-------------|---------|
| Sports & Leagues | `/sports`, `/leagues`, `/divisions` | [[mlb-stats-api-sports-leagues]] |
| Teams | `/teams`, `/teams/{id}/roster`, `/teams/{id}/stats` | [[mlb-stats-api-teams]] |
| Schedule | `/schedule` | [[mlb-stats-api-schedule]] |
| Standings | `/standings` | [[mlb-stats-api-standings]] |
| Players | `/people/{id}`, `/people/{id}/stats`, `/people/search` | [[mlb-stats-api-people]] |
| Game Data | `/game/{gamePk}/feed/live`, `/game/{gamePk}/boxscore`, etc. | [[mlb-stats-api-game]] |
| Venues | `/venues`, `/venues/{id}` | [[mlb-stats-api-venues]] |
| Draft | `/draft/{year}` | [[mlb-stats-api-draft]] |
| Transactions | `/transactions` | [[mlb-stats-api-transactions]] |
| Stats & Leaders | `/stats/leaders`, `/stats/streaks` | [[mlb-stats-api-stats]] |
| Reference | `/positions`, `/gameTypes`, `/awards`, `/attendance` | [[mlb-stats-api-reference]] |
| Seasons | `/seasons`, `/seasons/{id}` | [[mlb-stats-api-seasons]] |
| Game Pace | `/gamePace`, `/highLow/{orgType}` | [[mlb-stats-api-gamepace]] |

## Universal Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `sportId` | int | 1=MLB, 11=AAA, 12=AA, 13=A+, 14=A, 16=ROK |
| `leagueId` | int | 103=AL, 104=NL |
| `season` | int | Season year |
| `teamId` | int | MLB team ID (see [[mlb-team-ids]]) |
| `gamePk` | int | Unique game primary key |
| `personId` | int | MLB player ID |
| `date` | string | YYYY-MM-DD |
| `startDate` / `endDate` | string | YYYY-MM-DD range |
| `hydrate` | string | Comma-separated sub-resources to embed |
| `fields` | string | Comma-separated fields to include in response |
| `limit` / `offset` | int | Pagination |

(source: mlb-stats-api-public-docs-readme.md)

## Hydrate Pattern

The `hydrate` parameter embeds nested sub-resources in a single request,
reducing round-trips. Common values:

- `team` — full team object
- `person` — full person object
- `venue`, `league`, `division` — organizational objects
- `linescore` — inning-by-inning scoring in schedule responses
- `probablePitcher` — probable pitcher in schedule responses
- `stats(group=[hitting],type=[season])` — inline statistics
- `location,fieldInfo` — venue coordinates and field dimensions

(source: mlb-stats-api-public-docs-readme.md)

## Response Structure

All responses follow a consistent shape:

```json
{
  "copyright": "Copyright 2025 MLB Advanced Media, L.P. ...",
  "<data_key>": [ ... ]
}
```

The data key matches the resource name (e.g., `teams`, `people`, `dates`,
`records`). (source: mlb-stats-api-public-docs-readme.md)

## Source

Community documentation by pseudo-r (MIT license):
https://github.com/pseudo-r/Public-MLB-API
(source: mlb-stats-api-public-docs-readme.md)
