---
title: Are Kalshi MLB Game Winner Prices Actually Accurate?
date: 2026-07-06
description: How to look for mispricings on Kalshi MLB Game Winner markets. I walk through an approach using 3,507 games, checking a handful of dimensions (time, innings, teams, weather) as a jumping off point.
---

Do Kalshi MLB Game Winner Prices Reflect Accurate Probabilities?

Kalshi lists a "Game Winner" market for every MLB game. You can buy YES on the team you think will win, and the contract settles at $1 or $0 after the game ends. If a YES contract is trading at 45 cents, the market is saying that team has a 45% chance of winning.

If you find a reliable mispricing, you can always buy the underpriced side and make money on average over time.

This article goes through a basic methodology to search for mispricings.

You take a bunch of games, split them up different ways, and see if prices line up with what actually happened. I checked a few obvious ones here (time, innings, home/away, team, weather) but there are a lot more you could look at. The MLB Stats API has fields for day/night games, division matchups, rest days, pitcher handedness, and that's just one data source. You could pull in Vegas lines, starting pitcher stats, injury reports, umpire assignments. The world is your oyster really.

A write up on the data pull methodology for this analysis can be found [here](https://www.zhinit.dev/blog/pulling-every-mlb-trade-from-kalshi) and the project code is on [GitHub](https://github.com/zhinit/prediction-market-analysis).

## Data

The dataset used in this analysis covers 3,507 MLB games from April 16th, 2025 through July 3rd, 2026. April 16th, 2025 is when Kalshi first listed MLB Game Winner markets. The 2025 MLB season actually started March 27th, so we're missing about three weeks of that season.

Each data point represents the last trade on the home team's market before the scheduled start time. Using a single data point per game/inning avoids a problem of being overconfident by having a large sample size of highly correlated trades happening right next to each other. 

### Calibration

If the prices match the actual win probabilities, we say the market is calibrated. A perfectly calibrated market would have teams priced at 40 cents winning exactly 40% of the time, teams priced at 60 cents winning exactly 60% of the time, and so on. If you plotted price on one axis and win rate on the other, every point would sit on a 45-degree line.

The 45-degree line is what we're checking against in our analysis.

### Confidence intervals

If a team priced at 45 cents wins 48% of the time, is that 3 cent gap real or just meaningless random noise? With 1000 observations it might be meaningful, but with 10 observations it doesn't carry much weight. Confidence intervals give us convenient boundaries we can use to reason about this.

You can visually observe these boundaries in this analysis as the vertical bands on our plots.

At 95% confidence, if the true deviation is zero (i.e. the market is perfectly calibrated), there's a 5% chance the interval excludes zero just by luck. So when you run 30 tests at 95% confidence, you expect one or two false positives.

The standard confidence interval most people learn is called the Wald interval. It works well on an unbounded domain, but it can produce intervals that go below 0% or above 100%. Our domain is always bounded between 0 and 1, so we need something well suited for that. The Wilson score interval stays within [0, 1] by construction which is why I used them throughout this analysis. For the rest of this write up I'll just call them confidence intervals.

### What would a profitable mispricing look like?

A deviation only matters if it survives the cost of trading it. To exploit a mispricing you'd buy the underpriced side and hold to settlement  The costs are

- Taker fee: 7 * p * (1-p) per contract
- Roughly half the bid-ask spread

Most pre-game MLB prices land around 50 cents. At 50 cents the taker fee is 7 * 0.5 * 0.5 = 1.75 cents, and the median bid-ask spread is about 1 cent (see Appendix C), so half the spread adds another 0.5 cents. That puts the total cost at roughly 2.2 cents per contract.

Thus any successful strategy should have a deviation of more than ~2 cents.

## Overall calibration

Each game contributes one data point. I grouped them into 10 cent price buckets and compared the average price in each bucket to the actual win rate.

![Pre-game calibration and deviation from the diagonal](images/overall-calibration.png)


| price range | avg price | win rate | win - price | 95% CI (win - price) | samples |
|---|---|---|---|---|---|
| 0-10c | 1.6c | 0.0% | -1.6c | [-1.6c, 41.8c] | 5 |
| 20-30c | 27.8c | 38.1% | +10.3c | [-7.1c, 31.3c] | 21 |
| 30-40c | 36.3c | 36.7% | +0.4c | [-6.3c, 7.6c] | 180 |
| 40-50c | 45.4c | 48.5% | +3.1c | [-0.1c, 6.4c] | 892 |
| 50-60c | 54.5c | 53.7% | -0.9c | [-3.4c, 1.6c] | 1,532 |
| 60-70c | 63.3c | 58.2% | -5.1c | [-8.8c, -1.6c] | 717 |
| 70-80c | 72.6c | 73.1% | +0.4c | [-7.0c, 6.8c] | 156 |
| 80-90c | 80.0c | 100.0% | +20.0c | [-45.8c, 20.0c] | 2 |
| 90-100c | 99.0c | 100.0% | +1.0c | [-64.8c, 1.0c] | 2 |

The left panel shows the calibration curve. Points near the 45-degree line mean the market is well calibrated in that price range. The right panel shows the deviation (win rate minus price) with 95% confidence bands. 

Pre-game MLB prices live almost entirely between 30 and 80 cents. This makes sense because its hard to know who will win before the game begins. The extreme price buckets (below 30 cents, above 80 cents) have only a handful of games, so those points are not very meaningful. In the rest of the analysis I dont show bands with less than 30 samples which makes the plots easier to read.

In the populated range, most buckets sit on or near the diagonal. There is one bucket where the confidence interval excludes zero. The 60 to 70 cent range shows a deviation of -5.1 cents across 717 games. Teams priced in this range won about 58% of the time instead of the implied 63%.

If you step back and think about it though, it seems fairly random that just one bucket from 60 to 70 cents would be mispriced. Why would 60 to 70 cents be mispriced but 50 to 60 and 70 to 80 be well calibrated? It might be convincing if we saw something asymmetric, like everything above 60 cents being mispriced in the same direction. Perhaps when a team is highly likely to win it distorts people's perceptions and they overestimate that probability based on emotions. However, one isolated bucket is likely just random noise.

## Stability over time

Whenever you think you've found a mispricing, the first thing to check is whether it persists through time. If an edge existed in early 2025, other participants may have found it too, started trading it, and pushed prices back to where they should be. An opportunity that got exploited and "patched" like this isn't one you can trade going forward. 

Here I split each season in half at its median game date, giving four periods.

| period | first game | last game | games |
|---|---|---|---|
| 2025 early | 2025-04-16 | 2025-07-08 | 1,103 |
| 2025 late | 2025-07-08 | 2025-11-01 | 1,100 |
| 2026 early | 2026-03-26 | 2026-05-14 | 652 |
| 2026 late | 2026-05-14 | 2026-07-03 | 652 |

![Pre-game calibration by period](images/calibration-by-period.png)

The calibration holds across all four periods. There's some variation (expected with smaller sample sizes per period), but no period where the market was systematically off. This also weakens the case for the 60 to 70 cent bucket from the overall view being real. If it were a true mispricing, you'd expect to see it show up consistently, not appear in one time window and vanish in the next.

## Breakdown by inning

The pre-game price isn't the only thing worth checking. Kalshi markets stay open during the game, so prices update as the game unfolds. For inning views, I use the last trade during the preceding inning as the data point entering that inning.

![Calibration by inning, innings 2 through extras](images/calibration-by-inning.png)

Markets appear well calibrated throughout the game. A handful of buckets across various innings have confidence intervals that exclude zero, but there's no pattern in where they land. For example why would only the 60 cent to 70 cent band be mispriced in the 6th inning but not the 5th or 7th inning.

An interesting thing to note is how the sample distribution changes as the game progresses.

- pre-game
    - samples are concentrated between 40c to 60c
    - ie prior to the game it's hard to know who will win
- during the beginning and middle of the game
    - samples are fairly evenly spread across buckets
    - ie one team could take the lead causing probabilities to skew towards either side
- and towards the end of the game
    - samples are concentrated at prices in the middle and at the ends
    - ie if the score is close either team could win it, or one team has a lead and will likely win

## Home vs. away

Home field advantage is a real thing in baseball, but does the market price it correctly?

If bettors are systematically underpricing or overpricing home teams, that would show up as a split between the home and away calibration curves.

For this view I use two data points per game, one for each team.

![Pre-game calibration by side, home vs away](images/calibration-home-away.png)

| side | avg price | win rate | deviation | 95% CI | games |
|---|---|---|---|---|---|
| away | 47.5c | 46.8% | -0.6c | [-2.3c, 1.0c] | 3,507 |
| home | 53.7c | 53.2% | -0.5c | [-2.2c, 1.1c] | 3,507 |

Home teams are priced at about 53.7 cents on average and win 53.2% of the time. Away teams are priced at 47.5 cents and win 46.8%. Both deviations are less than a cent with confidence intervals comfortably including zero. Thus, the market knows about home field advantage and prices it appropriately.

## Breakdown by team

Maybe the aggregate is fine but a specific team is consistently mispriced. Die-hard fans who bet on their team no matter what could push prices up.

This view uses two data points per game (one per team), giving roughly 230 observations per team across 30 MLB teams.

![Pre-game calibration by team](images/calibration-by-team.png)

Only 1 confidence intervals with more than 30 samples excludes zero.\
The New York Mets at -8.2 cents (the market overpriced them).

But with 30 teams tested at 95% confidence, you expect 1.5 false positives on average. Getting one or two is what random chance produces. Thus this could easily just be random niose. 

Worth watching with more data, but not something I'd trade on.

## Weather

Could weather cause pricing inefficiencies? Maybe a team performs differently in the heat or rain and the market hasn't priced it in.

I grouped weather conditions into four categories
- clear (clear, sunny)
- clouds (partly cloudy, cloudy, overcast)
- roof/dome (roof closed, dome)
- rain (rain, drizzle)

*Note temperature and wind views only use outdoor games.*

![Pre-game calibration by weather condition](images/calibration-by-condition.png)

| condition | avg price | win rate | deviation | 95% CI | games |
|---|---|---|---|---|---|
| clear | 54.2c | 55.0% | +0.8c | [-2.2c, 3.8c] | 1,058 |
| clouds | 53.4c | 51.2% | -2.2c | [-4.5c, 0.1c] | 1,839 |
| rain | 55.0c | 45.2% | -9.9c | [-25.9c, 7.2c] | 31 |
| roof/dome | 53.4c | 56.3% | +2.9c | [-1.2c, 6.9c] | 579 |

No weather group deviates significantly. Rain looks dramatic at -9.9 cents but that's based on 31 games which give a a confidence interval so wide it's meaningless. Also note there were no 10 cent buckets for rain with more than 30 samples which is why the plot is blank.

![Pre-game calibration by temperature, outdoor games](images/calibration-by-temperature.png)

![Pre-game calibration by wind speed, outdoor games](images/calibration-by-wind.png)

Temperature and wind tell the same story. All confidence intervals include zero. The market prices in weather appropriately.

## Findings

No mispricings were found in the dimensions checked here. Across 3,507 games, everything came back well calibrated. A few buckets here and there had confidence intervals that excluded zero, but they were scattered with no pattern which is consistent with what you'd expect from random noise at 95% confidence.

Across these dimensions, Kalshi MLB Game Winner prices do accurately reflect real world probabilities. The market knows about home field advantage, it prices in weather, and it doesn't systematically misprice any particular team. When it says a team has a 55% chance of winning, that team wins about 55% of the time.

**If a mispricing exists on these markets, you will need to more creative 😉.**

But this is a handful of cuts out of a much larger search space. For example, you could look at additional breakdowns by day vs night games, rest days between games, doubleheader game order, starting pitcher stats, bullpen usage, umpire tendencies, travel schedules, yada, yada, yada, the list goes on.


## Appendix A: no-arbitrage check

Each game has two markets, one per team, each with its own order book. If the books are consistent, the two pre-game data points should sum to $1.

They do. The median of home price plus away price is about $1.01. 73% of games land within 2 cents of $1, and only 16 of 3,507 games land beyond 5 cents.

*The two data points are last trades from two separate books, possibly minutes apart, and each prints at its book's bid or ask. A cent or two of slack is expected, and a stale leg explains sums further out.*

A fat tail far from $1 would have been a finding in its own right (free arbitrage). 16 games of 3,507 is not one.

Because the away market is the home market's mirror and carries no extra information, the analysis uses only the home side.

## Appendix B: data point freshness

How stale is the pre-game data point at first pitch?

| metric | value |
|---|---|
| median age | 1 minute |
| 90th percentile | 5 minutes |
| 99th percentile | 29 minutes |

Every game has a home-side trade inside the 24 hour window, and most have one within a few minutes of first pitch. So the exact definition of "shortly before the game" doesn't matter much. How much could available information possibly change in the 30 minutes leading up to the game?

## Appendix C: effective spread

Trades hit the bid or the ask, never in between. A taker buying YES prints at the ask, a taker selling YES prints at the bid. If spreads were wide, a last-trade data point could sit up to half a spread away from the market's actual estimate, and that alone could look like miscalibration.

For each game I take the last taker-bought-YES print (the ask) and the last taker-sold-YES print (the bid) on the home team's market in the pre-game window. The gap is a proxy for the spread.

| metric | value |
|---|---|
| median spread | 1 cent |
| 90th percentile | 2 cents |
| games above 3 cents | 92 of 3,392 |

The spread is basically one cent. So the last trade sits at most about half a cent from where the market actually is. That half cent is the half-spread charged in the cost calculation.

*The two legs can be minutes apart, so if the market moved between them the gap can come out zero or negative.*
