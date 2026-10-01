Where the minute-0 edge lives, 2025-10 to 2026-08, walk-forward by month. Each window's call at the open (forest on price + flow, and the prev-window baseline) signs every minute's return: positive means the minute moved the way the call said. Minute 1 runs from the open price to the first close. Mean signed return in basis points with a day-block 95% interval, and the share of windows in which that minute moved with the call.

| model | minute | signed return, bp [95% CI] | moved with the call |
|---|---|---|---|
| forest | 1 | +0.195 [+0.104, +0.281] | 50.7% |
| forest | 2 | +0.115 [+0.025, +0.212] | 49.8% |
| forest | 3 | +0.032 [-0.044, +0.122] | 49.6% |
| forest | 4 | +0.078 [-0.011, +0.171] | 49.5% |
| forest | 5 | +0.015 [-0.064, +0.094] | 48.8% |
| forest | 6 | +0.158 [+0.074, +0.249] | 49.8% |
| forest | 7 | +0.005 [-0.085, +0.092] | 48.9% |
| forest | 8 | -0.039 [-0.117, +0.042] | 48.7% |
| forest | 9 | +0.003 [-0.077, +0.079] | 48.5% |
| forest | 10 | +0.007 [-0.073, +0.086] | 48.9% |
| forest | 11 | +0.134 [+0.056, +0.211] | 50.1% |
| forest | 12 | -0.020 [-0.101, +0.063] | 48.5% |
| forest | 13 | -0.036 [-0.109, +0.036] | 47.7% |
| forest | 14 | -0.037 [-0.112, +0.042] | 47.4% |
| forest | 15 | -0.020 [-0.083, +0.043] | 48.0% |
| prev-window | 1 | +0.054 [-0.044, +0.148] | 50.1% |
| prev-window | 2 | +0.018 [-0.073, +0.111] | 49.4% |
| prev-window | 3 | -0.009 [-0.099, +0.082] | 49.4% |
| prev-window | 4 | +0.034 [-0.047, +0.115] | 49.4% |
| prev-window | 5 | -0.024 [-0.107, +0.056] | 48.2% |
| prev-window | 6 | +0.127 [+0.036, +0.221] | 49.6% |
| prev-window | 7 | +0.035 [-0.056, +0.116] | 49.1% |
| prev-window | 8 | +0.015 [-0.076, +0.105] | 48.7% |
| prev-window | 9 | +0.036 [-0.051, +0.126] | 48.6% |
| prev-window | 10 | -0.037 [-0.117, +0.040] | 48.4% |
| prev-window | 11 | +0.108 [+0.029, +0.188] | 49.7% |
| prev-window | 12 | +0.018 [-0.051, +0.087] | 48.5% |
| prev-window | 13 | +0.002 [-0.072, +0.074] | 48.4% |
| prev-window | 14 | -0.010 [-0.076, +0.057] | 47.9% |
| prev-window | 15 | -0.059 [-0.129, +0.011] | 47.9% |

By boundary type: the gap between the previous candle's close and this window's open. Accuracy at the open with day-block 95% intervals; the last column is forest minus prev-window on the same windows.

| boundary | windows | share | prev-window | forest | forest minus prev-window |
|---|---|---|---|---|---|
| flat (under 0.5 bp) | 23320 | 100.0% | 52.21% [51.64, 52.82] | 52.65% [52.01, 53.32] | +0.44 [-0.26, +1.17] |
| gap (0.5 bp or more) | 8 | 0.0% | 50.00% [14.29, 85.71] | 62.50% [28.57, 91.14] | +12.50 [+0.00, +42.86] |

By phase: windows starting this many minutes after the quarter hour (0 is the clock grid). Accuracy at the open, day-block 95% intervals, forest minus prev-window on the same windows, and the share of days the forest beats prev-window.

| phase (minutes) | windows | prev-window | forest | forest minus prev-window | days forest better |
|---|---|---|---|---|---|
| 0 | 23328 | 52.21% [51.63, 52.82] | 52.65% [52.01, 53.33] | +0.44 [-0.25, +1.18] | 54% |
| 1 | 23327 | 52.32% [51.70, 52.93] | 52.65% [52.07, 53.23] | +0.33 [-0.36, +1.10] | 49% |
| 2 | 23327 | 51.92% [51.27, 52.56] | 51.71% [51.14, 52.32] | -0.21 [-0.94, +0.51] | 47% |
| 3 | 23327 | 51.89% [51.24, 52.54] | 51.69% [51.07, 52.31] | -0.21 [-0.97, +0.54] | 51% |
| 4 | 23327 | 51.33% [50.64, 52.03] | 52.36% [51.69, 52.99] | +1.02 [+0.25, +1.78] | 56% |
| 5 | 23327 | 52.01% [51.37, 52.66] | 51.62% [51.06, 52.18] | -0.39 [-1.11, +0.31] | 44% |
| 6 | 23327 | 51.37% [50.77, 52.00] | 51.79% [51.16, 52.40] | +0.42 [-0.38, +1.20] | 54% |
| 7 | 23327 | 51.31% [50.68, 51.93] | 51.85% [51.19, 52.54] | +0.54 [-0.24, +1.39] | 55% |
| 8 | 23327 | 51.86% [51.25, 52.42] | 51.58% [50.96, 52.22] | -0.29 [-1.02, +0.48] | 50% |
| 9 | 23327 | 51.50% [50.87, 52.11] | 52.53% [51.88, 53.16] | +1.03 [+0.22, +1.83] | 60% |
| 10 | 23327 | 52.31% [51.70, 52.98] | 52.34% [51.73, 52.95] | +0.03 [-0.72, +0.80] | 48% |
| 11 | 23327 | 52.57% [51.97, 53.20] | 52.21% [51.59, 52.81] | -0.36 [-1.10, +0.38] | 45% |
| 12 | 23327 | 52.41% [51.79, 53.00] | 52.28% [51.60, 52.96] | -0.12 [-0.83, +0.60] | 48% |
| 13 | 23327 | 52.67% [52.12, 53.22] | 52.70% [52.07, 53.32] | +0.03 [-0.63, +0.69] | 49% |
| 14 | 23327 | 52.13% [51.52, 52.74] | 52.41% [51.79, 52.99] | +0.28 [-0.41, +0.99] | 52% |
