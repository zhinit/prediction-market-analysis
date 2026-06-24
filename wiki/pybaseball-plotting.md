# pybaseball — Plotting

Visualization functions in [[pybaseball]] for stadium outlines, spraycharts, batted ball profiles, team stat scatters, and strike zone overlays. (source: pybaseball-docs-misc.md)

## plot_stadium()

```python
plot_stadium(team)
```

Plots the outline of a team's stadium using MLBAM coordinates. (source: pybaseball-docs-misc.md)

Accepted team names: `angels`, `astros`, `athletics`, `blue_jays`, `braves`, `brewers`, `cardinals`, `cubs`, `diamondbacks`, `dodgers`, `generic`, `giants`, `indians`, `mariners`, `marlins`, `mets`, `nationals`, `orioles`, `padres`, `phillies`, `pirates`, `rangers`, `rays`, `red_sox`, `reds`, `rockies`, `royals`, `tigers`, `twins`, `white_sox`, `yankees`.

## spraychart()

```python
spraychart(data, team_stadium, title='', tooltips=[], size=100,
           colorby='events', legend_title='', width=500, height=500)
```

Overlays hit data on a stadium outline. (source: pybaseball-docs-misc.md)

- `data` — StatCast DataFrame with at minimum `hc_x`, `hc_y`, and `events`
- `team_stadium` — team name (same values as `plot_stadium`)
- `title` — chart title
- `size` — mark size
- `colorby` — category for color-coding. Default: 'events'. Use 'player' for multi-player comparisons.
- `legend_title` — legend title
- `width` / `height` — plot dimensions. Default: 500 each.

```python
from pybaseball import statcast_batter, spraychart

data = statcast_batter('2019-05-01', '2019-07-01', 514888)
sub_data = data[data['home_team'] == 'HOU']
spraychart(sub_data, 'astros', title='Jose Altuve: May-June 2019')
```

Multi-player example:

```python
import pandas as pd
from pybaseball import statcast_batter, spraychart

votto = statcast_batter('2019-08-01', '2019-10-01', 458015)
aquino = statcast_batter('2019-08-01', '2019-10-01', 606157)
data = pd.concat([votto, aquino])
home_data = data[data['home_team'] == 'CIN']
spraychart(home_data, 'reds', title='Votto vs. Aquino', colorby='player')
```

## plot_bb_profile()

```python
plot_bb_profile(df, parameter="launch_angle")
```

Plots a StatCast parameter split by batted ball type. (source: pybaseball-docs-misc.md)

- `df` — StatCast DataFrame
- `parameter` — parameter to plot. Default: "launch_angle"

```python
from pybaseball.plotting import plot_bb_profile
from pybaseball import statcast

df = statcast("2018-05-01", "2018-05-04")
plot_bb_profile(df, parameter="launch_angle")
```

## plot_teams()

```python
plot_teams(data, x_axis, y_axis, title=None)
```

Scatter plot of team stats. (source: pybaseball-docs-misc.md)

- `data` — FanGraphs team data from `team_batting()` or `team_pitching()` (see [[pybaseball-team-game]])
- `x_axis` — stat name for x-axis
- `y_axis` — stat name for y-axis
- `title` — chart title

```python
from pybaseball import plot_teams, team_batting

data = team_batting(2023)
plot_teams(data, "HR", "BB")
```

## plot_strike_zone()

```python
plot_strike_zone(data, title='', colorby='pitch_type', legend_title='',
                 annotation='pitch_type', axis=None)
```

Overlays pitch data on a strike zone diagram. (source: pybaseball-docs-misc.md)

- `data` — StatCast pitcher DataFrame
- `title` — plot title
- `colorby` — color category: 'pitch_type', 'pitcher', 'description', or any column in data
- `legend_title` — legend title (default based on `colorby`)
- `annotation` — marker annotation: 'pitch_type', 'release_speed', 'effective_speed', 'launch_speed', or any column
- `axis` — matplotlib Axes object. If None, creates new Axes. Returns Axes.

```python
from pybaseball.plotting import plot_strike_zone
from pybaseball import statcast_pitcher

data = statcast_pitcher('2022-09-03', '2022-09-03', 656302)
plot_strike_zone(data, title="Dylan Cease's 1-hitter on Sept 3, 2022")
```

Filtered by pitch type with custom annotation:

```python
plot_strike_zone(
    data.loc[data["pitch_type"] == "SL"],
    title="Exit Velocities on Cease's Slider",
    colorby='description',
    annotation="launch_speed"
)
```
