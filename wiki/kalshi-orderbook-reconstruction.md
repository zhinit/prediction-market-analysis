# Kalshi Orderbook Reconstruction

No public Level 2 microstructure dataset exists for Kalshi's prediction
markets. A method for collecting and reconstructing every tick of every
full-depth limit order book uses Kalshi's public WebSocket API
(source: ssrn-kalshi-lob-reconstruction.md).

## Method

The system collects Kalshi's WebSocket data streams, anchored by periodic
REST API snapshots, then uses "snapshot-anchored windowing with sequential
delta replay" to process these streams into tick-level LOB states
(source: ssrn-kalshi-lob-reconstruction.md).

## Delta application protocol

Two message types: Snapshot (complete state, on initial subscription) and
Delta (incremental changes, per update). Positive deltas add contracts at a
price level, negative deltas remove contracts, zero totals eliminate the
level entirely (source: kalshi-websocket-delta-application.md).

## Data structure

BTreeMap (or equivalent sorted map) for efficient price level management.
Bids sorted descending, asks sorted ascending. O(log n) operations with
automatic sorting
(source: kalshi-websocket-delta-application.md).

## Price conversion model

YES/NO binary markets convert to bid/ask: YES side becomes bid at
(price / 100), NO side becomes ask at ((100 - price) / 100)
(source: kalshi-websocket-delta-application.md).

## Safety measures

Kalshi prices range 1–99 cents; invalid values should be rejected. Memory
should be bounded to max ~200 price levels per side to prevent exhaustion.
Non-blocking sends prevent slow consumers from disconnecting the WebSocket
(source: kalshi-websocket-delta-application.md).

## Related pages

- [[kalshi-api-websocket]] — Kalshi WebSocket channels and message types
- [[prediction-market-orderbook-microstructure]] — orderbook behavior on Polymarket
- [[cross-platform-arbitrage]] — cross-platform arbitrage overview
