# pybaseball — Batting and Pitching Stats

Individual batting and pitching stat functions in [[pybaseball]], covering FanGraphs leaderboards, Baseball Reference season and date-range stats, split stats, and WAR. (source: pybaseball-docs-batting-pitching.md)

## FanGraphs Functions

### batting_stats()

```python
batting_stats(start_season, end_season=None, league='all', qual=None, ind=1,
              split_seasons=False, month='ALL', on_active_roster=False,
              minimum_age=0, maximum_age=100, team='', position='',
              max_results=1000000, stat_columns='ALL')
```

Season-level batting data from FanGraphs. (source: pybaseball-docs-batting-pitching.md)

| Parameter | Type | Description |
|---|---|---|
| `start_season` | int | First season. If no `end_season`, only this season returned. |
| `end_season` | int | Last season. |
| `league` | str | ALL, AL, FL, NL, MNL. Default: ALL |
| `qual` | Optional[int] | Minimum plate appearances. None = FanGraphs qualified default. |
| `ind` | int | Deprecated. Use `split_seasons`. 1 = individual seasons, 0 = aggregate. |
| `split_seasons` | bool | True = one row per player per season, False = aggregate. Default: False |
| `month` | str | Filter by month. 'ALL' = no filter. |
| `on_active_roster` | bool | Active roster only. Default: False |
| `minimum_age` | int | Default: 0 |
| `maximum_age` | int | Default: 100 |
| `team` | str | Filter by team. "0,ts" for aggregate team data. |
| `position` | str | Filter by position. Default: ALL |
| `max_results` | int | Default: 1000000 (effectively all) |
| `stat_columns` | str or List[str] | Columns to return. Default: ALL |

Some modern stats (contact %, zone %, etc.) are not available before certain historical dates. (source: pybaseball-docs-batting-pitching.md)

```python
from pybaseball import batting_stats

data = batting_stats(2017)                    # single season
data = batting_stats(2017, qual=50)           # min 50 PA
data = batting_stats(2010, 2016)              # per-season rows
data = batting_stats(2010, 2016, ind=0)       # aggregated
```

### pitching_stats()

```python
pitching_stats(start_season, end_season=None, league='all', qual=None, ind=1,
               split_seasons=False, month='ALL', on_active_roster=False,
               minimum_age=0, maximum_age=100, team='', position='',
               max_results=1000000, stat_columns='ALL')
```

Season-level pitching data from FanGraphs. Same parameters as `batting_stats()`. (source: pybaseball-docs-batting-pitching.md)

```python
from pybaseball import pitching_stats

data = pitching_stats(2017)
data = pitching_stats(2017, qual=50)
data = pitching_stats(2010, 2016)
data = pitching_stats(2010, 2016, ind=0)
```

## Baseball Reference Functions

### batting_stats_bref() / pitching_stats_bref()

```python
batting_stats_bref(season)
pitching_stats_bref(season)
```

Season-level stats from Baseball Reference. Data available from 2008 to present only. Defaults to current calendar year if no season provided. For historical data, use the FanGraphs functions instead. (source: pybaseball-docs-batting-pitching.md)

```python
from pybaseball import batting_stats_bref, pitching_stats_bref

data = batting_stats_bref(2009)
data = pitching_stats_bref(2009)
```

### batting_stats_range() / pitching_stats_range()

```python
batting_stats_range(start_dt, end_dt=None)
pitching_stats_range(start_dt, end_dt=None)
```

Stats from Baseball Reference aggregated over a date range. Dates in "YYYY-MM-DD" format. If `end_dt` omitted, returns only `start_dt` data. (source: pybaseball-docs-batting-pitching.md)

```python
from pybaseball import batting_stats_range, pitching_stats_range

data = batting_stats_range("2017-05-01", "2017-05-28")
data = pitching_stats_range("2016-08-24")
```

## Split Stats

### get_splits()

```python
get_splits(playerid, year=None, player_info=False, pitching_splits=False)
```

Split stats from Baseball Reference. Returns a multi-index DataFrame by split category and split. (source: pybaseball-docs-batting-pitching.md)

- `playerid` — Baseball Reference player ID string (e.g. 'troutmi01')
- `year` — optional year for season splits; omit for career splits
- `player_info` — if True, returns both the splits DataFrame and a dictionary with position, handedness, height, weight, team
- `pitching_splits` — if True, returns pitching splits instead of batting

```python
from pybaseball import get_splits

df = get_splits('troutmi01')
df, player_info_dict = get_splits('troutmi01', player_info=True)
df = get_splits('lestejo01', pitching_splits=True)
```

## WAR

### bwar_bat() / bwar_pitch()

```python
bwar_bat(return_all=False)
bwar_pitch(return_all=False)
```

Baseball Reference WAR from the `war_daily_bat` and `war_daily_pitch` tables. `return_all=True` returns all fields; `return_all=False` (default) returns a subset of commonly used columns. (source: pybaseball-docs-batting-pitching.md)

```python
from pybaseball import bwar_bat, bwar_pitch

data = bwar_bat()
data = bwar_pitch(return_all=True)
```
