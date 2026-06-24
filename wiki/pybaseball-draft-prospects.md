# pybaseball — Draft and Prospects

Draft and prospect data functions in [[pybaseball]]. (source: pybaseball-docs-misc.md)

## amateur_draft()

```python
amateur_draft(year, round, keep_stats=True)
```

Amateur draft results by year and round. No distinction between competitive balance, supplementary, and main portions of a round. (source: pybaseball-docs-misc.md)

- `year` — draft year
- `round` — round number
- `keep_stats` — include major league stats for drafted players. Default: True

```python
from pybaseball import amateur_draft

data = amateur_draft(2017, 1)                  # 2017 first round
data = amateur_draft(2016, 2, False)           # 2016 second round, no stats
```

## amateur_draft_by_team()

```python
amateur_draft_by_team(team, year, keep_stats=True)
```

Amateur draft results filtered by team. (source: pybaseball-docs-misc.md)

- `team` — team code (see table below)
- `year` — draft year
- `keep_stats` — include major league stats. Default: True

### Team Codes

| Team | Code | | Team | Code |
|---|---|---|---|---|
| Angels | ANA | | Nationals | WSN |
| Astros | HOU | | Orioles | BAL |
| Athletics | OAK | | Padres | SDP |
| Blue Jays | TOR | | Phillies | PHI |
| Braves | ATL | | Pirates | PIT |
| Brewers | MIL | | Rangers | TEX |
| Cardinals | STL | | Rays | TBD |
| Cubs | CHC | | Red Sox | BOS |
| Diamondbacks | ARI | | Reds | CIN |
| Dodgers | LAD | | Rockies | COL |
| Giants | SFG | | Royals | KCR |
| Indians (Guardians) | CLE | | Tigers | DET |
| Mariners | SEA | | Twins | MIN |
| Marlins | FLA | | White Sox | CHW |
| Mets | NYM | | Yankees | NYY |

```python
from pybaseball import amateur_draft_by_team

data = amateur_draft_by_team("TBD", 2011)                       # 2011 Rays draft
data = amateur_draft_by_team("KCR", 2013, keep_stats=False)     # 2013 Royals, no stats
```

## top_prospects()

```python
top_prospects(team=None, playerType=None)
```

Top prospects by team or leaguewide. (source: pybaseball-docs-misc.md)

- `team` — team name, no whitespace (e.g. "bluejays", "padres"). If omitted, returns leaguewide prospects.
- `playerType` — "pitchers" or "batters". If omitted, returns both. Note: if `playerType` is specified, `team` must also be included (use None for leaguewide).

```python
from pybaseball import top_prospects

data = top_prospects("bluejays", "pitchers")    # Blue Jays pitching prospects
data = top_prospects()                          # leaguewide, all players
data = top_prospects(None, "batters")           # leaguewide batters
data = top_prospects("padres")                  # Padres, all players
```
