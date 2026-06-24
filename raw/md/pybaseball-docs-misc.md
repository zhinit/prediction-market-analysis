# pybaseball Miscellaneous Functions Documentation

Documentation for player lookup, plotting, and draft functions in the pybaseball Python library.

Source: https://github.com/jldbc/pybaseball/tree/master/docs (playerid_lookup.md, playerid_reverse_lookup.md, chadwick_register.md, plotting.md, amateur_draft.md, amateur_draft_by_team.md, top_prospects.md)
Accessed: 2026-06-24

---

## Player ID Lookup

### playerid_lookup()

`playerid_lookup(last, first=None, fuzzy=False)`

Look up a player's MLBAM, Retrosheet, FanGraphs, and Baseball Reference ID by name. Data comes from the Chadwick Bureau. Note that several people in this data are not MLB players.

- `last`: String. Player's last name. Case insensitive.
- `first`: String. Optional. Player's first name. Case insensitive.
- `fuzzy`: Boolean. Optional. If True, returns the 5 closest name matches.

Providing last name only returns all matches (e.g. 1,314 rows for "Jones"). If multiple players share a name, use `mlb_played_first` and `mlb_played_last` fields to distinguish.

```python
from pybaseball import playerid_lookup

data = playerid_lookup('jones')
data = playerid_lookup('jones', 'chipper')
data = playerid_lookup("martinez", "pedro", fuzzy=True)
data = playerid_lookup("molina", "yadi", fuzzy=True)
```

### player_search_list()

`player_search_list(player_list)`

Batch lookup of player IDs by name. Returns a dataframe of all matching players.

- `player_list`: List of tuples `(last, first)`. Case insensitive. Exact match only.

```python
from pybaseball import player_search_list

data = player_search_list([("brock", "lou"), ("jones", "chipper")])
```

### playerid_reverse_lookup()

`playerid_reverse_lookup(player_ids, key_type='mlbam')`

Find names and IDs given a list of player IDs. Data from Chadwick Bureau.

- `player_ids`: List of player IDs.
- `key_type`: ID system: 'mlbam', 'retro', 'bbref', or 'fangraphs'. Default: 'mlbam'.

```python
from pybaseball import playerid_reverse_lookup

data = playerid_reverse_lookup([120074, 519242], key_type='mlbam')
```

### chadwick_register()

`chadwick_register(save=False)`

Retrieves the full Chadwick Bureau player register.

- `save`: Boolean. If True, saves the file to disk.

```python
from pybaseball import chadwick_register

data = chadwick_register()
data = chadwick_register(save=True)
```

---

## Plotting Functions

### plot_stadium()

`plot_stadium(team)`

Plot the outline of a specified team's stadium using MLBAM coordinates.

- `team`: Team name string. Acceptable values: angels, astros, athletics, blue_jays, braves, brewers, cardinals, cubs, diamondbacks, dodgers, generic, giants, indians, mariners, marlins, mets, nationals, orioles, padres, phillies, pirates, rangers, rays, red_sox, reds, rockies, royals, tigers, twins, white_sox, yankees.

### spraychart()

`spraychart(data, team_stadium, title='', tooltips=[], size=100, colorby='events', legend_title='', width=500, height=500)`

Overlay hit data on a stadium outline.

- `data`: StatCast DataFrame containing at minimum `hc_x`, `hc_y`, and `events`.
- `team_stadium`: Team name (same values as plot_stadium).
- `title`: Chart title.
- `size`: Mark size.
- `colorby`: Category for color-coding. Default: 'events'. Use 'player' for multi-player data.
- `legend_title`: Legend title.
- `width`: Plot width. Default: 500.
- `height`: Plot height. Default: 500.

```python
from pybaseball import statcast_batter, spraychart

data = statcast_batter('2019-05-01', '2019-07-01', 514888)
sub_data = data[data['home_team'] == 'HOU']
spraychart(sub_data, 'astros', title='Jose Altuve: May-June 2019')
```

### plot_bb_profile()

`plot_bb_profile(df, parameter="launch_angle")`

Plots a given StatCast parameter split by batted ball type.

- `df`: StatCast DataFrame.
- `parameter`: Parameter to plot. Default: "launch_angle".

```python
from pybaseball.plotting import plot_bb_profile
from pybaseball import statcast

df = statcast("2018-05-01", "2018-05-04")
plot_bb_profile(df, parameter="launch_angle")
```

### plot_teams()

`plot_teams(data, x_axis, y_axis, title=None)`

Scatter plot of team stats.

- `data`: FanGraphs team data from team_batting or team_pitching.
- `x_axis`: Stat for x-axis.
- `y_axis`: Stat for y-axis.
- `title`: Chart title.

```python
from pybaseball import plot_teams, team_batting

data = team_batting(2023)
plot_teams(data, "HR", "BB")
```

### plot_strike_zone()

`plot_strike_zone(data, title='', colorby='pitch_type', legend_title='', annotation='pitch_type', axis=None)`

Overlay pitch data on a strike zone.

- `data`: StatCast pitcher DataFrame.
- `title`: Plot title.
- `colorby`: Color category. Options: 'pitch_type', 'pitcher', 'description', or any column in data.
- `legend_title`: Legend title. Default based on colorby.
- `annotation`: Marker annotation. Options: 'pitch_type', 'release_speed', 'effective_speed', 'launch_speed', or any column.
- `axis`: matplotlib Axes. If None, creates new Axes.

```python
from pybaseball.plotting import plot_strike_zone
from pybaseball import statcast_pitcher

data = statcast_pitcher('2022-09-03', '2022-09-03', 656302)
plot_strike_zone(data, title="Dylan Cease's 1-hitter on Sept 3, 2022")
```

---

## Draft and Prospect Functions

### amateur_draft()

`amateur_draft(year, round, keep_stats=True)`

Get amateur draft results by year and round. No distinction between competitive balance, supplementary, and main portions of a round.

- `year`: Draft year.
- `round`: Round number.
- `keep_stats`: Boolean. Include major league stats. Default: True.

```python
from pybaseball import amateur_draft

data = amateur_draft(2017, 1)
data = amateur_draft(2016, 2, False)
```

### amateur_draft_by_team()

`amateur_draft_by_team(team, year, keep_stats=True)`

Get amateur draft results by team and year.

- `team`: Team code string.
- `year`: Draft year.
- `keep_stats`: Boolean. Default: True.

Team codes:

| Team | Code |
|---|---|
| Angels | ANA |
| Astros | HOU |
| Athletics | OAK |
| Blue Jays | TOR |
| Braves | ATL |
| Brewers | MIL |
| Cardinals | STL |
| Cubs | CHC |
| Rays | TBD |
| Diamondbacks | ARI |
| Dodgers | LAD |
| Giants | SFG |
| Indians (Guardians) | CLE |
| Mariners | SEA |
| Marlins | FLA |
| Mets | NYM |
| Nationals | WSN |
| Orioles | BAL |
| Padres | SDP |
| Phillies | PHI |
| Pirates | PIT |
| Rangers | TEX |
| Red Sox | BOS |
| Reds | CIN |
| Rockies | COL |
| Royals | KCR |
| Tigers | DET |
| Twins | MIN |
| White Sox | CHW |
| Yankees | NYY |

```python
from pybaseball import amateur_draft_by_team

data = amateur_draft_by_team("TBD", 2011)
data = amateur_draft_by_team("KCR", 2013, keep_stats=False)
```

### top_prospects()

`top_prospects(team=None, playerType=None)`

Retrieves top prospects by team or leaguewide.

- `team`: Team name (no whitespace). If not specified, returns leaguewide prospects.
- `playerType`: "pitchers" or "batters". If not specified, returns both.

Note: If playerType is specified, team must also be included (use None for leaguewide).

```python
from pybaseball import top_prospects

data = top_prospects("bluejays", "pitchers")
data = top_prospects()
data = top_prospects(None, "batters")
data = top_prospects("padres")
```
