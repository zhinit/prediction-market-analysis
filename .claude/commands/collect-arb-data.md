Collect live orderbook snapshots from Kalshi and Polymarket US for all matched markets.

## Steps

1. Check that `db/data/matches.json` exists and is non-empty. If not, say "Run /matcher first to create matches" and stop.
2. Run:
   ```
   uv run python db/scripts/collect_orderbooks.py
   ```
3. Monitor stdout for connection status lines. Both websockets should report "connected" within a few seconds.
4. The script runs until interrupted (Ctrl+C / SIGINT). It flushes remaining snapshots on shutdown.
5. After stopping, verify data was collected:
   ```
   uv run python -c "import duckdb; con = duckdb.connect('db/pma.db'); con.sql('SELECT platform, count(*) FROM orderbook_snapshots GROUP BY platform').show(); con.close()"
   ```
