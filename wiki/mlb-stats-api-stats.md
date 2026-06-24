# MLB Stats API — Stats & Leaders

Aggregated statistics, leaderboards, and active streaks.

## Endpoints

| Endpoint | Status | Description |
|----------|--------|-------------|
| `GET /stats/leaders` | verified | Statistical leaderboards |
| `GET /stats` | partial | Aggregated cross-player stats |
| `GET /stats/streaks` | partial | Active streaks |

(source: mlb-stats-api-stats.md)

## Statistical Leaders

Required parameters:
- `leaderCategories` — stat category to rank
- `season` — season year

Optional: `sportId`, `leagueId`, `teamId`, `statGroup`, `gameType`, `limit`,
`offset`, `position`.

```bash
# Home run leaders
curl "https://statsapi.mlb.com/api/v1/stats/leaders?leaderCategories=homeRuns&season=2025&sportId=1"

# ERA leaders, top 10
curl "https://statsapi.mlb.com/api/v1/stats/leaders?leaderCategories=era&season=2025&sportId=1&limit=10"

# AL-only batting average leaders
curl "https://statsapi.mlb.com/api/v1/stats/leaders?leaderCategories=battingAverage&season=2025&leagueId=103&limit=10"
```

Response keys: `copyright`, `leagueLeaders`. Each leader entry has `rank`,
`value`, `team`, `league`, `person`.

(source: mlb-stats-api-stats.md)

## Available Leader Categories

**Hitting:** `battingAverage`, `onBasePercentage`, `slugging`,
`onBasePlusSlugging`, `hits`, `homeRuns`, `doubles`, `triples`, `totalBases`,
`rbi`, `runs`, `stolenBases`, `walks`, `strikeouts`, `groundIntoDoublePlay`,
`atBats`, `plateAppearances`, `sacBunts`, `sacFlies`, `hitByPitch`,
`intentionalWalks`.

**Pitching:** `era`, `wins`, `losses`, `saves`, `holds`, `blownSaves`,
`strikeouts`, `walks`, `whip`, `inningsPitched`, `earnedRuns`, `homeRuns`,
`shutouts`, `completeGames`, `strikeoutsPer9Inn`, `walksPer9Inn`,
`strikeoutWalkRatio`, `hitsPer9Inn`, `saveOpportunities`.

(source: mlb-stats-api-stats.md)

## Stats Aggregates

Required: `stats` (`season`/`career`/`yearByYear`), `group`
(`hitting`/`pitching`/`fielding`).

Optional: `season`, `teamId`, `playerPool` (`All`/`Qualified`/`Rookies`),
`position`, `limit`, `offset`, `sortStat`, `order` (`asc`/`desc`).

```bash
# Qualified hitters by OPS, descending
curl "https://statsapi.mlb.com/api/v1/stats?stats=season&group=hitting&season=2025&playerPool=Qualified&sortStat=onBasePlusSlugging&order=desc"

# Qualified pitchers by ERA, ascending
curl "https://statsapi.mlb.com/api/v1/stats?stats=season&group=pitching&season=2025&playerPool=Qualified&sortStat=era&order=asc"
```

(source: mlb-stats-api-stats.md)

## Active Streaks

Required: `streakType` (`hitting`, `onBase`, `wins`, `saves`).

Optional: `streakSpan` (`career`/`season`), `season`, `sportId`, `limit`.

```bash
curl "https://statsapi.mlb.com/api/v1/stats/streaks?streakType=hitting&streakSpan=season&season=2025&sportId=1"
```

(source: mlb-stats-api-stats.md)

See also: [[mlb-stats-api]], [[mlb-stats-api-people]]
