Feature-set ablation, walk-forward by month. Last column: accuracy minus the price-only forest on the same windows, day-block 95% interval.

| minute | features | model | n | accuracy | AUC | log loss | vs price-only forest |
|---|---|---|---|---|---|---|---|
| 0 | price | forest | 23327 | 52.72% | 0.536 | 0.6917 | +0.00 [+0.00, +0.00] |
| 0 | price | xgb | 23327 | 52.28% | 0.534 | 0.6924 | -0.44 [-0.93, +0.06] |
| 0 | price + flow | forest | 23327 | 52.98% | 0.540 | 0.6909 | +0.26 [-0.30, +0.87] |
| 0 | price + flow | xgb | 23327 | 52.54% | 0.536 | 0.6920 | -0.18 [-0.80, +0.41] |
| 0 | price + flow + indicators | forest | 23327 | 53.40% | 0.546 | 0.6900 | +0.68 [+0.14, +1.25] |
| 0 | price + flow + indicators | xgb | 23327 | 53.29% | 0.544 | 0.6908 | +0.57 [-0.05, +1.20] |
| 0 | price + flow + tick flow | forest | 23327 | 53.01% | 0.544 | 0.6902 | +0.29 [-0.31, +0.93] |
| 0 | price + flow + tick flow | xgb | 23327 | 52.92% | 0.540 | 0.6915 | +0.20 [-0.43, +0.84] |
| 0 | everything | forest | 23327 | 53.18% | 0.546 | 0.6900 | +0.46 [-0.19, +1.15] |
| 0 | everything | xgb | 23327 | 53.19% | 0.545 | 0.6908 | +0.47 [-0.17, +1.10] |
| 3 | price | forest | 23327 | 66.00% | 0.719 | 0.6166 | +0.00 [+0.00, +0.00] |
| 3 | price | xgb | 23327 | 66.22% | 0.718 | 0.6170 | +0.22 [-0.07, +0.50] |
| 3 | price + flow | forest | 23327 | 66.20% | 0.719 | 0.6161 | +0.20 [-0.04, +0.45] |
| 3 | price + flow | xgb | 23327 | 66.17% | 0.718 | 0.6172 | +0.18 [-0.13, +0.48] |
| 3 | price + flow + indicators | forest | 23327 | 66.15% | 0.720 | 0.6156 | +0.15 [-0.11, +0.41] |
| 3 | price + flow + indicators | xgb | 23327 | 66.34% | 0.720 | 0.6157 | +0.35 [+0.03, +0.68] |
| 3 | price + flow + tick flow | forest | 23327 | 66.29% | 0.720 | 0.6160 | +0.29 [+0.03, +0.54] |
| 3 | price + flow + tick flow | xgb | 23327 | 66.32% | 0.719 | 0.6168 | +0.33 [+0.02, +0.63] |
| 3 | everything | forest | 23327 | 66.29% | 0.720 | 0.6155 | +0.29 [+0.05, +0.54] |
| 3 | everything | xgb | 23327 | 66.32% | 0.720 | 0.6159 | +0.33 [+0.03, +0.63] |
