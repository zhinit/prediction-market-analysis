import httpx
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


base_url = "https://external-api.kalshi.com/trade-api/v2"
read_timeout = 10.0
connect_timeout = 2.0
timeouts = httpx.Timeout(connect=connect_timeout, read=read_timeout)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, max=60),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
    reraise=True,
)
async def fetch(path, params, client):
    r = await client.get(path, params=params)
    r.raise_for_status()
    return r.content


async def main():
    async with httpx.AsyncClient(base_url=base_url, timeout=timeouts) as client:
        path = "filler"
        params = {"a": 1, "b": 2}
        await fetch(path, params, client)
