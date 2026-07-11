"""Refresh db/pma.db from all sources, then rebuild derived tables.

Runs the Kalshi and MLB pulls sequentially (duckdb allows one writer per
database), then build_kalshi_mlb_map. Each script also runs standalone:

    uv run db/game_winners/refresh.py
"""

import asyncio

from db.game_winners import build_kalshi_mlb_map
from db.game_winners import pull_kalshi_mlb
from db.game_winners import pull_mlb_stats


async def main() -> None:
    print("=== Kalshi pull ===")
    await pull_kalshi_mlb.main()
    print("=== MLB Stats pull ===")
    await pull_mlb_stats.main()
    print("=== Kalshi <-> MLB map ===")
    build_kalshi_mlb_map.main()


if __name__ == "__main__":
    asyncio.run(main())
