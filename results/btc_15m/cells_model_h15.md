One probability per minute from the cells, horizon 15 minutes, 2018 to 2026-08: a logistic regression on every event of both libraries (0/1) plus the trailing-hour volatility tercile, fit on all earlier years and scored on each later year. Baselines on the same minutes: call the opposite of the previous 15 minutes (one bit), and 'the strongest firing cell decides' (direction and ranking from the training years, abstaining when nothing fires). Day-block 95% intervals; 'vs the reversal rule' is the paired difference with the share of days the model wins.

| test year | model | minutes scored | share of minutes | accuracy [95% CI] | vs the reversal rule |
|---|---|---|---|---|---|
| 2020 | cells model | 513,782 | 100% | 54.23% [53.91, 54.56] | +1.04 [+0.77, +1.31], days better 65% |
| 2020 | previous-h reversal rule | 513,782 | 100% | 53.19% [52.92, 53.49] | baseline |
| 2020 | strongest firing cell decides | 513,782 | 100% | 54.13% [53.78, 54.47] | abstains when no cell fires |
| 2020 | cells model, confident only (p beyond 0.55) | 157,261 | 31% | 58.45% [57.90, 59.04] |  |
| 2021 | cells model | 515,599 | 100% | 52.99% [52.64, 53.30] | +0.29 [-0.01, +0.58], days better 53% |
| 2021 | previous-h reversal rule | 515,599 | 100% | 52.70% [52.40, 53.00] | baseline |
| 2021 | strongest firing cell decides | 515,599 | 100% | 53.17% [52.83, 53.50] | abstains when no cell fires |
| 2021 | cells model, confident only (p beyond 0.55) | 188,244 | 37% | 55.76% [55.18, 56.29] |  |
| 2022 | cells model | 525,586 | 100% | 52.55% [52.22, 52.91] | +0.17 [-0.11, +0.43], days better 53% |
| 2022 | previous-h reversal rule | 525,586 | 100% | 52.38% [52.05, 52.73] | baseline |
| 2022 | strongest firing cell decides | 525,586 | 100% | 53.01% [52.66, 53.39] | abstains when no cell fires |
| 2022 | cells model, confident only (p beyond 0.55) | 157,701 | 30% | 55.85% [55.16, 56.55] |  |
| 2023 | cells model | 524,007 | 100% | 53.07% [52.75, 53.39] | +0.73 [+0.46, +0.99], days better 62% |
| 2023 | previous-h reversal rule | 524,007 | 100% | 52.35% [52.03, 52.66] | baseline |
| 2023 | strongest firing cell decides | 524,007 | 100% | 53.05% [52.72, 53.38] | abstains when no cell fires |
| 2023 | cells model, confident only (p beyond 0.55) | 157,388 | 30% | 56.46% [55.85, 57.10] |  |
| 2024 | cells model | 527,026 | 100% | 52.34% [51.97, 52.68] | +0.47 [+0.19, +0.73], days better 58% |
| 2024 | previous-h reversal rule | 527,026 | 100% | 51.88% [51.53, 52.21] | baseline |
| 2024 | strongest firing cell decides | 527,026 | 100% | 52.14% [51.77, 52.48] | abstains when no cell fires |
| 2024 | cells model, confident only (p beyond 0.55) | 165,926 | 31% | 54.92% [54.26, 55.53] |  |
| 2025 | cells model | 525,586 | 100% | 51.66% [51.32, 52.01] | +0.30 [+0.02, +0.58], days better 50% |
| 2025 | previous-h reversal rule | 525,586 | 100% | 51.36% [51.02, 51.68] | baseline |
| 2025 | strongest firing cell decides | 525,586 | 100% | 51.52% [51.16, 51.89] | abstains when no cell fires |
| 2025 | cells model, confident only (p beyond 0.55) | 163,611 | 31% | 53.85% [53.15, 54.57] |  |
| 2026 | cells model | 349,906 | 100% | 52.58% [52.18, 52.98] | +0.59 [+0.28, +0.91], days better 62% |
| 2026 | previous-h reversal rule | 349,906 | 100% | 51.99% [51.60, 52.36] | baseline |
| 2026 | strongest firing cell decides | 349,906 | 100% | 52.68% [52.29, 53.08] | abstains when no cell fires |
| 2026 | cells model, confident only (p beyond 0.55) | 89,648 | 26% | 55.20% [54.41, 56.02] |  |

Calibration of the strong cells, forward: for every event whose training-years deviation was at least 3 points, the up-rate the training years promised against the up-rate the test year delivered (both as deviations from the respective base rates), pooled into bins of the promised size. 684 cell-years.

| promised deviation (points) | cell-years | mean promised | mean delivered | delivered as a share of promised | sign kept |
|---|---|---|---|---|---|
| [3, 4) | 78 | 3.6 | 3.9 | 109% | 95% |
| [4, 5) | 149 | 4.5 | 4.5 | 100% | 98% |
| [5, 6) | 143 | 5.4 | 5.1 | 94% | 99% |
| [6, 8) | 211 | 6.8 | 5.7 | 83% | 100% |
| [8, 12) | 85 | 9.1 | 7.6 | 84% | 100% |
