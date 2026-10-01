One probability per minute from the cells, horizon 5 minutes, 2018 to 2026-08: a logistic regression on every event of both libraries (0/1) plus the trailing-hour volatility tercile, fit on all earlier years and scored on each later year. Baselines on the same minutes: call the opposite of the previous 5 minutes (one bit), and 'the strongest firing cell decides' (direction and ranking from the training years, abstaining when nothing fires). Day-block 95% intervals; 'vs the reversal rule' is the paired difference with the share of days the model wins.

| test year | model | minutes scored | share of minutes | accuracy [95% CI] | vs the reversal rule |
|---|---|---|---|---|---|
| 2020 | cells model | 513,792 | 100% | 52.96% [52.76, 53.17] | +0.09 [-0.17, +0.36], days better 53% |
| 2020 | previous-h reversal rule | 513,792 | 100% | 52.87% [52.62, 53.13] | baseline |
| 2020 | strongest firing cell decides | 513,792 | 100% | 53.00% [52.79, 53.22] | abstains when no cell fires |
| 2020 | cells model, confident only (p beyond 0.55) | 80,538 | 16% | 58.48% [57.90, 59.07] |  |
| 2021 | cells model | 515,609 | 100% | 52.70% [52.50, 52.89] | +1.08 [+0.81, +1.32], days better 67% |
| 2021 | previous-h reversal rule | 515,609 | 100% | 51.62% [51.41, 51.84] | baseline |
| 2021 | strongest firing cell decides | 515,609 | 100% | 52.81% [52.58, 53.01] | abstains when no cell fires |
| 2021 | cells model, confident only (p beyond 0.55) | 115,603 | 22% | 56.57% [56.16, 56.97] |  |
| 2022 | cells model | 525,596 | 100% | 52.25% [52.04, 52.46] | +0.41 [+0.12, +0.67], days better 56% |
| 2022 | previous-h reversal rule | 525,596 | 100% | 51.84% [51.62, 52.08] | baseline |
| 2022 | strongest firing cell decides | 525,596 | 100% | 52.56% [52.32, 52.81] | abstains when no cell fires |
| 2022 | cells model, confident only (p beyond 0.55) | 93,591 | 18% | 56.44% [55.93, 56.97] |  |
| 2023 | cells model | 524,017 | 100% | 52.14% [51.91, 52.35] | +0.97 [+0.71, +1.25], days better 63% |
| 2023 | previous-h reversal rule | 524,017 | 100% | 51.17% [50.89, 51.43] | baseline |
| 2023 | strongest firing cell decides | 524,017 | 100% | 52.00% [51.76, 52.22] | abstains when no cell fires |
| 2023 | cells model, confident only (p beyond 0.55) | 94,810 | 18% | 55.73% [55.12, 56.38] |  |
| 2024 | cells model | 527,036 | 100% | 51.62% [51.39, 51.83] | +1.08 [+0.83, +1.34], days better 68% |
| 2024 | previous-h reversal rule | 527,036 | 100% | 50.53% [50.32, 50.75] | baseline |
| 2024 | strongest firing cell decides | 527,036 | 100% | 51.45% [51.21, 51.68] | abstains when no cell fires |
| 2024 | cells model, confident only (p beyond 0.55) | 101,119 | 19% | 54.30% [53.77, 54.82] |  |
| 2025 | cells model | 525,596 | 100% | 51.34% [51.12, 51.57] | +0.88 [+0.60, +1.20], days better 61% |
| 2025 | previous-h reversal rule | 525,596 | 100% | 50.46% [50.22, 50.69] | baseline |
| 2025 | strongest firing cell decides | 525,596 | 100% | 51.04% [50.80, 51.30] | abstains when no cell fires |
| 2025 | cells model, confident only (p beyond 0.55) | 85,313 | 16% | 53.81% [53.25, 54.36] |  |
| 2026 | cells model | 349,916 | 100% | 51.95% [51.71, 52.20] | +0.52 [+0.19, +0.86], days better 60% |
| 2026 | previous-h reversal rule | 349,916 | 100% | 51.43% [51.15, 51.70] | baseline |
| 2026 | strongest firing cell decides | 349,916 | 100% | 52.17% [51.90, 52.44] | abstains when no cell fires |
| 2026 | cells model, confident only (p beyond 0.55) | 47,053 | 13% | 54.89% [54.22, 55.59] |  |

Calibration of the strong cells, forward: for every event whose training-years deviation was at least 3 points, the up-rate the training years promised against the up-rate the test year delivered (both as deviations from the respective base rates), pooled into bins of the promised size. 650 cell-years.

| promised deviation (points) | cell-years | mean promised | mean delivered | delivered as a share of promised | sign kept |
|---|---|---|---|---|---|
| [3, 4) | 77 | 3.6 | 3.4 | 93% | 99% |
| [4, 5) | 139 | 4.6 | 4.8 | 104% | 100% |
| [5, 6) | 167 | 5.5 | 4.8 | 89% | 100% |
| [6, 8) | 195 | 6.8 | 5.8 | 85% | 100% |
| [8, 12) | 59 | 8.9 | 6.9 | 77% | 100% |
