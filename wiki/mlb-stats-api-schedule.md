# MLB Stats API — Schedule

Retrieves games filtered by date, team, league, or sport.

## Endpoint

`GET /schedule` (also available as `GET /schedule/games`, identical behavior)

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `sportId` | no | 1 = MLB |
| `date` | no | Single date (YYYY-MM-DD) |
| `startDate` | no | Range start |
| `endDate` | no | Range end |
| `teamId` | no | Filter to one team |
| `leagueId` | no | Filter to one league |
| `season` | no | Season year |
| `gamePk` | no | Filter to one game |
| `gameType` | no | Game type code (R, S, F, D, L, W, etc.) |
| `hydrate` | no | e.g. `team,linescore,probablePitcher` |
| `fields` | no | Selective response fields |

## Examples

```bash
# All MLB games on a date
curl "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2025-04-01"

# Team schedule for a month
curl "https://statsapi.mlb.com/api/v1/schedule?teamId=119&startDate=2025-04-01&endDate=2025-04-30"

# With hydrated linescore and probable pitchers
curl "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2025-04-01&hydrate=team,linescore,probablePitcher"

# Postseason games
curl "https://statsapi.mlb.com/api/v1/schedule?sportId=1&season=2025&gameType=P"
```

(source: mlb-stats-api-schedule.md; the `/schedule/games` alias from
mlb-stats-api-public-docs-readme.md)

## Response

Top-level keys: `copyright`, `totalItems`, `totalEvents`, `totalGames`,
`totalGamesInProgress`, `dates`.

Each date contains a `games` array. Key game fields:

| Field | Description |
|-------|-------------|
| `gamePk` | Unique game identifier |
| `gameDate` | UTC timestamp |
| `officialDate` | Local date |
| `status.abstractGameState` | e.g. "Final", "Live", "Preview" |
| `status.detailedState` | e.g. "Final", "In Progress" |
| `status.codedGameState` | S, P, I, F, D, U, T, O |
| `teams.away` / `teams.home` | Team info with `score` |
| `venue` | Venue object |
| `gameType` | R, S, F, D, L, W, etc. |
| `doubleHeader` | Y/N |
| `seriesDescription` | e.g. "Regular Season" |

(source: mlb-stats-api-schedule.md)

## Game Type Codes

| Code | Meaning |
|------|---------|
| S | Spring Training |
| E | Exhibition |
| R | Regular Season |
| F | Wild Card |
| D | Division Series |
| L | League Championship |
| W | World Series |
| C | Championship |
| N | Nineteenth Century |
| A | All-Star Game |
| P | All Postseason |

(source: mlb-stats-api-schedule.md; code A from mlb-stats-api-reference.md)

## Coded Game States

| Code | Meaning |
|------|---------|
| S | Scheduled |
| P | Pre-Game |
| I | In Progress |
| F | Final |
| D | Delayed |
| U | Suspended |
| T | Tied |
| O | Game Over |

(source: mlb-stats-api-schedule.md)

## Postseason Schedule

`GET /schedule/postseason` returns the postseason bracket.
`GET /schedule/postseason/series` returns series breakdowns.
Both accept `season` and `sportId` parameters.
(source: mlb-stats-api-reference.md)

See also: [[mlb-stats-api]], [[mlb-stats-api-game]]
