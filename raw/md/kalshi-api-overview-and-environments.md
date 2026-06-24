# Kalshi API Overview and Environments

Source: https://docs.kalshi.com/welcome, https://docs.kalshi.com/getting_started/api_environments
Fetched: 2026-06-24

---

## Introduction

The Kalshi API documentation serves as a comprehensive guide for accessing real-time market data and executing trades on the Kalshi Exchange platform.

### APIs Offered

- **Predictions APIs** for event-contract markets supporting REST, WebSocket, and FIX protocols
- **Perps APIs** for perpetual futures (margin) trading across REST, WebSocket, and FIX

### Getting Started Resources

The documentation directs new users to foundational materials including making initial API requests, accessing the demo environment for safe testing, and generating API credentials.

### Technical Specifications

Raw specification files are available for developers:
- OpenAPI schema for Predictions REST: https://docs.kalshi.com/openapi.yaml
- AsyncAPI schema for Predictions WebSocket: https://docs.kalshi.com/asyncapi.yaml
- Separate OpenAPI and AsyncAPI schemas for Perps markets

Full documentation index: https://docs.kalshi.com/llms.txt

**Legal**: "By continuing to use or access Kalshi's API, you are agreeing to be bound to our Developer Agreement"

---

## API Environments and Endpoints

Kalshi maintains distinct production and demo environments with non-shared credentials. "Demo API keys only work against demo endpoints and production API keys only work against production endpoints."

### REST API Base URLs

**Production:**
- Primary: `https://external-api.kalshi.com/trade-api/v2`
- Alternative: `https://api.elections.kalshi.com/trade-api/v2`

**Demo:**
- Primary: `https://external-api.demo.kalshi.co/trade-api/v2`
- Alternative: `https://demo-api.kalshi.co/trade-api/v2`

The external-api hosts are recommended for API traders and dedicated to the Trade API.

### WebSocket API URLs

**Production:**
- Primary: `wss://external-api-ws.kalshi.com/trade-api/ws/v2`
- Alternative: `wss://api.elections.kalshi.com/trade-api/ws/v2`

**Demo:**
- Primary: `wss://external-api-ws.demo.kalshi.co/trade-api/ws/v2`
- Alternative: `wss://demo-api.kalshi.co/trade-api/ws/v2`

### Request Signing Path

When signing requests, use only the path portion excluding hostname and query parameters. For example, sign `/trade-api/v2/portfolio/orders` regardless of which host is used.
