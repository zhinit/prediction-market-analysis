# pybaseball

Pull current and historical baseball statistics using Python (Statcast, Baseball Reference, FanGraphs).

Source: https://github.com/jldbc/pybaseball/blob/master/README.md
Accessed: 2026-06-24

---

pybaseball is a Python package for baseball data analysis. It scrapes Baseball Reference, Baseball Savant, and FanGraphs so you don't have to.

## Installation

Via pip:
```
pip install pybaseball
```

From source (potentially more recent):
```
git clone https://github.com/jldbc/pybaseball
cd pybaseball
pip install -e .
```

## Data Sources

- Baseball Savant (Statcast pitch-level data)
- FanGraphs (season-level stats, leaderboards)
- Baseball Reference (game logs, standings, WAR)
- Chadwick Bureau (player ID registry)
- Retrosheet (historical game logs, rosters, events)
- Sean Lahman's Baseball Database (comprehensive historical data)

## Core Functions

### Statcast

`statcast(start_dt=[yesterday], end_dt=None, team=None, verbose=True, parallel=True)` — Retrieves pitch-level data from Baseball Savant. One row per pitch. Data from 2008+; some metrics (launch angle) from 2015+. Baseball Savant enforces 30k row limit per query; pybaseball auto-splits larger requests.

- `statcast('2017-07-04')` — single day
- `statcast('2016-08-01', '2016-08-07')` — date range
- `statcast('2016-04-01', '2016-10-30', team='TEX')` — team-filtered

### Player-Specific Statcast

`statcast_pitcher(start_dt, end_dt, player_id)` — pitch-level data for a single pitcher
`statcast_batter(start_dt, end_dt, player_id)` — pitch-level data for a single batter

Player IDs obtained via `playerid_lookup()`.

### Pitching Stats (FanGraphs)

`pitching_stats(start_season, end_season=None, league='all', qual=1, ind=1)` — season-level pitching data from FanGraphs. One row per player per season (ind=1) or aggregated (ind=0).

### Batting Stats (FanGraphs)

`batting_stats(start_season, end_season=None, league='all', qual=1, ind=1)` — season-level batting data from FanGraphs.

### Pitching Stats (Baseball Reference)

`pitching_stats_range(start_dt, end_dt)` — pitching stats over a date range from Baseball Reference.
`pitching_stats_bref(season)` — season-level from Baseball Reference (2008+).

### Batting Stats (Baseball Reference)

`batting_stats_range(start_dt, end_dt)` — batting stats over a date range from Baseball Reference.
`batting_stats_bref(season)` — season-level from Baseball Reference (2008+).

### Schedule and Record

`schedule_and_record(season, team)` — game-by-game results (W/L, score, attendance, pitchers). Team abbreviation required (e.g. "NYY", "PHI").

### Standings

`standings(season)` — division standings. Historical data from 1969+. Returns list of dataframes (one per division).

### Caching

```python
from pybaseball import cache
cache.enable()   # enable caching (disabled by default)
cache.disable()  # disable
cache.purge()    # clear cache
```

Default cache location: `~/.pybaseball/cache`. Supports CSV or Parquet (Parquet default). Cache is parameter-level (same function + same params = cache hit; no subset matching).

## Version and Metadata

- Version: 2.2.7 (Released September 8, 2023)
- License: MIT
- Author: James LeDoux
- Maintainer: Moshe Schorr
- Python: 3.8, 3.9, 3.10, 3.11
- Inspired by Bill Petti's R package baseballr
