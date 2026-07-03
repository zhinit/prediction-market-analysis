# MLB data pull: schedule, game data, Kalshi join

**Status: implemented and run, 2026-07-03.** All scripts exist, the data
is in `db/pma.db`, and `uv run pytest tests/` passes (52 tests).
Re-run everything with `uv run db/scripts/refresh.py`; every step is
incremental except the map, which rebuilds from scratch by design.

Pull MLB reference data from the MLB Stats API (base URL
`https://statsapi.mlb.com/api/v1`, no auth) and join it to the Kalshi
markets already in `db/pma.db`. This is Step 1 of
[first_analysis](first_analysis.md), which needs home/away labels and
(if available) inning times.

## Architecture

One pull script per source, a separate join script, a thin orchestrator:

```
db/scripts/pull_kalshi_mlb.py       -- exists; mirror Kalshi → db
db/scripts/pull_mlb_stats.py        -- new; mirror MLB Stats API → db
db/scripts/build_kalshi_mlb_map.py  -- new; derive ticker ↔ gamePk map
db/scripts/refresh.py               -- new; runs pulls, then the map
```

- Pull scripts are dumb mirrors of their source; the map script holds all
  join logic and is cheap to re-run alone.
- `refresh.py` imports and calls each script's `main()`; every script
  keeps `if __name__ == "__main__"` so it also runs standalone.
- Same stack as the Kalshi pull ([[data-pipeline-stack]]): httpx →
  tenacity → pydantic → polars → duckdb. Same db conventions: raw TEXT
  tables, typed views, `INSERT OR REPLACE BY NAME`, resume by skipping
  completed rows.
- Adding a future source = new pull script + one line in `refresh.py`
  + extend the map.

## Step 1 — spike (by hand, before any code)

Two unknowns the wiki can't answer ([[mlb-stats-api-game]]). Check one
completed game (gamePk from `/schedule` for a known date):

- Does `/game/{gamePk}/playByPlay` carry wall-clock timestamps per play?
  If not, the analysis falls back to hourly snapshots and playByPlay is
  not worth pulling.
- Does `/game/{gamePk}/feed/live` 404 for completed games? It is the
  only documented weather source; if it 404s, check `boxscore.info`,
  else descope weather.

Record the answers in this file; they decide Step 3's scope.

**Spike answers (2026-07-03, gamePk 777505, completed 2025-06-15 game):**

- `playByPlay` plays DO carry wall-clock UTC timestamps
  (`about.startTime` / `about.endTime` per play) → inning-level
  bucketing is possible; pull a slim plays table.
- `/feed/live` (v1.1 path) returns 200 for completed games, weather
  present. With `?fields=gameData,weather,condition,temp,wind` the
  response is ~90 bytes vs ~850 KB → weather is cheap; include it.
- Ticker conventions verified against the schedule
  (`KXMLBGAME-26APR301235STLPIT` ↔ gamePk 823391, gameDate
  2026-04-30T16:35Z, away STL @ home PIT): ticker time is
  **US/Eastern**, team pair is **away then home**.
- 2025 tickers have **no time component** (`KXMLBGAME-25SEP24KCLAA`);
  doubleheaders carry a `G1`/`G2` or bare-digit suffix
  (`...BALDETG1`, `...MIAPHI2`). The start time was added for 2026.
- Kalshi team abbreviations (from market ticker suffixes): 30 teams
  matching MLB abbrs, except Arizona appears as both `ARI` and `AZ`;
  All-Star events use `ALHS`/`ALLS`/`NLHS`/`NLLS` (excluded).
- Skip `linescore`: inning times come from playByPlay; the analysis
  doesn't need inning-by-inning runs.

## Step 2 — `pull_mlb_stats.py`: schedule ✅

- `GET /schedule?sportId=1&startDate=...&endDate=...` in monthly chunks,
  2025-04-16 → today **+10 days** (so already-listed Kalshi markets for
  upcoming games can be mapped). No pagination, no auth.
- Table `mlb_games`: `game_pk` (PK), `game_date`, `official_date`,
  `game_type`, `double_header`, `game_number`, state, home/away team
  id/name/score/winner, venue, `day_night`. Typed view `mlb_games_typed`.
  Team abbreviations are not in the schedule response; the map script
  carries the Kalshi-abbr → MLB-team-id table instead.
- Reuses the retry policy from the Kalshi script (timeouts, 429, 5xx).
- Filtered to game types R, F, D, L, W (no spring training, exhibition,
  All-Star). 3,671 games as of 2026-07-03.

## Step 3 — `pull_mlb_stats.py`: per-game endpoints ✅

Pulled for **all Final games** in the window (not just Kalshi-matched
ones — keeps the mirror independent of the map; ~4% waste):

- `/game/{gamePk}/playByPlay` → `mlb_plays` — slim rows: inning,
  half-inning, wall-clock start/end per play, event, running score.
  ~940k plays.
- `/game/{gamePk}/winProbability` → `mlb_win_probability` —
  comparison series for Kalshi prices.
- `/feed/live?fields=...` (v1.1) → `mlb_weather`.
- `linescore` skipped per the spike.

3,522 games × 3 endpoints, ~10 minutes: 5 games concurrently
(semaphore), the 3 endpoints per game gathered. Resume via an
`mlb_game_pulls` bookkeeping table (a row = game fully pulled); a 404
on any endpoint is recorded and skipped, other errors fail the run.

## Step 4 — `build_kalshi_mlb_map.py` ✅

- Parses each event ticker into date, start time (2026 format only),
  team pair, and doubleheader game number (2025 format only). The pair
  is split using the event's two market-ticker suffixes.
- Match order per event: date + team pair, then doubleheaders resolved
  by G1/G2 game number → settlement-vs-actual-game-end → scheduled-start
  proximity. Postponed games fall back to settlement matching against
  any pair game up to 200 days out (see Implementation notes).
- Output: table `kalshi_mlb_map` (event_ticker PK, game_pk, away/home
  abbr + team id, ticker_start_utc, orientation_ok,
  start_delta_minutes, match_method 'date' | 'settlement').
- Prints the match report (counts by method, every unmatched ticker
  with reason) and hard-asserts: away-then-home orientation on all date
  matches, match rate ≥ 99%, and zero finalized yes/no markets whose
  result disagrees with the schedule winner.

## Step 5 — `refresh.py` ✅

- Imports `main()` from both pull scripts and the map script; runs the
  two pulls sequentially (duckdb allows one writer per database), then
  the map.
- Prints the match report at the end of every run.

## Testing ✅

All in `tests/` (the repo's existing test location, not `db/tests/`),
run with `uv run pytest tests/`. 52 tests as of 2026-07-03.

- `tests/test_kalshi_mlb_map.py` — 24 unit tests on the pure functions
  (no network, no db): ticker parsing for both formats incl. DST and
  malformed tickers, pair splitting, team-abbreviation map, and game
  selection (doubleheaders by game number / settlement / start time,
  postponement fallback, zombie-settlement rejection).
- `tests/test_mlb_data_quality.py` — post-run checks against the db:
  tables/views exist and are populated, typed views cast cleanly,
  every Final game has scores + exactly one winner + plays, play
  timestamps within 48h of scheduled start (suspended games span two
  days), win probabilities sum to 100, map uniqueness, match rate
  ≥ 99%, result-vs-winner agreement, no scalar market mapped.
- The map script itself hard-asserts on every run (see Step 4), so a
  bad refresh fails loudly rather than writing a quietly wrong map.
- The result-vs-winner check ended up much stronger than the planned
  "spot-check a sample": it covers every checkable finalized market
  (7,028 as of the last run, 0 disagreements).

The planned "each gamePk maps to exactly 2 markets" check was dropped —
it is false in reality (duplicate Kalshi listings; see Implementation
notes).

## Implementation notes (2026-07-03)

Findings from building the map that the plan did not foresee:

- **Postponed games.** ~50 events reference a game that was postponed;
  their markets stayed open and settled on the makeup game (sometimes
  months later, at the opponent's next visit). Matched via a settlement
  fallback: the makeup is the pair game whose actual last-play end time
  (from `mlb_plays`) immediately precedes the market's `close_time`
  (`match_method = 'settlement'` in `kalshi_mlb_map`).
- **Traditional doubleheaders** list both games with scheduled starts
  minutes apart, so start-time proximity cannot disambiguate; settlement
  time against actual game end does.
- **Cancelled games** (10 events) settle with `result = 'scalar'` and are
  deliberately left unmatched — a scalar mis-match would be invisible to
  the result-vs-winner check.
- **Duplicate listings**: 7 zombie events from 2025-04-18 (opened the day
  after the game, near-zero volume) mean event↔game is not strictly 1:1;
  the map reports multi-event games instead of asserting uniqueness.
- Final numbers (refresh of 2026-07-03): 3,558/3,568 game events matched
  (99.72%; 3,506 by date, 52 by settlement); all 10 unmatched are
  cancelled games; all 7,028 checkable finalized markets agree with the
  schedule winner.

## Order

Spike → schedule pull → map + its tests → per-game endpoints (scope from
spike) → orchestrator. The schedule pull + map alone unblock the
home/away and pre-game/in-game cuts in
[first_analysis](first_analysis.md).
