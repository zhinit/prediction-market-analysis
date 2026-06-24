# pybaseball — Statcast

Statcast functions in [[pybaseball]] for retrieving pitch-level data, aggregate batting/pitching metrics, fielding analytics, running metrics, and spin analysis from Baseball Savant. (source: pybaseball-docs-statcast.md)

## Core Pitch-Level Functions

### statcast()

```python
statcast(start_dt=[yesterday], end_dt=None, team=None, verbose=True, parallel=True)
```

Retrieves pitch-level data from Baseball Savant. One row per pitch. (source: pybaseball-docs-statcast.md)

- `start_dt` — first day, format YYYY-MM-DD, defaults to yesterday
- `end_dt` — last day, defaults to None (single day query)
- `team` — optional team abbreviation (e.g. BOS, NYY, TEX)
- `verbose` — progress updates, default True
- `parallel` — parallelize HTTP requests, default True

Data availability: 2008+ (system introduction). Some metrics (launch angle) only from 2015+. Baseball Savant enforces a 30,000 row limit per query; requests over 5 days are auto-split but returned as a single DataFrame. (source: pybaseball-docs-statcast.md)

```python
from pybaseball import statcast

data = statcast('2017-07-04')                              # single day
data = statcast('2016-08-01', '2016-08-07')                # date range
data = statcast('2016-04-01', '2016-10-30', team='TEX')   # team-filtered
```

### statcast_single_game()

```python
statcast_single_game(game_pk)
```

Retrieves all statcast data for a given game ID (integer, from MLB Advanced Media). (source: pybaseball-docs-statcast.md)

```python
from pybaseball import statcast_single_game

data = statcast_single_game(529429)
```

### statcast_batter()

```python
statcast_batter(start_dt=[yesterday], end_dt=None, player_id)
```

Pitch-level data for a single batter. Requires MLBAM player ID (see [[pybaseball-player-lookup]]). (source: pybaseball-docs-statcast.md)

```python
from pybaseball import statcast_batter, playerid_lookup

playerid_lookup('ortiz', 'david')
data = statcast_batter('2008-04-01', '2017-07-15', player_id=120074)
```

### statcast_pitcher()

```python
statcast_pitcher(start_dt=[yesterday], end_dt=None, player_id)
```

Pitch-level data for a single pitcher. Requires MLBAM player ID. In rare cases where a pitcher exceeds 30,000 pitches in the query range, only the first 30,000 are returned. (source: pybaseball-docs-statcast.md)

```python
from pybaseball import statcast_pitcher, playerid_lookup

playerid_lookup('sale', 'chris')
data = statcast_pitcher('2008-04-01', '2017-07-15', player_id=519242)
```

## Batter Aggregate Functions

All aggregate functions return season-level data for qualified batters (or those meeting a minimum threshold). (source: pybaseball-docs-statcast.md)

| Function | Signature | Description |
|---|---|---|
| `statcast_batter_exitvelo_barrels` | `(year, minBBE=[qualified])` | Batted ball data (exit velo, barrels) |
| `statcast_batter_expected_stats` | `(year, minPA=[qualified])` | Expected stats based on contact quality |
| `statcast_batter_percentile_ranks` | `(year)` | Percentile ranks (2.1 PA per team game threshold) |
| `statcast_batter_pitch_arsenal` | `(year, minPA=25)` | Outcome data split by pitch type |

## Pitcher Aggregate Functions

All aggregate functions return season-level data for qualified pitchers (or those meeting a minimum threshold). (source: pybaseball-docs-statcast.md)

| Function | Signature | Description |
|---|---|---|
| `statcast_pitcher_exitvelo_barrels` | `(year, minBBE=[qualified])` | Batted ball against data |
| `statcast_pitcher_expected_stats` | `(year, minPA=[qualified])` | Expected stats on contact against |
| `statcast_pitcher_pitch_arsenal` | `(year, minP=[qualified], arsenal_type="average_speed")` | Arsenal stats; types: "average_speed", "n_" (share %), "average_spin" |
| `statcast_pitcher_arsenal_stats` | `(year, minPA=25)` | Outcome stats per arsenal; run value and whiff % per pitch, others per PA |
| `statcast_pitcher_pitch_movement` | `(year, minP=[qualified], pitch_type="FF")` | Pitch movement; types: FF, SIFT, CH, CUKC, FC, SL, FS, ALL |
| `statcast_pitcher_active_spin` | `(year, minP=250)` | Active spin on all pitches |
| `statcast_pitcher_percentile_ranks` | `(year)` | Percentile ranks on expected stats, batted ball data, spin rates |
| `statcast_pitcher_spin_dir_comp` | `(year, pitch_a="4-Seamer", pitch_b="Changeup", minP=100, pitcher_pov=True)` | Spin direction comparison between two pitch types |

### Spin Direction Comparison Details

Valid pitch types for `pitch_a` and `pitch_b`: "4-Seamer", "Sinker", "Changeup", "Curveball", "Cutter", "Slider". Pitch codes also accepted. `pitch_b` must differ from `pitch_a`. `pitcher_pov` controls whether movement direction is from pitcher's (True) or batter's (False) point of view. (source: pybaseball-docs-statcast.md)

## statcast_pitcher_spin()

```python
statcast_pitcher_spin(start_dt=[yesterday], end_dt=None, player_id)
```

Retrieves pitch-level data and calculates spin-related metrics. Piggybacks on `statcast_pitcher`. (source: pybaseball-docs-statcast.md)

### Added Columns

- `Mx` — movement in x-direction due to Magnus effect (positive towards first base / catcher's right)
- `Mz` — movement in z-direction due to Magnus effect (positive upwards)
- `theta` — angle of spin axis relative to movement direction (0-90). 0 = perpendicular (all "useful" spin); 90 = parallel (gyroball)
- `phi` — angle of spin axis in x-z plane oriented to x-axis (axis of rotation from catcher's perspective)

Calculations modeled from Professor Alan Nathan (University of Illinois). Uses PITCHf/x coordinate system (origin at home plate, x to catcher's right, y toward mound, z upward). All calculations assume Tropicana Field conditions (no wind, 70 degrees). (source: pybaseball-docs-statcast.md)

```python
from pybaseball import statcast_pitcher_spin, playerid_lookup

playerid_lookup('darvish', 'yu')
data = statcast_pitcher_spin('2019-07-01', '2019-07-31', player_id=506433)
```

## Fielding Functions

All fielding functions accept a year parameter (YYYY) and a minimum attempts/opportunities threshold. (source: pybaseball-docs-statcast.md)

### statcast_outs_above_average()

```python
statcast_outs_above_average(year, pos, min_att="q", view="Fielder")
```

Outs Above Average (OAA) — the cumulative effect of all individual plays a fielder has been credited or debited with.

- `pos` — "all", "IF", "OF", position names, numbers, or abbreviations. Pitchers and catchers excluded.
- `min_att` — minimum fielding attempts. Default "q" (qualified: 1 per game for 2B/SS/3B/OF, 1 per every other game for 1B).
- `view` — "Fielder" (default), "Pitcher" (defense behind pitcher), "Fielding_Team", "Batter" (defense when player at bat), "Batting_Team". `min_att` ignored on team views.

### statcast_outfield_directional_oaa()

```python
statcast_outfield_directional_oaa(year, min_opp="q")
```

Directional OAA across six zones: Back Left, Back, Back Right, In Left, In, In Right.

### statcast_outfield_catch_prob()

```python
statcast_outfield_catch_prob(year, min_opp="q")
```

Outfielder performance aggregated into five-star difficulty categories.

### statcast_outfielder_jump()

```python
statcast_outfielder_jump(year, min_att="q")
```

Jump performance on plays with 90% or lower catch probability (two-star or harder).

### statcast_catcher_poptime()

```python
statcast_catcher_poptime(year, min_2b_att=5, min_3b_att=0)
```

Time from ball hitting catcher's mitt to arrival at projected receiving point at center of base. Not available for 2020.

### statcast_catcher_framing()

```python
statcast_catcher_framing(year, min_called_p="q")
```

Strike-call percentage in eight zones around the strike zone (shadow zone). Default minimum: 6 called pitches in shadow zone per team game.

### statcast_fielding_run_value()

```python
statcast_fielding_run_value(year, pos, min_inn=100)
```

Total Fielding Run Value (FRV) by season and position. Pitchers excluded. Minimum 100 innings at position.

## Running Functions

### statcast_sprint_speed()

```python
statcast_sprint_speed(year, min_opp=10)
```

Feet per second in a player's fastest one-second window, calculated from approximately the top two-thirds of qualifying runs. (source: pybaseball-docs-statcast.md)

Sprinting opportunities defined as:
- Runs of 2+ bases on non-homers (excluding runner on 2B on extra-base hits)
- Home to first on topped or weakly hit balls

### statcast_running_splits()

```python
statcast_running_splits(year, min_opp=5, raw_splits=True)
```

90-foot sprint splits at five-foot intervals. `raw_splits=True` returns raw times; `raw_splits=False` returns percentile rankings.

## Utility Functions

### add_spray_angle()

```python
from pybaseball.datahelpers.statcast_utils import add_spray_angle

add_spray_angle(df, adjusted=False)
```

Adds spray angle column to a StatCast DataFrame. With `adjusted=True`, flips sign for left-handed batters to create a push/pull angle (inspired by Alan Nathan). (source: pybaseball-docs-statcast.md)

Note: Statcast data is liable to change unexpectedly due to the large number of observations. (source: pybaseball-docs-statcast.md)
