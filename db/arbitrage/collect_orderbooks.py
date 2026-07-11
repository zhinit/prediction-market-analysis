from __future__ import annotations

import asyncio
import json
import signal
import time
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import websockets
from dotenv import load_dotenv

from db.shared.auth import load_ed25519_key, load_rsa_key, require_env, sign_ed25519, sign_rsa

_MATCHES_PATH = Path("db/arbitrage/matches.json")
_DB_PATH = Path("db/pma.db")

_KALSHI_WS_URL = "wss://external-api-ws.kalshi.com/trade-api/ws/v2"
_POLY_WS_URL = "wss://api.polymarket.us/v1/ws/markets"

_BATCH_SIZE = 100
_FLUSH_INTERVAL = 30.0


def _init_db(path: Path) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(str(path))
    con.sql("""
        CREATE TABLE IF NOT EXISTS orderbook_snapshots (
            timestamp TEXT,
            platform TEXT,
            market_id TEXT,
            match_id TEXT,
            best_bid TEXT,
            best_ask TEXT,
            bid_size TEXT,
            ask_size TEXT,
            mid_price TEXT
        )
    """)
    con.sql("""
        CREATE OR REPLACE VIEW orderbook_snapshots_typed AS
        SELECT
            CAST(timestamp AS TIMESTAMP) AS timestamp,
            platform,
            market_id,
            match_id,
            CAST(best_bid AS DECIMAL(18, 6)) AS best_bid,
            CAST(best_ask AS DECIMAL(18, 6)) AS best_ask,
            CAST(bid_size AS DECIMAL(18, 6)) AS bid_size,
            CAST(ask_size AS DECIMAL(18, 6)) AS ask_size,
            CAST(mid_price AS DECIMAL(18, 6)) AS mid_price
        FROM orderbook_snapshots
    """)
    return con


def _load_matches() -> list[dict]:
    if not _MATCHES_PATH.exists():
        raise SystemExit(f"{_MATCHES_PATH} not found. Run /matcher first.")
    matches = json.loads(_MATCHES_PATH.read_text())
    if not matches:
        raise SystemExit(f"{_MATCHES_PATH} is empty. Run /matcher first.")
    return matches


class SnapshotWriter:
    def __init__(self, con: duckdb.DuckDBPyConnection) -> None:
        self._con = con
        self._buffer: list[dict] = []
        self._last_flush = time.monotonic()

    def add(self, snapshot: dict) -> None:
        self._buffer.append(snapshot)
        if (
            len(self._buffer) >= _BATCH_SIZE
            or time.monotonic() - self._last_flush >= _FLUSH_INTERVAL
        ):
            self.flush()

    def flush(self) -> None:
        if not self._buffer:
            return
        import polars as pl
        df = pl.DataFrame(self._buffer)
        self._con.sql("INSERT INTO orderbook_snapshots BY NAME SELECT * FROM df")
        count = len(self._buffer)
        self._buffer.clear()
        self._last_flush = time.monotonic()
        print(f"  Flushed {count} snapshots", flush=True)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class KalshiOrderbook:
    def __init__(self) -> None:
        self.yes_bids: dict[int, int] = {}
        self.no_bids: dict[int, int] = {}
        self.seq: int = -1
        self.needs_snapshot: bool = True

    def apply_snapshot(self, data: dict) -> None:
        self.yes_bids.clear()
        self.no_bids.clear()
        for price, qty in data.get("yes", []):
            self.yes_bids[price] = qty
        for price, qty in data.get("no", []):
            self.no_bids[price] = qty
        self.seq = data.get("seq", 0)
        self.needs_snapshot = False

    def apply_delta(self, data: dict) -> bool:
        seq = data.get("seq", 0)
        if self.needs_snapshot or seq != self.seq + 1:
            self.needs_snapshot = True
            return False
        self.seq = seq
        for price, qty in data.get("yes", []):
            if qty == 0:
                self.yes_bids.pop(price, None)
            else:
                self.yes_bids[price] = qty
        for price, qty in data.get("no", []):
            if qty == 0:
                self.no_bids.pop(price, None)
            else:
                self.no_bids[price] = qty
        return True

    def best_bid_ask(self) -> tuple[float, float, float, float]:
        # YES best bid
        best_bid = max(self.yes_bids.keys(), default=0) / 100
        bid_size = self.yes_bids.get(int(best_bid * 100), 0) / 100

        # NO bids → YES asks (YES ask = 1 - NO bid price)
        no_prices = sorted(self.no_bids.keys(), reverse=True)
        if no_prices:
            best_no_bid = no_prices[0] / 100
            yes_ask_from_no = 1.0 - best_no_bid
        else:
            yes_ask_from_no = 1.0

        best_ask = yes_ask_from_no
        ask_size = self.no_bids.get(int(no_prices[0]), 0) / 100 if no_prices else 0

        return best_bid, best_ask, bid_size, ask_size


async def _kalshi_ws(
    matches: list[dict],
    writer: SnapshotWriter,
    shutdown: asyncio.Event,
) -> None:
    api_key_id = require_env("KALSHI_API_KEY_ID")
    private_key = load_rsa_key(Path(require_env("KALSHI_PRIVATE_KEY_PATH")))

    kalshi_tickers = {m["kalshi_ticker"]: m["id"] for m in matches}
    if not kalshi_tickers:
        return

    backoff = 1.0
    while not shutdown.is_set():
        try:
            timestamp, signature = sign_rsa(private_key, "GET", "/trade-api/ws/v2")
            headers = {
                "KALSHI-ACCESS-KEY": api_key_id,
                "KALSHI-ACCESS-TIMESTAMP": timestamp,
                "KALSHI-ACCESS-SIGNATURE": signature,
            }
            print(f"Kalshi WS: connecting...", flush=True)
            async with websockets.connect(
                _KALSHI_WS_URL, additional_headers=headers,
            ) as ws:
                print(f"Kalshi WS: connected", flush=True)
                backoff = 1.0

                sub_msg = json.dumps({
                    "id": 1,
                    "cmd": "subscribe",
                    "params": {
                        "channels": ["orderbook_delta"],
                        "market_tickers": list(kalshi_tickers.keys()),
                    },
                })
                await ws.send(sub_msg)

                orderbooks: dict[str, KalshiOrderbook] = {
                    t: KalshiOrderbook() for t in kalshi_tickers
                }

                async for raw in ws:
                    if shutdown.is_set():
                        break
                    msg = json.loads(raw)
                    msg_type = msg.get("type")
                    ticker = msg.get("msg", {}).get("market_ticker", "")

                    if ticker not in orderbooks:
                        continue

                    ob = orderbooks[ticker]
                    if msg_type == "orderbook_snapshot":
                        ob.apply_snapshot(msg["msg"])
                    elif msg_type == "orderbook_delta":
                        if not ob.apply_delta(msg["msg"]):
                            print(f"Kalshi: seq gap on {ticker}, requesting re-snapshot", flush=True)
                            continue

                    if ob.needs_snapshot:
                        continue

                    bid, ask, bid_sz, ask_sz = ob.best_bid_ask()
                    mid = (bid + ask) / 2 if bid > 0 and ask < 1 else 0
                    writer.add({
                        "timestamp": _now_iso(),
                        "platform": "kalshi",
                        "market_id": ticker,
                        "match_id": kalshi_tickers[ticker],
                        "best_bid": str(round(bid, 4)),
                        "best_ask": str(round(ask, 4)),
                        "bid_size": str(round(bid_sz, 2)),
                        "ask_size": str(round(ask_sz, 2)),
                        "mid_price": str(round(mid, 4)),
                    })

        except Exception as e:
            if shutdown.is_set():
                break
            print(f"Kalshi WS error: {e}. Reconnecting in {backoff:.0f}s...", flush=True)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)


async def _poly_ws(
    matches: list[dict],
    writer: SnapshotWriter,
    shutdown: asyncio.Event,
) -> None:
    api_key_id = require_env("POLYMARKET_US_API_KEY_ID")
    private_key = load_ed25519_key(require_env("POLYMARKET_US_PRIVATE_KEY"))

    # Multiple matches can share a slug; build slug→list[match] map
    slug_to_matches: dict[str, list[dict]] = {}
    for m in matches:
        slug_to_matches.setdefault(m["polymarket_slug"], []).append(m)
    if not slug_to_matches:
        return

    all_slugs = list(slug_to_matches.keys())

    backoff = 1.0
    while not shutdown.is_set():
        try:
            timestamp, signature = sign_ed25519(private_key, "GET", "/v1/ws/markets")
            headers = {
                "X-PM-Access-Key": api_key_id,
                "X-PM-Timestamp": timestamp,
                "X-PM-Signature": signature,
            }
            print(f"Polymarket WS: connecting...", flush=True)
            async with websockets.connect(
                _POLY_WS_URL, additional_headers=headers,
            ) as ws:
                print(f"Polymarket WS: connected", flush=True)
                backoff = 1.0

                # Max 100 slugs per subscription
                for i in range(0, len(all_slugs), 100):
                    batch = all_slugs[i:i + 100]
                    sub_msg = json.dumps({
                        "subscribe": {
                            "requestId": f"md-sub-{i}",
                            "subscriptionType": "SUBSCRIPTION_TYPE_MARKET_DATA",
                            "marketSlugs": batch,
                        },
                    })
                    await ws.send(sub_msg)
                    print(f"  Subscribed to {len(batch)} Poly slugs (batch {i // 100 + 1})", flush=True)

                async for raw in ws:
                    if shutdown.is_set():
                        break
                    msg = json.loads(raw)

                    if "error" in msg:
                        print(f"Polymarket WS error msg: {msg['error']}", flush=True)
                        continue

                    md = msg.get("marketData", {})
                    if not md:
                        continue
                    slug = md.get("marketSlug", "")
                    if slug not in slug_to_matches:
                        continue

                    for match_info in slug_to_matches[slug]:
                        bids = md.get("bids", [])
                        offers = md.get("offers", [])

                        best_bid = 0.0
                        bid_size = 0.0
                        if bids:
                            top = max(bids, key=lambda b: float(b.get("px", {}).get("value", "0")))
                            best_bid = float(top.get("px", {}).get("value", "0"))
                            bid_size = float(top.get("qty", "0"))

                        best_ask = 1.0
                        ask_size = 0.0
                        if offers:
                            top = min(offers, key=lambda a: float(a.get("px", {}).get("value", "1")))
                            best_ask = float(top.get("px", {}).get("value", "1"))
                            ask_size = float(top.get("qty", "0"))

                        mid = (best_bid + best_ask) / 2 if best_bid > 0 and best_ask < 1 else 0

                        direction = match_info.get("direction", "kalshi_yes_eq_poly_yes")
                        if direction == "kalshi_yes_eq_poly_no":
                            best_bid, best_ask = 1 - best_ask, 1 - best_bid
                            bid_size, ask_size = ask_size, bid_size
                            mid = (best_bid + best_ask) / 2

                        writer.add({
                            "timestamp": _now_iso(),
                            "platform": "polymarket",
                            "market_id": slug,
                            "match_id": match_info["id"],
                            "best_bid": str(round(best_bid, 4)),
                            "best_ask": str(round(best_ask, 4)),
                            "bid_size": str(round(bid_size, 2)),
                            "ask_size": str(round(ask_size, 2)),
                            "mid_price": str(round(mid, 4)),
                        })

        except Exception as e:
            if shutdown.is_set():
                break
            print(f"Polymarket WS error: {e}. Reconnecting in {backoff:.0f}s...", flush=True)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)


async def _run() -> None:
    matches = _load_matches()
    print(f"Loaded {len(matches)} matches from {_MATCHES_PATH}")

    con = _init_db(_DB_PATH)
    writer = SnapshotWriter(con)

    shutdown = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _signal_handler():
        print("\nShutting down...", flush=True)
        shutdown.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    tasks = [
        asyncio.create_task(_kalshi_ws(matches, writer, shutdown)),
        asyncio.create_task(_poly_ws(matches, writer, shutdown)),
    ]

    await shutdown.wait()

    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    writer.flush()
    con.close()
    print("Done. Final flush complete.")


def main() -> None:
    load_dotenv()
    asyncio.run(_run())


if __name__ == "__main__":
    main()
