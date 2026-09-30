Day-block bootstrap (95%) and within-day permutation test. "vs" is accuracy minus the baseline named, on the same windows.

| minute | model | accuracy [95% CI] | vs baseline | permutation p |
|---|---|---|---|---|
| 0 | majority | 50.14 [49.60, 50.65] | baseline |  |
| 0 | logistic-all | 52.79 [52.18, 53.45] | +2.65 [+1.85, +3.50] vs majority |  |
| 0 | forest | 52.98 [52.36, 53.64] | +2.84 [+2.02, +3.72] vs majority |  |
| 0 | hgb-all | 52.94 [52.34, 53.59] | +2.80 [+1.98, +3.64] vs majority | 0.002 |
| 0 | xgb-price | 52.28 [51.66, 52.91] | +2.14 [+1.24, +3.04] vs majority | 0.002 |
| 0 | xgb-all | 52.54 [51.96, 53.19] | +2.40 [+1.55, +3.27] vs majority | 0.002 |
| 1 | majority | 50.14 [49.60, 50.65] | -8.77 [-9.57, -8.01] vs lead-only |  |
| 1 | lead-only | 58.91 [58.29, 59.56] | baseline | 0.002 |
| 1 | logistic-all | 59.19 [58.62, 59.79] | +0.28 [-0.18, +0.75] vs lead-only |  |
| 1 | forest | 59.09 [58.45, 59.72] | +0.18 [-0.24, +0.62] vs lead-only |  |
| 1 | hgb-all | 59.39 [58.74, 60.04] | +0.48 [+0.04, +0.89] vs lead-only | 0.002 |
| 1 | xgb-price | 59.15 [58.47, 59.82] | +0.24 [-0.21, +0.72] vs lead-only | 0.002 |
| 1 | xgb-all | 59.09 [58.43, 59.77] | +0.18 [-0.29, +0.66] vs lead-only | 0.002 |
| 3 | majority | 50.14 [49.60, 50.65] | -16.18 [-17.06, -15.37] vs lead-only |  |
| 3 | lead-only | 66.32 [65.71, 66.93] | baseline | 0.002 |
| 3 | logistic-all | 65.69 [65.09, 66.30] | -0.63 [-1.04, -0.23] vs lead-only |  |
| 3 | forest | 66.20 [65.58, 66.84] | -0.12 [-0.44, +0.20] vs lead-only |  |
| 3 | hgb-all | 66.36 [65.73, 66.99] | +0.04 [-0.27, +0.35] vs lead-only | 0.002 |
| 3 | xgb-price | 66.22 [65.62, 66.83] | -0.10 [-0.46, +0.23] vs lead-only | 0.002 |
| 3 | xgb-all | 66.17 [65.56, 66.82] | -0.15 [-0.50, +0.19] vs lead-only | 0.002 |
| 5 | majority | 50.14 [49.60, 50.65] | -19.87 [-20.66, -19.08] vs lead-only |  |
| 5 | lead-only | 70.00 [69.41, 70.58] | baseline | 0.002 |
| 5 | logistic-all | 69.14 [68.57, 69.71] | -0.87 [-1.29, -0.46] vs lead-only |  |
| 5 | forest | 70.15 [69.56, 70.72] | +0.14 [-0.19, +0.48] vs lead-only |  |
| 5 | hgb-all | 69.88 [69.30, 70.43] | -0.13 [-0.42, +0.16] vs lead-only | 0.002 |
| 5 | xgb-price | 69.90 [69.33, 70.46] | -0.11 [-0.43, +0.20] vs lead-only | 0.002 |
| 5 | xgb-all | 69.96 [69.39, 70.51] | -0.04 [-0.38, +0.29] vs lead-only | 0.002 |
| 8 | majority | 50.14 [49.60, 50.65] | -27.26 [-28.01, -26.55] vs lead-only |  |
| 8 | lead-only | 77.40 [76.89, 77.91] | baseline | 0.002 |
| 8 | logistic-all | 76.85 [76.35, 77.35] | -0.55 [-0.88, -0.24] vs lead-only |  |
| 8 | forest | 77.48 [76.95, 77.99] | +0.08 [-0.10, +0.27] vs lead-only |  |
| 8 | hgb-all | 77.41 [76.87, 77.94] | +0.01 [-0.19, +0.21] vs lead-only | 0.002 |
| 8 | xgb-price | 77.32 [76.79, 77.85] | -0.08 [-0.32, +0.17] vs lead-only | 0.002 |
| 8 | xgb-all | 77.36 [76.81, 77.88] | -0.04 [-0.27, +0.19] vs lead-only | 0.002 |
