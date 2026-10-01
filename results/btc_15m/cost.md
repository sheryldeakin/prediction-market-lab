Break-even accuracy under hypothetical costs. Forest, price + flow features, walk-forward, acting only when the probability is far enough from 0.5. Under a hypothetical cost model (buy the favoured side at 0.5 plus half a 1c spread, pay a 1.75c fee, receive 1 if right) the break-even accuracy is 52.25%. These are sensitivity figures, not a backtest of trades: no venue settles on a Binance last print, and the price model is an assumption. After the open a market would not be priced at 0.5, so only the minute-0 rows are even hypothetically meaningful. Last column: accuracy minus break-even, in points, day-block 95% interval.

| minute | act when probability | windows | share acted on | accuracy | accuracy minus break-even, points [95% CI] |
|---|---|---|---|---|---|
| 0 | >= 0.50 or <= 0.50 | 23328 | 100% | 52.65% | +0.40 [-0.24, +1.08] |
| 0 | >= 0.53 or <= 0.47 | 12585 | 54% | 54.17% | +1.92 [+1.06, +2.79] |
| 0 | >= 0.55 or <= 0.45 | 7300 | 31% | 55.11% | +2.86 [+1.83, +3.98] |
| 0 | >= 0.58 or <= 0.42 | 2645 | 11% | 57.77% | +5.52 [+3.78, +7.30] |
| 3 | >= 0.50 or <= 0.50 | 23328 | 100% | 66.13% | +13.88 [+13.27, +14.50] |
| 3 | >= 0.53 or <= 0.47 | 21114 | 91% | 67.64% | +15.39 [+14.78, +16.02] |
| 3 | >= 0.55 or <= 0.45 | 19584 | 84% | 68.83% | +16.58 [+15.96, +17.24] |
| 3 | >= 0.58 or <= 0.42 | 17306 | 74% | 70.41% | +18.16 [+17.51, +18.83] |
