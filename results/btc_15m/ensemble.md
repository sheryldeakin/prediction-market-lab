Ensembles: the mean of four base models' out-of-fold probabilities, and a logistic stacker fit on earlier months' out-of-fold probabilities only. Scored on the months where every variant exists (the stacker needs one month of base predictions to start). Last column: accuracy minus the best single base model on the same windows, day-block 95% interval.

| minute | model | n | accuracy [95% CI] | AUC | log loss | vs best single |
|---|---|---|---|---|---|---|
| 0 | logistic-all | 20351 | 52.88% [52.18, 53.59] | 0.544 | 0.6905 | -0.37 [-1.02, +0.25] vs forest |
| 0 | forest | 20351 | 53.26% [52.62, 53.91] | 0.543 | 0.6906 | best single |
| 0 | hgb-all | 20351 | 52.91% [52.25, 53.57] | 0.540 | 0.6904 | -0.34 [-0.89, +0.18] vs forest |
| 0 | xgb-all | 20351 | 52.83% [52.22, 53.46] | 0.541 | 0.6914 | -0.43 [-0.93, +0.08] vs forest |
| 0 | average | 20351 | 53.26% [52.61, 53.93] | 0.545 | 0.6899 | +0.00 [-0.45, +0.45] vs forest |
| 0 | stacking | 20351 | 53.16% [52.53, 53.81] | 0.543 | 0.6902 | -0.09 [-0.51, +0.29] vs forest |
| 3 | logistic-all | 20351 | 65.74% [65.11, 66.38] | 0.715 | 0.6208 | -0.65 [-1.05, -0.23] vs xgb-all |
| 3 | forest | 20351 | 66.19% [65.54, 66.89] | 0.720 | 0.6155 | -0.20 [-0.46, +0.10] vs xgb-all |
| 3 | hgb-all | 20351 | 66.23% [65.61, 66.87] | 0.720 | 0.6157 | -0.16 [-0.41, +0.09] vs xgb-all |
| 3 | xgb-all | 20351 | 66.38% [65.74, 67.06] | 0.720 | 0.6158 | best single |
| 3 | average | 20351 | 66.32% [65.67, 67.00] | 0.722 | 0.6143 | -0.06 [-0.29, +0.17] vs xgb-all |
| 3 | stacking | 20351 | 66.14% [65.49, 66.82] | 0.721 | 0.6146 | -0.24 [-0.52, +0.06] vs xgb-all |
