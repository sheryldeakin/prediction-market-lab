The named events against a compact continuous model, horizon 5 minutes, 2018 to 2026-08, walk-forward by year on every minute. 'compact' is a spline logistic regression on nine continuous quantities (returns over 5 to 240 minutes in volatility units, 4-hour range position, log trailing-hour volatility, the last candle's wick shares and body sign); 'cells' is the published cells model (186 events plus the volatility tercile); 'compact + cells' has both; 'strongest cell' lets the strongest firing cell decide. Day-block 95% intervals; 'vs compact' is the paired accuracy difference with the share of days the row wins.

| test year | model | minutes | accuracy [95% CI] | log loss | vs compact |
|---|---|---|---|---|---|
| 2020 | compact | 513,792 | 53.27% [53.06, 53.48] | 0.6900 | reference |
| 2020 | cells | 513,792 | 52.80% [52.59, 53.00] | 0.6900 | -0.47 [-0.68, -0.27], days better 41% |
| 2020 | compact + cells | 513,792 | 53.18% [52.98, 53.38] | 0.6895 | -0.09 [-0.26, +0.07], days better 50% |
| 2020 | strongest cell | 513,792 | 53.01% [52.80, 53.23] |  | -0.26 [-0.44, -0.09], days better 45% |
| 2020 | previous-h reversal rule | 513,792 | 52.87% [52.62, 53.13] |  | -0.40 [-0.59, -0.20], days better 42% |
| 2021 | compact | 515,609 | 52.46% [52.25, 52.66] | 0.6912 | reference |
| 2021 | cells | 515,609 | 52.60% [52.39, 52.79] | 0.6909 | +0.15 [-0.04, +0.33], days better 52% |
| 2021 | compact + cells | 515,609 | 52.87% [52.67, 53.06] | 0.6907 | +0.41 [+0.24, +0.57], days better 60% |
| 2021 | strongest cell | 515,609 | 52.83% [52.61, 53.03] |  | +0.37 [+0.20, +0.53], days better 60% |
| 2021 | previous-h reversal rule | 515,609 | 51.62% [51.41, 51.84] |  | -0.83 [-1.03, -0.64], days better 35% |
| 2022 | compact | 525,596 | 52.52% [52.29, 52.76] | 0.6912 | reference |
| 2022 | cells | 525,596 | 52.27% [52.05, 52.48] | 0.6914 | -0.25 [-0.47, -0.05], days better 45% |
| 2022 | compact + cells | 525,596 | 52.27% [52.07, 52.48] | 0.6915 | -0.24 [-0.42, -0.08], days better 43% |
| 2022 | strongest cell | 525,596 | 52.56% [52.32, 52.81] |  | +0.04 [-0.15, +0.23], days better 53% |
| 2022 | previous-h reversal rule | 525,596 | 51.84% [51.62, 52.08] |  | -0.68 [-0.89, -0.47], days better 36% |
| 2023 | compact | 524,017 | 51.96% [51.73, 52.19] | 0.6916 | reference |
| 2023 | cells | 524,017 | 52.20% [51.98, 52.43] | 0.6915 | +0.24 [+0.05, +0.43], days better 57% |
| 2023 | compact + cells | 524,017 | 52.39% [52.16, 52.60] | 0.6914 | +0.42 [+0.27, +0.57], days better 61% |
| 2023 | strongest cell | 524,017 | 52.00% [51.76, 52.22] |  | +0.04 [-0.13, +0.21], days better 50% |
| 2023 | previous-h reversal rule | 524,017 | 51.17% [50.89, 51.43] |  | -0.80 [-1.00, -0.58], days better 32% |
| 2024 | compact | 527,036 | 51.52% [51.29, 51.75] | 0.6927 | reference |
| 2024 | cells | 527,036 | 51.63% [51.41, 51.85] | 0.6927 | +0.11 [-0.07, +0.31], days better 55% |
| 2024 | compact + cells | 527,036 | 51.67% [51.46, 51.89] | 0.6927 | +0.15 [-0.02, +0.32], days better 54% |
| 2024 | strongest cell | 527,036 | 51.43% [51.20, 51.66] |  | -0.09 [-0.25, +0.06], days better 49% |
| 2024 | previous-h reversal rule | 527,036 | 50.53% [50.32, 50.75] |  | -0.99 [-1.19, -0.79], days better 33% |
| 2025 | compact | 525,596 | 51.12% [50.89, 51.37] | 0.6934 | reference |
| 2025 | cells | 525,596 | 51.36% [51.14, 51.57] | 0.6932 | +0.23 [+0.04, +0.43], days better 55% |
| 2025 | compact + cells | 525,596 | 51.51% [51.30, 51.72] | 0.6930 | +0.39 [+0.19, +0.59], days better 58% |
| 2025 | strongest cell | 525,596 | 51.05% [50.81, 51.31] |  | -0.08 [-0.22, +0.07], days better 50% |
| 2025 | previous-h reversal rule | 525,596 | 50.46% [50.22, 50.69] |  | -0.66 [-0.89, -0.44], days better 37% |
| 2026 | compact | 349,916 | 52.20% [51.95, 52.45] | 0.6917 | reference |
| 2026 | cells | 349,916 | 51.91% [51.66, 52.16] | 0.6922 | -0.29 [-0.50, -0.08], days better 42% |
| 2026 | compact + cells | 349,916 | 51.91% [51.67, 52.16] | 0.6921 | -0.28 [-0.46, -0.09], days better 43% |
| 2026 | strongest cell | 349,916 | 52.17% [51.91, 52.45] |  | -0.02 [-0.19, +0.14], days better 50% |
| 2026 | previous-h reversal rule | 349,916 | 51.43% [51.15, 51.70] |  | -0.77 [-1.03, -0.50], days better 35% |
