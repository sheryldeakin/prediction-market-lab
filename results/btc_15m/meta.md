Minute-bar barrier labels: which comes first in the minutes after entry, a minute's high reaching the upper barrier, a minute's low reaching the lower barrier, or the time limit (then the sign of the final move). A minute that crosses both is ambiguous with one-minute bars and is labelled by its close. XGBoost, price + flow + indicators, walk-forward.

| minute | label | how windows resolved | share up | accuracy [95% CI] | AUC |
|---|---|---|---|---|---|
| 0 | close >= open (plain) |  | 49.7% | 53.11% [52.55, 53.70] | 0.544 |
| 0 | minute-bar barrier, fixed 10 bp | upper 39%, lower 40%, ambiguous 0.7%, time 20% | 49.6% | 52.22% [51.56, 52.87] | 0.531 |
| 0 | minute-bar barrier, 1.0 x volatility | upper 26%, lower 26%, ambiguous 0.0%, time 48% | 49.5% | 52.28% [51.69, 52.89] | 0.532 |
| 0 | minute-bar barrier, 2.0 x volatility | upper 6%, lower 7%, ambiguous 0.0%, time 87% | 49.7% | 53.04% [52.45, 53.70] | 0.543 |
| 3 | close >= open (plain) |  | 49.7% | 66.32% [65.70, 66.93] | 0.720 |
| 3 | minute-bar barrier, fixed 10 bp | upper 36%, lower 36%, ambiguous 0.6%, time 27% | 50.1% | 50.91% [50.28, 51.51] | 0.513 |
| 3 | minute-bar barrier, 1.0 x volatility | upper 25%, lower 25%, ambiguous 0.0%, time 50% | 50.1% | 50.89% [50.24, 51.47] | 0.513 |
| 3 | minute-bar barrier, 2.0 x volatility | upper 6%, lower 6%, ambiguous 0.0%, time 88% | 50.1% | 50.99% [50.34, 51.58] | 0.518 |

Meta-labelling: a second model predicts whether the primary direction call is right, trained only on out-of-sample primary predictions from earlier months. Under a hypothetical cost model (buy the favoured side at 0.5 plus half a 1c spread, pay a 1.75c fee, receive 1 if right) the break-even accuracy is 52.25%. These are sensitivity figures, not a backtest of trades: no venue settles on a Binance last print, and the price model is an assumption. Only the minute-0 rows are even hypothetically meaningful. The AUC is the secondary model's ability to rank right calls above wrong ones.

| minute | rule | windows | share acted on | accuracy of primary [95% CI] | accuracy minus break-even, points [95% CI] | meta AUC |
|---|---|---|---|---|---|---|
| 0 | act always | 20352 | 100% | 52.95% [52.33, 53.55] | +0.70 [+0.08, +1.30] | 0.514 |
| 0 | act when meta >= 0.5 | 15086 | 74% | 53.14% [52.41, 53.86] | +0.89 [+0.16, +1.61] |  |
| 0 | act when meta >= 0.55 | 7225 | 36% | 54.62% [53.54, 55.66] | +2.37 [+1.29, +3.41] |  |
| 0 | act when meta >= 0.6 | 2470 | 12% | 57.25% [55.31, 59.21] | +5.00 [+3.06, +6.96] |  |
| 3 | act always | 20352 | 100% | 66.40% [65.77, 67.06] | +14.15 [+13.52, +14.81] | 0.616 |
| 3 | act when meta >= 0.5 | 18938 | 93% | 67.10% [66.45, 67.79] | +14.85 [+14.20, +15.54] |  |
| 3 | act when meta >= 0.55 | 16273 | 80% | 69.15% [68.45, 69.85] | +16.90 [+16.20, +17.60] |  |
| 3 | act when meta >= 0.6 | 12855 | 63% | 72.05% [71.35, 72.78] | +19.80 [+19.10, +20.53] |  |
