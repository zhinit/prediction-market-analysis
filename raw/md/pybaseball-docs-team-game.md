# pybaseball Team and Game Data Documentation

Documentation for team stats, game data, and standings functions in the pybaseball Python library.

Source: https://github.com/jldbc/pybaseball/tree/master/docs (team_batting.md, team_pitching.md, team_fielding.md, team_batting_bref.md, team_pitching_bref.md, team_fielding_bref.md, schedule_and_record.md, team_game_logs.md, standings.md, teamid_lookup.md)
Accessed: 2026-06-24

---

## FanGraphs Team Functions

### team_batting()

`team_batting(start_season, end_season=None, league='all', ind=1)`

Returns a dataframe of team-level batting stats.

- `start_season`: Integer. First season.
- `end_season`: Integer. Optional. Last season.
- `league`: "all", "nl", "al", or "mnl". Default: "all".
- `ind`: 1 = one row per team per year, 0 = aggregate across seasons. Default: 1.

```python
from pybaseball import team_batting

data = team_batting(2010, 2013)
data = team_batting(2010, 2013, ind=0)
data = team_batting(1999)
```

### team_pitching()

`team_pitching(start_season, end_season=None, league='all', ind=1)`

Returns a dataframe of team-level pitching stats.

- `start_season`: Integer. First season.
- `end_season`: Integer. Optional. Last season.
- `league`: "all", "nl", "al", or "mnl". Default: "all".
- `ind`: 1 = one row per team per year, 0 = aggregate. Default: 1.

Also available: `team_pitching_starters()` and `team_pitching_relievers()` with the same parameters, filtering to starters and relievers respectively.

```python
from pybaseball import team_pitching

data = team_pitching(2010, 2012, ind=1)  # 90 rows (30 teams x 3 years)
data = team_pitching(2010, 2012, ind=0)  # 30 rows (aggregated)
```

### team_fielding()

`team_fielding(start_season, end_season=None, league='all', ind=1)`

Returns a dataframe of team-level fielding stats.

- `start_season`: Integer. First season.
- `end_season`: Integer. Optional. Last season.
- `league`: "all", "nl", "al", or "mnl". Default: "all".
- `ind`: 1 = one row per team per year, 0 = aggregate. Default: 1.

```python
from pybaseball import team_fielding

data = team_fielding(2010, 2013)
data = team_fielding(2010, 2013, ind=0)
data = team_fielding(1999)
```

---

## Baseball Reference Team Functions

### team_batting_bref()

`team_batting_bref(team, start_season, end_season=None)`

Team-level batting stats for a single team from Baseball Reference.

- `team`: String. Team abbreviation (e.g. "NYY").
- `start_season`: Integer. First season.
- `end_season`: Integer. Optional. Last season.

Includes a 'Year' column. Players on team across multiple years get separate rows per year.

```python
from pybaseball import team_batting_bref

data = team_batting_bref('NYY', 2010, 2013)
data = team_batting_bref('NYY', 1999)
```

### team_pitching_bref()

`team_pitching_bref(team, start_season, end_season=None)`

Team-level pitching stats for a single team from Baseball Reference. Same structure as team_batting_bref.

```python
from pybaseball import team_pitching_bref

data = team_pitching_bref('NYY', 2010, 2013)
data = team_pitching_bref('NYY', 1999)
```

### team_fielding_bref()

`team_fielding_bref(team, start_season, end_season=None)`

Team-level fielding stats for a single team from Baseball Reference. Same structure as team_batting_bref.

```python
from pybaseball import team_fielding_bref

data = team_fielding_bref('NYY', 2010, 2013)
data = team_fielding_bref('NYY', 1999)
```

---

## Game Data

### schedule_and_record()

`schedule_and_record(season, team)`

Returns game-by-game results including win/loss/tie result, score, attendance, and winning/losing/saving pitcher. If the season is incomplete, provides scheduling information for future games.

- `season`: Integer.
- `team`: String. Team abbreviation (e.g. "PHI", "BOS", "LAD").

Note: Historical team name/city changes can cause issues. The Los Angeles Dodgers ("LAD") are abbreviated "BRO" in older seasons (Brooklyn Dodgers).

```python
from pybaseball import schedule_and_record

data = schedule_and_record(1927, "NYY")
data = schedule_and_record(2017, "PHI")
```

### team_game_logs()

`team_game_logs(season, team, log_type="batting")`

Retrieves batting or pitching game logs for a single team-season from Baseball Reference.

- `season`: Year.
- `team`: 3-letter Baseball Reference team abbreviation.
- `log_type`: "batting" (default) or "pitching".

```python
from pybaseball import team_game_logs

batting_logs = team_game_logs(2019, "ATL")
pitching_logs = team_game_logs(2018, "BAL", "pitching")
```

---

## Standings

### standings()

`standings(season)`

Get division standings for a given season. Data exists from 1969 to present (when divisions were introduced). Returns a list of dataframes, one per division (6 total).

- `season`: Integer. Defaults to current calendar year.

```python
from pybaseball import standings

data = standings()
data = standings(1980)
```

---

## Team ID Lookup

### team_ids()

`team_ids(season=None, league='ALL')`

Returns a mapping dataframe to map FanGraphs, Retrosheet, Baseball Reference, and Lahman team data.

- `season`: Optional integer. If omitted, returns data across all seasons.
- `league`: Optional string. Default: 'ALL'.

```python
from pybaseball import team_ids, team_batting

teams = team_ids(2019)
batting = team_batting(2019).add_prefix('batting.')
teams.merge(batting, left_on=['yearID', 'teamIDfg'], right_on=['batting.Season', 'batting.teamIDfg'])
```
