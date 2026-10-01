# Conditional direction by horizon, 2018 to 2026

The question: if a named pattern holds at some minute, which way does Bitcoin go over the next 1, 3, 5, 10, 15 or 30 minutes, how often, and did that hold in every year? This is the question the 15-minute window model ([btc_15m.md](btc_15m.md)) asked at one horizon and one time (the quarter-hour boundary), asked everywhere. Every table is generated into `results/btc_15m/` and spliced here by `scripts/update_readme.py`; the studies, decisions and bugs are in [process.md](process.md).

## Method

- **Data.** Binance BTCUSDT 1-minute candles from 2018-01 to 2026-08 (4.5 million decision minutes), each year loaded with the month before it for feature history.
- **Decision times.** Every minute, not only boundaries. The features are the minute-0 features of the main model, built by a vectorised builder that is tested row for row against the per-window one.
- **Labels.** For horizon h, the close of minute i+h-1 against the open of minute i.
- **Patterns.** The hand-named event library and the threshold sweeps of the wide search, about 107 per year; volatility-decile cutoffs come from the previous year.
- **Statistic.** The up-rate when the pattern holds minus when it does not, with a day-clustered standard error, per year and per horizon. A pattern is scored in a year only if it fires at least 500 times.
- **Null.** Per year, labels rotated within each month (which keeps the labels' own runs and base rate), 50 runs; the largest |z| across all cells in a run gives every cell a search-wide adjusted p (single-step max-T). The smallest adjusted p reachable is 1 in 451.
- **Stability.** Years in which a cell's sign matched its pooled sign, out of the years in which it fired enough.

## Results

<!-- table:horizons:start -->
Conditional direction by horizon, 2018 to 2026-08, every minute as a decision time. For each pattern and horizon: pooled up-rate of the next h minutes when the pattern holds, deviation from the unconditional rate in points, share of minutes on which it fires, years in which the sign matched the pooled sign out of years with at least 500 firings, and the smallest search-wide adjusted p across years (single-step max-T over 50 rotated-label runs per year; the smallest possible value is 0.0022). Top 40 cells by absolute deviation that held in every year; every cell is in horizons_summary.csv and every year in horizons_cells.csv.

| pattern | horizon (min) | up-rate | deviation (points) | fires on | years held | min adjusted p |
|---|---|---|---|---|---|---|
| sweep: range position > 0.95 | 30 | 41.8% | -8.7 | 3.4% | 9/9 | 0.0022 |
| price at 4h high (rangepos >= 0.98) | 30 | 41.8% | -8.7 | 1.4% | 9/9 | 0.0022 |
| sweep: range position < 0.05 | 30 | 58.8% | +8.3 | 2.5% | 9/9 | 0.0022 |
| price at 4h low (rangepos <= 0.02) | 30 | 58.7% | +8.3 | 1.1% | 9/9 | 0.0022 |
| price at 4h low (rangepos <= 0.02) | 15 | 58.2% | +8.0 | 1.1% | 9/9 | 0.0022 |
| price at 4h low (rangepos <= 0.02) | 10 | 58.0% | +7.9 | 1.1% | 9/9 | 0.0022 |
| sweep: range position < 0.1 | 30 | 58.2% | +7.8 | 5.6% | 9/9 | 0.0022 |
| sweep: range position > 0.95 | 15 | 42.6% | -7.7 | 3.4% | 9/9 | 0.0022 |
| price at 4h high (rangepos >= 0.98) | 15 | 42.6% | -7.7 | 1.4% | 9/9 | 0.0022 |
| sweep: range position > 0.90 | 30 | 42.8% | -7.7 | 7.5% | 9/9 | 0.0022 |
| sweep: 15-min move < -3 sd | 3 | 57.8% | +7.5 | 0.3% | 9/9 | 0.0754 |
| sweep: 5-min move < -3 sd | 3 | 57.8% | +7.5 | 0.5% | 9/9 | 0.0022 |
| sweep: range position < 0.05 | 15 | 57.7% | +7.5 | 2.5% | 9/9 | 0.0022 |
| sweep: RSI14 < 25 | 10 | 57.6% | +7.4 | 1.4% | 9/9 | 0.0022 |
| sweep: RSI14 < 25 | 5 | 57.6% | +7.4 | 1.4% | 9/9 | 0.0022 |
| price at 4h high (rangepos >= 0.98) | 10 | 43.0% | -7.2 | 1.4% | 9/9 | 0.0022 |
| sweep: RSI14 < 25 | 3 | 57.5% | +7.2 | 1.4% | 9/9 | 0.0022 |
| sweep: RSI14 < 30 | 10 | 57.4% | +7.2 | 3.8% | 9/9 | 0.0022 |
| RSI14 below 30 | 10 | 57.4% | +7.2 | 3.8% | 9/9 | 0.0022 |
| RSI14 below 30 | 5 | 57.3% | +7.2 | 3.8% | 9/9 | 0.0022 |
| sweep: RSI14 < 30 | 5 | 57.3% | +7.2 | 3.8% | 9/9 | 0.0022 |
| sweep: RSI14 < 20 | 3 | 57.5% | +7.1 | 0.5% | 9/9 | 0.0022 |
| sweep: range position < 0.05 | 10 | 57.2% | +7.1 | 2.5% | 9/9 | 0.0022 |
| sweep: RSI60 < 40 | 30 | 57.5% | +7.1 | 3.0% | 9/9 | 0.0022 |
| sweep: 5-min move < -3 sd | 5 | 57.2% | +7.0 | 0.5% | 9/9 | 0.0022 |
| sweep: range position < 0.1 | 15 | 57.2% | +7.0 | 5.6% | 9/9 | 0.0022 |
| sweep: range position > 0.95 | 10 | 43.3% | -6.9 | 3.4% | 9/9 | 0.0022 |
| sweep: 15-min move < -3 sd | 5 | 57.1% | +6.9 | 0.3% | 9/9 | 0.1619 |
| sweep: range position < 0.15 | 30 | 57.3% | +6.9 | 9.6% | 9/9 | 0.0022 |
| sweep: RSI14 < 25 | 30 | 57.3% | +6.8 | 1.4% | 9/9 | 0.0022 |
| RSI14 below 30 | 15 | 57.1% | +6.8 | 3.8% | 9/9 | 0.0022 |
| sweep: RSI14 < 30 | 15 | 57.1% | +6.8 | 3.8% | 9/9 | 0.0022 |
| sweep: RSI14 < 20 | 5 | 57.0% | +6.8 | 0.5% | 9/9 | 0.0022 |
| sweep: RSI60 < 40 | 15 | 57.0% | +6.8 | 3.0% | 9/9 | 0.0022 |
| sweep: 15-min move < -2.5 sd | 5 | 56.9% | +6.8 | 0.8% | 9/9 | 0.0022 |
| sweep: range position > 0.85 | 30 | 43.7% | -6.8 | 12.7% | 9/9 | 0.0022 |
| sweep: RSI14 < 25 | 15 | 57.0% | +6.8 | 1.4% | 9/9 | 0.0022 |
| sweep: RSI14 < 30 | 30 | 57.2% | +6.8 | 3.8% | 9/9 | 0.0022 |
| RSI14 below 30 | 30 | 57.2% | +6.8 | 3.8% | 9/9 | 0.0022 |
| sweep: 15-min move < -2.5 sd | 3 | 57.0% | +6.7 | 0.8% | 9/9 | 0.0022 |

By horizon: how many cells held their sign in every year, and the largest absolute deviation among them.

| horizon (min) | cells tested | held every year | largest deviation among those (points) |
|---|---|---|---|
| 1 | 107 | 47 | 5.8 |
| 3 | 107 | 92 | 7.5 |
| 5 | 107 | 95 | 7.4 |
| 10 | 107 | 87 | 7.9 |
| 15 | 107 | 82 | 8.0 |
| 30 | 107 | 80 | 8.7 |

Null: the largest |z| across all patterns and horizons on rotated labels has median 3.51 and 95th percentile 6.17; the real search's largest |z| is 25.70.

The reversal rule by year: call the opposite of the previous 15 minutes, scored on the next 15 minutes, at the quarter-hour grid and at every minute. Day-block 95% intervals.

| year | decision times | n | accuracy [95% CI] |
|---|---|---|---|
| 2018 | quarter-hour grid | 33912 | 52.99% [52.41, 53.55] |
| 2018 | every minute | 508610 | 52.56% [52.27, 52.85] |
| 2019 | quarter-hour grid | 34322 | 53.36% [52.86, 53.83] |
| 2019 | every minute | 514758 | 53.01% [52.73, 53.29] |
| 2020 | quarter-hour grid | 34259 | 53.57% [53.10, 54.05] |
| 2020 | every minute | 513782 | 53.19% [52.92, 53.48] |
| 2021 | quarter-hour grid | 34379 | 52.26% [51.79, 52.75] |
| 2021 | every minute | 515599 | 52.70% [52.40, 53.00] |
| 2022 | quarter-hour grid | 35040 | 52.17% [51.70, 52.67] |
| 2022 | every minute | 525586 | 52.39% [52.05, 52.74] |
| 2023 | quarter-hour grid | 34935 | 52.84% [52.31, 53.35] |
| 2023 | every minute | 524007 | 52.35% [52.04, 52.67] |
| 2024 | quarter-hour grid | 35136 | 52.30% [51.74, 52.80] |
| 2024 | every minute | 527026 | 51.88% [51.53, 52.21] |
| 2025 | quarter-hour grid | 35040 | 51.73% [51.21, 52.21] |
| 2025 | every minute | 525586 | 51.36% [51.02, 51.68] |
| 2026 | quarter-hour grid | 23328 | 52.21% [51.63, 52.82] |
| 2026 | every minute | 349906 | 51.99% [51.60, 52.36] |
<!-- table:horizons:end -->

What the tables say:

- **The reversal between consecutive 15-minute stretches has existed since 2018.** Calling the opposite of the previous 15 minutes scores 52 to 53.6% in every year, at the quarter-hour grid and at every minute. It was strongest in 2018 to 2020 and has thinned to about 52% since 2024. It is a nine-year property of the price path, not an artefact of the current market structure, and it is slowly fading.
- **The strongest conditional cells are reversals from extremes, and they held in all nine years.** When the price is at its 4-hour low, the next 10 to 30 minutes close up 58 to 59% of the time; at its 4-hour high, down 57 to 58%. RSI14 below 25 or 30 is followed by an up move 57% of the time over 3 to 30 minutes. A 3-standard-deviation drop in the last 5 or 15 minutes is followed by an up move 57 to 58% of the time over the next 3 to 5 minutes. These fire on 0.3 to 4% of minutes. The search's largest |z| is 25.7 against a null whose largest |z| has a 95th percentile of 6.2, so the structure is not a product of testing 642 cells.
- **The cells are one effect in many costumes.** "Range position below 0.05", "price at the 4-hour low", "RSI14 below 25" and "a 3-sd drop" all describe a price that just fell hard; their mirrors describe one that just rose. The table lists them separately because each is a rule someone could act on, not because each is a separate finding.
- **One minute ahead is the hardest horizon.** 47 of 107 cells keep their sign in every year at one minute; 92 to 95 do at three to five minutes; 80 to 87 at 10 to 30. The information is in the next few minutes, and the largest deviations are at 15 to 30 minutes.
- **No cell is close to certain.** The best is 59% up on about 1% of minutes. A conditional probability, an interval, a firing rate and a record across years is the honest form of "if this pattern, then up".

## Eras and spans

Patterns change over time, so the cells were also read by era and tested by how much history a live rule should look back on.

<!-- table:horizons_spans:start -->
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

Across all test years and spans, 8,195 of 8,212 selected cell-years kept their sign in the test year.

By span, averaged over test years:

| selected on | mean cells selected | share that kept their sign | mean accuracy of the selected direction |
|---|---|---|---|
| previous year | 362 | 100% | 52.8% |
| previous 2 years | 306 | 100% | 52.9% |
| previous 3 years | 274 | 100% | 52.9% |
| all earlier years | 231 | 100% | 53.1% |
<!-- table:horizons_spans:end -->

- **The effects are fading.** The 4-hour-high reversal over 30 minutes was 13 points in 2018-19 and 6.4 points in 2024-26; the 4-hour-low mirror went from 10 to 11 points to about 6. Across the 483 cells that never flipped sign, 79% drifted toward zero over the nine years. They are still there in 2024-26, at about half their 2018 size.
- **Direction is stable; size is not.** Cells selected on earlier years kept their sign in the test year almost without exception (the count is under the span table), so the sign of these effects is reliable. Their size in the test year is smaller than in the selection years, which is the fading above and the usual shrinkage of a selected estimate.
- **More history selects fewer, slightly better cells.** Selecting on all earlier years picks about 230 cells against 360 for the previous year alone, and the selected direction is right 53.1% of the time in the test year against 52.8%. The differences between spans are small; what the span mostly changes is how many cells survive, not how good they are. The accuracy figures here are firing-weighted across all selected cells, so the frequent weak cells (range position beyond 0.85, firing on 13% of minutes) dominate them; the strong cells above are rarer and stronger than these averages.

## What is not yet done

- The label is the Binance last print. For the shortest horizons a "new 4-hour low" is partly a last trade at the bid, and the next print is more likely above it. The 15-minute reversal survived a VWAP label (btc_15m.md, study 21); the same check is owed to these cells, from the tick data, once its history is downloaded.
- Regimes: the same cells within bull, bear and flat states, and the characteristics of those states beyond direction. Planned, with the state known at decision time.
- Direction with magnitude from any minute: the probability of touching +X before -X within h minutes given a pattern.
