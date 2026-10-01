Perpetual-futures inputs (basis, its change, perp taker flow, perp volume ratio, funding rate, open-interest change over 15 and 60 minutes, top-trader and all-account long/short ratios, taker buy/sell ratio) added to price + flow + indicators. Walk-forward by month; last column is accuracy with minus without, on the same windows, day-block 95% interval.

| minute | model | features | n | accuracy [95% CI] | AUC | log loss | with minus without |
|---|---|---|---|---|---|---|---|
| 0 | forest | without derivatives | 23328 | 53.48% [52.88, 54.10] | 0.547 | 0.6899 | -0.41 [-0.94, +0.11] |
| 0 | forest | with derivatives | 23328 | 53.07% [52.49, 53.67] | 0.545 | 0.6897 | -0.41 [-0.94, +0.11] |
| 0 | xgb | without derivatives | 23328 | 53.11% [52.55, 53.70] | 0.544 | 0.6909 | -0.32 [-0.88, +0.25] |
| 0 | xgb | with derivatives | 23328 | 52.79% [52.13, 53.46] | 0.541 | 0.6911 | -0.32 [-0.88, +0.25] |
| 3 | forest | without derivatives | 23328 | 66.13% [65.53, 66.77] | 0.720 | 0.6158 | +0.06 [-0.16, +0.28] |
| 3 | forest | with derivatives | 23328 | 66.19% [65.56, 66.81] | 0.720 | 0.6155 | +0.06 [-0.16, +0.28] |
| 3 | xgb | without derivatives | 23328 | 66.32% [65.70, 66.93] | 0.720 | 0.6161 | -0.12 [-0.31, +0.10] |
| 3 | xgb | with derivatives | 23328 | 66.20% [65.60, 66.82] | 0.719 | 0.6165 | -0.12 [-0.31, +0.10] |

Forward check: models trained on 2025-10 to 2026-08, scored on 2026-09-01 to 2026-09-30. Left out of the forward models because they are not known for the whole period: funding_bp, doi15, doi60, ls_top, ls_all, taker_ls.

| minute | model | features | n | accuracy [95% CI] |
|---|---|---|---|---|
| 0 | forest | without derivatives | 2880 | 50.56% [48.96, 52.26] |
| 0 | forest | with derivatives | 2880 | 52.01% [50.59, 53.58] |
| 0 | xgb | without derivatives | 2880 | 51.67% [50.21, 53.40] |
| 0 | xgb | with derivatives | 2880 | 52.71% [51.11, 54.27] |
| 3 | forest | without derivatives | 2880 | 67.57% [66.15, 68.96] |
| 3 | forest | with derivatives | 2880 | 67.29% [65.90, 68.68] |
| 3 | xgb | without derivatives | 2880 | 66.88% [65.21, 68.51] |
| 3 | xgb | with derivatives | 2880 | 66.91% [65.38, 68.47] |

Spike events split by what open interest did over the same 15 minutes (minute 0). Falling open interest during a move means positions were closed or liquidated; rising means positions were opened.

| event | open interest | fires | up-rate [95% CI] | vs base |
|---|---|---|---|---|
| 5-min move > +2 sd | open interest fell (doi15 < -0.1%) | 195 | 38.5% [31.7, 45.7] | -11.3 |
| 5-min move > +2 sd | open interest flat | 335 | 44.8% [39.2, 50.6] | -5.0 |
| 5-min move > +2 sd | open interest rose (doi15 > +0.1%) | 158 | 40.5% [32.9, 48.1] | -9.2 |
| 5-min move < -2 sd | open interest fell (doi15 < -0.1%) | 224 | 58.0% [52.0, 64.2] | +8.3 |
| 5-min move < -2 sd | open interest flat | 339 | 54.3% [48.7, 59.8] | +4.5 |
| 5-min move < -2 sd | open interest rose (doi15 > +0.1%) | 125 | 48.0% [39.5, 56.7] | -1.7 |
| 15-min move > +2 sd | open interest fell (doi15 < -0.1%) | 232 | 38.4% [31.8, 44.9] | -11.4 |
| 15-min move > +2 sd | open interest flat | 311 | 41.8% [36.1, 47.5] | -7.9 |
| 15-min move > +2 sd | open interest rose (doi15 > +0.1%) | 175 | 42.9% [35.6, 49.7] | -6.9 |
| 15-min move < -2 sd | open interest fell (doi15 < -0.1%) | 344 | 60.5% [55.0, 65.7] | +10.7 |
| 15-min move < -2 sd | open interest flat | 307 | 56.0% [50.2, 61.8] | +6.3 |
| 15-min move < -2 sd | open interest rose (doi15 > +0.1%) | 161 | 58.4% [50.9, 65.9] | +8.7 |
| price at 4h high | open interest fell (doi15 < -0.1%) | 99 | 33.3% [24.5, 42.4] | -16.4 |
| price at 4h high | open interest flat | 294 | 39.5% [34.1, 45.3] | -10.3 |
| price at 4h high | open interest rose (doi15 > +0.1%) | 146 | 39.7% [31.9, 47.6] | -10.0 |
| price at 4h low | open interest fell (doi15 < -0.1%) | 129 | 57.4% [48.3, 66.4] | +7.6 |
| price at 4h low | open interest flat | 264 | 56.8% [50.5, 63.3] | +7.1 |
| price at 4h low | open interest rose (doi15 > +0.1%) | 128 | 51.6% [43.0, 59.7] | +1.8 |

Permutation importance of each derivative feature on the held-out months (accuracy drop in points when shuffled; mean over months and range).

| minute | feature | mean | range |
|---|---|---|---|
| 0 | basis_bp | +0.11 | -0.45 to +1.14 |
| 0 | dbasis5 | -0.12 | -1.35 to +1.01 |
| 0 | dbasis15 | +0.07 | -0.47 to +0.74 |
| 0 | pflow5 | +0.20 | -0.30 to +0.71 |
| 0 | pflow15 | +0.21 | -0.30 to +0.64 |
| 0 | pvol_ratio5 | -0.02 | -0.47 to +0.67 |
| 0 | funding_bp | -0.07 | -0.47 to +0.28 |
| 0 | doi15 | +0.09 | -0.44 to +0.84 |
| 0 | doi60 | +0.11 | -0.30 to +0.60 |
| 0 | ls_top | +0.23 | -0.07 to +0.64 |
| 0 | ls_all | +0.00 | -0.62 to +0.30 |
| 0 | taker_ls | -0.05 | -0.34 to +0.17 |
| 3 | basis_bp | +0.01 | -0.14 to +0.37 |
| 3 | dbasis5 | +0.00 | -0.34 to +0.19 |
| 3 | dbasis15 | +0.13 | -0.07 to +0.34 |
| 3 | pflow5 | +0.10 | -0.20 to +0.60 |
| 3 | pflow15 | -0.05 | -0.34 to +0.17 |
| 3 | pvol_ratio5 | +0.01 | -0.24 to +0.27 |
| 3 | funding_bp | +0.02 | -0.11 to +0.17 |
| 3 | doi15 | -0.00 | -0.63 to +0.38 |
| 3 | doi60 | -0.05 | -0.45 to +0.20 |
| 3 | ls_top | +0.00 | -0.10 to +0.07 |
| 3 | ls_all | -0.07 | -0.44 to +0.19 |
| 3 | taker_ls | -0.02 | -0.47 to +0.27 |
