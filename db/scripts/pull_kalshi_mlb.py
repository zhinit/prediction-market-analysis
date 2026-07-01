import asyncio
import httpx
import duckdb
import polars as pl
from pydantic import BaseModel
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)


class Event(BaseModel):
    event_ticker: str
    series_ticker: str
    title: str
    category: str
    sub_title: str | None = None


class EventResponse(BaseModel):
    events: list[Event]
    cursor: str | None = None


class Market(BaseModel):
    ticker: str
    event_ticker: str
    market_type: str
    yes_sub_title: str | None = None
    no_sub_title: str | None = None
    status: str
    result: str | None = None
    open_time: str | None = None
    close_time: str | None = None
    settlement_ts: str | None = None
    settlement_value_dollars: str | None = None
    volume_fp: str | None = None
    open_interest_fp: str | None = None
    rules_primary: str | None = None


class MarketResponse(BaseModel):
    markets: list[Market]
    cursor: str | None = None


class Trade(BaseModel):
    trade_id: str
    ticker: str
    count_fp: str
    yes_price_dollars: str
    no_price_dollars: str
    taker_outcome_side: str
    taker_book_side: str
    created_time: str
    is_block_trade: bool


class TradeResponse(BaseModel):
    trades: list[Trade]
    cursor: str | None = None


async def fetch_all(client, path, params, response_model, result_key, page_size=200):
    full_content = []
    cursor = None
    while True:
        new_params = {**params, "limit": page_size}
        if cursor:
            new_params["cursor"] = cursor
        raw = await fetch(client, path, new_params)

        response = response_model.model_validate_json(raw)
        full_content.extend(getattr(response, result_key))

        cursor = response.cursor
        if not cursor:
            break
    return full_content


@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, max=60),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ReadTimeout)),
    reraise=True,
)
async def fetch(client, path, params):
    r = await client.get(path, params=params)
    r.raise_for_status()
    return r.content


def init_db(path="db/pma.db"):
    con = duckdb.connect(path)
    con.sql("""
        CREATE TABLE IF NOT EXISTS events (
            event_ticker TEXT PRIMARY KEY,
            series_ticker TEXT NOT NULL,
            title TEXT,
            category TEXT,
            sub_title TEXT
        )
    """)
    con.sql("""
        CREATE TABLE IF NOT EXISTS markets (
            ticker TEXT PRIMARY KEY,
            event_ticker TEXT NOT NULL,
            market_type TEXT,
            yes_sub_title TEXT,
            no_sub_title TEXT,
            status TEXT NOT NULL,
            result TEXT,
            open_time TEXT,
            close_time TEXT,
            settlement_ts TEXT,
            settlement_value_dollars TEXT,
            volume_fp TEXT,
            open_interest_fp TEXT,
            rules_primary TEXT
        )
    """)
    con.sql("""
        CREATE TABLE IF NOT EXISTS trades (
            trade_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            count_fp TEXT,
            yes_price_dollars TEXT,
            no_price_dollars TEXT,
            taker_outcome_side TEXT,
            taker_book_side TEXT,
            created_time TEXT,
            is_block_trade BOOLEAN NOT NULL
        )
    """)
    return con


base_url = "https://external-api.kalshi.com/trade-api/v2"
timeouts = httpx.Timeout(connect=2.0, read=10.0, write=5.0, pool=5.0)


async def main():
    async with httpx.AsyncClient(base_url=base_url, timeout=timeouts) as client:
        settled = await fetch_all(
            client,
            "/events",
            {"series_ticker": "KXMLBGAME", "status": "settled"},
            EventResponse,
            "events",
        )
        open_ = await fetch_all(
            client,
            "/events",
            {"series_ticker": "KXMLBGAME", "status": "open"},
            EventResponse,
            "events",
        )
        events = list({e.event_ticker: e for e in settled + open_}.values())
        print(f"Found {len(events)} events")
        # for e in events[:5]:
        #    print(f"  {e.event_ticker}  {e.title}")

        r = await client.get("historical/cutoff")
        cutoff = r.json()
        print(f"Historical cutoff: {cutoff}")

        hist_markets = await fetch_all(
            client,
            "/historical/markets",
            {"series_ticker": "KXMLBGAME"},
            MarketResponse,
            "markets",
        )
        print(f"Historical markets: {len(hist_markets)}")

        live_markets = await fetch_all(
            client,
            "/markets",
            {"series_ticker": "KXMLBGAME"},
            MarketResponse,
            "markets",
        )
        print(f"Live markets: {len(live_markets)}")

        # use a dictionary comprehension to remove duplicate markets
        markets = list({m.ticker: m for m in hist_markets + live_markets}.values())
        print(f"Total markets: {len(markets)}")

        con = init_db()

        events_df = pl.DataFrame([e.model_dump() for e in events])
        con.sql("INSERT OR REPLACE INTO events SELECT * FROM events_df")
        print(f"Saved {len(events)} events to db")

        markets_df = pl.DataFrame([m.model_dump() for m in markets])
        con.sql("INSERT OR REPLACE INTO markets SELECT * FROM markets_df")
        print(f"Saved {len(markets)} markets to db")

        for i, m in enumerate(markets):
            trades = await fetch_all(
                client,
                "/historical/trades",
                {"ticker": m.ticker},
                TradeResponse,
                "trades",
            )
            if trades:
                trades_df = pl.DataFrame([t.model_dump() for t in trades])
                con.sql("INSERT OR REPLACE INTO trades SELECT * FROM trades_df")
            if (i + 1) % 5 == 0:
                print(f"  ... {i + 1}/{len(markets)} markets")
        print("Historical trades done")

        for i, m in enumerate(markets):
            trades = await fetch_all(
                client,
                "/markets/trades",
                {"ticker": m.ticker},
                TradeResponse,
                "trades",
            )
            if trades:
                trades_df = pl.DataFrame([t.model_dump() for t in trades])
                con.sql("INSERT OR REPLACE INTO trades SELECT * FROM trades_df")
            if (i + 1) % 5 == 0:
                print(f"  ... {i + 1}/{len(markets)} live markets")
        print("Live trades done")

        con.close()


if __name__ == "__main__":
    asyncio.run(main())
