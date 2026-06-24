# pybaseball Batting and Pitching Stats Documentation

Documentation for individual batting and pitching stat functions in the pybaseball Python library.

Source: https://github.com/jldbc/pybaseball/tree/master/docs (fangraphs.md, batting_stats.md, pitching_stats.md, batting_stats_bref.md, pitching_stats_bref.md, batting_stats_range.md, pitching_stats_range.md, split_stats.md, bwar_bat.md, bwar_pitch.md)
Accessed: 2026-06-24

---

## FanGraphs Functions

### batting_stats()

`batting_stats(start_season, end_season=None, league='all', qual=None, ind=1, split_seasons=False, month='ALL', on_active_roster=False, minimum_age=0, maximum_age=100, team='', position='', max_results=1000000, stat_columns='ALL')`

Returns season-level batting data from FanGraphs.

#### Parameters

| Parameter | Type | Description |
|---|---|---|
| start_season | int | First season to pull data for. If no end_season, only this season returned. |
| end_season | int | Last season to pull data for. |
| league | str | ALL, AL, FL, NL, MNL (see FangraphsLeague). Default: ALL |
| ind | int | DEPRECATED. Use split_seasons. 1 = individual seasons, 0 = aggregate. |
| stat_columns | str or List[str] | Columns to return. Default: ALL |
| qual | Optional[int] | Minimum plate appearances. None = FanGraphs "Qualified" default. |
| split_seasons | bool | True = individual season rows, False = aggregate. Default: False |
| month | str | Filter by month. 'ALL' = no filter. Default: 'ALL' |
| on_active_roster | bool | Only active roster players. Default: False |
| minimum_age | int | Minimum player age. Default: 0 |
| maximum_age | int | Maximum player age. Default: 100 |
| team | str | Filter by team. "0,ts" for aggregate team data. |
| position | str | Filter by position. Default: ALL |
| max_results | int | Maximum results. Default: 1000000 |

#### Data Availability

While this query works for any historical season, some modern stats (contact %, zone %, etc.) will not be available before certain dates.

#### Examples

```python
from pybaseball import batting_stats

data = batting_stats(2017)
data = batting_stats(2017, qual=50)
data = batting_stats(2010, 2016)
data = batting_stats(2010, 2016, ind=0)
```

### pitching_stats()

`pitching_stats(start_season, end_season=None, league='all', qual=None, ind=1, split_seasons=False, month='ALL', on_active_roster=False, minimum_age=0, maximum_age=100, team='', position='', max_results=1000000, stat_columns='ALL')`

Returns season-level pitching data from FanGraphs. Same parameters as batting_stats().

#### Examples

```python
from pybaseball import pitching_stats

data = pitching_stats(2017)
data = pitching_stats(2017, qual=50)
data = pitching_stats(2010, 2016)
data = pitching_stats(2010, 2016, ind=0)
```

---

## Baseball Reference Functions

### batting_stats_bref()

`batting_stats_bref(season)`

Get batting stats from Baseball Reference for a given season.

- `season`: Integer. Defaults to current calendar year if not provided.

Data availability: 2008 to present only. Use batting_stats() for historical data.

```python
from pybaseball import batting_stats_bref

data = batting_stats_bref()
data = batting_stats_bref(2009)
```

### pitching_stats_bref()

`pitching_stats_bref(season)`

Get pitching stats from Baseball Reference for a given season.

- `season`: Integer. Defaults to current calendar year if not provided.

Data availability: 2008 to present only. Use pitching_stats() for historical data.

```python
from pybaseball import pitching_stats_bref

data = pitching_stats_bref()
data = pitching_stats_bref(2009)
```

### batting_stats_range()

`batting_stats_range(start_dt, end_dt=None)`

Batting stats from Baseball Reference aggregated over a date range.

- `start_dt`: String. Format: "YYYY-MM-DD".
- `end_dt`: String. Optional. Format: "YYYY-MM-DD".

```python
from pybaseball import batting_stats_range

data = batting_stats_range("2017-05-01", "2017-05-28")
data = batting_stats_range("2016-08-24")
```

### pitching_stats_range()

`pitching_stats_range(start_dt, end_dt=None)`

Pitching stats from Baseball Reference aggregated over a date range.

- `start_dt`: String. Format: "YYYY-MM-DD".
- `end_dt`: String. Optional. Format: "YYYY-MM-DD".

```python
from pybaseball import pitching_stats_range

data = pitching_stats_range("2017-05-01", "2017-05-28")
data = pitching_stats_range("2016-08-24")
```

---

## Split Stats

### get_splits()

`get_splits(playerid, year=None, player_info=False, pitching_splits=False)`

Look up a player's split stats from Baseball Reference. Returns batting or pitching splits for any season or career. Split stats returned as a multi-index dataframe by split category and split.

- `playerid`: String. The player's bbref playerid (e.g. 'troutmi01').
- `year`: Integer. Optional. Year for split stats. Omit for career splits.
- `player_info`: Boolean. If True, also returns a dictionary of player info (position, handedness, height, weight, team).
- `pitching_splits`: Boolean. If True, returns pitching splits. Otherwise batting splits.

```python
from pybaseball import get_splits

df = get_splits('troutmi01')
df, player_info_dict = get_splits('troutmi01', player_info=True)
df = get_splits('lestejo01', pitching_splits=True)
```

---

## WAR Functions

### bwar_bat()

`bwar_bat(return_all=False)`

Retrieves Baseball Reference's WAR statistics from the `war_daily_bat` table.

- `return_all`: Bool. True = all fields, False = subset of columns. Default: False.

```python
from pybaseball import bwar_bat

data = bwar_bat()
data = bwar_bat(return_all=True)
```

### bwar_pitch()

`bwar_pitch(return_all=False)`

Retrieves Baseball Reference's WAR statistics from the `war_daily_pitch` table.

- `return_all`: Bool. True = all fields, False = subset of columns. Default: False.

```python
from pybaseball import bwar_pitch

data = bwar_pitch()
data = bwar_pitch(return_all=True)
```
