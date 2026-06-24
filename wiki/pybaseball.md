# pybaseball

Python package for baseball data analysis. Scrapes multiple baseball data sources so users do not have to write their own scrapers. (source: pybaseball-readme.md)

## Installation

```
pip install pybaseball
```

Or from source:

```
git clone https://github.com/jldbc/pybaseball
cd pybaseball
pip install -e .
```

(source: pybaseball-readme.md)

## Data Sources

- **Baseball Savant** — Statcast pitch-level data
- **FanGraphs** — season-level stats, leaderboards
- **Baseball Reference** — game logs, standings, WAR
- **Chadwick Bureau** — player ID registry
- **Retrosheet** — historical game logs, rosters, events
- **Sean Lahman's Baseball Database** — comprehensive historical data

(source: pybaseball-readme.md)

## Caching

Built-in caching system, disabled by default. Supports CSV or Parquet format (Parquet default). Cache is parameter-level: same function + same parameters = cache hit, with no subset matching. Default location: `~/.pybaseball/cache`. (source: pybaseball-readme.md)

```python
from pybaseball import cache

cache.enable()
cache.disable()
cache.purge()
```

## Version and Metadata

- Version: 2.2.7 (September 8, 2023)
- License: MIT
- Author: James LeDoux
- Maintainer: Moshe Schorr
- Python: 3.8, 3.9, 3.10, 3.11
- Inspired by Bill Petti's R package baseballr

(source: pybaseball-readme.md)

## Sub-Pages

- [[pybaseball-statcast]] — Statcast pitch-level data, fielding, running, spin analysis
- [[pybaseball-batting-pitching]] — Individual batting and pitching stats (FanGraphs, Baseball Reference, splits, WAR)
- [[pybaseball-team-game]] — Team stats, game logs, standings, team ID lookup
- [[pybaseball-historical]] — Lahman database and Retrosheet historical data
- [[pybaseball-player-lookup]] — Player ID lookup and Chadwick Bureau register
- [[pybaseball-plotting]] — Visualization functions (stadium plots, spraycharts, strike zones)
- [[pybaseball-draft-prospects]] — Amateur draft data and top prospects
