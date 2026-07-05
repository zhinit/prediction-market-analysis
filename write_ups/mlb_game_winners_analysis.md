# Do Kalshi MLB Game Winner Prices Reflect Accurate Probabilities?

If a YES contract trades at 45c just before first pitch, does that team win 45% of the time?

That's the whole question. If prices match probabilities the market is calibrated and there's nothing to make.
If they don't, there's potentially money on the table: a team priced at 45c that actually wins 50% of the time earns 5c per contract on average.

The full analysis lives in `analysis/mlb_calibration.ipynb`. This is the write-up.

## The data

3,507 games, April 16 2025 through July 3 2026.
Kalshi's MLB markets started trading April 16 2025 and I ran the last data pull on July 3 2026, so that's the range.
Note
- the 2025 season started March 27, so ~3 weeks of that season are missing

Prices come from the official Kalshi API. Game outcomes, innings, and weather come from the MLB Stats API.
The extensive write-up on the data pull is [data_pull.md](data_pull.md).

## Method

Each game contributes a single data point: the last trade on its home team's market before the scheduled start, restricted to the 24 hours before start so stale quotes don't leak in.

Why one point per game? A game's trades are highly correlated with each other.
Counting them all inflates the sample size and makes every confidence interval overconfident.

For the by-inning view, the data point is the last trade during the preceding inning, ie the price entering that inning.

Data is displayed in 10c price buckets, with a 95% confidence interval on win rate minus price.
Wilson intervals, because prices and probabilities live between 0 and 1 and Wilson is designed to stay in that range.

The snapshots are fresh: median age at first pitch is 1 minute, 90th percentile 5 minutes, 99th 29 minutes.
So the exact definition of "shortly before the game" shouldn't matter much.

## What counts as an opportunity

A deviation is only interesting if it survives the cost of trading it.
Exploiting one means buying the underpriced side as a taker and holding to settlement (settlement is free). The cost:

- taker fee: 7c × price × (1 − price) per contract, about 1.7c at 45c
- half the bid-ask spread, about 0.5c. The effective spread is basically one cent: median gap between the last taker-bought and last taker-sold print is 1c, 90th percentile 2c, only 92 of 3,392 games above 3c.

That comes to about 2.2c in the mid-range where MLB games trade before the game starts.
A mispricing has to be bigger than that before it's profit.

## Cut 1 - Overall

One data point per game, the home-side market just before first pitch.

| price range | avg price | win rate | win − price | 95% CI | samples |
|---|---|---|---|---|---|
| 0–10¢ | 1.6¢ | 0.0% | -1.6¢ | [-1.6¢, 41.8¢] | 5 |
| 20–30¢ | 27.8¢ | 38.1% | +10.3¢ | [-7.1¢, 31.3¢] | 21 |
| 30–40¢ | 36.3¢ | 36.7% | +0.4¢ | [-6.3¢, 7.6¢] | 180 |
| 40–50¢ | 45.4¢ | 48.5% | +3.1¢ | [-0.1¢, 6.4¢] | 892 |
| 50–60¢ | 54.5¢ | 53.7% | -0.9¢ | [-3.4¢, 1.6¢] | 1,532 |
| 60–70¢ | 63.3¢ | 58.2% | -5.1¢ | [-8.8¢, -1.6¢] | 717 |
| 70–80¢ | 72.6¢ | 73.1% | +0.4¢ | [-7.0¢, 6.8¢] | 156 |
| 80–90¢ | 80.0¢ | 100.0% | +20.0¢ | [-45.8¢, 20.0¢] | 2 |
| 90–100¢ | 99.0¢ | 100.0% | +1.0¢ | [-64.8¢, 1.0¢] | 2 |

Note
- pre-game MLB prices live almost entirely between 25c and 75c, so the tails of this curve are nearly empty
- ie prior to the game it's hard to know who will win

![Pre-game calibration and deviation from the diagonal](images/cut1_pre_game_calibration.png)

One bucket's CI excludes zero: 60-70c favorites win only 58.2%, a deviation of -5.1c.

Do I believe it? Why would 60-70c be mispriced but 50-60c and 70-80c be well calibrated?
An asymmetric pattern would make more sense, like everything above 60c mispriced in the same direction.
Maybe when a team is highly likely to win it distorts people's perceptions and they overestimate based on emotions. But that's not what the data shows.
Reasons to distrust the bucket instead:

- the bucket boundaries were chosen after looking at the data
- ~10 buckets were tested, so one exclusion is close to the false positive rate of 95% intervals
- it doesn't show up consistently across time periods (Cut 5)
- even at face value it's untradeable after costs (below)

My read: noise.

## Cut 2 - By inning

The price entering innings 2-9 and extras (entering the 10th), same bucketing.

![Calibration by inning](images/cut2_by_inning.png)

In-game prices are well calibrated.
Across the nine entering-inning tables, 5 of 86 buckets' CIs exclude zero, roughly the false positive rate of 95% intervals, with no pattern in where they land.
Entering extras is the thinnest slice (302 samples) and shows nothing significant.

The sample distribution tells its own story: pre-game the samples concentrate between 40c and 60c, mid-game they spread across all buckets as one team takes a lead, and late-game they pile up in the middle and at the ends. Either the score is close and it's a coin flip, or someone has a lead and will likely win.

## Cut 3 - Home vs Away

A home team bias would show up here. Two data points per game for this cut, one per team.

| side | avg price | win rate | win − price | 95% CI | samples |
|---|---|---|---|---|---|
| away | 47.5¢ | 46.8% | -0.6¢ | [-2.3¢, 1.0¢] | 3,507 |
| home | 53.7¢ | 53.2% | -0.5¢ | [-2.2¢, 1.1¢] | 3,507 |

![Pre-game calibration by side](images/cut3_home_away.png)

No home team bias. Neither side deviates significantly.

Worth flagging: an earlier version of this analysis used one observation per trade, volume-weighted, and it flagged home mid-range markets as significantly overpriced.
That result did not survive the switch to one observation per game.
A caution against reading too much into any single cut here.

## Cut 4 - By team

Potentially a team could have die-hard fans that bet they will win no matter what. Is this the case?

![Pre-game calibration by team](images/cut4_by_team.png)

Two of thirty teams have intervals excluding zero: Milwaukee at +6.4c and the Mets at -8.2c.
Note
- ~230 samples per team, 30 teams
- at 95% confidence, one or two of every thirty intervals excluding zero is what random chance alone produces

Anything that looks like it possibly could be miscalibrated has a small sample size behind it.
Markets look calibrated team by team.

## Cut 5 - Stability over time

If there are opportunities, do they persist? Maybe there used to be one and market players found it.

Each season is split in half at its median game date, giving four periods (2025 early/late at ~1,100 games each, 2026 early/late at 652 each).

![Pre-game calibration by period](images/cut5_by_period.png)

Pre-game markets are well calibrated in all four, with some variation between periods.
The 60-70c dip from Cut 1 does not repeat consistently across periods, which is more evidence it's noise.

## Cut 6 - Weather

Could weather cause pricing inefficiencies? Perhaps a particular team performs worse in heat/cold/rain and the market hasn't priced it in.

Conditions grouped into clear, clouds, roof/dome, and rain. Temperature in four bands, wind in three, both on outdoor games only.

![Pre-game calibration by condition](images/cut6_conditions.png)

![Pre-game calibration by temperature](images/cut6_temperature.png)

![Pre-game calibration by wind](images/cut6_wind.png)

Eleven intervals, none exclude zero.
The rain group is 31 games and says nothing either way.

## Costs - Calibrated vs Exploitable

Netting the taker fee plus half the one-tick spread (~2.2c in the mid-range) against the curve, no bucket's CI clears the cost band.
Even the one significant bucket (60-70c) has a CI near edge of -1.6c against a ~2.1c cost.
So even if that deviation were real, trading it loses money.

## Method checks

Three checks backing the setup, details in the notebook appendices.

**No-arbitrage.** Each game has two markets, one per team, each with its own order book. If the books are consistent the two pre-game snapshots should sum to $1. They do: median p_home + p_away is 101.0c, 73% of games land within 2c of $1, and only 16 of 3,507 land beyond 5c. So the away market is the home market's mirror and carries no extra information. The analysis keeps the home side. A fat tail far from $1 would have been a finding in its own right (free arbitrage). 16 games of 3,507 is not one.

**Snapshot freshness.** Median age at first pitch 1 minute, p99 29 minutes, and every game has a home-side trade inside the 24 hour window.

**Effective spread.** Trades print at the bid or the ask, never in between, so a last-trade snapshot could sit half a spread from the market's actual estimate. If spreads were wide, that alone could look like miscalibration. They aren't: the spread is basically one cent, so the last trade sits at most about half a cent from where the market actually is. That half cent is what the cost section charges.

## Verdict

Kalshi's MLB game winner markets are calibrated.

- Pre-game: one significant bucket out of ~10, judged noise
- By inning: 5 of 86 buckets significant, the false positive rate
- Home vs away: -0.5c and -0.6c, neither significant
- By team: 2 of 30 significant, what chance produces
- Over time: calibrated in all four periods
- Weather: 11 intervals, none significant

And the deviations that do appear are smaller than the ~2.2c it costs to trade them.
No exploitable mispricing found in these markets.
