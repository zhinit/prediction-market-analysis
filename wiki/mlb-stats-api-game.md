# MLB Stats API — Game Data

Endpoints for live game feeds, boxscores, linescores, play-by-play, and win
probability. All use the `gamePk` identifier obtained from the schedule endpoint.

## Endpoints

| Endpoint | Status | Description |
|----------|--------|-------------|
| `GET /game/{gamePk}/feed/live` | partial | Full live feed (play-by-play, boxscore, linescore, metadata) |
| `GET /game/{gamePk}/boxscore` | verified | Statistical summary |
| `GET /game/{gamePk}/linescore` | verified | Inning-by-inning scoring |
| `GET /game/{gamePk}/playByPlay` | partial | All discrete play events |
| `GET /game/{gamePk}/winProbability` | partial | Win probability shifts by play |
| `GET /game/{gamePk}/decisions` | partial | W/L/S pitcher decisions |
| `GET /game/{gamePk}/content` | partial | Highlights, editorial, media |

"Verified" means community-tested; "partial" means tested but not all fields
confirmed. (source: mlb-stats-api-game.md)

## Live Feed (`/feed/live`)

The most comprehensive endpoint. Returns nested `gameData` and `liveData`.

**gameData** contains:
- `game` — season, type, ID, doubleheader flag
- `datetime` — game date/time
- `status` — game state (coded states per [[mlb-stats-api-schedule]])
- `teams` — home and away team objects
- `players` — map keyed by `ID{personId}`
- `venue` — full venue details
- `weather` — condition, temp, wind
- `gameInfo` — attendance, first pitch, duration
- `flags` — `noHitter`, `perfectGame`, `awayTeamNoHitter`, `homeTeamNoHitter`
- `probablePitchers` — home and away pitcher links

**liveData** contains:
- `plays` — `currentPlay`, `allPlays[]`, `scoringPlays[]`, `playsByInning[]`
- `linescore` — full inning-by-inning breakdown
- `boxscore` — team and player statistics
- `decisions` — W/L/S pitcher decisions
- `leaders` — in-game stat leaders

Note: `/feed/live` may return 404 for completed historical games. Use
`/boxscore` and `/linescore` for historical data.
(source: mlb-stats-api-game.md)

## Boxscore

Response keys: `copyright`, `teams`, `officials`, `info`, `pitchingNotes`.

Each team side (`teams.away`, `teams.home`) contains:
- `team` — ID and name
- `teamStats` — `batting`, `pitching`, `fielding` aggregates
- `players` — keyed by `ID{personId}`, each with `stats.batting`,
  `stats.pitching`, `stats.fielding`, and `seasonStats`
- `batters`, `pitchers`, `battingOrder`, `bench`, `bullpen` — player ID arrays

(source: mlb-stats-api-game.md)

## Linescore

Response keys: `copyright`, `currentInning`, `currentInningOrdinal`,
`inningState`, `innings`, `teams`, `balls`, `strikes`, `outs`, `offense`,
`defense`.

Each inning entry:
```json
{
  "num": 1,
  "ordinalNum": "1st",
  "home": { "runs": 0, "hits": 1, "errors": 0, "leftOnBase": 1 },
  "away": { "runs": 2, "hits": 3, "errors": 0, "leftOnBase": 2 }
}
```

(source: mlb-stats-api-game.md)

## Play-by-Play

Response keys: `copyright`, `allPlays`, `currentPlay`, `scoringPlays`,
`playsByInning`.

Key play fields:
- `result.event` — "Single", "Strikeout", "Home Run", etc.
- `result.description` — full narrative
- `result.rbi`, `result.awayScore`, `result.homeScore`
- `about.halfInning` — "top" or "bottom"
- `about.inning`, `about.isScoringPlay`, `about.isComplete`
- `count` — balls, strikes, outs
- `matchup` — batter, pitcher, sides
- `runners` — movement and details
- `playEvents` — individual pitch/event records

(source: mlb-stats-api-game.md)

## Win Probability

Returns an array of objects tracking probability shifts:

| Field | Description |
|-------|-------------|
| `atBatIndex` | Play number |
| `homeTeamWinProbability` | Probability (decimal) |
| `awayTeamWinProbability` | Probability (decimal) |
| `homeTeamWinProbabilityAdded` | Change from previous state |

(source: mlb-stats-api-game.md)

## DiffPatch Polling (v1.1)

For efficient live tracking without full refetches:

```bash
# Get available timecodes
curl "https://statsapi.mlb.com/api/v1.1/game/{gamePk}/feed/live/timestamps"

# Get changes between two timecodes
curl "https://statsapi.mlb.com/api/v1.1/game/{gamePk}/feed/live/diffPatch?startTimecode=20250415_001234&endTimecode=20250415_001300"
```

Pattern: fetch timestamps, record latest, wait, request diffPatch with old
and new timecodes. (source: mlb-stats-api-game.md)

## Other Game Endpoints

- `GET /game/{gamePk}/contextMetrics` — current win probability and leverage
  index without full history (lighter than winProbability)
- `GET /game/{gamePk}/feed/color` — color/audio/broadcast metadata
- `GET /game/changes?updatedSince={ISO8601}` — games modified since timestamp
  (useful for database sync)
- `GET /uniforms/game?gamePks={ids}` — uniform specifications
- `GET /people/{personId}/stats/game/{gamePk}` — player stats in a specific game

(source: mlb-stats-api-game.md)

See also: [[mlb-stats-api]], [[mlb-stats-api-schedule]]
