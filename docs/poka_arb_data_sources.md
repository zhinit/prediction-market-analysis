# poka-arb Data Sources

Exhaustive list of external data sources used in the poka-arb project.

## APIs at a Glance

1. Kalshi — `external-api.kalshi.com/trade-api/v2`
2. Polymarket US — `gateway.polymarket.us`, `api.polymarket.us`
3. MLB Stats API — `statsapi.mlb.com/api/v1`
4. NHL API — `api-web.nhle.com/v1`
5. Baseball Reference — via `pybaseball` library
6. Open-Meteo Historical-Forecast — `historical-forecast-api.open-meteo.com/v1/forecast`
7. Open-Meteo Ensemble — `ensemble-api.open-meteo.com/v1/ensemble`
8. Open-Meteo Archive — `archive-api.open-meteo.com/v1/archive`
9. dYdX v4 Indexer — `indexer.dydx.trade/v4`
10. arXiv — `arxiv.org` atom feed

## Prediction Markets

### Kalshi
- **Endpoint:** `external-api.kalshi.com/trade-api/v2`
- **Auth:** Ed25519 API key
- **Client:** httpx async
- **Data:** Events, markets, orderbooks, trade tapes, candlesticks, series listings

### Polymarket US
- **Endpoints:** `gateway.polymarket.us` (public), `api.polymarket.us` (authenticated)
- **Auth:** Ed25519 API key
- **Client:** httpx async
- **Data:** Markets, orderbooks, balances, trades

## Sports

### MLB Stats API
- **Endpoint:** `statsapi.mlb.com/api/v1`
- **Auth:** None (public)
- **Client:** urllib
- **Data:** Game schedules, probable pitchers, team batting/pitching stats, standings, injury rosters, play-by-play

### NHL API
- **Endpoint:** `api-web.nhle.com/v1`
- **Auth:** None (public)
- **Client:** urllib
- **Data:** Standings, schedules, play-by-play

### Baseball Reference (via pybaseball)
- **Auth:** None (scraped by library)
- **Data:** Historical WAR for batters and pitchers by season

## Weather (Open-Meteo)

### Historical-Forecast API
- **Endpoint:** `historical-forecast-api.open-meteo.com/v1/forecast`
- **Auth:** None (public)
- **Client:** urllib
- **Models:** GFS deterministic, HRRR deterministic (3km, CONUS)
- **Data:** Daily max temperature forecasts for 6 US cities (NYC, Chicago, Miami, Austin, LA, Denver)

### Ensemble API
- **Endpoint:** `ensemble-api.open-meteo.com/v1/ensemble`
- **Auth:** None (public)
- **Client:** urllib
- **Model:** GFS 31-member ensemble
- **Data:** Daily max temperature ensemble forecasts

### Archive API
- **Endpoint:** `archive-api.open-meteo.com/v1/archive`
- **Auth:** None (public)
- **Client:** urllib
- **Data:** Observed ground-truth temperatures

## Crypto

### dYdX v4 Indexer
- **Endpoint:** `indexer.dydx.trade/v4/candles/perpetualMarkets/{market}`
- **Auth:** None (public)
- **Client:** httpx, paginated in 2-hour windows
- **Markets:** BTC-USD, ETH-USD, SOL-USD, AVAX-USD, DOGE-USD, LINK-USD, MATIC-USD, ARB-USD, OP-USD, SUI-USD, APT-USD, PEPE-USD, WIF-USD, SEI-USD, TIA-USD
- **Data:** 1-minute OHLCV candles

## Academic

### arXiv
- **Endpoint:** arxiv.org atom feed
- **Auth:** None (public)
- **Client:** urllib + XML parsing
- **Keywords:** prediction markets, Kalshi, Polymarket, betting markets, options trading, quantitative trading, statistical arbitrage, Kelly criterion, forecast calibration, behavioral finance
- **Data:** Paper metadata (title, abstract, authors, date, PDF URL, DOI, categories)

## Local Storage

All fetched data lands in SQLite databases:

| Database | Contents |
|---|---|
| `settled.db` | Kalshi settled markets snapshot |
| `collect.db` | MLB/NHL games, team stats, pitching stats, WAR |
| `mentions.db` | Kalshi mention series and trade tapes |
| `gefs.db` | Weather forecasts (ensemble + deterministic + HRRR) |
| `fat_fingers.db` | dYdX perpetual candles |
| `trades.db` | Crypto market candlesticks (via Kalshi API) |
