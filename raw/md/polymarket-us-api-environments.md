# Polymarket US API Environments

Source: https://docs.polymarket.us/trader-guide/environments
Fetched: 2026-06-24

## Environments

### Development
- REST: `https://api.dev01.polymarketexchange.com`
- Auth0: `pmx-dev01.us.auth0.com`
- Purpose: initial testing

### Pre-Production
- REST: `https://api.preprod.polymarketexchange.com`
- Auth0: `pmx-preprod.us.auth0.com`
- Purpose: validation before launch

### Production
- REST: `https://api.prod.polymarketexchange.com`
- Auth0: `pmx-prod.us.auth0.com`
- Purpose: live trading

## Common Details

- REST pattern: `/v1/{service}/{operation}`
- Health check: `GET /v1/health` (returns status and version)
- gRPC: dedicated ports at `polymarketexchange.com:443`
- Tokens must be refreshed every 3 minutes in all environments

## Connectivity

- REST and gRPC APIs use public endpoints (no VPC required)
- FIX API requires VPC (AWS PrivateLink)
- VPC Service Names and PrivateLink endpoints provisioned per-firm during
  FIX onboarding

## Recommended Path

Dev → Preprod → Prod

Contact onboarding@polymarket.us for access credentials per environment.
