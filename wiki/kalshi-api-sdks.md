# Kalshi API SDKs

Kalshi provides official SDKs in Python and TypeScript. SDKs are updated
periodically and may lag the API — the OpenAPI and AsyncAPI specs are
authoritative. (source: kalshi-api-sdks.md)

## Official SDKs

| Language | Package | Install |
|----------|---------|---------|
| Python (sync) | `kalshi_python_sync` | `pip install kalshi_python_sync` |
| Python (async) | `kalshi_python_async` | `pip install kalshi_python_async` |
| TypeScript | `kalshi-typescript` | `npm install kalshi-typescript` |

The old `kalshi-python` package is deprecated — use the sync or async variant.
Weekly SDK releases typically occur Tuesday-Wednesday, tracking OpenAPI
updates. (source: kalshi-api-sdks.md)

## Authoritative Specs

- REST: https://docs.kalshi.com/openapi.yaml
- WebSocket: https://docs.kalshi.com/asyncapi.yaml

(source: kalshi-api-sdks.md)

## Community SDKs

- **kalshi-python-sdk** (TexasCoding) — 104 operations, 19 resources, WebSocket
- **pykalshi** (arshka) — pandas integration, automatic retries
- **KalshiPythonClient** (AndrewNolte) — auto-generated from OpenAPI
- **kalshi-python-unofficial** (humz2k) — lightweight wrapper

(source: kalshi-api-sdks.md)
