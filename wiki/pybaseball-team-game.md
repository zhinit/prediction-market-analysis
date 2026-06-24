# pybaseball — Team Stats, Game Data, Standings

Team-level stats, game logs, standings, and team ID lookup functions in [[pybaseball]]. (source: pybaseball-docs-team-game.md)

## FanGraphs Team Functions

### team_batting()

```python
team_batting(start_season, end_season=None, league='all', ind=1)
```

Team-level batting stats from FanGraphs. (source: pybaseball-docs-team-game.md)

- `start_season` — first season
- `end_season` — optional last season
- `league` — "all", "nl", "al", or "mnl". Default: "all"
- `ind` — 1 = one row per team per year, 0 = aggregate across seasons. Default: 1

```python
from pybaseball import team_batting

data = team_batting(2010, 2013)           # per-year rows
data = team_batting(2010, 2013, ind=0)    # aggregated
data = team_batting(1999)                 # single season
```

### team_pitching()

```python
team_pitching(start_season, end_season=None, league='all', ind=1)
```

Team-level pitching stats. Same parameters as `team_batting()`. With `ind=1`, a 3-season query returns 90 rows (30 teams x 3 years); with `ind=0`, 30 rows. (source: pybaseball-docs-team-game.md)

Also available with the same parameters:
- `team_pitching_starters()` — starters only
- `team_pitching_relievers()` — relievers only

### team_fielding()

```python
team_fielding(start_season, end_season=None, league='all', ind=1)
```

Team-level fielding stats. Same parameters as `team_batting()`. (source: pybaseball-docs-team-game.md)

## Baseball Reference Team Functions

These functions query a single team at a time, unlike the FanGraphs functions which return all teams. Each includes a 'Year' column for multi-season queries. Players appearing across multiple years get separate rows per year. (source: pybaseball-docs-team-game.md)

### team_batting_bref()

```python
team_batting_bref(team, start_season, end_season=None)
```

- `team` — team abbreviation (e.g. "NYY")
- `start_season` / `end_season` — season range

### team_pitching_bref()

```python
team_pitching_bref(team, start_season, end_season=None)
```

Same structure as `team_batting_bref()`.

### team_fielding_bref()

```python
team_fielding_bref(team, start_season, end_season=None)
```

Same structure as `team_batting_bref()`.

```python
from pybaseball import team_batting_bref, team_pitching_bref, team_fielding_bref

data = team_batting_bref('NYY', 2010, 2013)
data = team_pitching_bref('NYY', 1999)
data = team_fielding_bref('NYY', 2010, 2013)
```

## Game Data

### schedule_and_record()

```python
schedule_and_record(season, team)
```

Game-by-game results for a team-season: win/loss/tie, score, attendance, winning/losing/saving pitcher. If the season is incomplete, provides scheduling information for future games. (source: pybaseball-docs-team-game.md)

- `season` — integer
- `team` — team abbreviation (e.g. "PHI", "BOS", "LAD")

Historical team name/city changes can cause issues. The Los Angeles Dodgers ("LAD") are abbreviated "BRO" in older seasons (Brooklyn Dodgers origin). (source: pybaseball-docs-team-game.md)

```python
from pybaseball import schedule_and_record

data = schedule_and_record(1927, "NYY")
data = schedule_and_record(2017, "PHI")
```

### team_game_logs()

```python
team_game_logs(season, team, log_type="batting")
```

Batting or pitching game logs for a single team-season from Baseball Reference. (source: pybaseball-docs-team-game.md)

- `season` — year
- `team` — 3-letter Baseball Reference abbreviation
- `log_type` — "batting" (default) or "pitching"

```python
from pybaseball import team_game_logs

batting_logs = team_game_logs(2019, "ATL")
pitching_logs = team_game_logs(2018, "BAL", "pitching")
```

## Standings

### standings()

```python
standings(season)
```

Division standings. Data from 1969 to present (when divisions were introduced). Returns a list of 6 DataFrames, one per division. Defaults to current calendar year if no season provided. (source: pybaseball-docs-team-game.md)

```python
from pybaseball import standings

data = standings()       # current season
data = standings(1980)   # historical
```

## Team ID Lookup

### team_ids()

```python
team_ids(season=None, league='ALL')
```

Cross-reference mapping DataFrame for FanGraphs, Retrosheet, Baseball Reference, and Lahman team IDs. If season is omitted, returns data across all seasons. (source: pybaseball-docs-team-game.md)

```python
from pybaseball import team_ids, team_batting

teams = team_ids(2019)
batting = team_batting(2019).add_prefix('batting.')
merged = teams.merge(
    batting,
    left_on=['yearID', 'teamIDfg'],
    right_on=['batting.Season', 'batting.teamIDfg']
)
```
