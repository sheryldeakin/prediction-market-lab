Second holdout: 2025-01 to 2025-09, months no study had loaded, scored on 2026-10-01 04:37 UTC at commit a19e3fb4e8. Frozen models dbba22d74696 trained on 2025-10 to 2026-08; baselines fitted on the same months; the indicator forest is fit once on the same months (see the process log for why it was added in a second run). Accuracy with day-block then month-block 95% intervals; the last column is minus the baseline on the same windows (day-block interval, share of days better, sign-flip p).

| minute | model | windows | accuracy [day CI] [month CI] | minus baseline |
|---|---|---|---|---|
| 0 | forest | 26107 | 51.64% [51.09, 52.18] [51.09, 52.22] | +0.08 [-0.58, +0.72], days better 50%, p 0.3948 |
| 0 | forest (price + flow + indicators) | 26107 | 51.96% [51.37, 52.52] [51.50, 52.40] | +0.40 [-0.22, +1.02], days better 54%, p 0.1129 |
| 0 | prev-window | 26107 | 51.56% [51.01, 52.12] [50.94, 52.16] | baseline |
| 3 | xgb-all | 26107 | 65.41% [64.88, 65.95] [64.88, 65.93] | -0.06 [-0.28, +0.16], days better 48%, p 0.7066 |
| 3 | lead-z | 26107 | 65.47% [64.91, 66.01] [64.92, 66.00] | baseline |

Stable event rules from the wide search: 745 of 745 fired at least 30 times in the holdout, and 737 of those kept the direction they had in the search.
