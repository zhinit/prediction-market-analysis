# MLB Stats API — People (Players)

Player profiles, statistics, game logs, and search.

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /people/{personId}` | Player profile |
| `GET /people/{personId}/stats` | Player statistics |
| `GET /people/{personId}/currentGameStats` | Live game stats |
| `GET /people/{personId}/gameLog` | Game log |
| `GET /people/search` | Search by name |
| `GET /people` | Bulk lookup (comma-separated `personIds`) |
| `GET /people/changes` | Players whose data changed since timestamp |
| `GET /people/freeAgents` | Current free agents |
| `GET /sports/{sportId}/players` | All players for a sport |

(source: mlb-stats-api-people.md)

## Player Profile

```bash
curl "https://statsapi.mlb.com/api/v1/people/660271"
```

Key fields: `id`, `fullName`, `firstName`, `lastName`, `primaryNumber`,
`currentTeam`, `primaryPosition`, `batSide`, `pitchHand`, `birthDate`,
`birthCity`, `birthCountry`, `height`, `weight`, `active`, `mlbDebutDate`.

(source: mlb-stats-api-public-docs-readme.md)

## Player Stats

Parameters:
- `stats` (required): `season`, `career`, `yearByYear`, `gameLog`
- `group` (required): `hitting`, `pitching`, `fielding`, `catching`, `running`
- `season` (optional): season year
- `gameType` (optional): game type filter
- `sitCodes` (optional): situational splits

```bash
# Season hitting stats
curl "https://statsapi.mlb.com/api/v1/people/660271/stats?stats=season&group=hitting&season=2024"

# Career pitching stats
curl "https://statsapi.mlb.com/api/v1/people/660271/stats?stats=career&group=pitching"

# Year-by-year hitting
curl "https://statsapi.mlb.com/api/v1/people/660271/stats?stats=yearByYear&group=hitting"
```

(source: mlb-stats-api-people.md)

## Player Search

```bash
curl "https://statsapi.mlb.com/api/v1/people/search?names=Ohtani"
```

Optional filters: `active` (boolean), `sportIds`.

(source: mlb-stats-api-public-docs-readme.md)

See also: [[mlb-stats-api]], [[mlb-stats-api-stats]]
