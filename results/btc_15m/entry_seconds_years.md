The one-bit rules by year, 2018 to 2026-08, quarter-hour windows whose own and previous candles are present and that have a trade in the first 60 seconds. Open: the opposite of the previous window. 10 s, 30 s, 60 s: up if the tick lead at that second is above the open, down if below, the open rule if exactly zero. Minute 1 and minute 3: the same rule on the candle lead (close of the last closed minute against the window open). Accuracy with day-block 95% intervals; the last column is the share of windows whose second 10 had no trade, so the last VWAP before it was used.

| year | windows | open | 10 s | 30 s | 60 s | minute 1 | minute 3 | no trade at second 10 |
|---|---|---|---|---|---|---|---|---|
| 2018 | 34648 | 53.07% [52.53, 53.62] | 53.27% [52.73, 53.78] | 55.80% [55.29, 56.31] | 58.49% [57.94, 59.02] | 58.74% [58.18, 59.29] | 65.74% [65.25, 66.21] | 28.14% |
| 2019 | 34908 | 53.36% [52.87, 53.81] | 52.34% [51.82, 52.83] | 55.39% [54.86, 55.91] | 57.88% [57.35, 58.39] | 58.04% [57.52, 58.55] | 65.66% [65.16, 66.17] | 17.64% |
| 2020 | 35043 | 53.50% [53.03, 53.97] | 51.97% [51.47, 52.48] | 54.30% [53.80, 54.80] | 56.96% [56.41, 57.49] | 57.03% [56.48, 57.57] | 64.19% [63.68, 64.71] | 6.17% |
| 2021 | 34962 | 52.26% [51.79, 52.76] | 52.85% [52.29, 53.36] | 55.44% [54.95, 55.93] | 58.10% [57.55, 58.64] | 58.17% [57.64, 58.69] | 65.41% [64.91, 65.91] | 0.53% |
| 2022 | 35040 | 52.17% [51.70, 52.67] | 52.35% [51.84, 52.83] | 54.71% [54.20, 55.27] | 57.14% [56.64, 57.72] | 57.19% [56.66, 57.77] | 63.23% [62.79, 63.72] | 1.65% |
| 2023 | 35029 | 52.84% [52.31, 53.35] | 52.30% [51.75, 52.80] | 54.66% [54.15, 55.20] | 57.09% [56.55, 57.66] | 57.20% [56.68, 57.76] | 64.10% [63.62, 64.65] | 5.00% |
| 2024 | 35136 | 52.30% [51.74, 52.80] | 52.70% [52.20, 53.21] | 55.21% [54.69, 55.73] | 57.33% [56.79, 57.86] | 57.54% [57.01, 58.09] | 64.44% [63.93, 64.95] | 3.19% |
| 2025 | 35040 | 51.73% [51.21, 52.21] | 53.84% [53.34, 54.36] | 56.18% [55.66, 56.72] | 58.44% [57.96, 58.94] | 58.57% [58.08, 59.08] | 65.77% [65.27, 66.26] | 4.95% |
| 2026 | 23328 | 52.21% [51.63, 52.82] | 54.15% [53.51, 54.81] | 56.12% [55.48, 56.74] | 58.85% [58.20, 59.54] | 58.94% [58.29, 59.60] | 66.29% [65.69, 66.91] | 8.42% |
| all | 303134 | 52.62% [52.45, 52.78] | 52.81% [52.63, 52.99] | 55.28% [55.11, 55.46] | 57.77% [57.59, 57.95] | 57.90% [57.72, 58.07] | 64.93% [64.75, 65.11] | 8.38% |

Spread across years for each column: the year with the lowest and the year with the highest accuracy, and whether their day-block intervals overlap.

| column | lowest year | its accuracy | highest year | its accuracy | intervals overlap |
|---|---|---|---|---|---|
| open | 2025 | 51.73% | 2020 | 53.50% | no |
| 10 s | 2020 | 51.97% | 2026 | 54.15% | no |
| 30 s | 2020 | 54.30% | 2025 | 56.18% | no |
| 60 s | 2020 | 56.96% | 2026 | 58.85% | no |
| minute 1 | 2020 | 57.03% | 2026 | 58.94% | no |
| minute 3 | 2022 | 63.23% | 2026 | 66.29% | no |

In 9 of the 9 years the accuracy rises at every step from 10 s to 30 s, 60 s, minute 1 and minute 3.
