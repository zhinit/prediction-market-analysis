# MLB Stats API — Game Pace, High-Low, Home Run Derby

## Game Pace

`GET /gamePace` — pace-of-game metrics (average game time, time between
pitches, etc.).

Required: `season`. Optional: `teamIds`, `leagueIds`, `sportId`, `gameType`,
`venueIds`, `orgType`, date ranges.

```bash
curl "https://statsapi.mlb.com/api/v1/gamePace?season=2025&sportId=1"
```

(source: mlb-stats-api-gamepace-highlow.md)

## High-Low Records

`GET /highLow/{orgType}` — single-game or single-season high/low statistical
records.

`orgType` options: `player`, `team`, `division`, `league`, `sport`, `types`.

Required: `sortStat`, `season`. Optional: `statGroup`
(`hitting`/`pitching`/`fielding`), `gameType`, `teamId`, `limit`.

```bash
curl "https://statsapi.mlb.com/api/v1/highLow/player?sortStat=homeRuns&season=2025"
```

(source: mlb-stats-api-gamepace-highlow.md)

## Home Run Derby

`GET /homeRunDerby/{gamePk}` — bracket and pool data. Append `/bracket` or
`/pool` for specific views.

Use the schedule endpoint with `gameType=A` to find the gamePk for Home Run
Derby events. (source: mlb-stats-api-gamepace-highlow.md)

See also: [[mlb-stats-api]]
