Feature importance on each held-out month. Permutation importance is the accuracy drop (points) when the feature is shuffled; SHAP is the mean absolute contribution from the booster. Top five of each.

| minute | month | permutation importance (points) | mean |SHAP| |
|---|---|---|---|
| 0 | 2026-01 | rsi60 +1.11, flow15 +0.94, macd_hist +0.87, flow1 +0.71, flow5 +0.57 | flow15 0.080, vratio15 0.056, atr14 0.049, obv_slope60 0.041, bb_pctb 0.038 |
| 0 | 2026-02 | macd_hist +0.89, rsi14 +0.63, win2 +0.56, win1 +0.48, rsi60 +0.48 | flow15 0.072, rsi60 0.052, obv_slope60 0.044, vratio15 0.037, rangepos 0.036 |
| 0 | 2026-03 | rsi60 +1.08, obv_slope60 +0.91, flow1 +0.67, vol240 +0.44, hour +0.44 | flow15 0.053, rsi60 0.052, obv_slope60 0.048, bb_pctb 0.048, vratio15 0.034 |
| 0 | 2026-04 | rsi60 +1.39, ret5 +1.01, rangepos +1.01, bb_pctb +0.83, rsi14 +0.76 | rsi60 0.063, flow15 0.042, rangepos 0.041, obv_slope60 0.041, bb_pctb 0.028 |
| 0 | 2026-05 | flow1 +0.57, vratio15 +0.44, rsi60 +0.34, flow3 +0.17, lead +0.00 | rsi60 0.063, rangepos 0.053, flow15 0.052, obv_slope60 0.046, bb_pctb 0.033 |
| 0 | 2026-06 | rangepos +1.01, ret240 +0.69, atr14 +0.63, ret5 +0.45, ret15 +0.45 | rangepos 0.065, rsi60 0.056, flow15 0.041, obv_slope60 0.038, ret5 0.037 |
| 0 | 2026-07 | obv_slope60 +1.48, atr14 +1.24, rsi60 +0.94, nratio5 +0.87, adx14 +0.81 | rangepos 0.055, rsi60 0.048, obv_slope60 0.044, bb_pctb 0.040, flow15 0.039 |
| 0 | 2026-08 | win3 +0.67, win4 +0.34, obv_slope60 +0.27, vratio5 +0.24, size5 +0.24 | rangepos 0.057, rsi60 0.054, obv_slope60 0.052, bb_pctb 0.041, flow15 0.037 |
| 3 | 2026-01 | lead +14.05, vol240 +0.60, vol15 +0.47, ret5 +0.44, flow1 +0.44 | lead 0.571, win1 0.085, flow15 0.068, stoch14 0.065, rangepos 0.054 |
| 3 | 2026-02 | lead +12.61, vol15 +0.63, win1 +0.60, flow3 +0.30, flow60 +0.30 | lead 0.736, win1 0.102, stoch14 0.062, flow15 0.053, obv_slope60 0.049 |
| 3 | 2026-03 | lead +11.32, win1 +0.40, ret5 +0.34, vratio15 +0.30, adx14 +0.30 | lead 0.632, win1 0.099, flow3 0.071, stoch14 0.056, obv_slope60 0.048 |
| 3 | 2026-04 | lead +14.44, win1 +0.56, stoch14 +0.45, obv_slope60 +0.35, vratio5 +0.21 | lead 0.556, win1 0.071, ret5 0.056, flow3 0.051, stoch14 0.050 |
| 3 | 2026-05 | lead +14.52, win1 +0.24, ret5 +0.07, vol15 +0.07, wday +0.03 | lead 0.530, win1 0.068, stoch14 0.058, flow3 0.053, ret5 0.052 |
| 3 | 2026-06 | lead +15.83, flow15 +0.49, ret5 +0.45, ret240 +0.35, rsi60 +0.31 | lead 0.663, win1 0.069, ret5 0.060, rangepos 0.053, flow3 0.052 |
| 3 | 2026-07 | lead +13.41, win1 +0.27, bb_pctb +0.20, rangepos +0.10, win2 +0.07 | lead 0.530, win1 0.067, flow3 0.056, ret5 0.054, stoch14 0.046 |
| 3 | 2026-08 | lead +12.24, win1 +0.67, rangepos +0.57, flow3 +0.44, vol60 +0.27 | lead 0.510, win1 0.066, flow3 0.065, ret5 0.049, stoch14 0.046 |
