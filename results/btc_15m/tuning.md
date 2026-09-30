XGBoost with default parameters vs Optuna search (30 trials per month) validated honestly (on the month before the test month) and validated on the test month itself. Walk-forward, price + flow + indicator features. Last column: accuracy minus default on the same windows, day-block 95% interval.

| minute | variant | n | accuracy [95% CI] | AUC | log loss | vs default |
|---|---|---|---|---|---|---|
| 0 | default | 23327 | 52.96% [52.36, 53.58] | 0.542 | 0.6913 | baseline |
| 0 | tuned-honest | 23327 | 53.41% [52.82, 54.03] | 0.547 | 0.6898 | +0.45 [+0.00, +0.87] |
| 0 | tuned-on-test | 23327 | 53.45% [52.85, 54.09] | 0.550 | 0.6890 | +0.49 [+0.03, +0.94] |
| 3 | default | 23327 | 66.34% [65.71, 66.96] | 0.720 | 0.6162 | baseline |
| 3 | tuned-honest | 23327 | 66.21% [65.59, 66.84] | 0.720 | 0.6158 | -0.13 [-0.35, +0.09] |
| 3 | tuned-on-test | 23327 | 66.29% [65.67, 66.89] | 0.722 | 0.6148 | -0.05 [-0.27, +0.17] |
