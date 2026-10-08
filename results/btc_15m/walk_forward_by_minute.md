The one-feature rule of the minute against each fitted family, accuracy at every entry minute, walk-forward 2025-10 to 2026-08, test months after the first three, 23,328 windows at each minute. The rule is the previous window's direction at minute 0 and the lead z-score after. Accuracy is the share of windows called right; the families are fitted on all features (logistic-all, forest, hgb-all) or on price (xgb-price) or price and flow (xgb-all). The last column is the most accurate of the five families at that minute minus the rule on the same windows, in points, with a 95% interval from resampling whole days and the family's name. The best of five is chosen on these windows, so the difference is biased upward and the interval does not correct for the choice (study 23 does, for minutes 0 and 3).

| minute | one-feature rule (prev-window at 0, lead-z after) | logistic-all | forest | hgb-all | xgb-price | xgb-all | best fitted minus rule (points) [95% interval] |
|---|---|---|---|---|---|---|---|
| 0 | 52.21% | 52.89% | 52.65% | 52.73% | 52.38% | 52.37% | +0.69 [-0.01, +1.37] (logistic-all) |
| 1 | 58.86% | 59.21% | 59.22% | 59.34% | 59.08% | 59.24% | +0.48 [+0.06, +0.88] (hgb-all) |
| 2 | 63.24% | 62.52% | 63.15% | 63.06% | 63.25% | 62.88% | +0.01 [-0.37, +0.41] (xgb-price) |
| 3 | 66.35% | 65.66% | 66.13% | 66.35% | 66.14% | 66.28% | +0.00 [-0.29, +0.29] (hgb-all) |
| 4 | 68.27% | 67.73% | 68.12% | 68.20% | 68.28% | 68.22% | +0.01 [-0.30, +0.31] (xgb-price) |
| 5 | 69.98% | 69.09% | 69.98% | 69.85% | 69.91% | 69.96% | -0.00 [-0.33, +0.33] (forest) |
| 6 | 72.90% | 72.26% | 72.90% | 72.81% | 72.90% | 72.77% | +0.00 [-0.25, +0.24] (xgb-price) |
| 7 | 75.66% | 74.79% | 75.57% | 75.56% | 75.50% | 75.55% | -0.09 [-0.27, +0.10] (forest) |
| 8 | 77.46% | 76.87% | 77.51% | 77.38% | 77.45% | 77.33% | +0.05 [-0.12, +0.21] (forest) |
| 9 | 79.59% | 79.03% | 79.43% | 79.39% | 79.58% | 79.47% | -0.00 [-0.24, +0.24] (xgb-price) |
| 10 | 82.25% | 81.63% | 82.00% | 82.03% | 81.99% | 82.04% | -0.21 [-0.41, -0.02] (xgb-all) |
| 11 | 84.46% | 84.04% | 84.38% | 84.28% | 84.25% | 84.23% | -0.08 [-0.23, +0.06] (forest) |
| 12 | 86.35% | 86.17% | 86.34% | 86.33% | 86.28% | 86.25% | -0.01 [-0.14, +0.12] (forest) |
| 13 | 89.23% | 89.04% | 89.18% | 89.16% | 89.08% | 89.05% | -0.04 [-0.13, +0.05] (forest) |
| 14 | 92.30% | 91.94% | 92.31% | 92.24% | 92.25% | 92.23% | +0.00 [-0.05, +0.06] (forest) |

Across minutes 1 to 14 the largest best-fitted-minus-rule difference is +0.48 [+0.06, +0.88] points at minute 1 (hgb-all) and the smallest is -0.21 [-0.41, -0.02] points at minute 10 (xgb-all); at minute 0 it is +0.69 [-0.01, +1.37] points (logistic-all).

The interval lies entirely above zero at 1 of the 15 minutes (minute 1) and entirely below zero at 1 (minute 10). The intervals are not adjusted for the number of minutes.
