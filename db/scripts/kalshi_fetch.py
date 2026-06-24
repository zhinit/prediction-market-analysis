import requests

BASE = "https://external-api.kalshi.com/trade-api/v2"


def get_event_markets(event_ticker):
    markets = []
    cursor = None
    while True:
        params = {"event_ticker": event_ticker, "limit": 100}
        if cursor:
            params["cursor"] = cursor
        resp = requests.get(f"{BASE}/markets", params=params).json()
        markets.extend(resp["markets"])
        cursor = resp.get("cursor")
        if not cursor:
            break
    return markets


if __name__ == "__main__":
    markets = get_event_markets("KXINX-26JUN26H1600")
    markets.sort(key=lambda m: float(m["yes_bid_dollars"]), reverse=True)
    for m in markets:
        ticker = m["ticker"]
        bid = m["yes_bid_dollars"]
        ask = m["yes_ask_dollars"]
        vol = m["volume_fp"]
        print(f"{ticker:50s} bid={bid} ask={ask} vol={vol}")
