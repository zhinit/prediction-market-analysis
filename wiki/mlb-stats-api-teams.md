# MLB Stats API — Teams

Team listings, rosters, stats, leaders, history, affiliates, and personnel.

## Endpoints

| Endpoint | Status | Description |
|----------|--------|-------------|
| `GET /teams` | verified | All teams (filter by sport/league/season) |
| `GET /teams/{teamId}` | verified | Single team details |
| `GET /teams/{teamId}/roster` | verified | Active roster |
| `GET /teams/{teamId}/stats` | partial | Team statistics |
| `GET /teams/{teamId}/leaders` | partial | Team stat leaders |
| `GET /teams/history` | unverified | Historical names/relocations |
| `GET /teams/affiliates` | unverified | MiLB affiliations |
| `GET /teams/{teamId}/alumni` | unverified | Former players |
| `GET /teams/{teamId}/coaches` | unverified | Coaching staff |
| `GET /teams/{teamId}/personnel` | unverified | Front office |
| `GET /uniforms/team` | unverified | Uniform info |

(source: mlb-stats-api-teams.md)

## Teams List

Parameters: `sportId`, `leagueIds`, `season`, `activeStatus` (Y/N/B),
`hydrate`, `fields`.

```bash
curl "https://statsapi.mlb.com/api/v1/teams?sportId=1"
```

Key fields: `id`, `name`, `teamName`, `locationName`, `shortName`,
`abbreviation`, `teamCode`, `fileCode`, `firstYearOfPlay`, `active`,
`venue`, `league`, `division`, `sport`.

(source: mlb-stats-api-teams.md)

## Roster

Parameters: `rosterType`, `season`, `date`, `hydrate`.

Roster types: `active`, `40Man`, `fullRoster`, `depthChart`, `gameday`.

```bash
curl "https://statsapi.mlb.com/api/v1/teams/119/roster?rosterType=active"
curl "https://statsapi.mlb.com/api/v1/teams/119/roster?rosterType=40Man"
```

Response fields per player: `person` (id, fullName), `jerseyNumber`,
`position` (code, name, abbreviation), `status` (code, description).

(source: mlb-stats-api-teams.md)

## Team Stats

Required: `stats` (`season`/`career`/`yearByYear`), `group`
(`hitting`/`pitching`/`fielding`). Optional: `season`.

```bash
curl "https://statsapi.mlb.com/api/v1/teams/119/stats?stats=season&group=hitting&season=2025"
```

(source: mlb-stats-api-teams.md)

## Team IDs

See [[mlb-team-ids]] for the full table of all 30 MLB team IDs.

See also: [[mlb-stats-api]], [[mlb-stats-api-standings]]
