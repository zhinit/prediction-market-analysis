# pybaseball Historical Data Documentation

Documentation for Lahman database and Retrosheet functions in the pybaseball Python library.

Source: https://github.com/jldbc/pybaseball/tree/master/docs (lahman.md, retrosheet.md)
Accessed: 2026-06-24

---

## Lahman Database

Data from Sean Lahman's Baseball Database, hosted by Chadwick Bureau on GitHub (https://github.com/chadwickbureau/baseballdatabank).

### download_lahman()

`download_lahman()`

Downloads the entire Lahman database to the current working directory.

### Available Tables

```python
from pybaseball.lahman import *

# Player biographical info and IDs
people = people()
# (alias)
master = master()

# Park ID, name, alias, city, state, country
parks = parks()

# All-Star roster: player, year, team, league, position
allstar = all_star_full()

# Games played per position per season
appearances = appearances()

# Manager awards by year
awards_mgr = awards_managers()

# Player awards by year
awards_player = awards_players()

# Vote shares for manager awards
award_share_mgr = awards_share_managers()

# Vote shares for player awards
award_share_player = awards_share_players()

# Batting stats by year, regular season
batting = batting()

# Batting stats by year, post season
batting_post = batting_post()

# College played at each year
college_playing = college_playing()

# Fielding stats by year
fielding = fielding()

# Games played in LF, CF, RF
fielding_of = fielding_of()

# LF/CF/RF splits
fielding_of_split = fielding_of_split()

# Postseason fielding
fielding_post = fielding_post()

# Hall of Fame voting by year
hall_of_fame = hall_of_fame()

# Home game attendance by park by year
home_games = home_games()

# Managers by team and year
managers = managers()

# Split season managers data
managers_half = managers_half()

# Historical player pitching stats
pitching = pitching()

# Postseason pitching stats
pitching_post = pitching_post()

# Salary data
salaries = salaries()

# Schools attended by each player
schools = schools()

# Playoff series winners and losers
series_post = series_post()

# Teams by year: record, division, stadium, attendance, etc.
teams = teams()

# Current and historical franchises, active status, IDs
teams_franchises = teams_franchises()

# Split season data for teams
teams_half = teams_half()
```

---

## Retrosheet

Data from Retrosheet via the Chadwick Bureau's GitHub repository.

### Copyright Notice

The information used here was obtained free of charge from and is copyrighted by Retrosheet. Interested parties may contact Retrosheet at www.retrosheet.org.

### GitHub Rate Limits

Retrosheet data is fetched from GitHub. Unauthenticated requests are limited to 60 per hour. Setting a GH_TOKEN environment variable enables authenticated requests at 5,000 per hour, with better error reporting.

### Game Log Functions

```python
from pybaseball import retrosheet

# Game logs for a season
logs = retrosheet.season_game_logs(season)

# World Series game logs
logs = retrosheet.world_series_logs()

# All-Star Game logs
logs = retrosheet.all_star_game_logs()

# Wild Card Game logs
logs = retrosheet.wild_card_logs()

# Division Series logs
logs = retrosheet.division_series_logs()

# League Championship Series logs
logs = retrosheet.lcs_logs()
```

### Other Functions

```python
# Schedules and postponements for a season
schedules = retrosheet.schedules(season)

# Facility identifiers used by Retrosheet
parks = retrosheet.park_codes()

# Major league roster data for a season
rosters = retrosheet.rosters(season)

# Event files (regular, post-season, or all-star)
events = retrosheet.events(season, type='regular', export_dir='.')
```
