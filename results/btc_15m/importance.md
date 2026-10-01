Feature importance on each held-out month. Permutation importance is the accuracy drop (points) when the feature is shuffled; SHAP is the mean absolute contribution from the booster. Top five of each.

| minute | month | permutation importance (points) | mean |SHAP| |
|---|---|---|---|
| 0 | 2026-01 | flow15 +1.04, rangepos +0.84, vwap_dev60 +0.57, ret5 +0.50, rsi14 +0.50 | flow15 0.087, vratio15 0.052, atr14 0.048, obv_slope60 0.039, win4 0.036 |
| 0 | 2026-02 | rsi60 +0.74, flow1 +0.71, macd_hist +0.67, win2 +0.56, win1 +0.52 | flow15 0.070, rsi60 0.053, obv_slope60 0.043, vratio15 0.040, win4 0.037 |
| 0 | 2026-03 | rsi60 +1.21, win2 +0.60, flow15 +0.57, obv_slope60 +0.40, size5 +0.37 | flow15 0.059, rsi60 0.051, obv_slope60 0.044, bb_pctb 0.043, vratio15 0.034 |
| 0 | 2026-04 | ret5 +1.01, rangepos +0.90, atr14 +0.66, rsi60 +0.59, win3 +0.49 | rsi60 0.068, flow15 0.044, obv_slope60 0.042, rangepos 0.039, size5 0.028 |
| 0 | 2026-05 | obv_slope60 +0.97, size5 +0.44, flow1 +0.40, vratio5 +0.40, vratio15 +0.27 | rsi60 0.064, flow15 0.052, rangepos 0.050, obv_slope60 0.044, ret5 0.032 |
| 0 | 2026-06 | nratio5 +0.31, win4 +0.24, vwap_dev60 +0.17, lead +0.00, win1 -0.10 | rangepos 0.067, rsi60 0.060, flow15 0.041, obv_slope60 0.037, ret5 0.037 |
| 0 | 2026-07 | stoch14 +0.91, ret5 +0.77, rangepos +0.74, rsi60 +0.64, flow5 +0.60 | rangepos 0.055, rsi60 0.049, obv_slope60 0.044, flow15 0.042, bb_pctb 0.039 |
| 0 | 2026-08 | obv_slope60 +1.51, atr14 +1.34, rsi60 +1.31, rangepos +1.08, win4 +0.97 | rangepos 0.056, rsi60 0.054, obv_slope60 0.048, bb_pctb 0.038, flow15 0.034 |
| 3 | 2026-01 | lead +13.71, flow15 +0.67, vol240 +0.64, ret5 +0.44, flow3 +0.37 | lead 0.569, win1 0.086, stoch14 0.078, flow15 0.066, rangepos 0.055 |
| 3 | 2026-02 | lead +12.54, flow60 +0.82, vol15 +0.48, ema_cross +0.45, obv_slope60 +0.45 | lead 0.739, win1 0.108, stoch14 0.067, flow15 0.058, rangepos 0.044 |
| 3 | 2026-03 | lead +12.06, vol15 +0.50, win1 +0.44, ema_cross +0.44, rangepos +0.40 | lead 0.652, win1 0.091, flow3 0.067, stoch14 0.061, flow15 0.049 |
| 3 | 2026-04 | lead +14.27, stoch14 +0.49, adx14 +0.28, nratio5 +0.24, win1 +0.21 | lead 0.558, win1 0.074, stoch14 0.062, flow3 0.056, rangepos 0.039 |
| 3 | 2026-05 | lead +15.15, stoch14 +0.40, ret5 +0.34, win1 +0.27, rsi14 +0.24 | lead 0.533, win1 0.069, stoch14 0.068, flow3 0.057, rangepos 0.049 |
| 3 | 2026-06 | lead +15.83, flow15 +0.42, vol240 +0.31, vratio15 +0.24, size5 +0.24 | lead 0.663, win1 0.076, stoch14 0.060, flow3 0.057, rangepos 0.051 |
| 3 | 2026-07 | lead +13.91, size5 +0.44, stoch14 +0.44, flow60 +0.37, rangepos +0.34 | lead 0.541, win1 0.066, flow3 0.055, stoch14 0.054, rangepos 0.039 |
| 3 | 2026-08 | lead +16.30, stoch14 +0.84, ret5 +0.77, flow3 +0.64, rangepos +0.44 | lead 0.515, flow3 0.066, win1 0.063, stoch14 0.056, obv_slope60 0.041 |
