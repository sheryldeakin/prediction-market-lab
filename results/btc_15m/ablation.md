Feature-set ablation, walk-forward by month. The last two columns are accuracy minus the price-only forest and minus the one-feature baseline (the previous window at the open, the lead z-score after), on the same windows, day-block 95% intervals.

| minute | features | model | n | accuracy | AUC | log loss | vs price-only forest | vs one-feature baseline |
|---|---|---|---|---|---|---|---|---|
| 0 | price | forest | 23328 | 52.49% | 0.537 | 0.6916 | +0.00 [+0.00, +0.00] | +0.28 [-0.32, +0.91] |
| 0 | price | xgb | 23328 | 52.38% | 0.533 | 0.6926 | -0.10 [-0.60, +0.39] | +0.18 [-0.52, +0.86] |
| 0 | price + flow | forest | 23328 | 52.65% | 0.539 | 0.6910 | +0.16 [-0.42, +0.76] | +0.44 [-0.25, +1.18] |
| 0 | price + flow | xgb | 23328 | 52.37% | 0.536 | 0.6918 | -0.11 [-0.74, +0.52] | +0.17 [-0.55, +0.87] |
| 0 | price + flow + indicators | forest | 23328 | 53.48% | 0.547 | 0.6899 | +0.99 [+0.42, +1.55] | +1.27 [+0.58, +1.95] |
| 0 | price + flow + indicators | xgb | 23328 | 53.11% | 0.544 | 0.6909 | +0.63 [+0.05, +1.21] | +0.90 [+0.26, +1.59] |
| 0 | price + flow + tick flow | forest | 23328 | 53.03% | 0.546 | 0.6898 | +0.55 [-0.03, +1.15] | +0.83 [+0.16, +1.53] |
| 0 | price + flow + tick flow | xgb | 23328 | 53.01% | 0.542 | 0.6912 | +0.53 [-0.09, +1.11] | +0.81 [+0.13, +1.51] |
| 0 | everything | forest | 23328 | 53.15% | 0.546 | 0.6899 | +0.66 [+0.06, +1.29] | +0.94 [+0.24, +1.66] |
| 0 | everything | xgb | 23328 | 53.02% | 0.546 | 0.6906 | +0.53 [-0.09, +1.13] | +0.81 [+0.15, +1.48] |
| 0 | one-feature baseline (prev-window) |  | 23328 | 52.21% | 0.519 | 0.6922 |  | baseline |
| 3 | price | forest | 23328 | 65.96% | 0.719 | 0.6165 | +0.00 [+0.00, +0.00] | -0.39 [-0.72, -0.07] |
| 3 | price | xgb | 23328 | 66.14% | 0.718 | 0.6171 | +0.18 [-0.09, +0.46] | -0.21 [-0.53, +0.12] |
| 3 | price + flow | forest | 23328 | 66.13% | 0.719 | 0.6162 | +0.17 [-0.05, +0.41] | -0.22 [-0.54, +0.11] |
| 3 | price + flow | xgb | 23328 | 66.28% | 0.719 | 0.6169 | +0.32 [+0.04, +0.61] | -0.07 [-0.42, +0.27] |
| 3 | price + flow + indicators | forest | 23328 | 66.13% | 0.720 | 0.6158 | +0.18 [-0.06, +0.41] | -0.21 [-0.56, +0.10] |
| 3 | price + flow + indicators | xgb | 23328 | 66.32% | 0.720 | 0.6161 | +0.36 [+0.07, +0.65] | -0.03 [-0.38, +0.28] |
| 3 | price + flow + tick flow | forest | 23328 | 66.19% | 0.719 | 0.6161 | +0.24 [-0.02, +0.49] | -0.15 [-0.48, +0.16] |
| 3 | price + flow + tick flow | xgb | 23328 | 66.34% | 0.718 | 0.6171 | +0.38 [+0.11, +0.65] | -0.01 [-0.36, +0.34] |
| 3 | everything | forest | 23328 | 66.33% | 0.720 | 0.6156 | +0.37 [+0.13, +0.63] | -0.02 [-0.36, +0.29] |
| 3 | everything | xgb | 23328 | 66.27% | 0.720 | 0.6163 | +0.32 [+0.02, +0.61] | -0.07 [-0.43, +0.27] |
| 3 | one-feature baseline (lead-z) |  | 23328 | 66.35% | 0.721 | 0.6150 |  | baseline |
