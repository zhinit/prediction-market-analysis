import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)

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
        path = "buttsex"
        params = {"a": 1, "b": 2}
        await fetch(path, params, client)
