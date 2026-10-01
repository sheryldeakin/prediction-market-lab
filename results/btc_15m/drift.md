Training window: for each test month, train on the last W months only or on every earlier month. XGBoost, price + flow + indicators, walk-forward. Last column: accuracy minus expanding on the same windows, day-block 95% interval.

| minute | training window | n | accuracy [95% CI] | log loss | vs expanding |
|---|---|---|---|---|---|
| 0 | last 2 months | 23328 | 53.02% [52.40, 53.66] | 0.6942 | +0.19 [-0.46, +0.81] |
| 0 | last 3 months | 23328 | 52.87% [52.28, 53.47] | 0.6929 | +0.04 [-0.54, +0.59] |
| 0 | last 4 months | 23328 | 52.75% [52.14, 53.38] | 0.6917 | -0.08 [-0.54, +0.39] |
| 0 | last 6 months | 23328 | 52.71% [52.12, 53.31] | 0.6912 | -0.12 [-0.48, +0.24] |
| 0 | expanding | 23328 | 52.83% [52.25, 53.45] | 0.6911 | baseline |
| 3 | last 2 months | 23328 | 66.23% [65.64, 66.87] | 0.6212 | -0.19 [-0.50, +0.15] |
| 3 | last 3 months | 23328 | 66.06% [65.46, 66.71] | 0.6186 | -0.36 [-0.61, -0.10] |
| 3 | last 4 months | 23328 | 66.17% [65.55, 66.80] | 0.6173 | -0.25 [-0.51, -0.01] |
| 3 | last 6 months | 23328 | 66.26% [65.63, 66.88] | 0.6162 | -0.16 [-0.33, +0.00] |
| 3 | expanding | 23328 | 66.42% [65.80, 67.03] | 0.6160 | baseline |

Retrain frequency: on each target month (2026-04 to 2026-08), the model retrained just before it and the models last retrained one, two and three months earlier, all scored on the same windows. Last column: accuracy minus the fresh model, day-block 95% interval.

| minute | months since retrain | target months | n | accuracy [95% CI] | vs fresh model |
|---|---|---|---|---|---|
| 0 | 0 | 5 | 14688 | 52.79% [51.98, 53.64] | reference |
| 0 | 1 | 5 | 14688 | 53.02% [52.23, 53.81] | +0.22 [-0.37, +0.80] |
| 0 | 2 | 5 | 14688 | 52.41% [51.65, 53.19] | -0.38 [-1.01, +0.26] |
| 0 | 3 | 5 | 14688 | 52.38% [51.57, 53.23] | -0.41 [-1.10, +0.31] |
| 3 | 0 | 5 | 14688 | 66.98% [66.20, 67.73] | reference |
| 3 | 1 | 5 | 14688 | 66.76% [66.01, 67.50] | -0.22 [-0.44, +0.01] |
| 3 | 2 | 5 | 14688 | 66.87% [66.15, 67.58] | -0.11 [-0.39, +0.20] |
| 3 | 3 | 5 | 14688 | 66.74% [66.04, 67.46] | -0.24 [-0.52, +0.05] |
