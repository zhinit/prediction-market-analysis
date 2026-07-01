# pybaseball — Player ID Lookup

Player identification functions in [[pybaseball]] for resolving names to cross-database IDs (MLBAM, FanGraphs, Baseball Reference, Retrosheet) using the Chadwick Bureau register. (source: pybaseball-docs-misc.md)

## playerid_lookup()

```python
playerid_lookup(last, first=None, fuzzy=False)
```

Look up a player's MLBAM, Retrosheet, FanGraphs, and Baseball Reference IDs by name. Data from the Chadwick Bureau. Note that several people in this dataset are not MLB players; supplying both last and first name is recommended. (source: pybaseball-docs-misc.md)

- `last` — player's last name (case insensitive)
- `first` — optional first name (case insensitive)
- `fuzzy` — if True, returns the 5 closest name matches

If multiple players share a name, use `mlb_played_first` and `mlb_played_last` fields to distinguish them.

```python
from pybaseball import playerid_lookup

data = playerid_lookup('jones')                              # all players named Jones (1,314 rows)
data = playerid_lookup('jones', 'chipper')                   # exact match
data = playerid_lookup("martinez", "pedro", fuzzy=True)
data = playerid_lookup("molina", "yadi", fuzzy=True)
```

## player_search_list()

```python
player_search_list(player_list)
```

Batch lookup of player IDs. Returns a DataFrame of all matching players. Exact match only. (source: pybaseball-docs-misc.md)

- `player_list` — list of `(last, first)` tuples, case insensitive

```python
from pybaseball import player_search_list

data = player_search_list([("brock", "lou"), ("jones", "chipper")])
```

## playerid_reverse_lookup()

```python
playerid_reverse_lookup(player_ids, key_type='mlbam')
```

Reverse lookup: find names and all cross-database IDs given a list of IDs. Data from Chadwick Bureau. (source: pybaseball-docs-misc.md)

- `player_ids` — list of player IDs
- `key_type` — ID system being provided: 'mlbam', 'retro', 'bbref', or 'fangraphs'. Default: 'mlbam'

```python
from pybaseball import playerid_reverse_lookup

data = playerid_reverse_lookup([120074, 519242], key_type='mlbam')
```

## chadwick_register()

```python
chadwick_register(save=False)
```

Full dump of the Chadwick Bureau player register. (source: pybaseball-docs-misc.md)

- `save` — if True, saves the file to disk

```python
from pybaseball import chadwick_register

data = chadwick_register()
data = chadwick_register(save=True)
```
