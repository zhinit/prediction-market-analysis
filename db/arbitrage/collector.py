"""WebSocket-based orderbook collector for Kalshi and Polymarket US MLB markets."""

from __future__ import annotations

import asyncio
import json
import logging
import signal
from datetime import datetime
from pathlib import Path

import websockets
from dotenv import load_dotenv

from db.arbitrage.matcher import EASTERN, match_markets
from db.arbitrage.storage import (
    init_db,
    load_matched_markets,
    log_event,
    save_matched_markets,
    save_snapshot,
)
from db.shared.auth import (
    load_ed25519_key,
    load_rsa_key,
    require_env,
    sign_ed25519,
    sign_rsa,
)

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("collector")

KALSHI_WS = "wss://external-api-ws.kalshi.com/trade-api/ws/v2"
POLY_WS = "wss://api.polymarket.us/v1/ws/markets"
MAX_BACKOFF = 30


class KalshiBooks:
    """Local orderbook state built from Kalshi snapshots + deltas."""

    def __init__(self) -> None:
        self.books: dict[str, dict[str, dict[str, str]]] = {}

    def apply_snapshot(
        self, ticker: str, yes_levels: list, no_levels: list,
    ) -> None:
        self.books[ticker] = {
            "yes": {str(p): str(q) for p, q in yes_levels},
            "no": {str(p): str(q) for p, q in no_levels},
        }

    def apply_delta(
        self, ticker: str, side: str, price: str, delta: str,
    ) -> bool:
        if ticker not in self.books:
            return False
        book = self.books[ticker].setdefault(side, {})
        current = float(book.get(price, "0"))
        new_qty = current + float(delta)
        if new_qty <= 0:
            book.pop(price, None)
        else:
            book[price] = f"{new_qty:.2f}"
        return True

    def get_book_json(self, ticker: str, side: str) -> str:
        if ticker not in self.books:
            return "[]"
        levels = self.books[ticker].get(side, {})
        return json.dumps([[p, q] for p, q in sorted(levels.items())])


async def run_kalshi(con, tickers: list[str], shutdown: asyncio.Event) -> None:
    key_path = Path(require_env("KALSHI_PRIVATE_KEY_PATH"))
    key_id = require_env("KALSHI_API_KEY_ID")
    rsa_key = load_rsa_key(key_path)
    books = KalshiBooks()
    backoff = 1

    while not shutdown.is_set():
        try:
            ts, sig = sign_rsa(rsa_key, "GET", "/trade-api/ws/v2")
            headers = {
                "KALSHI-ACCESS-KEY": key_id,
                "KALSHI-ACCESS-TIMESTAMP": ts,
                "KALSHI-ACCESS-SIGNATURE": sig,
            }
            async with websockets.connect(
                KALSHI_WS, additional_headers=headers,
            ) as ws:
                log.info("Kalshi connected, subscribing to %d markets", len(tickers))
                log_event(con, "start", "kalshi", f"{len(tickers)} markets")

                await ws.send(json.dumps({
                    "id": 1,
                    "cmd": "subscribe",
                    "params": {
                        "channels": ["orderbook_delta"],
                        "market_tickers": tickers,
                    },
                }))

                backoff = 1
                count = 0

                async for raw in ws:
                    if shutdown.is_set():
                        break
                    msg = json.loads(raw)
                    msg_type = msg.get("type")

                    if msg_type == "orderbook_snapshot":
                        data = msg["msg"]
                        ticker = data["market_ticker"]
                        source_ts = data.get("ts_ms")
                        books.apply_snapshot(
                            ticker,
                            data.get("yes_dollars_fp", []),
                            data.get("no_dollars_fp", []),
                        )
                        for side in ("yes", "no"):
                            save_snapshot(
                                con, "kalshi", ticker, side,
                                books.get_book_json(ticker, side),
                                str(source_ts) if source_ts is not None else None,
                            )
                        count += 1
                        if count <= len(tickers):
                            log.info("Kalshi snapshot: %s", ticker)

                    elif msg_type == "orderbook_delta":
                        data = msg["msg"]
                        ticker = data["market_ticker"]
                        side = data["side"]
                        source_ts = data.get("ts_ms")
                        if books.apply_delta(
                            ticker, side, data["price_dollars"], data["delta_fp"],
                        ):
                            save_snapshot(
                                con, "kalshi", ticker, side,
                                books.get_book_json(ticker, side),
                                str(source_ts) if source_ts is not None else None,
                            )
                            count += 1

                    elif msg_type == "error":
                        log.error("Kalshi error: %s", msg)

                    if count > 0 and count % 500 == 0:
                        log.info("Kalshi: %d updates stored", count)

        except (websockets.ConnectionClosed, OSError, asyncio.TimeoutError) as e:
            if shutdown.is_set():
                break
            log.warning("Kalshi disconnected: %s — reconnecting in %ds", e, backoff)
            log_event(con, "reconnect", "kalshi", str(e))
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)
        except Exception as e:
            if shutdown.is_set():
                break
            log.error("Kalshi unexpected error: %s", e, exc_info=True)
            log_event(con, "error", "kalshi", str(e))
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)

    log_event(con, "stop", "kalshi")
    log.info("Kalshi collector stopped")


async def run_polymarket(con, slugs: list[str], shutdown: asyncio.Event) -> None:
    ed_key = load_ed25519_key(require_env("POLYMARKET_US_PRIVATE_KEY"))
    key_id = require_env("POLYMARKET_US_API_KEY_ID")
    backoff = 1

    while not shutdown.is_set():
        try:
            ts, sig = sign_ed25519(ed_key, "GET", "/v1/ws/markets")
            headers = {
                "X-PM-Access-Key": key_id,
                "X-PM-Timestamp": ts,
                "X-PM-Signature": sig,
            }
            async with websockets.connect(
                POLY_WS, additional_headers=headers,
            ) as ws:
                log.info("Polymarket connected, subscribing to %d markets", len(slugs))
                log_event(con, "start", "polymarket", f"{len(slugs)} markets")

                await ws.send(json.dumps({
                    "subscribe": {
                        "requestId": "arb-books",
                        "subscriptionType": "SUBSCRIPTION_TYPE_MARKET_DATA",
                        "marketSlugs": slugs,
                    },
                }))

                backoff = 1
                count = 0

                async for raw in ws:
                    if shutdown.is_set():
                        break
                    msg = json.loads(raw)

                    if "heartbeat" in msg:
                        continue

                    market_data = msg.get("marketData")
                    if not market_data:
                        continue

                    slug = market_data.get("marketSlug", "")
                    source_ts = market_data.get("transactTime")

                    bids_json = json.dumps([
                        [b["px"]["value"], b["qty"]]
                        for b in market_data.get("bids", [])
                    ])
                    offers_json = json.dumps([
                        [o["px"]["value"], o["qty"]]
                        for o in market_data.get("offers", [])
                    ])

                    save_snapshot(con, "polymarket", slug, "bids", bids_json, source_ts)
                    save_snapshot(con, "polymarket", slug, "offers", offers_json, source_ts)

                    count += 1
                    if count == 1:
                        log.info("Polymarket first update: %s", slug)
                    elif count % 500 == 0:
                        log.info("Polymarket: %d updates stored", count)

        except (websockets.ConnectionClosed, OSError, asyncio.TimeoutError) as e:
            if shutdown.is_set():
                break
            log.warning(
                "Polymarket disconnected: %s — reconnecting in %ds", e, backoff,
            )
            log_event(con, "reconnect", "polymarket", str(e))
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)
        except Exception as e:
            if shutdown.is_set():
                break
            log.error("Polymarket unexpected error: %s", e, exc_info=True)
            log_event(con, "error", "polymarket", str(e))
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)

    log_event(con, "stop", "polymarket")
    log.info("Polymarket collector stopped")


async def main() -> None:
    today = datetime.now(EASTERN).date()
    log.info("Matching markets for %s", today)

    matched, match_log = match_markets(today)
    for msg in match_log:
        log.info(msg)

    con = init_db()
    save_matched_markets(con, matched)
    log.info("Saved %d matched market pairs", len(matched))

    # Subscribe to the union of today's pairs, including ones matched by an
    # earlier run whose markets may no longer be discoverable.
    pairs = load_matched_markets(con, today)
    if len(pairs) > len(matched):
        log.info(
            "Including %d pairs carried over from earlier runs today",
            len(pairs) - len(matched),
        )
    if not pairs:
        log.error("No matched markets — nothing to collect")
        con.close()
        return

    kalshi_tickers: list[str] = []
    poly_slugs: list[str] = []
    for away_ticker, home_ticker, poly_slug in pairs:
        for ticker in (away_ticker, home_ticker):
            if ticker not in kalshi_tickers:
                kalshi_tickers.append(ticker)
        if poly_slug not in poly_slugs:
            poly_slugs.append(poly_slug)

    log.info(
        "Subscribing: %d Kalshi tickers, %d Polymarket slugs",
        len(kalshi_tickers), len(poly_slugs),
    )

    shutdown = asyncio.Event()
    tasks: list[asyncio.Task] = []

    def handle_signal() -> None:
        log.info("Shutdown signal received")
        shutdown.set()
        for t in tasks:
            t.cancel()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)

    tasks = [
        asyncio.create_task(run_kalshi(con, kalshi_tickers, shutdown)),
        asyncio.create_task(run_polymarket(con, poly_slugs, shutdown)),
    ]
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass

    con.close()
    log.info("Collector shut down cleanly")


if __name__ == "__main__":
    asyncio.run(main())
