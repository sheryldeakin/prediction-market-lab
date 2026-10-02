Eras: each cell's deviation of the conditional up-rate from the unconditional rate, in points, firing-weighted within each era, for the 25 cells with the largest pooled deviation that never flipped sign. Slope is the change in deviation per year from a straight-line fit across the nine years.

| pattern | horizon (min) | 2018-19 | 2020-21 | 2022-23 | 2024-26 | pooled | slope per year |
|---|---|---|---|---|---|---|---|
| sweep: range position > 0.95 | 30 | -13.0 | -10.4 | -7.9 | -6.4 | -8.7 | +0.91 |
| price at 4h high (rangepos >= 0.98) | 30 | -12.5 | -10.6 | -8.3 | -6.5 | -8.7 | +0.80 |
| sweep: range position < 0.05 | 30 | +11.4 | +13.0 | +8.4 | +5.7 | +8.3 | -0.99 |
| price at 4h low (rangepos <= 0.02) | 30 | +10.2 | +13.7 | +8.6 | +6.1 | +8.3 | -0.81 |
| price at 4h low (rangepos <= 0.02) | 15 | +8.6 | +13.8 | +8.6 | +6.0 | +8.0 | -0.66 |
| price at 4h low (rangepos <= 0.02) | 10 | +9.1 | +13.1 | +8.8 | +5.8 | +7.9 | -0.79 |
| sweep: range position < 0.1 | 30 | +11.1 | +10.6 | +8.0 | +5.2 | +7.8 | -0.90 |
| sweep: range position > 0.95 | 15 | -9.9 | -8.5 | -8.1 | -6.2 | -7.7 | +0.48 |
| price at 4h high (rangepos >= 0.98) | 15 | -9.4 | -8.8 | -8.2 | -6.4 | -7.7 | +0.41 |
| sweep: range position > 0.90 | 30 | -11.7 | -8.7 | -6.8 | -5.6 | -7.7 | +0.80 |
| sweep: 15-min move < -3 sd | 3 | +8.1 | +10.9 | +6.5 | +6.2 | +7.5 | -0.48 |
| sweep: 5-min move < -3 sd | 3 | +7.3 | +9.7 | +7.4 | +6.2 | +7.5 | -0.26 |
| sweep: range position < 0.05 | 15 | +9.2 | +11.9 | +8.3 | +5.0 | +7.5 | -0.78 |
| sweep: RSI14 < 25 | 10 | +8.1 | +10.2 | +6.0 | +6.8 | +7.4 | -0.43 |
| sweep: RSI14 < 25 | 5 | +9.5 | +10.8 | +5.9 | +5.8 | +7.4 | -0.81 |
| price at 4h high (rangepos >= 0.98) | 10 | -8.6 | -8.5 | -8.2 | -5.8 | -7.2 | +0.36 |
| sweep: RSI14 < 25 | 3 | +9.4 | +11.2 | +5.9 | +5.3 | +7.2 | -0.84 |
| RSI14 below 30 | 10 | +8.3 | +9.8 | +6.4 | +5.9 | +7.2 | -0.51 |
| sweep: RSI14 < 30 | 10 | +8.3 | +9.8 | +6.4 | +5.9 | +7.2 | -0.51 |
| sweep: RSI14 < 30 | 5 | +9.0 | +10.2 | +6.2 | +5.2 | +7.2 | -0.73 |
| RSI14 below 30 | 5 | +9.0 | +10.2 | +6.2 | +5.2 | +7.2 | -0.73 |
| sweep: RSI14 < 20 | 3 | +8.6 | +12.2 | +5.0 | +6.3 | +7.1 | -0.74 |
| sweep: range position < 0.05 | 10 | +9.0 | +11.2 | +8.0 | +4.7 | +7.1 | -0.83 |
| sweep: RSI60 < 40 | 30 | +6.0 | +8.6 | +7.5 | +6.6 | +7.1 | -0.04 |
| sweep: 5-min move < -3 sd | 5 | +5.4 | +8.9 | +7.3 | +6.7 | +7.0 | +0.08 |

Across the 483 cells that never flipped sign, the deviation moved toward zero over the years in 79% of them; the median absolute deviation was 4.7 points in 2018-19 and 3.1 in 2024-26.

Spans: cells selected on earlier years only (adjusted p at or below 0.05 and the same sign in every year of the span), then scored on the test year alone. Accuracy is the firing-weighted rate at which the selected direction was right in the test year; 50% is chance.

| test year | selected on | cells selected | kept their sign | accuracy of the selected direction | firings in test year |
|---|---|---|---|---|---|
| 2020 | previous year | 413 | 413 | 53.8% | 27,848,818 |
| 2020 | previous 2 years | 297 | 297 | 54.1% | 21,783,933 |
| 2020 | previous 3 years | 297 | 297 | 54.1% | 21,783,933 |
| 2020 | all earlier years | 297 | 297 | 54.1% | 21,783,933 |
| 2021 | previous year | 416 | 416 | 53.1% | 33,341,538 |
| 2021 | previous 2 years | 374 | 374 | 53.3% | 29,732,303 |
| 2021 | previous 3 years | 280 | 280 | 53.5% | 24,028,823 |
| 2021 | all earlier years | 280 | 280 | 53.5% | 24,028,823 |
| 2022 | previous year | 407 | 406 | 52.9% | 31,484,500 |
| 2022 | previous 2 years | 370 | 370 | 52.9% | 28,474,988 |
| 2022 | previous 3 years | 345 | 345 | 53.1% | 25,313,673 |
| 2022 | all earlier years | 265 | 265 | 53.4% | 20,098,511 |
| 2023 | previous year | 396 | 389 | 52.5% | 28,403,447 |
| 2023 | previous 2 years | 338 | 333 | 52.7% | 26,157,972 |
| 2023 | previous 3 years | 318 | 314 | 52.7% | 24,475,315 |
| 2023 | all earlier years | 240 | 240 | 53.4% | 17,574,434 |
| 2024 | previous year | 396 | 396 | 52.4% | 26,774,364 |
| 2024 | previous 2 years | 307 | 307 | 52.3% | 22,437,164 |
| 2024 | previous 3 years | 281 | 281 | 52.4% | 21,484,101 |
| 2024 | all earlier years | 224 | 224 | 52.6% | 17,934,702 |
| 2025 | previous year | 323 | 323 | 51.8% | 27,745,281 |
| 2025 | previous 2 years | 292 | 292 | 51.9% | 23,611,437 |
| 2025 | previous 3 years | 237 | 237 | 51.8% | 19,979,794 |
| 2025 | all earlier years | 194 | 194 | 51.9% | 17,143,056 |
| 2026 | previous year | 181 | 181 | 52.8% | 10,663,613 |
| 2026 | previous 2 years | 165 | 165 | 52.9% | 10,123,758 |
| 2026 | previous 3 years | 159 | 159 | 52.9% | 9,789,234 |
| 2026 | all earlier years | 120 | 120 | 53.0% | 7,314,120 |

Across all test years and spans, 8,195 of 8,212 selected cell-years kept their sign in the test year. These cell-years are not independent observations: the events overlap heavily (the clusters table in the cells section reduces them to a few effects), so the count says the sign of those effects is reliable, not that there are thousands of separate confirmations.

By span, averaged over test years:

| selected on | mean cells selected | share that kept their sign | mean accuracy of the selected direction |
|---|---|---|---|
| previous year | 362 | 100% | 52.8% |
| previous 2 years | 306 | 100% | 52.9% |
| previous 3 years | 274 | 100% | 52.9% |
| all earlier years | 231 | 100% | 53.1% |
