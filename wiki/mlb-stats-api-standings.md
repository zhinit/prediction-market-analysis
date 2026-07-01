# MLB Stats API — Standings

Division standings for the American and National Leagues.

## Endpoint

`GET /standings`

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `leagueId` | yes | 103=AL, 104=NL (comma-separated for both) |
| `season` | yes | Season year |
| `standingsTypes` | no | Type of standings (see below) |
| `date` | no | Historical standings as of date (YYYY-MM-DD) |
| `hydrate` | no | e.g. `team,league,division` |
| `fields` | no | Selective response fields |

## Examples

```bash
# Current AL + NL regular season standings
curl "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2025&standingsTypes=regularSeason"

# Historical standings as of July 4
curl "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2025&standingsTypes=regularSeason&date=2025-07-04"

# With team and division details hydrated
curl "https://statsapi.mlb.com/api/v1/standings?leagueId=103&season=2025&standingsTypes=regularSeason&hydrate=team,division"
```

## Standings Types

| Value | Description |
|-------|-------------|
| `regularSeason` | Standard regular season |
| `wildCard` | Wild card standings |
| `divisionLeaders` | Division leader standings |
| `firstHalf` / `secondHalf` | Split-season standings |
| `springTraining` | Spring training |
| `postseason` | Postseason standings |
| `byLeague` / `byDivision` | League/division-level views |

(source: mlb-stats-api-standings.md)

## Response

Top-level keys: `copyright`, `records`.

The `records` array has one entry per division, each containing:

```json
{
  "standingsType": "regularSeason",
  "league": { "id": 103, "name": "American League" },
  "division": { "id": 200, "name": "AL West" },
  "teamRecords": [ ... ]
}
```

(source: mlb-stats-api-standings.md)

## Team Record Fields

| Field | Description |
|-------|-------------|
| `team` | Team name and ID |
| `wins` / `losses` / `ties` | Record |
| `winningPercentage` | String, e.g. `".603"` |
| `gamesBack` | Games behind first place |
| `wildCardGamesBack` | WC games behind |
| `divisionRank` | Position in division |
| `leagueRank` | Overall league rank |
| `wildCardRank` | Wild card rank |
| `sportRank` | Overall MLB rank |
| `streak` | e.g. `{ "streakCode": "W4" }` |
| `clinched` | Boolean |
| `eliminationNumber` | Games until eliminated |
| `magicNumber` | Games until clinching |
| `runsScored` / `runsAllowed` | Run totals |
| `runDifferential` | RS - RA |
| `leagueRecord` | `{ wins, losses, pct }` |
| `divisionRecord` | `{ wins, losses, pct }` |

(source: mlb-stats-api-standings.md)

## Split Records

Each team record includes `records.splitRecords[]` with type-specific W/L/pct:

`home`, `away`, `lastTen`, `extraInning`, `oneRun`, `winners`, `day`,
`night`, `grassSurface`, `artificialTurf`.

(source: mlb-stats-api-standings.md)

See also: [[mlb-stats-api]], [[mlb-team-ids]]
