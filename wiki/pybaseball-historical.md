# pybaseball — Lahman and Retrosheet

Historical data functions in [[pybaseball]] for accessing the Lahman database and Retrosheet archives. (source: pybaseball-docs-historical.md)

## Lahman Database

Data from Sean Lahman's Baseball Database, hosted by the Chadwick Bureau on GitHub. (source: pybaseball-docs-historical.md)

### download_lahman()

```python
from pybaseball.lahman import download_lahman

download_lahman()
```

Downloads the entire Lahman database to the current working directory.

### Available Tables

25+ tables accessible as individual functions from `pybaseball.lahman`: (source: pybaseball-docs-historical.md)

```python
from pybaseball.lahman import *
```

**Players and People**

| Function | Contents |
|---|---|
| `people()` | Player biographical info and IDs |
| `master()` | Alias for `people()` |

**Batting**

| Function | Contents |
|---|---|
| `batting()` | Batting stats by year, regular season |
| `batting_post()` | Batting stats, postseason |

**Pitching**

| Function | Contents |
|---|---|
| `pitching()` | Pitching stats by year |
| `pitching_post()` | Pitching stats, postseason |

**Fielding**

| Function | Contents |
|---|---|
| `fielding()` | Fielding stats by year |
| `fielding_of()` | Games played in LF, CF, RF |
| `fielding_of_split()` | LF/CF/RF splits |
| `fielding_post()` | Postseason fielding |
| `appearances()` | Games played per position per season |

**Awards and Hall of Fame**

| Function | Contents |
|---|---|
| `awards_managers()` | Manager awards by year |
| `awards_players()` | Player awards by year |
| `awards_share_managers()` | Manager award vote shares |
| `awards_share_players()` | Player award vote shares |
| `hall_of_fame()` | Hall of Fame voting by year |

**Teams and Parks**

| Function | Contents |
|---|---|
| `teams()` | Teams by year: record, division, stadium, attendance |
| `teams_franchises()` | Current and historical franchises, active status, IDs |
| `teams_half()` | Split season team data |
| `parks()` | Park ID, name, alias, city, state, country |
| `home_games()` | Home game attendance by park by year |

**Other**

| Function | Contents |
|---|---|
| `all_star_full()` | All-Star roster: player, year, team, league, position |
| `managers()` | Managers by team and year |
| `managers_half()` | Split season managers |
| `salaries()` | Salary data |
| `schools()` | Schools attended by each player |
| `college_playing()` | College played at each year |
| `series_post()` | Playoff series winners and losers |

## Retrosheet

Historical game logs, rosters, schedules, and events from Retrosheet via the Chadwick Bureau's GitHub repository. (source: pybaseball-docs-historical.md)

### Copyright Notice

> The information used here was obtained free of charge from and is copyrighted by Retrosheet. Interested parties may contact Retrosheet at www.retrosheet.org.

This notice is required when using Retrosheet data. (source: pybaseball-docs-historical.md)

### GitHub Rate Limits

Retrosheet data is fetched from GitHub. Unauthenticated requests: 60 per hour. Setting a `GH_TOKEN` environment variable enables authenticated requests at 5,000 per hour with better error reporting. (source: pybaseball-docs-historical.md)

### Game Log Functions

```python
from pybaseball import retrosheet

logs = retrosheet.season_game_logs(season)       # regular season
logs = retrosheet.world_series_logs()            # World Series
logs = retrosheet.all_star_game_logs()           # All-Star Game
logs = retrosheet.wild_card_logs()               # Wild Card
logs = retrosheet.division_series_logs()         # Division Series
logs = retrosheet.lcs_logs()                     # League Championship Series
```

### Other Retrosheet Functions

```python
schedules = retrosheet.schedules(season)          # scheduled games and postponements
parks = retrosheet.park_codes()                   # facility identifiers
rosters = retrosheet.rosters(season)              # major league roster data
events = retrosheet.events(season, type='regular', export_dir='.')  # event files
```

The `events()` function downloads event files. `type` accepts 'regular', 'post', or 'asg' (All-Star Game). Files are exported to the specified directory. (source: pybaseball-docs-historical.md)
