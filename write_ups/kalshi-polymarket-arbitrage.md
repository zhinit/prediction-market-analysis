---
title: Arbitrage exists between Kalshi and Polymarket but you can't exploit it
date: 2026-08-03
description: I recorded every orderbook change on matched MLB markets across Kalshi and Polymarket for 3 days. 8,870 price crossings, 480 bigger than fees, and none of them tradeable. Here's the data on why.
---

Kalshi and Polymarket both list markets on same MLB games. Since both platforms have prices for the same event, the prices can potentially diverge. Do they ever differ enough to profit after fees?

This article goes through what arbitrage is, how you can pull live order book data using websockets, and an analysis of arbitrage opportunities between Kalshi and Polymarket. The project code is on [GitHub](https://github.com/zhinit/prediction-market-analysis).

## What is arbitrage?

If you can buy apples on one side of Bleeker street for \$7 then cross the street and sell the apples for \$10, that is arbitrage. You just made a profit of $3. Arbitrage is the name of this phenomenon where the same item has different prices in different markets. Profiting off of an arbitrage opportunity is called exploiting it.

## What is a bid ask spread

On a prediction market, buyers post "bids" which are the prices they're willing to buy at and sellers post "asks" which are the prices they're willing to sell for. The "best bid" is the highest bid and the "best ask" is the lowest ask. The gap between them is the bid-ask spread.

The price is considered to be somewhere in the bid ask spread interval.

A contract with a best bid of 47 cents and a best ask of 49 cents has a 2 cent spread (the price may be listed at 48 cents at this time). If you want to buy instantly you pay the ask (49 cents). If you want to sell instantly you get the bid (47 cents).

Both Kalshi and Polymarket are order book exchanges which list bids and asks as well as the amount of each (i.e. do you want to sell 1 contract at that ask or 100?).

## Method

We compare the best bid and best ask on each platform at every order book snapshot. When one platform's best bid rises above the other platform's best ask, the books are said to be "crossed". 

A crossing means you can buy on one platform and sell on the other for an instant profit, before fees. Arbitrage exists when the books cross by more than the combined fees.

### Episodes

Consecutive order book snapshots where the deviation stays open are grouped into one "episode". An episode starts at the time when the books first cross and ends at the time they uncross.

So one episode is one arbitrage opportunity. Each carries a

- duration (AKA time)
- peak deviation (AKA dollar amount)
- bottleneck volume (AKA liquidity)

### Bottleneck volume

Exploiting an arbitrage opportunity has two legs. A buy on one platform and a sell on the other. The bottleneck volume is the minimum number of contracts available at the best price across those two sides.

Whichever side is thinner limits how many contracts you can actually trade. Anything beyond that means walking the book to worse prices.

### Takers vs makers

Exchanges want liquidity, meaning an active pool of buyers and sellers willing to trade with each other. An exchange without liquidity is like a pawn shop with no iventory, so it's easy to see why they want liquidity.

A taker takes liquidity from the market. They come in and buy or sell immediately based on the best bid or best ask already on the books.

A maker creates liquidity. They put bids and asks on the market waiting for a taker to take them.

Thus the exchanges like the market makers a bit more than the takers, and the fee schedules below reflect that.

### Fees

For arbitrage we want to execute quickly so we are a taker and we have 2 legs to fill (buying on one platform, selling on the other).

Taker fees per contract

- Kalshi: 7¢ × p × (1 − p)
- Polymarket: 6¢ × p × (1 − p)

Maker fees per contract

- Kalshi: 1.75¢ × p × (1 − p)
- Polymarket: −1.25¢ × p × (1 − p)
    - This is a rebate

At a 50 cent price the total round-trip taker fee is 7¢(0.5)(0.5) + 6¢(0.5)(0.5) = 3.25¢. That is the bar an opportunity has to clear before it's worth anything.

![Taker and maker fee curves for Kalshi and Polymarket](images/arb-fee-curves.png)

### Taker delay

Polymarket enforces a 1 to 3 second matching delay on taker orders. A taker order is accepted but held in a delayed status before the matching engine attempts to fill it. During that window the book can move or be consumed by other participants. Official sources say both 1 and 3 seconds: [Polymarket's Create Order docs](https://docs.polymarket.com/trading/orders/create) say 1 second, the [Polymarket agent-skills repo](https://github.com/Polymarket/agent-skills/blob/main/order-patterns.md) says 3 seconds.

I ran an arbitrage bot on these platforms in a separate private repo and I observed this delay directly: 15 of 16 taker orders on Polymarket sports markets were killed during the delay window due to movement, while the Kalshi leg filled in about 150ms. I never measured the exact delay duration, but the kill pattern matched the documented 1 to 3 second window.

This means opportunities shorter than 1 to 3 seconds will not be executable even assuming instantaneous orders.

## The data

To find crossings we need the full order book on both platforms for the same game, at the same time, updated every time either one changes.

### What is a websocket

A websocket is a connection between your machine and a server that stays open. Both sides can send messages over it whenever they want, for hours as long as they want until disconnected.

Both Kalshi and Polymarket offer websocket feeds of their order books. You connect, subscribe to the markets you care about, and the exchange pushes every order book update to you the moment it happens. Most of the opportunities in this analysis live for a fraction of a second, so getting pushed every update as it happens is the only way to catch them all.

### Snapshots vs deltas

The two exchanges send their order book data differently.

Polymarket sends the entire book in every message, i.e. every bid and every ask along with their amounts. This is easy, you just save each message as it arrives.

Kalshi sends the entire book once when you subscribe, then after that only sends what changed. A message might say the bids at 47 cents went down by 200 contracts, and nothing else. So for Kalshi we keep our own copy of the book and apply each change to it as it arrives.

After that both platforms give us the same thing, a full order book at every point in time, and the two can be compared directly.

### Matching markets across platforms

The two platforms have no shared identifier for the same game. Kalshi has tickers like KXMLBGAME-26AUG01NYYCHC and Polymarket has its own, so we match markets ourselves using the team pair and the game date. Doubleheaders (two games between the same teams on the same day) have the same team pair and date, so those are matched by scheduled start time.

### What was collected

- 3 days (July 30th, 31st, and August 1st 2026)
- 40 games
- 3,529,564 cross-platform book states

| | |
|---|---|
| **dates** | 2026-07-30 to 2026-08-02 |
| **games** | 40 |
| **cross-platform book states** | 3,529,564 |
| **opportunities before fees** | 8,870 |
| **opportunities after fees** | 480 |

*Timestamps are in UTC and evening games run past midnight UTC, which is why the end date says August 2nd.*

## How many opportunities before fees?

Every crossing is a "gross" arbitrage opportunity, meaning it ignores fees.

Over 3 days and 40 games there were 8,870 gross opportunities, which is about 220 per game. The books cross frequently.

## How many opportunities after fees?

Most of those crossings are smaller than the round-trip taker fee. Only episodes where the peak deviation exceeds the combined fees could be real opportunities.

That filter takes us from 8,870 down to 480, which is about 12 per game. For Each of these 12 moments per game you could theoretically buy on one platform, sell on the other, and profit the difference after fees.

### How much are these opportunities worth?

Each episode has a value: the peak net arb per contract times the bottleneck liquidity. This is the most you could have made if you filled the entire bottleneck at the best moment.

Across all 480 episodes the total theoretical value is $405.89, or $10.15 per game. Here are the 10 biggest.

| game | date | direction | peak arb/contract | bottleneck | value |
|---|---|---|---|---|---|
| TEX@TB | 2026-07-30 | buy_kalshi | 0.56¢ | 10,000 | $56.16 |
| NYY@CWS | 2026-07-30 | buy_kalshi | 1.27¢ | 3,463 | $43.89 |
| NYY@CHC | 2026-08-01 | buy_poly | 19.41¢ | 138 | $26.79 |
| CHC@STL | 2026-07-30 | buy_kalshi | 2.8¢ | 927 | $25.93 |
| CHC@STL | 2026-07-30 | buy_kalshi | 0.86¢ | 3,000 | $25.76 |
| NYY@CHC | 2026-08-01 | buy_poly | 9.89¢ | 170 | $16.81 |
| KC@COL | 2026-08-01 | buy_kalshi | 1.83¢ | 529 | $9.66 |
| SF@SD | 2026-07-31 | buy_kalshi | 1.51¢ | 609 | $9.20 |
| AZ@CLE | 2026-08-01 | buy_poly | 0.09¢ | 9,561 | $8.95 |
| MIA@NYM | 2026-07-30 | buy_kalshi | 8.12¢ | 107 | $8.71 |

Note the two different flavors.
- A big per-contract edge on a thin book (19.41 cents on 138 contracts)
- A tiny edge on a deep book (0.56 cents on 10,000 contracts).

### By bottleneck liquidity

Not all 480 opportunities have real size behind them. If the bottleneck liquidity is one contract you can make a couple pennies which is nothing to write home about.

| total | ≥1 | ≥10 | ≥50 | ≥100 | ≥500 | ≥1,000 | ≥5,000 |
|---|---|---|---|---|---|---|---|
| 480 | 416 | 170 | 104 | 76 | 24 | 11 | 2 |

*Fractional contracts exist which is why total is not equal to ≥1.*

A few opportunities exist with decent volume, but (480 − 170)/480 = 65% don't even have 10 contracts behind them.

## How big are the opportunities?

For each episode we look at the peak net arb per contract. That is the most you could have made on a single contract at the best moment in the episode, after fees.

| bottleneck | episodes | median | mean |
|---|---|---|---|
| all | 480 | 0.48¢ | 1.48¢ |
| ≥1 | 416 | 0.49¢ | 1.57¢ |
| ≥10 | 170 | 0.33¢ | 1.47¢ |
| ≥100 | 76 | 0.44¢ | 1.31¢ |
| ≥1,000 | 11 | 0.15¢ | 0.38¢ |

![Opportunity size by bottleneck liquidity](images/arb-size-by-liquidity.png)

Most opportunities are worth less than a cent per contract, and the edge shrinks as liquidity grows. 

## How long do opportunities persist?

An opportunity that disappears in 100ms is not the same as one that lasts 10 seconds. The taker delay on Polymarket makes anything under 1 to 3 seconds impossible to exploit, so duration is important!

| bottleneck | episodes | median | mean |
|---|---|---|---|
| all | 480 | 0.1s | 1.3s |
| ≥1 | 416 | 0.1s | 1.3s |
| ≥10 | 170 | 0.1s | 0.6s |
| ≥100 | 76 | 0.1s | 0.7s |
| ≥1,000 | 11 | 0.0s | 0.2s |

![Arbitrage opportunity duration by bottleneck liquidity](images/arb-duration-by-liquidity.png)

The median opportunity only lasts about 100ms (AKA 0.1s). The dashed lines on the plot are the 1 and 3 second Polymarket delay thresholds, and the vast majority of episodes die below them. The deepest opportunities (≥1,000 contracts) are also the fastest to vanish.

## The biggest opportunity up close

The biggest opportunity in the data was worth $56.16, during the Texas Rangers vs Tampa Bay Rays game on July 30th. The price gap was a mere 0.56 cents per contract after fees, but there were 10,000 contracts of bottleneck liquidity behind it. It appeared at 16:23:52 UTC and lasted 25 milliseconds.

Its direction was buy on Kalshi, sell on Polymarket, so only two prices matter. The Kalshi best ask (what you pay) and the Polymarket best bid (what you receive). When the Polymarket bid sits above the Kalshi ask, the difference is yours (before fees).

![TEX@TB, the two prices behind the biggest opportunity](images/arb-tex-tb-case-study.png)

So what actually happened in the game at that moment? It was tied at the bottom of the 1st inning, two outs, bases empty. Junior Caminero nearly hit a home run for Tampa Bay. It was close enough that the umpires reviewed the call. The ball went in play at 16:23:51.2 and both platforms slashed the Rangers' price while it was in the air, from about 37 cents to about 31 cents.

Kalshi cut first while Polymarket's bid was still sitting. For 25 milliseconds you could buy the Rangers on Kalshi at 33 cents and sell on Polymarket at 36.5 cents. Then Polymarket's bid dropped too and the books agreed again.

## Which direction do opportunities go?

Every opportunity has a direction. buy_kalshi means buy on Kalshi and sell on Polymarket, buy_poly is the reverse. If one platform were systematically slower or cheaper than the other, one direction would dominate.

| direction | opportunities | theoretical value |
|---|---|---|
| buy_kalshi | 240 | $257.24 |
| buy_poly | 240 | $148.65 |

The count split is dead even, 240 to 240. On any given event either book can be the one that reprices first. 

## Findings

Arbitrage between Kalshi and Polymarket exists on paper. Over 3 days and 40 games, 480 opportunities were bigger than the round-trip taker fees.

In practice it cannot be exploited.

71 opportunities persisted for 1 second or longer, together worth about $27.38 in theory, or $0.68 per game. But duration is only known after the fact. At the moment the books cross there is no way to tell whether the opportunity will last 1 second or 100 milliseconds, and the majority vanish in under a second. Firing at every crossing means the Polymarket leg sits in the 1 to 3 second taker delay while most of the opportunities close, leaving you with unfilled or one-sided positions. So the persistent opportunities cannot be separated from the rest in real time, and the pool as a whole is not tradeable.

**The two books are effectively one market.** They price within fees of each other almost all the time, and the gaps that do open are closed faster than a retail participant can act. Even if you could act instantly and capture every single opportunity at its peak, the whole pool is worth about $10 per game. The market makers racing each other across platforms have already collapsed this trade down to scraps, and Polymarket's taker delay makes sure you can't even pick those up.
