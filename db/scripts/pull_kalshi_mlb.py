import asyncio
from datetime import datetime
import httpx
import duckdb
import polars as pl
from pydantic import BaseModel
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception,
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


class EventLookup(BaseModel):
    event: Event


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


class Cutoff(BaseModel):
    trades_created_ts: str


def parse_timestamp(time_stamp: str) -> datetime:
    return datetime.fromisoformat(time_stamp.replace("Z", "+00:00"))


async def fetch_all(
    client: httpx.AsyncClient,
    path: str,
    params: dict,
    response_model: type[BaseModel],
    result_key: str,
    page_size: int = 200,
) -> list:
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


# Retry timeouts, 429s, and 5xx. Other 4xx fail immediately.
def is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.ReadTimeout):
        return True
    return isinstance(exc, httpx.HTTPStatusError) and (
        exc.response.status_code == 429 or exc.response.status_code >= 500
    )


@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, max=60),
    retry=retry_if_exception(is_retryable),
    reraise=True,
)
async def fetch(client: httpx.AsyncClient, path: str, params: dict) -> bytes:
    r = await client.get(path, params=params)
    r.raise_for_status()
    return r.content


def trade_params(market: Market, last_trade_time: dict[str, datetime]) -> dict:
    params = {"ticker": market.ticker}
    if market.ticker in last_trade_time:
        # 1s overlap in case min_ts is inclusive; the trade_id key dedupes
        params["min_ts"] = int(last_trade_time[market.ticker].timestamp()) - 1
    return params


async def pull_trades(
    client: httpx.AsyncClient,
    con: duckdb.DuckDBPyConnection,
    markets: list[Market],
    last_trade_time: dict[str, datetime],
    path: str,
    label: str,
) -> None:
    for i, m in enumerate(markets):
        trades = await fetch_all(
            client, path, trade_params(m, last_trade_time), TradeResponse, "trades"
        )
        if trades:
            trades_df = pl.DataFrame([t.model_dump() for t in trades])
            con.sql("INSERT OR REPLACE INTO trades BY NAME SELECT * FROM trades_df")
        if (i + 1) % 5 == 0:
            print(f"  ... {i + 1}/{len(markets)} {label}")


def init_db(path: str = "db/pma.db") -> duckdb.DuckDBPyConnection:
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
    # typed views over the raw TEXT tables; analyses query these
    con.sql("""
        CREATE OR REPLACE VIEW markets_typed AS
        SELECT
            ticker,
            event_ticker,
            market_type,
            yes_sub_title,
            no_sub_title,
            status,
            result,
            CAST(open_time AS TIMESTAMP) AS open_time,
            CAST(close_time AS TIMESTAMP) AS close_time,
            CAST(settlement_ts AS TIMESTAMP) AS settlement_ts,
            CAST(settlement_value_dollars AS DECIMAL(18, 6))
                AS settlement_value_dollars,
            CAST(volume_fp AS DECIMAL(18, 6)) AS volume_fp,
            CAST(open_interest_fp AS DECIMAL(18, 6)) AS open_interest_fp,
            rules_primary
        FROM markets
    """)
    con.sql("""
        CREATE OR REPLACE VIEW trades_typed AS
        SELECT
            trade_id,
            ticker,
            CAST(count_fp AS DECIMAL(18, 6)) AS count_fp,
            CAST(yes_price_dollars AS DECIMAL(18, 6)) AS yes_price_dollars,
            CAST(no_price_dollars AS DECIMAL(18, 6)) AS no_price_dollars,
            taker_outcome_side,
            taker_book_side,
            CAST(created_time AS TIMESTAMP) AS created_time,
            is_block_trade
        FROM trades
    """)
    return con


BASE_URL = "https://external-api.kalshi.com/trade-api/v2"
TIMEOUTS = httpx.Timeout(connect=2.0, read=10.0, write=5.0, pool=5.0)


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUTS) as client:
        # no status filter, so events in every status are included
        events = await fetch_all(
            client,
            "/events",
            {"series_ticker": "KXMLBGAME"},
            EventResponse,
            "events",
        )
        if not events:
            raise SystemExit("No events returned for KXMLBGAME, aborting")
        print(f"Found {len(events)} events")

        raw = await fetch(client, "/historical/cutoff", {})
        cutoff = Cutoff.model_validate_json(raw)
        trades_cutoff = parse_timestamp(cutoff.trades_created_ts)
        print(f"Historical trades cutoff: {cutoff.trades_created_ts}")

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

        # dedupe by ticker
        markets = list({m.ticker: m for m in hist_markets + live_markets}.values())
        if not markets:
            raise SystemExit("No markets returned for KXMLBGAME, aborting")
        print(f"Total markets: {len(markets)}")

        # some events never appear in the list endpoint; fetch them directly
        missing = {m.event_ticker for m in markets} - {e.event_ticker for e in events}
        for ticker in sorted(missing):
            raw = await fetch(client, f"/events/{ticker}", {})
            events.append(EventLookup.model_validate_json(raw).event)
        if missing:
            print(f"Fetched {len(missing)} events missing from the list endpoint")

        con = init_db()

        # previous-run state, read before the inserts below overwrite it
        last_trade_time = {
            ticker: parse_timestamp(created_time)
            for ticker, created_time in con.sql(
                "SELECT ticker, max(created_time) FROM trades GROUP BY ticker"
            ).fetchall()
        }
        finalized_tickers = {
            ticker
            for (ticker,) in con.sql(
                "SELECT ticker FROM markets WHERE status = 'finalized'"
            ).fetchall()
        }

        events_df = pl.DataFrame([e.model_dump() for e in events])
        con.sql("INSERT OR REPLACE INTO events BY NAME SELECT * FROM events_df")
        print(f"Saved {len(events)} events to db")

        markets_df = pl.DataFrame([m.model_dump() for m in markets])
        con.sql("INSERT OR REPLACE INTO markets BY NAME SELECT * FROM markets_df")
        print(f"Saved {len(markets)} markets to db")

        # finalized markets with stored trades are complete; skip them
        todo = [
            m
            for m in markets
            if not (m.ticker in finalized_tickers and m.ticker in last_trade_time)
        ]
        print(f"Markets to fetch trades for: {len(todo)}/{len(markets)}")

        # trades before the cutoff are on /historical/trades, the rest on
        # /markets/trades; new trades appear after the newest stored trade
        def new_trades_from(m):
            if m.ticker in last_trade_time:
                return last_trade_time[m.ticker]
            return parse_timestamp(m.open_time) if m.open_time else None

        pre_cutoff = [
            m
            for m in todo
            if (start := new_trades_from(m)) is None or start < trades_cutoff
        ]
        post_cutoff = [
            m
            for m in todo
            if m.close_time is None or parse_timestamp(m.close_time) >= trades_cutoff
        ]
        print(f"Markets needing historical trades: {len(pre_cutoff)}")
        print(f"Markets needing live trades: {len(post_cutoff)}")

        await pull_trades(
            client, con, pre_cutoff, last_trade_time, "/historical/trades", "markets"
        )
        print("Historical trades done")

        await pull_trades(
            client, con, post_cutoff, last_trade_time, "/markets/trades", "live markets"
        )
        print("Live trades done")

        con.close()


if __name__ == "__main__":
    asyncio.run(main())
