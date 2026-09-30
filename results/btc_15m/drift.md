Training window: for each test month, train on the last W months only or on every earlier month. XGBoost, price + flow + indicators, walk-forward. Last column: accuracy minus expanding on the same windows, day-block 95% interval.

| minute | training window | n | accuracy [95% CI] | log loss | vs expanding |
|---|---|---|---|---|---|
| 0 | last 2 months | 23327 | 52.98% [52.35, 53.63] | 0.6945 | +0.02 [-0.63, +0.65] |
| 0 | last 3 months | 23327 | 52.99% [52.40, 53.62] | 0.6932 | +0.03 [-0.56, +0.61] |
| 0 | last 4 months | 23327 | 52.97% [52.38, 53.59] | 0.6920 | +0.01 [-0.49, +0.50] |
| 0 | last 6 months | 23327 | 52.91% [52.36, 53.52] | 0.6915 | -0.05 [-0.40, +0.30] |
| 0 | expanding | 23327 | 52.96% [52.36, 53.58] | 0.6913 | baseline |
| 3 | last 2 months | 23327 | 66.18% [65.57, 66.83] | 0.6208 | -0.16 [-0.45, +0.16] |
| 3 | last 3 months | 23327 | 66.11% [65.50, 66.79] | 0.6189 | -0.23 [-0.50, +0.06] |
| 3 | last 4 months | 23327 | 66.35% [65.74, 67.00] | 0.6172 | +0.01 [-0.24, +0.29] |
| 3 | last 6 months | 23327 | 66.37% [65.75, 67.00] | 0.6165 | +0.03 [-0.12, +0.18] |
| 3 | expanding | 23327 | 66.34% [65.71, 66.96] | 0.6162 | baseline |

Retrain frequency: a model trained at the start of a month and kept without retraining. Accuracy by months since the last retrain, pooled over all start months (later ages have fewer start months).

| minute | months since retrain | start months | n | accuracy [95% CI] |
|---|---|---|---|---|
| 0 | 0 | 8 | 23327 | 52.96% [52.36, 53.58] |
| 0 | 1 | 7 | 20351 | 53.07% [52.42, 53.79] |
| 0 | 2 | 6 | 17663 | 52.71% [52.02, 53.38] |
| 0 | 3 | 5 | 14687 | 52.94% [52.16, 53.71] |
| 3 | 0 | 8 | 23327 | 66.34% [65.71, 66.96] |
| 3 | 1 | 7 | 20351 | 66.23% [65.59, 66.87] |
| 3 | 2 | 6 | 17663 | 66.29% [65.59, 66.93] |
| 3 | 3 | 5 | 14687 | 66.83% [66.09, 67.56] |
