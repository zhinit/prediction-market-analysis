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

- [ ] Commit the current state (collector/matcher/storage/prepare fixes +
      notebook + this plan).
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
- [ ] After day 1's data exists, sanity-check: every kalshi row has non-null
      `source_timestamp`; lag distributions (local minus source) look like
      tens to hundreds of ms on both platforms; doubleheader days match 2
      distinct Kalshi events for the shared team pair.

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

**Current state: Day 0 prep — code is ready, nothing committed.** All code
work is done (collector timestamps, doubleheader matching, upsert, prepare
rework). Next steps: commit everything, then the user starts collecting.
IMPORTANT: running `prepare_arb_analysis.py` now would wipe the July 23-24
`arb_*` tables the current notebook reads (it rebuilds them empty, since no
post-cutoff data exists yet) — do not run it until there is new data, and
re-execute the notebook only against tables that match its data window.

Log (append one line per session that advances this plan):

- 2026-07-29 — Plan created. Collector fixes verified (13/13 matched on
  today's slate; upsert and doubleheader unit tests pass). Old notebook
  finalized on July 23-24 data (conclusion, case study, direction sections
  added).
- 2026-07-29 — Prepare script reworked to exchange time and verified on a
  synthetic DB (scratchpad test, not committed). Real DB untouched.
