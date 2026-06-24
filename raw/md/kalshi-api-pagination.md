# Kalshi API Pagination

Source: https://docs.kalshi.com/getting_started/pagination
Fetched: 2026-06-24

---

## Cursor-Based Pagination

The Kalshi API implements cursor-based pagination for managing large datasets across list endpoints.

### How It Works

1. Make initial request without a cursor
2. Response includes a `cursor` field pointing to the next page
3. Pass cursor as query parameter in subsequent requests
4. When cursor returns `null`, no additional pages remain

### Parameters

- `cursor` (string) — pagination cursor from previous response
- `limit` (integer) — page size, typically 1-100 (default 100, max 1000 for some endpoints)

### Compatible Endpoints

Seven endpoints support cursor-based pagination:
- markets
- events
- series
- trades
- portfolio history
- fills
- orders

### Python Example

```python
all_markets = []
cursor = None
while True:
    params = {"limit": 100}
    if cursor:
        params["cursor"] = cursor
    response = requests.get(url, params=params)
    data = response.json()
    all_markets.extend(data["markets"])
    cursor = data.get("cursor")
    if not cursor:
        break
```

### Best Practices

- Respect rate limit constraints during bulk pagination
- Select appropriate page sizes based on actual needs
- Store results locally to minimize API calls
- Data changes between requests — implement refresh mechanisms
