Calibration of the confident calls by entry minute, 2026-01-01 to 2026-08-31, 23,328 windows. For each minute and threshold: the share of windows whose called-side probability (the larger of p and 1 - p; exactly 0.5 is not a call) is at or above the threshold, and the hit rate of those calls against the window's final direction, for xgb-all and for the one-feature rule at that minute (prev-window at minute 0, lead-z after). A dash means no window reached the threshold. Descriptive: no test.

| minute | xgb-all, share at 0.65 or more | xgb-all, hit rate at 0.65 or more | rule, share at 0.65 or more | rule, hit rate at 0.65 or more | xgb-all, share at 0.75 or more | xgb-all, hit rate at 0.75 or more | rule, share at 0.75 or more | rule, hit rate at 0.75 or more |
|---|---|---|---|---|---|---|---|---|
| 0 | 1.3% | 64.0% (314) | 0.0% | - | 0.0% | 0.0% (1) | 0.0% | - |
| 1 | 23.0% | 68.7% (5,376) | 17.7% | 71.5% (4,140) | 3.0% | 76.4% (709) | 4.0% | 77.3% (931) |
| 2 | 39.9% | 71.5% (9,306) | 34.5% | 73.4% (8,041) | 11.1% | 79.3% (2,581) | 11.9% | 79.7% (2,777) |
| 3 | 52.2% | 74.2% (12,174) | 45.3% | 75.9% (10,579) | 22.7% | 79.7% (5,289) | 20.2% | 81.6% (4,709) |
| 4 | 58.7% | 76.0% (13,699) | 52.9% | 77.5% (12,347) | 31.3% | 81.8% (7,306) | 27.4% | 83.1% (6,391) |
| 5 | 62.3% | 78.0% (14,531) | 57.4% | 79.5% (13,383) | 37.7% | 83.9% (8,788) | 33.8% | 85.1% (7,883) |
| 6 | 70.0% | 79.3% (16,324) | 64.3% | 80.9% (14,990) | 45.5% | 85.0% (10,611) | 41.5% | 86.4% (9,680) |
| 7 | 75.0% | 81.2% (17,491) | 69.5% | 82.7% (16,213) | 52.7% | 86.4% (12,299) | 48.6% | 87.5% (11,335) |
| 8 | 77.9% | 83.3% (18,170) | 74.7% | 84.3% (17,433) | 59.5% | 87.7% (13,890) | 56.0% | 88.7% (13,068) |
| 9 | 81.2% | 84.9% (18,952) | 78.2% | 85.8% (18,249) | 66.0% | 88.5% (15,399) | 61.5% | 90.0% (14,345) |
| 10 | 85.2% | 86.3% (19,865) | 81.4% | 87.6% (18,998) | 71.7% | 89.7% (16,732) | 66.8% | 90.9% (15,591) |
| 11 | 87.0% | 88.1% (20,307) | 84.2% | 89.2% (19,635) | 75.7% | 91.1% (17,651) | 72.3% | 92.1% (16,870) |
| 12 | 88.8% | 89.9% (20,709) | 86.9% | 90.6% (20,280) | 80.7% | 92.1% (18,817) | 76.7% | 93.3% (17,893) |
| 13 | 92.2% | 91.8% (21,505) | 89.2% | 92.8% (20,804) | 84.6% | 93.9% (19,742) | 80.9% | 94.8% (18,863) |
| 14 | 96.1% | 93.7% (22,410) | 92.2% | 94.9% (21,498) | 91.2% | 95.0% (21,285) | 85.8% | 96.4% (20,012) |

At minute 2: at 0.65, xgb-all has 39.9% of windows at or above it and those calls are right 71.5% of the time (9,306 calls), the rule 34.5% and 73.4% (8,041 calls); at 0.75, xgb-all has 11.1% of windows at or above it and those calls are right 79.3% of the time (2,581 calls), the rule 11.9% and 79.7% (2,777 calls).

At minute 7: at 0.65, xgb-all has 75.0% of windows at or above it and those calls are right 81.2% of the time (17,491 calls), the rule 69.5% and 82.7% (16,213 calls); at 0.75, xgb-all has 52.7% of windows at or above it and those calls are right 86.4% of the time (12,299 calls), the rule 48.6% and 87.5% (11,335 calls).
