XGBoost with default parameters vs Optuna search (30 trials per month) validated honestly (on the month before the test month) and validated on the test month itself. Walk-forward, price + flow + indicator features. Last column: accuracy minus default on the same windows, day-block 95% interval.

| minute | variant | n | accuracy [95% CI] | AUC | log loss | vs default |
|---|---|---|---|---|---|---|
| 0 | default | 23328 | 53.11% [52.55, 53.70] | 0.544 | 0.6909 | baseline |
| 0 | tuned-honest | 23328 | 53.34% [52.74, 53.99] | 0.546 | 0.6900 | +0.23 [-0.25, +0.71] |
| 0 | tuned-on-test | 23328 | 53.51% [52.91, 54.15] | 0.551 | 0.6889 | +0.40 [-0.05, +0.86] |
| 0 | one-feature baseline (prev-window) | 23328 | 52.21% [51.63, 52.82] | 0.519 | 0.6922 | -0.90 [-1.59, -0.26] |
| 3 | default | 23328 | 66.32% [65.70, 66.93] | 0.720 | 0.6161 | baseline |
| 3 | tuned-honest | 23328 | 66.13% [65.52, 66.75] | 0.720 | 0.6155 | -0.19 [-0.40, +0.04] |
| 3 | tuned-on-test | 23328 | 66.27% [65.69, 66.86] | 0.721 | 0.6147 | -0.04 [-0.26, +0.20] |
| 3 | one-feature baseline (lead-z) | 23328 | 66.35% [65.73, 66.98] | 0.721 | 0.6150 | +0.03 [-0.28, +0.38] |
