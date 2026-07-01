# MLB Stats API — Sports, Leagues & Divisions

Organizational hierarchy: sports → leagues → divisions.

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /sports` | All sports tracked (MLB, MiLB levels, international) |
| `GET /sports/{sportId}` | Single sport |
| `GET /leagues` | All leagues |
| `GET /leagues/{leagueId}` | Single league |
| `GET /divisions` | All divisions |
| `GET /divisions/{divisionId}` | Single division |

All accept optional `fields` parameter. `/leagues` and `/divisions` accept
`sportId`, `leagueId`, `season`. (source: mlb-stats-api-sports-leagues.md)

## Sport IDs

| ID | Sport |
|----|-------|
| 1 | Major League Baseball |
| 11 | Triple-A |
| 12 | Double-A |
| 13 | High-A |
| 14 | Single-A |
| 16 | Rookie |

Additional IDs exist for Winter Leagues, international leagues, college, and
amateur/independent baseball. (source: mlb-stats-api-sports-leagues.md)

## League IDs

| ID | League |
|----|--------|
| 103 | American League |
| 104 | National League |

(source: mlb-stats-api-sports-leagues.md)

## Division IDs

| ID | Division |
|----|----------|
| 200 | AL West |
| 201 | AL East |
| 202 | AL Central |
| 203 | NL West |
| 204 | NL East |
| 205 | NL Central |

(source: mlb-stats-api-sports-leagues.md)

See also: [[mlb-stats-api]], [[mlb-team-ids]]
