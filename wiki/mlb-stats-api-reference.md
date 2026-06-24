# MLB Stats API — Reference Endpoints

Lightweight endpoints returning static or semi-static lookup data.

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /positions` | All position codes and types |
| `GET /gameTypes` | Game type codes (R, S, F, D, L, W, etc.) |
| `GET /awards` | Awards list (MVP, Cy Young, etc.) |
| `GET /awards/{awardId}/recipients` | Award winners by year |
| `GET /attendance` | Team/league attendance records |
| `GET /jobs` | Umpire crew assignments |
| `GET /schedule/postseason` | Postseason bracket |
| `GET /schedule/postseason/series` | Postseason series breakdown |

(source: mlb-stats-api-reference.md)

## Awards

Parameters for `/awards`: `sportId`, `leagueId`.
Parameters for `/awards/{awardId}/recipients`: `season`.

Notable award IDs: `MLBMVP`, `MLBCY`, `MLBROY`, `MLBGOLD`, `MLBSILVER`,
`MLBHANK`, `MLBALL`.

```bash
curl "https://statsapi.mlb.com/api/v1/awards/MLBCY/recipients?season=2024"
```

## Attendance

Parameters: `teamId`, `leagueId`, `season`, `date`, `gameType`, `fields`.

```bash
curl "https://statsapi.mlb.com/api/v1/attendance?teamId=119&season=2024&gameType=R"
```

## Umpire Assignments

Parameters: `jobType` (use `UMP`), `sportId`, `date`.

```bash
curl "https://statsapi.mlb.com/api/v1/jobs?jobType=UMP&sportId=1&date=2025-04-15"
```

(source: mlb-stats-api-reference.md)

See also: [[mlb-stats-api]], [[mlb-stats-api-schedule]]
