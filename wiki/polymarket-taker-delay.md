# Polymarket Taker Delay

Marketable orders on Polymarket sports markets are subject to a 1-second
matching delay. During this period the order has a `delayed` status. After
the delay, unmatched orders transition to `unmatched` status and rest on the
book (source: polymarket-order-lifecycle-docs-2026.md).

## Order lifecycle

Orders follow a sequential lifecycle: creation and signing, submission to
the CLOB operator, matching or resting, settlement on blockchain. Execution
is atomic — trades either fully succeed or fail completely during the
onchain settlement phase
(source: polymarket-order-lifecycle-docs-2026.md).

## Order statuses

- `live`: order resting on the book
- `matched`: immediately matched with existing order
- `delayed`: marketable order subject to a matching delay (sports markets)
- `unmatched`: marketable but delay failed; placement still successful

(source: polymarket-order-lifecycle-docs-2026.md)

## Fill-or-Kill behavior

FOK requires complete fulfillment or immediate cancellation — no partial
executions permitted. Fill-and-Kill (FAK/IOC) fills what is available and
cancels the rest, allowing partial fills before cancelling remaining
quantity (source: polymarket-order-lifecycle-docs-2026.md).

## Implications for arbitrage

The 1-second delay on sports markets means that taker orders cannot execute
instantly. During the delay window, the orderbook can move against the
order. For cross-platform arbitrage strategies that rely on simultaneous
execution on both platforms, this delay is a structural barrier — the
Kalshi leg fills in ~130ms while the Polymarket leg is held for 1+ seconds
(source: polymarket-order-lifecycle-docs-2026.md).

## Related pages

- [[cross-platform-arbitrage]] — overview of cross-platform arbitrage and why prices diverge
- [[polymarket-us-api]] — full API reference
- [[polymarket-dynamic-fees]] — dynamic fees also introduced to curb latency arbitrage
