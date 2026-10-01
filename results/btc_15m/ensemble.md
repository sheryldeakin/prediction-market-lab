Ensembles: the mean of four base models' out-of-fold probabilities, and a logistic stacker fit on earlier months' out-of-fold probabilities only. Scored on the months where every variant exists (the stacker needs one month of base predictions to start). The last two columns are accuracy minus the best single base model and minus the one-feature baseline (the previous window at the open, the lead z-score after), on the same windows, day-block 95% intervals.

| minute | model | n | accuracy [95% CI] | AUC | log loss | vs best single | vs one-feature baseline |
|---|---|---|---|---|---|---|---|
| 0 | logistic-all | 20352 | 52.97% [52.30, 53.67] | 0.544 | 0.6905 | -0.41 [-1.02, +0.18] vs forest | +0.92 [+0.25, +1.58] |
| 0 | forest | 20352 | 53.38% [52.76, 54.02] | 0.544 | 0.6905 | best single | +1.33 [+0.62, +2.01] |
| 0 | hgb-all | 20352 | 52.90% [52.23, 53.55] | 0.540 | 0.6904 | -0.48 [-1.06, +0.08] vs forest | +0.85 [+0.28, +1.39] |
| 0 | xgb-all | 20352 | 52.72% [52.04, 53.47] | 0.541 | 0.6913 | -0.66 [-1.18, -0.12] vs forest | +0.67 [-0.13, +1.47] |
| 0 | average | 20352 | 53.24% [52.56, 53.92] | 0.545 | 0.6899 | -0.14 [-0.57, +0.24] vs forest | +1.19 [+0.53, +1.87] |
| 0 | stacking | 20352 | 53.23% [52.62, 53.85] | 0.544 | 0.6901 | -0.15 [-0.50, +0.20] vs forest | +1.18 [+0.49, +1.86] |
| 0 | prev-window | 20352 | 52.05% [51.45, 52.68] | 0.518 | 0.6924 | -1.33 [-2.01, -0.62] vs forest | baseline |
| 3 | logistic-all | 20352 | 65.78% [65.15, 66.43] | 0.715 | 0.6208 | -0.70 [-1.08, -0.27] vs xgb-all | -0.67 [-1.13, -0.19] |
| 3 | forest | 20352 | 66.19% [65.53, 66.88] | 0.720 | 0.6157 | -0.29 [-0.57, -0.01] vs xgb-all | -0.27 [-0.64, +0.10] |
| 3 | hgb-all | 20352 | 66.26% [65.62, 66.90] | 0.720 | 0.6157 | -0.22 [-0.47, +0.01] vs xgb-all | -0.19 [-0.51, +0.14] |
| 3 | xgb-all | 20352 | 66.48% [65.86, 67.14] | 0.720 | 0.6157 | best single | +0.03 [-0.32, +0.39] |
| 3 | average | 20352 | 66.30% [65.67, 66.96] | 0.721 | 0.6144 | -0.18 [-0.40, +0.04] vs xgb-all | -0.15 [-0.49, +0.20] |
| 3 | stacking | 20352 | 66.18% [65.53, 66.86] | 0.721 | 0.6147 | -0.30 [-0.59, -0.00] vs xgb-all | -0.27 [-0.61, +0.06] |
| 3 | lead-z | 20352 | 66.45% [65.80, 67.10] | 0.721 | 0.6146 | -0.03 [-0.39, +0.32] vs xgb-all | baseline |
