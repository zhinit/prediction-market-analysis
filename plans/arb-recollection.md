# Plan: Arbitrage Recollection and Daily Analysis Refresh

Read this file at the start of any session touching the arbitrage analysis.
The **Status** section at the bottom says where we are; do the next unchecked
step and update the log when done.

## Why we are recollecting

The July 23-24 collection (19 games, currently in `db/arb_orderbooks.db` and
analyzed in `analysis/cross_platform_arbitrage.ipynb`) stamped every orderbook
snapshot with local DB-insert time, not exchange time. Polymarket's
`transactTime` was stored but unused; Kalshi's `ts_ms` was not collected at
all. With median episode durations of 0.2s and one-sided collection lag
measured at 74-390ms, sub-second episode durations carry measurement noise on
the same scale as the measurement.

Fixes already made (2026-07-29, all verified):

- `db/arbitrage/collector.py` — Kalshi snapshots and deltas now store `ts_ms`
  in `source_timestamp`. Polymarket already stored `transactTime`.
- `db/arbitrage/matcher.py` — doubleheaders no longer collide: Kalshi
  candidates are kept per team pair and resolved against Polymarket's
  `game_start_time` by nearest scheduled start (`pick_kalshi`,
  6h tolerance). Ambiguous cases are skipped and logged, never mismatched.
- `db/arbitrage/storage.py` + `collector.py` — `save_matched_markets` upserts
  on `kalshi_event_ticker` instead of deleting the whole date, and the
  collector subscribes to the union of today's pairs from the DB. A restart
  no longer drops pairs matched by an earlier run (this is what orphaned
  SD@ATL on July 23).

## The rules for the new analysis

1. **New data only.** The July 23-24 data is excluded entirely. It stays in
   the DB untouched; the analysis filters it out with a cutoff (see
   `NEW_DATA_START` below).
2. **Exchange timestamps, not insert timestamps.** `prepare_arb_analysis.py`
   must build `arb_bbo`/`arb_states`/`arb_episodes` on `source_timestamp`:
   Kalshi rows hold epoch milliseconds as a string ("1669149841000"),
   Polymarket rows hold ISO UTC strings ("2026-07-24T23:25:21Z"). Normalize
   both to UTC timestamps. The local `timestamp` column remains only as a
   fallback ordering tiebreaker and for the blackout windows
   (`collection_metadata` has only local time; it is naive US/Eastern, so
   convert before comparing).
3. **The current notebook structure is kept.** Same sections, same charts
   (including the biggest-opportunity case study, direction table, and
   conclusion); only the data window and numbers change. The July 23-24
   version of the notebook is preserved in git history — commit before the
   first refresh.

## Daily loop

Day 0 (before first collection) — code prep:

- [x] Commit the current state (collector/matcher/storage/prepare fixes +
      notebook + this plan). Done as 85d3a36.
- [x] Rework `db/arbitrage/prepare_arb_analysis.py` per rule 2 (done
      2026-07-29): `arb_bbo` is built on `source_timestamp` normalized to
      naive UTC (Kalshi `epoch_ms`, Polymarket ISO cast), with the local
      insert time kept as `recv_ts` for tiebreaks and diagnostics; rows with
      NULL `source_timestamp` are dropped and warned about; blackout windows
      convert `collection_metadata`'s local Eastern times to UTC.
      `NEW_DATA_START = "2026-07-25"` excludes the old collection without
      needing to know the actual restart day. Verified on a synthetic DB:
      cutoff exclusion, epoch-ms/ISO alignment at the same instant,
      a 2.000s episode measured from exchange time, and blackout exclusion
      through the timezone conversion.
- [x] After day 1's data exists, sanity-check: every kalshi row has non-null
      `source_timestamp`; lag distributions (local minus source) look like
      tens to hundreds of ms on both platforms; doubleheader days match 2
      distinct Kalshi events for the shared team pair. Done 2026-07-31:
      68 of 5.9M kalshi rows null (dropped by prepare); lag after removing
      the -4h naive-Eastern offset is Kalshi p50 17ms / p99 235ms,
      Polymarket p50 67ms / p99 273ms; no doubleheaders on the July 30
      slate so that check was vacuous.

Each collection day (user runs the collector; then, in a session):

1. `uv run db/arbitrage/prepare_arb_analysis.py` — rebuild tables on all new
   days collected so far. Check the built-in `check()` passes and the
   per-game episode report looks sane.
2. Re-execute the notebook:
   `uv run --with jupyter jupyter nbconvert --to notebook --execute --inplace analysis/cross_platform_arbitrage.ipynb`
3. Update the notebook's Data section (dates covered, game count) and the
   hardcoded numbers in markdown cells if they drifted from the outputs
   (episode counts in prose, the case-study episode if a bigger one appears —
   the case-study cell hardcodes game_key, timestamps, and annotation).
4. Append a line to the Status log below (date, days of data, games,
   gross/net episodes, anything anomalous).
5. Commit.

## After a few days of collection

When the user says collection is done (target: at least 3-5 days):

- [ ] Final notebook pass: refresh all prose numbers, re-check the case
      study choice, confirm the conclusion's counts ($ values, 1s+ episode
      count) match outputs.
- [ ] Write-up in `write_ups/` following the pattern of
      `write_ups/mlb_game_winners_analysis.md` (exported plots via
      `write_ups/export_plots.py`). Conclusions and methodology notes go to
      `docs/` per repo conventions.
- [ ] User publishes to zh_init (their step).

## Known caveats that carry over (state them in the write-up)

- Fee coefficients: Kalshi 0.07 taker, Polymarket US 0.06 taker (raised from
  0.05 on 2026-07-01 per [[polymarket-us-fees]]). Verify neither changed
  before the write-up.
- Polymarket US taker delay (1-3s) is documented for the international
  platform's docs; live poka-arb trading confirmed the kill pattern on
  Polymarket US sports markets (15 of 16 FOK hedges killed, May-June 2026).
- Kalshi lag is measurable in the new data; with exchange timestamps on both
  feeds the old timestamp caveat is moot, which is the point of recollecting.

## Status

**Current state: Day 3 refresh done (July 30 - August 1 data), real DB
synced.** The notebook is rebuilt on 3 days / 40 games of
exchange-timestamped data — the collection target of 3-5 days is within
reach. The collector was stopped 2026-08-02 and `prepare_arb_analysis.py`
was run against the real DB, so its `arb_*` tables are now current and
the notebook runs with no env var. (The rebuild differed from the copy's
by 9 of 3.5M states / 1 of 8,871 sub-fee gross episodes — tie-order
noise on equal timestamps; all net results identical. Notebook
re-executed against the real DB.) The notebook's DB path honors an
`ARB_DB` env var (defaults to `../db/arb_orderbooks.db`) for future
locked-DB refreshes.
LESSON for trimming a copy: never cut at local midnight — West-coast games
run past midnight ET, so a midnight cut truncates live games (this
truncated 3 games in the day-1 refresh; healed in day 2). Cut at a real
collection gap instead (e.g. day-2 trim was at 08:00 Aug 1: overnight
collection ended 01:15, the day-3 collector started 08:26).

Log (append one line per session that advances this plan):

- 2026-07-29 — Plan created. Collector fixes verified (13/13 matched on
  today's slate; upsert and doubleheader unit tests pass). Old notebook
  finalized on July 23-24 data (conclusion, case study, direction sections
  added).
- 2026-07-29 — Prepare script reworked to exchange time and verified on a
  synthetic DB (scratchpad test, not committed). Real DB untouched.
- 2026-07-31 — Day 1 refresh: 1 day (July 30), 10 games, 2,682 gross /
  123 net episodes, $211.48 total theoretical value, 20 episodes ≥1s worth
  $7.08 ($0.71/game). Direction counts 66 buy_kalshi / 57 buy_poly but
  value $176 vs $35, driven by 4 large-bottleneck buy_kalshi episodes.
  New case study: TEX@TB 11.83¢ × 41 contracts, 13ms. Ran against a
  trimmed DB copy (collector held the lock; see Current state) — real DB's
  arb_* tables still stale. Sanity checks passed (see Day 0 checklist).
- 2026-08-01 — Day 2 refresh: 2 days (July 30-31), 25 games, 5,814 gross /
  321 net episodes, $287.03 total value, 52 episodes ≥1s worth $10.14
  ($0.41/game). Direction 157 buy_kalshi / 164 buy_poly, value $210 vs
  $77 (same 4 July-30 episodes ≈ $152). Case study unchanged (TEX@TB
  still largest with size). July 31: 15 pairs, 112 null-src rows, lag
  p50 19ms/79ms, no doubleheaders. Ran against a copy again (day-3
  collection was live); trimmed at Aug 1 08:00 — see the midnight-trim
  lesson in Current state.
- 2026-08-02 — Day 3 refresh: 3 days (July 30 - Aug 1), 40 games, 8,871
  gross / 480 net episodes, $405.89 total value, 71 episodes ≥1s worth
  $27.38 ($0.68/game). Direction dead even 240/240, value $257 vs $149.
  New case study: NYY@CHC (Aug 1) 19.41¢ × 138 contracts, 42ms. The
  Aug-1 collector ran overnight and never re-matched Aug 2, so the copy
  needed NO trim (data ends 00:55 Aug 2 local, all belonging to Aug 1
  games). Aug 1 checks passed: 15 pairs, 140 null-src rows dropped, lag
  p50 14ms/68ms, no doubleheaders. Real DB arb_* tables still stale.
