Triple-barrier labels: which comes first in the 15 minutes, the upper barrier, the lower barrier, or the time limit (then the sign of the final move). XGBoost, price + flow + indicators, walk-forward.

| minute | label | how windows resolved | share up | accuracy [95% CI] | AUC |
|---|---|---|---|---|---|
| 0 | close >= open (plain) |  | 49.7% | 52.96% [52.36, 53.58] | 0.542 |
| 0 | fixed 10 bp barriers | upper 37%, lower 38%, time 25% | 49.3% | 52.98% [52.31, 53.60] | 0.540 |
| 0 | 1.0 x volatility barriers | upper 22%, lower 22%, time 56% | 49.5% | 52.72% [52.11, 53.35] | 0.538 |
| 0 | 2.0 x volatility barriers | upper 5%, lower 5%, time 90% | 49.7% | 52.87% [52.30, 53.49] | 0.542 |
| 3 | close >= open (plain) |  | 49.7% | 66.34% [65.71, 66.96] | 0.720 |
| 3 | fixed 10 bp barriers | upper 34%, lower 34%, time 33% | 50.0% | 50.84% [50.27, 51.39] | 0.512 |
| 3 | 1.0 x volatility barriers | upper 21%, lower 21%, time 58% | 50.1% | 51.10% [50.47, 51.73] | 0.517 |
| 3 | 2.0 x volatility barriers | upper 5%, lower 5%, time 91% | 50.1% | 51.01% [50.38, 51.62] | 0.517 |

Meta-labelling: a second model predicts whether the primary direction call is right, trained only on out-of-sample primary predictions from earlier months. EV in cents per $1 contract at a 1c spread and 1.75c fee, priced at 0.5 (only meaningful at minute 0). The AUC is the secondary model's ability to rank right calls above wrong ones.

| minute | rule | windows | share acted on | accuracy of primary [95% CI] | EV cents [95% CI] | meta AUC |
|---|---|---|---|---|---|---|
| 0 | act always | 20351 | 100% | 52.83% [52.22, 53.46] | +0.58 [-0.03, +1.21] | 0.513 |
| 0 | act when meta >= 0.5 | 14919 | 73% | 53.21% [52.50, 53.92] | +0.96 [+0.25, +1.67] |  |
| 0 | act when meta >= 0.55 | 6997 | 34% | 54.01% [52.92, 55.16] | +1.76 [+0.67, +2.91] |  |
| 0 | act when meta >= 0.6 | 2340 | 11% | 55.34% [53.35, 57.52] | +3.09 [+1.10, +5.27] |  |
| 3 | act always | 20351 | 100% | 66.38% [65.74, 67.06] | +14.13 [+13.49, +14.81] | 0.614 |
| 3 | act when meta >= 0.5 | 19159 | 94% | 66.98% [66.31, 67.67] | +14.73 [+14.06, +15.42] |  |
| 3 | act when meta >= 0.55 | 16420 | 81% | 68.98% [68.27, 69.69] | +16.73 [+16.02, +17.44] |  |
| 3 | act when meta >= 0.6 | 13002 | 64% | 71.64% [70.88, 72.40] | +19.39 [+18.63, +20.15] |  |
