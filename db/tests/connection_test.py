import httpx

response = httpx.get("https://external-api.kalshi.com/trade-api/v2/exchange/status")
print(response.status_code, response.text)
