# First analysis: Kalshi MLB calibration

Are Kalshi MLB game prices honest probabilities? Bucket YES trade prices,
compare each bucket's implied probability to the empirical YES frequency,
and slice the result several ways.

## Data

- `db/pma.db` (DuckDB): `events`, `markets_typed`, `trades_typed`.
- ~7,008 finalized yes/no MLB game markets (3,500 yes / 3,508 no),
  ~25.3M trades, 2025-04-16 through 2026-07-02.
- YES side only. Both markets of each game are kept (mirror pairs), so the
  overall curve is symmetric around 50c by construction — the notebook states
  this; asymmetries show up in the team/home-away cuts.
- Exclusions: 82 active markets, 20 scalar markets, All-Star markets
  (`yes_sub_title` in AL/NL).
- Cleaning: normalize "Chicago W" / "Chicago WS" to one label.

## Step 1 — pull MLB reference data (before analysis)

Kalshi data has no home/away labels and no inning info. Pull from the MLB
Stats API — already researched in the wiki ([[mlb-stats-api]],
[[mlb-stats-api-schedule]], [[mlb-stats-api-game]], [[mlb-team-ids]]):

- Schedule (`/schedule?sportId=1&startDate=...&endDate=...`): `gamePk`,
  `gameDate`, `teams.home` / `teams.away`, `gameType`, `doubleHeader` —
  join to Kalshi tickers (ticker encodes date + start time + team pair,
  e.g. `KXMLBGAME-26JUN291910WSHBOS-WSH`).
- Verify the ticker's team-order convention against the schedule before
  trusting any home/away derivation.
- Inning times: `/game/{gamePk}/playByPlay` has `about.inning` /
  `about.halfInning` per play; the wiki does not document wall-clock
  timestamps on plays — check one game empirically before committing to
  inning-level bucketing (fallback: hourly snapshots).
- Weather: `/feed/live` returns `gameData.weather`, but may 404 for
  completed historical games — check empirically.
- Bonus join candidate: `/game/{gamePk}/winProbability` (MLB's model
  probability per play) as a comparison series for Kalshi prices.
- Reuse the `db/scripts/pull_kalshi_mlb.py` stack: httpx → tenacity →
  pydantic → polars → duckdb ([[data-pipeline-stack]]).

## Step 2 — notebook in `analysis/`

Methodology:

- Per-trade calibration, volume-weighted (`count_fp`): every YES trade at
  price p is an observation; did the market resolve yes?
- 5c price buckets overall; 10c buckets for team-level cuts.
- Wilson confidence intervals on every bucket. Note that trades within a
  game are not independent — effective sample size is closer to game count.
- Split pre-game vs in-game at scheduled start (from ticker).

Cuts:

| # | Cut | Form |
|---|-----|------|
| 1 | Overall calibration curve, 5c buckets | plot |
| 2 | Snapshots: pre-game, then by inning (hourly fallback) | small multiples |
| 3 | By team (30 teams) | small-multiples grid, 10c buckets, shared axes + table (n, avg price, win rate, deviation) |
| 4 | Home vs away | two curves + table |

Held for a second pass: trade size, taker side (78% of trades are
YES-taker), day/night, liquidity tiers, by month.

Descoped: time-to-close buckets within pre-game.

## Output

- Notebook + written summary in `analysis/`.
- Conclusions, if any, go to `docs/`.
