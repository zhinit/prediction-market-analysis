# pybaseball Statcast Documentation

Documentation for Statcast-related functions in the pybaseball Python library.

Source: https://github.com/jldbc/pybaseball/tree/master/docs (statcast.md, statcast_batter.md, statcast_pitcher.md, statcast_fielding.md, statcast_running.md, statcast_single_game.md, statcast_pitcher_spin.md, statcast_utils.md)
Accessed: 2026-06-24

---

## statcast()

`statcast(start_dt=[yesterday's date], end_dt=None, team=None, verbose=True, parallel=True)`

Retrieves pitch-level statcast data for a given date or range of dates. One row per pitch. Data fields documented on Baseball Savant.

### Arguments

- `start_dt`: First day for data retrieval. Defaults to yesterday's date. Format: YYYY-MM-DD.
- `end_dt`: Last day for data retrieval. Defaults to None. Format: YYYY-MM-DD.
- `team`: Optional team abbreviation (e.g. BOS, SEA, NYY).
- `verbose`: Boolean (default True) for progress updates.
- `parallel`: Boolean (default True) for parallelizing HTTP requests.

### Data Availability

The earliest available statcast data comes from the 2008 season when the system was first introduced to Major League Baseball. Queries before this year will not work. Some features were introduced after the 2008 season. Launch speed angle, for example, is only available from the 2015 season forward.

### Query Limits

Baseball Savant enforces a 30,000 row limit per query. Requests spanning more than 5 days are automatically split into smaller requests but returned as a single DataFrame.

### Examples

```python
from pybaseball import statcast

data = statcast('2017-07-04')
data = statcast('2016-08-01', '2016-08-07')
data = statcast('2016-04-01', '2016-10-30', team='TEX')
```

---

## statcast_single_game()

`statcast_single_game(game_pk)`

Retrieve all statcast data for a given game id.

### Arguments

- `game_pk`: Integer. Game id provided by MLB Advanced Media.

### Examples

```python
from pybaseball import statcast_single_game

data = statcast_single_game(529429)
```

---

## statcast_batter()

`statcast_batter(start_dt=[yesterday's date], end_dt=None, player_id)`

Retrieves pitch-level statcast data for a single batter over a given date or range of dates.

### Arguments

- `start_dt`: First day for data retrieval. Defaults to yesterday's date. Format: YYYY-MM-DD.
- `end_dt`: Last day for data retrieval. Defaults to None. Format: YYYY-MM-DD.
- `player_id`: MLBAM player ID. Obtained via `playerid_lookup()`.

### Examples

```python
from pybaseball import statcast_batter, playerid_lookup

playerid_lookup('ortiz', 'david')
data = statcast_batter('2008-04-01', '2017-07-15', player_id=120074)
data = statcast_batter('2014-08-16', player_id=120074)
```

---

## statcast_pitcher()

`statcast_pitcher(start_dt=[yesterday's date], end_dt=None, player_id)`

Retrieves pitch-level statcast data for a single pitcher over a given date or range of dates.

### Arguments

- `start_dt`: First day for data retrieval. Defaults to yesterday's date. Format: YYYY-MM-DD.
- `end_dt`: Last day for data retrieval. Defaults to None. Format: YYYY-MM-DD.
- `player_id`: MLBAM player ID. Obtained via `playerid_lookup()`.

### Known Issue

In rare cases where a player has seen greater than 30,000 pitches over the time period specified, only the first 30,000 plays will be returned.

### Examples

```python
from pybaseball import statcast_pitcher, playerid_lookup

playerid_lookup('sale', 'chris')
data = statcast_pitcher('2008-04-01', '2017-07-15', player_id=519242)
data = statcast_pitcher('2017-07-15', player_id=519242)
```

---

## Batter Aggregate Functions

### statcast_batter_exitvelo_barrels()

`statcast_batter_exitvelo_barrels(year, minBBE=[qualified])`

Retrieves batted ball data for all batters in a given year.

- `year`: Format YYYY.
- `minBBE`: Minimum batted ball events. Defaults to qualified batters only.

### statcast_batter_expected_stats()

`statcast_batter_expected_stats(year, minPA=[qualified])`

Retrieves expected stats based on quality of batted ball contact in a given year.

- `year`: Format YYYY.
- `minPA`: Minimum plate appearances. Defaults to qualified batters only.

### statcast_batter_percentile_ranks()

`statcast_batter_percentile_ranks(year)`

Retrieves percentile ranks for each qualified batter in a given year. Includes batters with 2.1 PA per team game.

- `year`: Format YYYY.

### statcast_batter_pitch_arsenal()

`statcast_batter_pitch_arsenal(year, minPA=25)`

Retrieves outcome data for batters split by pitch type in a given year.

- `year`: Format YYYY.
- `minPA`: Minimum plate appearances. Default: 25.

---

## Pitcher Aggregate Functions

### statcast_pitcher_exitvelo_barrels()

`statcast_pitcher_exitvelo_barrels(year, minBBE=[qualified])`

Retrieves batted ball against data for all qualified pitchers in a given year.

- `year`: Format YYYY.
- `minBBE`: Minimum batted ball against events. Defaults to qualified pitchers only.

### statcast_pitcher_expected_stats()

`statcast_pitcher_expected_stats(year, minPA=[qualified])`

Retrieves expected stats based on quality of batted ball contact against in a given year.

- `year`: Format YYYY.
- `minPA`: Minimum plate appearances against. Defaults to qualified pitchers only.

### statcast_pitcher_pitch_arsenal()

`statcast_pitcher_pitch_arsenal(year, minP=[qualified], arsenal_type="average_speed")`

Retrieves high level stats on each pitcher's arsenal in a given year.

- `year`: Format YYYY.
- `minP`: Minimum pitches thrown. Defaults to qualified pitchers only.
- `arsenal_type`: Options: "average_speed", "n_" (percentage share), "average_spin". Default: "average_speed".

### statcast_pitcher_arsenal_stats()

`statcast_pitcher_arsenal_stats(year, minPA=25)`

Retrieves assorted basic and advanced outcome stats for pitchers' arsenals in a given year. Run value and whiff % are on a per pitch basis; all others are on a per PA basis.

- `year`: Format YYYY.
- `minPA`: Minimum plate appearances against. Default: 25.

### statcast_pitcher_pitch_movement()

`statcast_pitcher_pitch_movement(year, minP=[qualified], pitch_type="FF")`

Retrieves pitch movement stats for all qualified pitchers with a specified pitch type for a given year.

- `year`: Format YYYY.
- `minP`: Minimum pitches thrown. Defaults to qualified pitchers only.
- `pitch_type`: Options: "FF", "SIFT", "CH", "CUKC", "FC", "SL", "FS", "ALL". Pitch names also accepted. Default: "FF".

### statcast_pitcher_active_spin()

`statcast_pitcher_active_spin(year, minP=250)`

Retrieves active spin stats on all of a pitcher's pitches in a given year.

- `year`: Format YYYY.
- `minP`: Minimum pitches thrown. Default: 250.

### statcast_pitcher_percentile_ranks()

`statcast_pitcher_percentile_ranks(year)`

Retrieves percentile ranks for each qualified pitcher in a given year. Includes percentiles on expected stats, batted ball data, and spin rates.

- `year`: Format YYYY.

### statcast_pitcher_spin_dir_comp()

`statcast_pitcher_spin_dir_comp(year, pitch_a="4-Seamer", pitch_b="Changeup", minP=100, pitcher_pov=True)`

Retrieves spin comparisons between two pitches for qualifying pitchers in a given year.

- `year`: Format YYYY.
- `pitch_a`: First pitch. Valid: "4-Seamer", "Sinker", "Changeup", "Curveball", "Cutter", "Slider". Pitch codes also accepted. Default: "4-Seamer".
- `pitch_b`: Second pitch (must differ from pitch_a). Default: "Changeup".
- `minP`: Minimum pitches of type pitch_a thrown. Default: 100.
- `pitcher_pov`: Boolean. True = pitcher's POV, False = batter's POV.

---

## statcast_pitcher_spin()

`statcast_pitcher_spin(start_dt=[yesterday's date], end_dt=None, player_id)`

Retrieves pitch-level statcast data for a pitcher and calculates spin-related metrics. Piggybacks off statcast_pitcher.

### Added Return Columns

- `Mx`: Movement in x-direction due to Magnus effect (positive towards first base / catcher's right).
- `Mz`: Movement in z-direction due to Magnus effect (positive upwards).
- `theta`: Angle of spin axis with respect to movement (0-90). 0 = perpendicular (all "useful" spin for Magnus effect); 90 = parallel (gyroball).
- `phi`: Angle of spin axis in x-z plane oriented to x-axis. The axis the ball is spinning from the catcher's eye.

### Notes

- Calculations modeled from Professor Alan Nathan (University of Illinois).
- Uses PITCHf/x coordinate system: origin at home plate, x-axis to catcher's right, y-axis toward mound, z-axis upward.
- Calculations assume Tropicana Field conditions (no wind, 70 degrees).

### Examples

```python
from pybaseball import statcast_pitcher_spin, playerid_lookup

playerid_lookup('darvish', 'yu')
data = statcast_pitcher_spin('2019-07-01', '2019-07-31', player_id=506433)
data = statcast_pitcher_spin('2019-05-03', player_id=543294)
```

---

## Fielding Functions

### statcast_outs_above_average()

`statcast_outs_above_average(year, pos, min_att="q", view="Fielder")`

Retrieves outs above average (OAA) for the given year, position, and attempts. OAA is the "cumulative effect of all individual plays a fielder has been credited or debited with."

- `year`: Format YYYY.
- `pos`: Valid: "all", "IF", "OF", position names, numbers, or abbreviations. Pitchers and catchers not included.
- `min_att`: Minimum fielding attempts. Default "q" (qualified). Statcast default: 1 attempt per game for 2B/SS/3B/OF, 1 per every other game for 1B.
- `view`: Perspective for OAA. Valid: "Fielder" (default), "Pitcher", "Fielding_Team", "Batter", "Batting_Team". min_att ignored on team views.

### statcast_outfield_directional_oaa()

`statcast_outfield_directional_oaa(year, min_opp="q")`

Retrieves outfielders' directional OAA data. Directions: Back Left, Back, Back Right, In Left, In, In Right.

- `year`: Format YYYY.
- `min_opp`: Minimum opportunities. Default: qualified (1 attempt per game).

### statcast_outfield_catch_prob()

`statcast_outfield_catch_prob(year, min_opp="q")`

Retrieves aggregated data for outfielder performance on fielding attempts binned into five-star categories.

- `year`: Format YYYY.
- `min_opp`: Minimum opportunities. Default: qualified.

### statcast_outfielder_jump()

`statcast_outfielder_jump(year, min_att="q")`

Retrieves data on outfielder's jump to the ball. Calculated only for two-star or harder plays (90% or less catch probability).

- `year`: Format YYYY.
- `min_att`: Minimum attempts. Default: qualified (2 two-star+ attempts per team game / 5).

### statcast_catcher_poptime()

`statcast_catcher_poptime(year, min_2b_att=5, min_3b_att=0)`

Retrieves pop time data for catchers. Pop time = time from ball hitting catcher's mitt to arrival at projected receiving point at center of base. Not available for 2020.

- `year`: Format YYYY.
- `min_2b_att`: Minimum SB attempts at 2B. Default: 5.
- `min_3b_att`: Minimum SB attempts at 3B. Default: 0.

### statcast_catcher_framing()

`statcast_catcher_framing(year, min_called_p="q")`

Retrieves catcher framing results. Uses eight zones around the strike zone (shadow zone); gives strike-call percentage in each zone.

- `year`: Format YYYY.
- `min_called_p`: Minimum called pitches in shadow zone. Default: qualified (6 per team game).

### statcast_fielding_run_value()

`statcast_fielding_run_value(year, pos, min_inn=100)`

Retrieves total Fielding Run Value (FRV) for a given season and position.

- `year`: Format YYYY.
- `pos`: Valid: "all", "IF", "OF", position names/numbers/abbreviations. Pitchers not included.
- `min_inn`: Minimum innings at position. Default: 100.

---

## Running Functions

### statcast_sprint_speed()

`statcast_sprint_speed(year, min_opp=10)`

Returns each player's sprint speed: "feet per second in a player's fastest one-second window," calculated using approximately the top two-thirds of a player's opportunities.

- `year`: Format YYYY.
- `min_opp`: Minimum sprinting opportunities. Default: 10. Opportunities defined as: runs of 2+ bases on non-homers (excluding runner on 2B on XBH), and home-to-first on topped/weakly hit balls.

### statcast_running_splits()

`statcast_running_splits(year, min_opp=5, raw_splits=True)`

Returns each player's 90-foot sprint splits at five-foot intervals.

- `year`: Format YYYY.
- `min_opp`: Minimum sprinting opportunities. Default: 5.
- `raw_splits`: Boolean. True = raw times, False = percentiles. Default: True.

---

## Utility Functions

### add_spray_angle()

`add_spray_angle(df, adjusted=False)`

Located in `pybaseball.datahelpers.statcast_utils`. Adds spray angle (and optionally adjusted spray angle) to StatCast DataFrames.

- `df`: StatCast DataFrame (from statcast, statcast_batter, etc.).
- `adjusted`: If True, flips sign for left-handed batters (push/pull angle). Inspired by Alan Nathan.

Spray angle formula from: https://baseballwithr.wordpress.com/2018/01/15/chance-of-hit-as-function-of-launch-angle-exit-velocity-and-spray-angle/

Note: Statcast data is liable to change unexpectedly due to the large number of observations.
