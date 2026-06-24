# Kalshi API SDKs

Source: https://docs.kalshi.com/sdks/overview
Fetched: 2026-06-24

---

## Official SDKs

Kalshi provides official SDKs in Python and TypeScript.

### Python (Synchronous)
- Package: `kalshi_python_sync`
- Install: `pip install kalshi_python_sync`
- PyPI: https://pypi.org/project/kalshi_python_sync/

### Python (Asynchronous)
- Package: `kalshi_python_async`
- Install: `pip install kalshi_python_async`
- PyPI: https://pypi.org/project/kalshi_python_async/

### TypeScript
- Package: `kalshi-typescript`
- Install: `npm install kalshi-typescript`
- npm: https://www.npmjs.com/package/kalshi-typescript

## Important Notes

"SDKs are updated periodically and may lag the API."

Active traders should consult the authoritative specs:
- REST: https://docs.kalshi.com/openapi.yaml
- WebSocket: https://docs.kalshi.com/asyncapi.yaml

The deprecated `kalshi-python` package should be replaced with either the sync or async variants.

All SDKs use API key authentication combined with RSA-PSS request signing.

Weekly SDK releases typically occur Tuesday-Wednesday, tracking OpenAPI updates.

## Unofficial SDKs (Community)

- **kalshi-python-sdk** (TexasCoding) — full coverage of REST API (104 operations across 19 resources) and WebSocket API
- **pykalshi** (arshka) — WebSocket streaming, automatic retries, pandas integration
- **KalshiPythonClient** (AndrewNolte) — auto-generated from OpenAPI spec
- **kalshi-python-unofficial** (humz2k) — lightweight wrapper
