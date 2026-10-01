Hidden Markov models, round two (forest on price + flow + indicators, walk-forward by month, 2025-10 to 2026-08). '+minute states': the filtered probabilities of a 3-state HMM on the minute series added as features; '+daily regime': the previous day's filtered state from the regime study, one-hot; 'per-state forest': a forest fit per minute-scale state, mixed by the filtered probabilities. 'vs without' is accuracy minus the same model without the extra columns on the same windows, day-block 95% interval and share of days better; the last column is against the one-feature baseline.

| minute | model | n | accuracy [95% CI] | AUC | log loss | vs without | vs one-feature baseline |
|---|---|---|---|---|---|---|---|
| 0 | base | 23328 | 53.48% [52.88, 54.10] | 0.547 | 0.6899 | reference | +1.27 [+0.58, +1.95] vs prev-window |
| 0 | +minute states | 23328 | 53.57% [52.96, 54.21] | 0.547 | 0.6898 | +0.09 [-0.33, +0.50], days better 51% | +1.36 [+0.68, +2.05] vs prev-window |
| 0 | +daily regime | 23328 | 53.39% [52.80, 54.05] | 0.546 | 0.6900 | -0.09 [-0.47, +0.31], days better 47% | +1.18 [+0.49, +1.92] vs prev-window |
| 0 | +both | 23328 | 53.37% [52.77, 54.03] | 0.546 | 0.6900 | -0.11 [-0.51, +0.30], days better 51% | +1.16 [+0.48, +1.87] vs prev-window |
| 0 | per-state forest | 23328 | 52.78% [52.21, 53.39] | 0.544 | 0.6908 | -0.70 [-1.22, -0.18], days better 41% | +0.57 [-0.08, +1.25] vs prev-window |
| 3 | base | 23328 | 66.13% [65.53, 66.77] | 0.720 | 0.6158 | reference | -0.21 [-0.56, +0.10] vs lead-z |
| 3 | +minute states | 23328 | 66.16% [65.54, 66.80] | 0.720 | 0.6157 | +0.03 [-0.17, +0.23], days better 54% | -0.18 [-0.51, +0.12] vs lead-z |
| 3 | +daily regime | 23328 | 66.24% [65.62, 66.87] | 0.720 | 0.6155 | +0.11 [-0.06, +0.29], days better 53% | -0.10 [-0.43, +0.22] vs lead-z |
| 3 | +both | 23328 | 66.17% [65.55, 66.80] | 0.720 | 0.6158 | +0.04 [-0.14, +0.23], days better 54% | -0.18 [-0.51, +0.15] vs lead-z |
| 3 | per-state forest | 23328 | 66.29% [65.67, 66.92] | 0.719 | 0.6163 | +0.15 [-0.09, +0.42], days better 53% | -0.06 [-0.35, +0.24] vs lead-z |
