# Kalshi API Authentication

Kalshi uses API key + RSA-PSS request signing. There is no JWT login flow —
every request is independently signed. (source: kalshi-api-authentication.md)

## API Key Generation

1. Navigate to Account Settings → Profile Settings
2. Click "Create New API Key"
3. Receive a **Key ID** and a **Private Key** in RSA_PRIVATE_KEY (PEM) format
4. The private key is shown once and never stored by Kalshi

(source: kalshi-api-authentication.md)

## Required Headers

Every authenticated request needs three headers:

| Header | Value |
|--------|-------|
| `KALSHI-ACCESS-KEY` | The Key ID |
| `KALSHI-ACCESS-TIMESTAMP` | Current time in milliseconds (Unix epoch) |
| `KALSHI-ACCESS-SIGNATURE` | Base64-encoded RSA-PSS signature |

(source: kalshi-api-authentication.md)

## Signing Algorithm

1. Concatenate: `timestamp + HTTP_METHOD + path`
2. The path excludes query parameters (e.g., sign `/trade-api/v2/portfolio/orders`, not `/trade-api/v2/portfolio/orders?limit=5`)
3. Sign with RSA-PSS, SHA256, MGF1(SHA256), max salt length
4. Base64-encode the result

(source: kalshi-api-authentication.md)

## WebSocket Authentication

Same signing mechanism, applied during the WebSocket handshake. Sign the
string: `timestamp + "GET" + "/trade-api/ws/v2"` and pass the three headers
as connection parameters. (source: kalshi-api-websocket.md)

## Public Endpoints

Market data endpoints (GET /markets, GET /markets/{ticker}, GET
/markets/trades, orderbook) do not require authentication.
(source: kalshi-api-market-data-endpoints.md)
