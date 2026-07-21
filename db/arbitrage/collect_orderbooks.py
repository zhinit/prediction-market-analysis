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

# Consecutive crossed (best_bid >= best_ask) reconstructions on one market
# before the connection is reset to pull fresh snapshots.
_CROSSED_RESNAPSHOT = 25


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
    # add() must never do I/O: it is called from inside the websocket receive
    # loops, and a synchronous DuckDB insert there blocks the event loop long
    # enough — on a hot market — that the local orderbook drifts into a stale,
    # crossed state (best_ask decays and sticks below best_bid). Instead, add()
    # only appends to an in-memory buffer; a dedicated writer task swaps the
    # buffer out and flushes it in a worker thread (see write_loop / flush),
    # so the receive loops are never blocked on the database.
    def __init__(self, con: duckdb.DuckDBPyConnection) -> None:
        self._con = con
        self._buffer: list[dict] = []

    def add(self, snapshot: dict) -> None:
        self._buffer.append(snapshot)

    def take(self) -> list[dict]:
        """Atomically detach the pending buffer (safe on the loop thread)."""
        batch, self._buffer = self._buffer, []
        return batch

    def insert(self, batch: list[dict]) -> None:
        """Blocking DuckDB insert. Run off the event loop via asyncio.to_thread;
        never call two inserts concurrently (the writer task awaits each)."""
        if not batch:
            return
        import polars as pl
        df = pl.DataFrame(batch)
        self._con.sql("INSERT INTO orderbook_snapshots BY NAME SELECT * FROM df")
        print(f"  Flushed {len(batch)} snapshots", flush=True)

    def flush(self) -> None:
        """Synchronous flush of whatever is buffered (used at shutdown)."""
        self.insert(self.take())


async def _write_loop(writer: SnapshotWriter, shutdown: asyncio.Event) -> None:
    """Drain the writer buffer to DuckDB in a worker thread, off the event loop.
    Polls frequently and flushes on size or interval so the receive loops only
    ever append and the buffer cannot grow without bound under load."""
    last_flush = time.monotonic()
    while not shutdown.is_set():
        try:
            await asyncio.wait_for(shutdown.wait(), timeout=0.5)
        except asyncio.TimeoutError:
            pass
        now = time.monotonic()
        if len(writer._buffer) >= _BATCH_SIZE or now - last_flush >= _FLUSH_INTERVAL:
            batch = writer.take()
            if batch:
                await asyncio.to_thread(writer.insert, batch)
            last_flush = now
    # final drain
    batch = writer.take()
    if batch:
        await asyncio.to_thread(writer.insert, batch)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class KalshiOrderbook:
    # Kalshi WS v2 payloads (captured 2026-07-11): snapshots carry the full
    # book as [price_dollars_str, qty_str] pairs under yes_dollars_fp /
    # no_dollars_fp; deltas adjust a single price level via side /
    # price_dollars / delta_fp. seq lives on the message envelope and is
    # per-connection, so it is tracked in _kalshi_ws, not here.
    def __init__(self) -> None:
        self.yes_bids: dict[float, float] = {}
        self.no_bids: dict[float, float] = {}

    def apply_snapshot(self, data: dict) -> None:
        self.yes_bids.clear()
        self.no_bids.clear()
        for price, qty in data.get("yes_dollars_fp", []):
            self.yes_bids[float(price)] = float(qty)
        for price, qty in data.get("no_dollars_fp", []):
            self.no_bids[float(price)] = float(qty)

    def apply_delta(self, data: dict) -> None:
        book = self.yes_bids if data.get("side") == "yes" else self.no_bids
        price = float(data["price_dollars"])
        qty = book.get(price, 0.0) + float(data["delta_fp"])
        if qty <= 0:
            book.pop(price, None)
        else:
            book[price] = qty

    def best_bid_ask(self) -> tuple[float, float, float, float]:
        best_bid = max(self.yes_bids, default=0.0)
        bid_size = self.yes_bids.get(best_bid, 0.0)

        # NO bids → YES asks (YES ask = 1 - best NO bid price)
        if self.no_bids:
            best_no_bid = max(self.no_bids)
            best_ask = 1.0 - best_no_bid
            ask_size = self.no_bids[best_no_bid]
        else:
            best_ask = 1.0
            ask_size = 0.0

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
                _KALSHI_WS_URL, additional_headers=headers, max_queue=None,
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

                # Books are created on first snapshot; deltas arriving for a
                # ticker without a snapshot yet are skipped.
                orderbooks: dict[str, KalshiOrderbook] = {}
                conn_seq: int | None = None
                # A reconstructed book that reports best_bid >= best_ask is
                # locked/crossed and therefore corrupt (a real book cannot
                # cross). Never record such a state; if one market stays
                # crossed, the local book is stale, so reconnect to force a
                # fresh snapshot for every market on this connection.
                crossed_streak: dict[str, int] = {}

                async for raw in ws:
                    if shutdown.is_set():
                        break
                    msg = json.loads(raw)
                    msg_type = msg.get("type")
                    if msg_type not in ("orderbook_snapshot", "orderbook_delta"):
                        continue

                    # seq is per-connection: any gap means missed messages for
                    # unknown tickers, so reconnect for fresh snapshots.
                    seq = msg.get("seq")
                    if seq is not None:
                        if conn_seq is not None and seq != conn_seq + 1:
                            print(
                                f"Kalshi: seq gap ({conn_seq} -> {seq}),"
                                " reconnecting for fresh snapshots",
                                flush=True,
                            )
                            break
                        conn_seq = seq

                    ticker = msg.get("msg", {}).get("market_ticker", "")
                    if ticker not in kalshi_tickers:
                        continue

                    if msg_type == "orderbook_snapshot":
                        ob = orderbooks.setdefault(ticker, KalshiOrderbook())
                        ob.apply_snapshot(msg["msg"])
                    else:
                        ob = orderbooks.get(ticker)
                        if ob is None:
                            continue
                        ob.apply_delta(msg["msg"])

                    bid, ask, bid_sz, ask_sz = ob.best_bid_ask()

                    # Drop corrupt (crossed) states; reconnect if one persists.
                    if bid >= ask:
                        streak = crossed_streak.get(ticker, 0) + 1
                        crossed_streak[ticker] = streak
                        if streak >= _CROSSED_RESNAPSHOT:
                            print(
                                f"Kalshi: {ticker} crossed {streak}x, "
                                "reconnecting for fresh snapshots",
                                flush=True,
                            )
                            break
                        continue
                    crossed_streak[ticker] = 0

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
                _POLY_WS_URL, additional_headers=headers, max_queue=None,
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

    ws_tasks = [
        asyncio.create_task(_kalshi_ws(matches, writer, shutdown)),
        asyncio.create_task(_poly_ws(matches, writer, shutdown)),
    ]
    # The writer owns the DuckDB connection; it is never cancelled, so its
    # insert never races a second insert. It drains and returns on shutdown.
    writer_task = asyncio.create_task(_write_loop(writer, shutdown))

    await shutdown.wait()

    for t in ws_tasks:
        t.cancel()
    await asyncio.gather(*ws_tasks, return_exceptions=True)
    await writer_task  # graceful final drain

    con.close()
    print("Done. Final flush complete.")


def main() -> None:
    load_dotenv()
    asyncio.run(_run())


if __name__ == "__main__":
    main()
