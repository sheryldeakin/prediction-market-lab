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

## The same cells under averaged prices

The labels above compare two prints. "Price at its 4-hour low" is partly "the last trade was at the bid", and the next print is then more likely above it; averaged prices remove most of that. Every cell was scored again with the VWAP of the decision minute against the VWAP of the horizon's last minute (at horizon 1, the minute's first and second halves), from the tick data for all nine years.

<!-- table:horizons_vwap:start -->
The conditional cells under two labels, 2018 to 2026-08, every minute as a decision time: the last print (close of the horizon's last minute against the open of the decision minute) and 60-second VWAPs (the decision minute's VWAP against the last minute's VWAP). Deviation from the unconditional up-rate in points, firing-weighted over the years; 'retained' is the VWAP deviation as a share of the last-print one; the last column is the number of years in which the VWAP deviation had the pooled last-print sign. At horizon 1 the VWAP label compares the decision minute's first and second 30 seconds, so it is a different (shorter) question from the last-print label there. The 30 cells with the largest last-print deviation.

| pattern | horizon (min) | deviation, last print | deviation, VWAP | retained | years same sign under VWAP |
|---|---|---|---|---|---|
| sweep: range position > 0.95 | 30 | -9.0 | -9.6 | 106% | 9/9 |
| price at 4h high (rangepos >= 0.98) | 30 | -8.8 | -9.5 | 108% | 9/9 |
| sweep: range position < 0.05 | 30 | +8.6 | +9.1 | 107% | 9/9 |
| price at 4h low (rangepos <= 0.02) | 30 | +8.4 | +9.0 | 107% | 9/9 |
| sweep: range position > 0.90 | 30 | -8.3 | -8.7 | 105% | 9/9 |
| sweep: range position < 0.1 | 30 | +8.2 | +8.6 | 105% | 9/9 |
| price at 4h low (rangepos <= 0.02) | 15 | +8.1 | +8.9 | 110% | 9/9 |
| sweep: range position > 0.95 | 15 | -8.0 | -8.5 | 106% | 9/9 |
| price at 4h low (rangepos <= 0.02) | 10 | +7.9 | +8.7 | 109% | 9/9 |
| price at 4h high (rangepos >= 0.98) | 15 | -7.8 | -8.3 | 107% | 9/9 |
| sweep: range position > 0.85 | 30 | -7.7 | -8.0 | 103% | 9/9 |
| sweep: range position < 0.05 | 15 | +7.7 | +8.4 | 110% | 9/9 |
| sweep: RSI60 < 45 | 30 | +7.6 | +7.9 | 104% | 9/9 |
| sweep: RSI60 > 55 | 30 | -7.6 | -7.8 | 103% | 9/9 |
| sweep: range position < 0.15 | 30 | +7.6 | +7.9 | 105% | 9/9 |
| sweep: 15-min move < -3 sd | 3 | +7.5 | +7.8 | 104% | 9/9 |
| sweep: 5-min move < -3 sd | 3 | +7.5 | +7.9 | 105% | 9/9 |
| sweep: RSI14 < 25 | 10 | +7.5 | +7.8 | 104% | 9/9 |
| RSI14 below 30 | 10 | +7.5 | +7.9 | 105% | 9/9 |
| sweep: RSI14 < 30 | 10 | +7.5 | +7.9 | 105% | 9/9 |
| sweep: RSI14 < 25 | 5 | +7.5 | +7.8 | 104% | 9/9 |
| RSI14 below 30 | 5 | +7.4 | +7.8 | 105% | 9/9 |
| sweep: RSI14 < 30 | 5 | +7.4 | +7.8 | 105% | 9/9 |
| sweep: range position < 0.1 | 15 | +7.4 | +7.9 | 108% | 9/9 |
| price at 4h high (rangepos >= 0.98) | 10 | -7.3 | -8.1 | 110% | 9/9 |
| sweep: RSI14 < 25 | 3 | +7.3 | +7.0 | 96% | 9/9 |
| sweep: range position < 0.05 | 10 | +7.3 | +8.2 | 112% | 9/9 |
| sweep: RSI60 < 40 | 30 | +7.3 | +7.6 | 104% | 9/9 |
| sweep: range position > 0.90 | 15 | -7.3 | -7.6 | 105% | 9/9 |
| sweep: RSI14 < 20 | 3 | +7.2 | +6.7 | 94% | 9/9 |

By horizon, over all cells: the median share of the last-print deviation retained under the VWAP label, and the share of cells whose sign is unchanged.

| horizon (min) | cells | median retained | sign unchanged |
|---|---|---|---|
| 1 | 107 | 110% | 93% |
| 3 | 107 | 103% | 99% |
| 5 | 107 | 105% | 100% |
| 10 | 107 | 108% | 100% |
| 15 | 107 | 106% | 99% |
| 30 | 107 | 106% | 100% |
<!-- table:horizons_vwap:end -->

The cells are not a last-print effect. Under the VWAP label the deviations are slightly larger than under the last print (the median cell retains 103 to 110% of its deviation) and the sign is unchanged in 99 to 100% of cells at 3 to 30 minutes and 93% at one minute, where the VWAP label asks a shorter question (the second half of the minute against the first). The reversals from extremes are moves in the price itself, as the 15-minute reversal was in the main report's study 21.

## The price-action library

Trader vernacular, written as events that read only earlier candles and scored like the cells above. 79 events in six families: levels (failed breakouts, wick rejections, liquidity sweeps, retests, acceptance, held levels, flips, repeated rejection, "rejecting the ups", lower highs and higher lows, previous day's high and low, the daily open, range breakouts, VWAP reclaim and loss), round numbers ($1,000 and $100 levels approached and crossed), time of day (funding settlements, the US open and close, the London open, hour, 4-hour and day boundaries, weekends), volume and flow (volume climax, absorption, delta divergence, one-minute taker imbalance), candles (engulfing, pin bar, inside bar, doji) and volatility (squeeze). Definitions are in `models/btc_15m/price_action.py`.

<!-- table:price_action:start -->
The price-action library, 2018 to 2026-08, every minute as a decision time: trader vernacular written as events that read only earlier candles (definitions in models/btc_15m/price_action.py), scored like the conditional tables in horizons.md. Pooled up-rate of the next h minutes when the event holds, deviation from the unconditional rate in points, share of minutes it fires on, years in which the sign matched the pooled sign out of years with at least 500 firings, and the smallest search-wide adjusted p across years (30 rotated-label runs per year). Top 40 cells by absolute deviation that held in every year.

| family | event | horizon (min) | up-rate | deviation (points) | fires on | years held | min adjusted p |
|---|---|---|---|---|---|---|---|
| levels | wick rejection at the daily low | 30 | 59.4% | +9.0 | 0.27% | 9/9 | 0.0074 |
| volume and flow | delta divergence: new 4h low with net taker buying over the hour | 30 | 59.2% | +8.7 | 0.27% | 8/8 | 0.0037 |
| levels | wick rejection at the 4h high | 30 | 41.9% | -8.6 | 1.01% | 9/9 | 0.0037 |
| levels | wick rejection at the 4h low | 30 | 58.6% | +8.1 | 0.94% | 9/9 | 0.0037 |
| levels | wick rejection at the daily low | 15 | 58.3% | +8.0 | 0.27% | 9/9 | 0.0074 |
| levels | wick rejection at the daily low | 10 | 58.1% | +7.9 | 0.27% | 9/9 | 0.0037 |
| levels | wick rejection at the 4h high | 15 | 42.4% | -7.9 | 1.01% | 9/9 | 0.0037 |
| levels | wick rejection at the 4h low | 15 | 57.9% | +7.7 | 0.94% | 9/9 | 0.0037 |
| volume and flow | delta divergence: new 4h high with net taker selling over the hour | 15 | 42.9% | -7.4 | 0.42% | 9/9 | 0.0074 |
| volume and flow | delta divergence: new 4h low with net taker buying over the hour | 15 | 57.7% | +7.4 | 0.27% | 8/8 | 0.0074 |
| levels | wick rejection at the 4h low | 10 | 57.5% | +7.3 | 0.94% | 9/9 | 0.0037 |
| levels | wick rejection at the 4h high | 10 | 43.1% | -7.1 | 1.01% | 9/9 | 0.0037 |
| candles | pin bar at a new 1h high (long upper wick) | 15 | 43.3% | -7.1 | 0.53% | 9/9 | 0.0037 |
| candles | pin bar at a new 1h high (long upper wick) | 30 | 43.6% | -6.9 | 0.53% | 9/9 | 0.0037 |
| levels | wick rejection at the daily high | 30 | 43.7% | -6.9 | 0.31% | 9/9 | 0.0295 |
| levels | wick rejection at the daily low | 5 | 57.0% | +6.8 | 0.27% | 9/9 | 0.0074 |
| levels | acceptance above the 4h high (last 5 closes all above it) | 30 | 43.7% | -6.8 | 2.97% | 9/9 | 0.0037 |
| volume and flow | delta divergence: new 4h high with net taker selling over the hour | 10 | 43.4% | -6.8 | 0.42% | 9/9 | 0.0074 |
| volume and flow | delta divergence: new 4h low with net taker buying over the hour | 10 | 57.0% | +6.8 | 0.27% | 8/8 | 0.0037 |
| candles | doji at a new 1h high | 30 | 43.8% | -6.8 | 0.46% | 9/9 | 0.0037 |
| candles | pin bar at a new 1h high (long upper wick) | 5 | 43.5% | -6.7 | 0.53% | 9/9 | 0.0037 |
| candles | doji at a new 1h high | 15 | 43.7% | -6.6 | 0.46% | 9/9 | 0.0037 |
| candles | pin bar at a new 1h low (long lower wick) | 10 | 56.9% | +6.6 | 0.56% | 9/9 | 0.0037 |
| candles | pin bar at a new 1h low (long lower wick) | 30 | 57.1% | +6.6 | 0.56% | 9/9 | 0.0037 |
| levels | liquidity sweep of the 1h high (took it out, closed back below) | 30 | 44.0% | -6.5 | 2.03% | 9/9 | 0.0037 |
| candles | pin bar at a new 1h high (long upper wick) | 10 | 43.7% | -6.5 | 0.53% | 9/9 | 0.0037 |
| volume and flow | volume climax at a new 1h low (hour's largest volume) | 30 | 57.0% | +6.5 | 0.72% | 9/9 | 0.0037 |
| levels | wick rejection at the 1h high | 30 | 44.1% | -6.5 | 2.57% | 9/9 | 0.0037 |
| levels | acceptance below the 4h low (last 5 closes all below it) | 30 | 56.9% | +6.4 | 2.54% | 9/9 | 0.0074 |
| levels | liquidity sweep of the 1h high (took it out, closed back below) | 15 | 44.0% | -6.3 | 2.03% | 9/9 | 0.0037 |
| candles | pin bar at a new 1h low (long lower wick) | 15 | 56.6% | +6.3 | 0.56% | 9/9 | 0.0037 |
| candles | doji at a new 1h low | 30 | 56.8% | +6.3 | 0.43% | 9/9 | 0.0037 |
| levels | liquidity sweep of the 1h low (took it out, closed back above) | 30 | 56.7% | +6.2 | 2.01% | 9/9 | 0.0037 |
| levels | wick rejection at the 1h high | 15 | 44.1% | -6.2 | 2.57% | 9/9 | 0.0037 |
| levels | liquidity sweep of the 1h low (took it out, closed back above) | 10 | 56.4% | +6.2 | 2.01% | 9/9 | 0.0037 |
| levels | wick rejection at the 4h low | 5 | 56.3% | +6.1 | 0.94% | 9/9 | 0.0037 |
| volume and flow | volume climax at a new 1h high (hour's largest volume) | 30 | 44.4% | -6.1 | 0.66% | 9/9 | 0.0037 |
| volume and flow | volume climax at a new 1h low (hour's largest volume) | 5 | 56.3% | +6.1 | 0.72% | 9/9 | 0.0037 |
| levels | wick rejection at the 1h low | 30 | 56.6% | +6.1 | 2.48% | 9/9 | 0.0037 |
| levels | liquidity sweep of the 1h low (took it out, closed back above) | 15 | 56.4% | +6.1 | 2.01% | 9/9 | 0.0037 |

By family: events defined, cells (event by horizon) that held their sign in every year, and the largest absolute deviation among them.

| family | events | cells tested | held every year | largest deviation among those (points) |
|---|---|---|---|---|
| candles | 7 | 42 | 23 | 7.1 |
| levels | 38 | 228 | 132 | 9.0 |
| round numbers | 8 | 48 | 24 | 3.1 |
| time | 17 | 102 | 2 | 1.3 |
| volatility | 1 | 6 | 0 | nan |
| volume and flow | 8 | 48 | 20 | 8.7 |

Every event at the 15-minute horizon, held or not, so that the null results are visible too.

| family | event | up-rate | deviation (points) | fires on | years held | min adjusted p |
|---|---|---|---|---|---|---|
| candles | pin bar at a new 1h high (long upper wick) | 43.3% | -7.1 | 0.53% | 9/9 | 0.0037 |
| candles | doji at a new 1h high | 43.7% | -6.6 | 0.46% | 9/9 | 0.0037 |
| candles | pin bar at a new 1h low (long lower wick) | 56.6% | +6.3 | 0.56% | 9/9 | 0.0037 |
| candles | doji at a new 1h low | 56.1% | +5.8 | 0.43% | 9/9 | 0.0037 |
| candles | bullish engulfing | 49.8% | -0.5 | 7.84% | 8/9 | 0.1033 |
| candles | bearish engulfing | 50.7% | +0.4 | 7.84% | 7/9 | 0.1993 |
| candles | inside bar (last minute inside the previous one) | 50.3% | -0.1 | 22.21% | 6/9 | 1.0000 |
| levels | wick rejection at the daily low | 58.3% | +8.0 | 0.27% | 9/9 | 0.0074 |
| levels | wick rejection at the 4h high | 42.4% | -7.9 | 1.01% | 9/9 | 0.0037 |
| levels | wick rejection at the 4h low | 57.9% | +7.7 | 0.94% | 9/9 | 0.0037 |
| levels | liquidity sweep of the 1h high (took it out, closed back below) | 44.0% | -6.3 | 2.03% | 9/9 | 0.0037 |
| levels | wick rejection at the 1h high | 44.1% | -6.2 | 2.57% | 9/9 | 0.0037 |
| levels | liquidity sweep of the 1h low (took it out, closed back above) | 56.4% | +6.1 | 2.01% | 9/9 | 0.0037 |
| levels | wick rejection at the daily high | 44.2% | -6.1 | 0.31% | 9/9 | 0.0295 |
| levels | acceptance below the 4h low (last 5 closes all below it) | 56.3% | +6.1 | 2.54% | 9/9 | 0.0037 |
| levels | acceptance above the 4h high (last 5 closes all above it) | 44.3% | -6.0 | 2.97% | 9/9 | 0.0074 |
| levels | wick rejection at the 1h low | 56.2% | +5.9 | 2.48% | 9/9 | 0.0037 |
| levels | failed breakdown below the daily low | 55.3% | +5.0 | 0.97% | 9/9 | 0.1033 |
| levels | retest from above of a 4h high broken in the last hour | 45.9% | -4.4 | 1.70% | 9/9 | 0.0332 |
| levels | range breakdown downward (prior hour under 15 bp) | 54.5% | +4.3 | 0.47% | 5/5 | 0.1587 |
| levels | failed breakout above the daily high | 46.0% | -4.3 | 1.08% | 9/9 | 0.2214 |
| levels | failed breakdown below the 4h low | 54.4% | +4.2 | 3.40% | 9/9 | 0.0074 |
| levels | failed breakout above the 4h high | 46.2% | -4.1 | 3.65% | 9/9 | 0.0037 |
| levels | reclaimed the session VWAP in the last 5 minutes after 30+ minutes below | 46.2% | -4.1 | 0.82% | 9/9 | 0.0923 |
| levels | retest from below of a 4h low broken in the last hour | 53.8% | +3.6 | 1.45% | 9/9 | 0.0590 |
| levels | lower highs (three successive 10-minute highs declining) | 53.8% | +3.5 | 29.33% | 9/9 | 0.0037 |
| levels | higher lows (three successive 10-minute lows rising) | 46.9% | -3.4 | 29.80% | 9/9 | 0.0037 |
| levels | resistance flipped to support (4h high broken, retested within 5 bp, last 3 closes above) | 46.9% | -3.3 | 0.36% | 5/5 | 1.0000 |
| levels | range breakout upward (prior hour under 15 bp) | 46.9% | -3.3 | 0.47% | 4/5 | 0.9705 |
| levels | lost the session VWAP in the last 5 minutes after 30+ minutes above | 53.4% | +3.1 | 0.84% | 9/9 | 0.1439 |
| levels | support held (4h low tested within 3 bp, no close below, price now 3+ bp above) | 53.0% | +2.7 | 2.52% | 8/9 | 0.0923 |
| levels | broke below the previous day's low in the last 5 minutes | 52.8% | +2.5 | 0.51% | 9/9 | 0.8266 |
| levels | support flipped to resistance (4h low broken, retested within 5 bp, last 3 closes below) | 52.5% | +2.4 | 0.33% | 3/4 | 1.0000 |
| levels | approaching the previous day's low from above (within 10 bp) | 52.6% | +2.3 | 0.93% | 5/9 | 0.1218 |
| levels | failed breakdown below the 1h low | 52.6% | +2.3 | 8.43% | 9/9 | 0.0037 |
| levels | failed breakout above the 1h high | 48.2% | -2.2 | 8.59% | 9/9 | 0.0037 |
| levels | broke above the previous day's high in the last 5 minutes | 48.2% | -2.1 | 0.60% | 9/9 | 0.6421 |
| levels | resistance held (4h high tested within 3 bp, no close above, price now 3+ bp below) | 48.2% | -2.1 | 2.94% | 9/9 | 0.3137 |
| levels | crossed above the daily open in the last 5 minutes | 48.2% | -2.1 | 1.80% | 8/9 | 0.1771 |
| levels | repeated rejection at the 4h high (2+ touches in 30 minutes, no close above) | 48.7% | -1.7 | 1.85% | 9/9 | 1.0000 |
| levels | repeated rejection at the 4h low (2+ touches in 30 minutes, no close below) | 52.0% | +1.7 | 1.56% | 7/9 | 0.9926 |
| levels | rejecting the downs (3+ down-minutes undone by the next minute in the last 15) | 48.7% | -1.6 | 19.51% | 9/9 | 0.0221 |
| levels | rejecting the ups (3+ up-minutes undone by the next minute in the last 15) | 51.5% | +1.2 | 19.34% | 9/9 | 0.0480 |
| levels | approaching the previous day's high from below (within 10 bp) | 49.2% | -1.1 | 1.21% | 5/9 | 1.0000 |
| levels | crossed below the daily open in the last 5 minutes | 50.9% | +0.6 | 1.80% | 6/9 | 1.0000 |
| round numbers | crossed a $1,000 level downward in the last 3 minutes | 52.8% | +2.7 | 1.76% | 9/9 | 0.1550 |
| round numbers | crossed a $100 level downward in the last 3 minutes | 52.2% | +2.0 | 14.25% | 9/9 | 0.0037 |
| round numbers | crossed a $1,000 level upward in the last 3 minutes | 48.4% | -1.7 | 1.76% | 9/9 | 0.2214 |
| round numbers | crossed a $100 level upward in the last 3 minutes | 48.6% | -1.6 | 14.25% | 9/9 | 0.0037 |
| round numbers | approaching a $100 level from below (within 10 bp, rising) | 49.0% | -1.1 | 20.08% | 9/9 | 0.0037 |
| round numbers | approaching a $1,000 level from above (within 10 bp, falling) | 49.1% | -1.0 | 1.95% | 8/9 | 0.9926 |
| round numbers | approaching a $100 level from above (within 10 bp, falling) | 51.0% | +0.9 | 19.95% | 7/9 | 0.0074 |
| round numbers | approaching a $1,000 level from below (within 10 bp, rising) | 49.7% | -0.4 | 2.09% | 6/9 | 1.0000 |
| time | 10 minutes after the US equity open (13:30 UTC) | 48.9% | -1.4 | 0.69% | 7/9 | 1.0000 |
| time | 10 minutes before funding settlement (00:00 UTC) | 49.0% | -1.3 | 0.69% | 6/9 | 0.9926 |
| time | last 5 minutes of the UTC day | 49.2% | -1.1 | 0.35% | 4/9 | 0.9926 |
| time | 10 minutes after funding settlement (16:00 UTC) | 49.3% | -1.0 | 0.70% | 7/9 | 1.0000 |
| time | first hour of the week (Monday 00:00 to 01:00 UTC) | 49.4% | -0.9 | 0.60% | 6/9 | 1.0000 |
| time | 10 minutes before funding settlement (16:00 UTC) | 51.2% | +0.9 | 0.70% | 6/9 | 1.0000 |
| time | 10 minutes after the US equity close (20:00 UTC) | 51.2% | +0.9 | 0.70% | 5/9 | 1.0000 |
| time | 10 minutes before funding settlement (08:00 UTC) | 50.9% | +0.6 | 0.69% | 6/9 | 1.0000 |
| time | first 5 minutes of the UTC day | 49.8% | -0.5 | 0.35% | 4/9 | 1.0000 |
| time | first 5 minutes of a 4-hour block | 49.9% | -0.4 | 2.08% | 6/9 | 1.0000 |
| time | 10 minutes after funding settlement (00:00 UTC) | 50.0% | -0.3 | 0.70% | 5/9 | 1.0000 |
| time | first 5 minutes of the hour | 50.1% | -0.3 | 8.33% | 7/9 | 1.0000 |
| time | 10 minutes after the London open (07:00 UTC) | 50.2% | -0.1 | 0.69% | 5/9 | 1.0000 |
| time | 10 minutes after funding settlement (08:00 UTC) | 50.3% | -0.0 | 0.69% | 5/9 | 1.0000 |
| time | last 5 minutes of the hour | 50.3% | -0.0 | 8.33% | 4/9 | 1.0000 |
| time | Saturday or Sunday | 50.3% | -0.0 | 28.60% | 4/9 | 1.0000 |
| time | last 5 minutes of a 4-hour block | 50.3% | +0.0 | 2.08% | 4/9 | 1.0000 |
| volatility | squeeze: last hour's range under 40% of the previous day's median hourly range | 50.0% | -0.2 | 1.63% | 6/9 | 1.0000 |
| volume and flow | delta divergence: new 4h high with net taker selling over the hour | 42.9% | -7.4 | 0.42% | 9/9 | 0.0074 |
| volume and flow | delta divergence: new 4h low with net taker buying over the hour | 57.7% | +7.4 | 0.27% | 8/8 | 0.0074 |
| volume and flow | volume climax at a new 1h low (hour's largest volume) | 56.4% | +6.1 | 0.72% | 9/9 | 0.0037 |
| volume and flow | volume climax at a new 1h high (hour's largest volume) | 45.4% | -5.0 | 0.66% | 9/9 | 0.0074 |
| volume and flow | taker buying above 70% of the last minute | 49.7% | -0.6 | 15.64% | 8/9 | 0.0111 |
| volume and flow | taker selling above 70% of the last minute | 50.8% | +0.5 | 16.20% | 7/9 | 0.1144 |
| volume and flow | absorption: heavy taker buying in the last 5 minutes, price did not rise | 50.2% | -0.1 | 1.86% | 5/9 | 0.5683 |
| volume and flow | absorption: heavy taker selling in the last 5 minutes, price did not fall | 50.2% | -0.1 | 1.89% | 4/9 | 0.9852 |

Null: the largest |z| across all events and horizons on rotated labels has median 3.47 and 95th percentile 5.68; the real search's largest |z| is 23.82.
<!-- table:price_action:end -->

- **The vocabulary describes one effect.** Every event that holds in all nine years is a probe of an extreme that came back: a wick rejection at the daily low (59% up over the next 30 minutes), a liquidity sweep of the hourly low (56%), a volume climax at a new hourly low (56%), a new 4-hour low with net taker buying over the hour (59%), a pin bar or doji at a new hourly high (43 to 44%), a failed breakout above the 4-hour high (46%). For these the direction traders quote is the direction in the data, and it is the reversal from extremes of the tables above with a trader's name on it.
- **The continuation stories run backwards at this horizon.** "Reclaimed VWAP" is followed by 46% up (9 of 9 years), losing VWAP by 53% up. The retest from above of a 4-hour high broken in the last hour, the textbook "resistance became support", is followed by 46% up. Five consecutive closes above the 4-hour high, the confirmed breakout, 44%. Three declining 10-minute highs, the textbook bearish structure, 54% up, firing on a third of all minutes. At 1 to 30 minutes Bitcoin pulls back after reclaims, retests, confirmed breaks and trend structure; it does not continue.
- **Repeated rejection means nothing.** Two or more touches of the 4-hour high in 30 minutes with no close through it: 48.7% up, adjusted p 1.0; the folklore runs both ways on this one and the data supports neither. Held levels and level flips are 2 to 3 points at most, and the flips fire too rarely to test in every year.
- **Time of day has no direction.** Of 102 time cells, two hold their sign every year and the largest deviation is 1.3 points: funding settlements, the US open and close, weekends and boundaries do nothing to direction, whatever they do to volatility. Round numbers are 2 to 3 points at $1,000 levels and do not survive the adjustment; the crossing effect points toward reversal, not the acceleration Osler found in currency orders. Engulfing candles, absorption and the volatility squeeze carry no direction.
- **The search is wide and the null is accordingly high** (largest |z| 5.7 at its 95th percentile against 23.8 in the real search), so a cell needs a deviation of several points and nine years to be listed; the full table at the 15-minute horizon shows the null results too.

## Direction with magnitude

"It will go up for the next five minutes" means, honestly, "it will touch +X before -X within h minutes". For every decision minute and pattern, barriers of 5, 10 and 20 basis points and horizons of 5, 15 and 30 minutes: how often either barrier is reached in time, and how often the upper one comes first, against the same shares for all minutes.

<!-- table:horizons_barrier:start -->
Direction with magnitude from any minute, 2018 to 2026-08: given a pattern, the probability that the price touches +X basis points before -X within h minutes. 'Touched' is the share of firings in which either barrier was reached in time (against the share for all minutes); 'up first' is the share of those touches that hit the upper barrier first, against the same share for all touched minutes; deviation is the difference in points. Years held: years in which the sign of the deviation matched the pooled sign. Adjusted p is search-wide (single-step max-T over rotated outcomes). Top 40 cells by absolute deviation that held in every year.

| pattern | barrier (bp) | horizon (min) | fires on | touched (pattern) | touched (all) | up first (pattern) | up first (all) | deviation (points) | years held | min adjusted p |
|---|---|---|---|---|---|---|---|---|---|---|
| sweep: 5-min move < -3 sd | 5 | 30 | 23,148 | 99% | 99% | 56.5% | 49.8% | +6.7 | 9/9 | 0.0061 |
| sweep: 5-min move < -3 sd | 5 | 5 | 23,148 | 96% | 88% | 56.5% | 49.8% | +6.7 | 9/9 | 0.0061 |
| sweep: 5-min move < -3 sd | 5 | 15 | 23,148 | 98% | 97% | 56.5% | 49.8% | +6.7 | 9/9 | 0.0061 |
| sweep: 5-min move < -2.5 sd | 5 | 30 | 50,984 | 99% | 99% | 55.6% | 49.8% | +5.8 | 9/9 | 0.0061 |
| sweep: 5-min move < -2.5 sd | 5 | 5 | 50,986 | 94% | 88% | 55.6% | 49.8% | +5.8 | 9/9 | 0.0061 |
| sweep: 5-min move < -3 sd | 10 | 30 | 23,148 | 97% | 95% | 55.3% | 49.6% | +5.8 | 9/9 | 0.0061 |
| sweep: 5-min move < -2.5 sd | 5 | 15 | 50,985 | 98% | 97% | 55.5% | 49.8% | +5.8 | 9/9 | 0.0061 |
| sweep: RSI14 < 25 | 5 | 5 | 64,233 | 88% | 86% | 55.5% | 49.8% | +5.7 | 9/9 | 0.0061 |
| sweep: RSI14 < 25 | 5 | 15 | 64,233 | 94% | 97% | 55.5% | 49.8% | +5.7 | 9/9 | 0.0061 |
| sweep: RSI14 < 25 | 5 | 30 | 64,233 | 97% | 99% | 55.5% | 49.8% | +5.7 | 9/9 | 0.0061 |
| sweep: RSI14 < 20 | 5 | 5 | 22,141 | 84% | 86% | 55.4% | 49.8% | +5.6 | 9/9 | 0.0061 |
| sweep: 5-min move < -3 sd | 10 | 15 | 23,148 | 94% | 87% | 55.2% | 49.6% | +5.6 | 9/9 | 0.0061 |
| sweep: 5-min move < -3 sd | 10 | 5 | 23,148 | 86% | 64% | 55.1% | 49.5% | +5.6 | 9/9 | 0.0061 |
| sweep: RSI14 < 20 | 5 | 30 | 22,141 | 95% | 99% | 55.4% | 49.8% | +5.6 | 9/9 | 0.0061 |
| sweep: RSI14 < 20 | 5 | 15 | 22,141 | 91% | 97% | 55.3% | 49.8% | +5.6 | 9/9 | 0.0061 |
| sweep: 15-min move < -3 sd | 5 | 30 | 12,180 | 99% | 99% | 55.3% | 49.8% | +5.5 | 9/9 | 0.0061 |
| sweep: 15-min move < -3 sd | 5 | 5 | 12,180 | 96% | 88% | 55.2% | 49.8% | +5.4 | 9/9 | 0.0061 |
| sweep: RSI14 < 20 | 10 | 30 | 22,141 | 87% | 93% | 55.0% | 49.6% | +5.4 | 9/9 | 0.0061 |
| sweep: 15-min move < -3 sd | 5 | 15 | 12,180 | 98% | 97% | 55.2% | 49.8% | +5.4 | 9/9 | 0.0061 |
| sweep: RSI14 < 25 | 10 | 30 | 64,233 | 91% | 94% | 55.0% | 49.6% | +5.4 | 9/9 | 0.0061 |
| sweep: 15-min move < -2.5 sd | 5 | 15 | 34,916 | 98% | 97% | 55.0% | 49.8% | +5.2 | 9/9 | 0.0061 |
| sweep: 15-min move < -2.5 sd | 5 | 30 | 34,916 | 99% | 99% | 55.0% | 49.8% | +5.2 | 9/9 | 0.0061 |
| sweep: 15-min move < -2.5 sd | 5 | 5 | 34,916 | 95% | 88% | 55.0% | 49.8% | +5.2 | 9/9 | 0.0061 |
| sweep: RSI14 < 25 | 10 | 15 | 64,233 | 86% | 85% | 54.5% | 49.6% | +4.9 | 9/9 | 0.0061 |
| sweep: 15-min move < -3 sd | 10 | 30 | 12,180 | 97% | 94% | 54.5% | 49.6% | +4.9 | 9/9 | 0.0061 |
| sweep: RSI14 < 20 | 10 | 15 | 22,141 | 82% | 84% | 54.4% | 49.6% | +4.8 | 9/9 | 0.0061 |
| sweep: 5-min move > +3 sd | 5 | 5 | 23,845 | 95% | 88% | 45.0% | 49.8% | -4.8 | 9/9 | 0.0061 |
| sweep: RSI14 < 30 | 5 | 30 | 169,063 | 98% | 99% | 54.6% | 49.8% | +4.8 | 9/9 | 0.0061 |
| RSI14 below 30 | 5 | 30 | 169,063 | 98% | 99% | 54.6% | 49.8% | +4.8 | 9/9 | 0.0061 |
| RSI14 below 30 | 5 | 15 | 169,064 | 96% | 97% | 54.6% | 49.8% | +4.8 | 9/9 | 0.0061 |
| sweep: RSI14 < 30 | 5 | 15 | 169,064 | 96% | 97% | 54.6% | 49.8% | +4.8 | 9/9 | 0.0061 |
| sweep: 5-min move < -2 sd | 5 | 30 | 115,171 | 99% | 99% | 54.6% | 49.8% | +4.8 | 9/9 | 0.0061 |
| last 5 min down more than 2 sd | 5 | 30 | 115,171 | 99% | 99% | 54.6% | 49.8% | +4.8 | 9/9 | 0.0061 |
| sweep: RSI14 < 20 | 10 | 5 | 22,141 | 73% | 60% | 54.4% | 49.6% | +4.8 | 9/9 | 0.0061 |
| sweep: RSI14 < 25 | 10 | 5 | 64,233 | 75% | 61% | 54.3% | 49.6% | +4.8 | 9/9 | 0.0061 |
| sweep: 5-min move < -2 sd | 5 | 15 | 115,173 | 98% | 97% | 54.5% | 49.8% | +4.8 | 9/9 | 0.0061 |
| last 5 min down more than 2 sd | 5 | 15 | 115,173 | 98% | 97% | 54.5% | 49.8% | +4.8 | 9/9 | 0.0061 |
| last 5 min down more than 2 sd | 5 | 5 | 115,174 | 93% | 88% | 54.5% | 49.8% | +4.7 | 9/9 | 0.0061 |
| sweep: 5-min move < -2 sd | 5 | 5 | 115,174 | 93% | 88% | 54.5% | 49.8% | +4.7 | 9/9 | 0.0061 |
| sweep: 5-min move > +3 sd | 5 | 15 | 23,845 | 99% | 97% | 45.1% | 49.8% | -4.7 | 9/9 | 0.0061 |

By barrier and horizon: the unconditional share of minutes with a touch and of touches that were up, the number of cells that held every year, and the largest deviation among them.

| barrier (bp) | horizon (min) | touched (all) | up first (all) | cells held every year | largest deviation (points) |
|---|---|---|---|---|---|
| 5 | 5 | 88% | 49.8% | 68 | 6.7 |
| 5 | 15 | 97% | 49.8% | 75 | 6.7 |
| 5 | 30 | 99% | 49.8% | 77 | 6.7 |
| 10 | 5 | 64% | 49.5% | 27 | 5.6 |
| 10 | 15 | 87% | 49.6% | 37 | 5.6 |
| 10 | 30 | 95% | 49.6% | 60 | 5.8 |
| 20 | 5 | 32% | 49.1% | 0 | nan |
| 20 | 15 | 59% | 49.2% | 4 | 2.8 |
| 20 | 30 | 76% | 49.3% | 6 | 2.7 |

Null: the largest |z| across cells on rotated outcomes has median 2.57 and 95th percentile 3.84; the real search's largest |z| is 24.10.
<!-- table:horizons_barrier:end -->

- **The edge is in small moves.** After a 3-standard-deviation drop in the last five minutes, the price touches +5 basis points before -5 in 56.5% of cases against 49.8% unconditionally, in every year. At 10 basis points the same patterns are at 55%; at 20 basis points no cell holds every year and the best deviations are under 3 points. The reversals from extremes are bounces of a few basis points, which is also what the minute-by-minute decomposition in the main report found for the boundary effect.
- **Touch rates are high at small barriers.** Within 15 minutes, 97% of all minutes reach +5 or -5 basis points, so the 5-point question is nearly always decided; within 5 minutes only 64% reach +10 or -10, and 32% reach 20, so at larger barriers "neither" is the common outcome and the direction question only applies to the minority that moved.
- **The search is far outside its null** (largest |z| 24 against a null 95th percentile of 3.8), and the cells that hold are the same families as in the direction tables: sharp drops, oversold RSI, and the 4-hour extremes.
- **A 5-basis-point bounce cannot be traded on spot.** Binance's spot taker fee for a regular account is 0.100% per side (0.075% with the BNB discount; schedule logged in [sources.md](sources.md)), so a round trip costs 15 to 20 basis points against a bounce of 5 and a touch rate of 56.5%: a certain loss. The only instrument where the size works is a binary contract on the window's direction, whose payoff does not scale with the move; whether the edge survives that contract's spread and fee is a question about real quotes, which this repo does not have, and the break-even table in the main report (study 6) is the hypothetical version.

## Inside the window: the next five minutes against the close

A pattern that fires at minute k of a 15-minute window says something about the next few minutes; it need not say the same about where the window closes, and a trader holding a window contract cares about both. Sixteen of the strongest patterns from both libraries, fired at minutes 1 to 10 of a quarter-hour window, scored on the next-5-minute direction and on the window's close against its open, with the agreement between the two and the move a 5-basis-point bounce implies for the contract at that minute (the driftless-market model of the main report's study 24; a model number, not a measured quote).

<!-- table:within_window:start -->
Patterns fired at minute k of a 15-minute window, 2018 to 2026-08: the next-5-minute direction against the window's close against its open. Up-rates with day-block 95% intervals and the deviation from the unconditional rate at those minutes (points); 'agree' is how often the two labels pointed the same way when the pattern fired; the last column is the change in the implied probability of the window contract, in cents on $1, from a 5 bp bounce at that minute under the driftless-market model (a model number, not a measured quote). Years held refers to the sign of the next-5 deviation.

| pattern | minute of window | fires | next 5 min up [95% CI] | deviation | window close up [95% CI] | deviation | agree | years held | implied contract move for a 5 bp bounce |
|---|---|---|---|---|---|---|---|---|---|
| failed breakdown below the 4h low | minutes 1-4 | 40,184 | 51.0% [50.4, 51.6] | +1.2 | 61.7% [60.9, 62.5] | +11.5 | 68% | 7/9 | 8.5c |
| failed breakdown below the 4h low | minutes 5-7 | 30,340 | 50.6% [49.9, 51.4] | +0.4 | 67.1% [66.3, 67.9] | +16.9 | 68% | 5/9 | 8.3c |
| failed breakdown below the 4h low | minutes 8-10 | 30,693 | 51.8% [51.0, 52.6] | +1.4 | 66.4% [65.6, 67.2] | +16.2 | 68% | 9/9 | 8.5c |
| failed breakout above the 4h high | minutes 1-4 | 42,571 | 48.0% [47.4, 48.7] | -1.8 | 37.9% [37.1, 38.6] | -12.4 | 69% | 8/9 | 10.0c |
| failed breakout above the 4h high | minutes 5-7 | 32,730 | 48.5% [47.8, 49.3] | -1.7 | 32.9% [32.1, 33.6] | -17.4 | 67% | 6/9 | 10.3c |
| failed breakout above the 4h high | minutes 8-10 | 33,461 | 48.1% [47.5, 48.8] | -2.3 | 33.0% [32.3, 33.8] | -17.2 | 67% | 9/9 | 10.5c |
| liquidity sweep of the 1h high (took it out, closed back below) | minutes 1-4 | 26,630 | 43.3% [42.6, 43.9] | -6.6 | 55.5% [54.8, 56.2] | +5.2 | 69% | 9/9 | 9.0c |
| liquidity sweep of the 1h high (took it out, closed back below) | minutes 5-7 | 18,338 | 45.3% [44.6, 46.0] | -4.9 | 76.8% [76.0, 77.4] | +26.5 | 63% | 9/9 | 7.1c |
| liquidity sweep of the 1h high (took it out, closed back below) | minutes 8-10 | 17,841 | 46.1% [45.3, 46.8] | -4.4 | 86.8% [86.3, 87.4] | +36.6 | 58% | 9/9 | 5.6c |
| liquidity sweep of the 1h low (took it out, closed back above) | minutes 1-4 | 25,558 | 56.9% [56.3, 57.6] | +7.1 | 44.2% [43.5, 44.8] | -6.1 | 69% | 9/9 | 9.9c |
| liquidity sweep of the 1h low (took it out, closed back above) | minutes 5-7 | 18,448 | 54.3% [53.4, 55.0] | +4.1 | 23.6% [23.0, 24.3] | -26.6 | 64% | 9/9 | 9.3c |
| liquidity sweep of the 1h low (took it out, closed back above) | minutes 8-10 | 18,106 | 54.3% [53.6, 55.1] | +3.9 | 13.3% [12.8, 13.8] | -36.9 | 58% | 9/9 | 8.2c |
| lost the session VWAP in the last 5 minutes after 30+ minutes above | minutes 1-4 | 11,765 | 52.5% [51.3, 53.8] | +2.6 | 33.5% [32.2, 34.8] | -16.7 | 67% | 8/9 | 10.7c |
| lost the session VWAP in the last 5 minutes after 30+ minutes above | minutes 5-7 | 8,362 | 52.6% [51.2, 54.0] | +2.4 | 16.0% [15.0, 17.3] | -34.2 | 60% | 8/9 | 9.3c |
| lost the session VWAP in the last 5 minutes after 30+ minutes above | minutes 8-10 | 7,024 | 53.9% [52.3, 55.3] | +3.4 | 7.8% [6.9, 8.7] | -42.5 | 53% | 9/9 | 7.6c |
| reclaimed the session VWAP in the last 5 minutes after 30+ minutes below | minutes 1-4 | 11,274 | 45.1% [44.0, 46.3] | -4.8 | 67.3% [65.9, 68.7] | +17.1 | 66% | 9/9 | 8.7c |
| reclaimed the session VWAP in the last 5 minutes after 30+ minutes below | minutes 5-7 | 7,992 | 46.0% [44.6, 47.4] | -4.2 | 85.2% [84.0, 86.1] | +34.9 | 58% | 7/9 | 5.9c |
| reclaimed the session VWAP in the last 5 minutes after 30+ minutes below | minutes 8-10 | 6,936 | 46.3% [44.7, 47.8] | -4.2 | 92.4% [91.5, 93.2] | +42.1 | 53% | 8/9 | 3.9c |
| sweep: 5-min move < -3 sd | minutes 1-4 | 5,986 | 57.6% [56.0, 59.3] | +7.8 | 21.3% [19.8, 22.8] | -28.9 | 58% | 9/9 | 5.6c |
| sweep: 5-min move < -3 sd | minutes 5-7 | 5,324 | 58.0% [56.4, 59.5] | +7.8 | 4.0% [3.4, 4.6] | -46.2 | 46% | 9/9 | 1.9c |
| sweep: 5-min move < -3 sd | minutes 8-10 | 4,910 | 57.3% [55.4, 58.8] | +6.8 | 2.7% [2.2, 3.2] | -47.6 | 45% | 8/9 | 1.9c |
| sweep: 5-min move > +3 sd | minutes 1-4 | 6,526 | 43.8% [42.4, 45.3] | -6.0 | 78.5% [77.1, 79.8] | +28.2 | 60% | 9/9 | 3.9c |
| sweep: 5-min move > +3 sd | minutes 5-7 | 5,222 | 44.4% [42.8, 46.0] | -5.8 | 96.6% [96.0, 97.1] | +46.3 | 47% | 9/9 | 0.5c |
| sweep: 5-min move > +3 sd | minutes 8-10 | 4,841 | 44.0% [42.2, 45.7] | -6.5 | 97.2% [96.6, 97.7] | +46.9 | 47% | 8/9 | 0.5c |
| sweep: RSI14 < 25 | minutes 1-4 | 16,959 | 58.6% [57.5, 59.6] | +8.7 | 31.4% [30.2, 32.4] | -18.9 | 63% | 9/9 | 11.7c |
| sweep: RSI14 < 25 | minutes 5-7 | 13,131 | 57.3% [56.2, 58.2] | +7.0 | 12.1% [11.2, 13.0] | -38.1 | 53% | 9/9 | 8.5c |
| sweep: RSI14 < 25 | minutes 8-10 | 13,326 | 57.2% [56.1, 58.4] | +6.7 | 4.4% [3.9, 4.9] | -45.8 | 47% | 9/9 | 6.5c |
| sweep: RSI14 > 75 | minutes 1-4 | 19,316 | 42.5% [41.6, 43.5] | -7.4 | 68.7% [67.7, 69.7] | +18.4 | 65% | 9/9 | 8.5c |
| sweep: RSI14 > 75 | minutes 5-7 | 14,381 | 44.2% [43.1, 45.2] | -6.1 | 89.0% [88.2, 89.8] | +38.8 | 53% | 9/9 | 3.8c |
| sweep: RSI14 > 75 | minutes 8-10 | 14,439 | 44.2% [42.9, 45.3] | -6.3 | 96.0% [95.6, 96.4] | +45.7 | 48% | 9/9 | 1.6c |
| sweep: range position < 0.05 | minutes 1-4 | 29,194 | 57.0% [56.2, 57.6] | +7.1 | 39.8% [39.0, 40.7] | -10.3 | 68% | 9/9 | 10.3c |
| sweep: range position < 0.05 | minutes 5-7 | 21,956 | 54.9% [54.1, 55.7] | +4.7 | 23.4% [22.8, 24.1] | -26.7 | 63% | 9/9 | 9.4c |
| sweep: range position < 0.05 | minutes 8-10 | 22,330 | 53.8% [52.9, 54.7] | +3.4 | 13.1% [12.4, 13.8] | -37.1 | 58% | 9/9 | 8.6c |
| sweep: range position > 0.95 | minutes 1-4 | 40,789 | 43.9% [43.3, 44.5] | -6.0 | 60.0% [59.2, 60.7] | +9.8 | 68% | 9/9 | 8.8c |
| sweep: range position > 0.95 | minutes 5-7 | 29,821 | 46.2% [45.4, 46.9] | -4.1 | 76.2% [75.5, 76.9] | +26.0 | 64% | 9/9 | 7.0c |
| sweep: range position > 0.95 | minutes 8-10 | 30,067 | 46.7% [45.9, 47.5] | -3.7 | 86.2% [85.6, 86.7] | +36.0 | 59% | 9/9 | 5.5c |
| volume climax at a new 1h high (hour's largest volume) | minutes 1-4 | 9,157 | 44.2% [43.2, 45.4] | -5.6 | 70.2% [69.2, 71.2] | +19.9 | 64% | 9/9 | 6.3c |
| volume climax at a new 1h high (hour's largest volume) | minutes 5-7 | 6,046 | 45.9% [44.6, 47.4] | -4.3 | 85.2% [84.2, 86.1] | +34.9 | 58% | 9/9 | 4.1c |
| volume climax at a new 1h high (hour's largest volume) | minutes 8-10 | 5,480 | 46.5% [45.2, 47.8] | -4.0 | 91.7% [91.0, 92.5] | +41.4 | 54% | 9/9 | 3.0c |
| volume climax at a new 1h low (hour's largest volume) | minutes 1-4 | 9,761 | 56.9% [55.9, 57.9] | +7.1 | 30.9% [29.9, 32.0] | -19.4 | 64% | 9/9 | 7.9c |
| volume climax at a new 1h low (hour's largest volume) | minutes 5-7 | 6,571 | 55.2% [53.9, 56.5] | +5.0 | 15.5% [14.6, 16.5] | -34.7 | 57% | 8/9 | 6.4c |
| volume climax at a new 1h low (hour's largest volume) | minutes 8-10 | 6,356 | 56.3% [55.0, 57.6] | +5.8 | 9.1% [8.4, 9.9] | -41.2 | 52% | 9/9 | 5.1c |
| wick rejection at the 4h high | minutes 1-4 | 13,424 | 42.5% [41.6, 43.4] | -7.3 | 53.9% [52.9, 54.8] | +3.6 | 69% | 9/9 | 8.7c |
| wick rejection at the 4h high | minutes 5-7 | 9,025 | 45.1% [44.0, 46.2] | -5.1 | 76.6% [75.7, 77.6] | +26.4 | 63% | 9/9 | 6.4c |
| wick rejection at the 4h high | minutes 8-10 | 8,684 | 45.1% [43.9, 46.1] | -5.3 | 86.7% [85.9, 87.5] | +36.4 | 57% | 9/9 | 4.8c |
| wick rejection at the 4h low | minutes 1-4 | 11,944 | 57.8% [56.9, 58.8] | +8.0 | 46.3% [45.2, 47.4] | -4.0 | 69% | 9/9 | 9.0c |
| wick rejection at the 4h low | minutes 5-7 | 8,456 | 55.9% [54.8, 57.2] | +5.8 | 24.5% [23.4, 25.5] | -25.7 | 63% | 9/9 | 8.1c |
| wick rejection at the 4h low | minutes 8-10 | 8,359 | 54.5% [53.3, 55.7] | +4.1 | 13.5% [12.8, 14.3] | -36.7 | 58% | 8/9 | 7.1c |

By minute of the window, firing-weighted over the patterns: the mean absolute deviation of the next-5 call and of the close call, and the mean implied contract move.

| minute of window | next-5 deviation (points) | close deviation (points) | implied move for 5 bp |
|---|---|---|---|
| minutes 1-4 | 5.3 | 12.1 | 9.1c |
| minutes 5-7 | 3.9 | 27.2 | 7.6c |
| minutes 8-10 | 3.8 | 33.2 | 6.7c |
<!-- table:within_window:end -->

- **The two calls disagree, mechanically.** After a 3-standard-deviation drop at minutes 5 to 7, the next five minutes are up 58% of the time (every year), but the window closes above its open only 4% of the time: the drop that fired the pattern already happened inside the window. The close column's large deviations are the lead, not forecasting skill, and the two labels agree less than half the time for the sharp-move patterns after minute 4.
- **The bounce is real at every minute; its value in the contract is not.** The same 5-basis-point bounce moves the contract's implied probability by about 2 cents when the contract is already near zero (a sharp drop late in the window) and by 9 to 12 cents when the pattern fires in minutes 1 to 4 with the contract still near the middle (RSI below 25: 58.6% up over the next five minutes, 11.7 cents; a liquidity sweep of the hourly low: 56.9%, 9.9 cents; a wick rejection at the 4-hour low: 57.8%, 9.0 cents).
- **The continuation names point the two ways at once for a good reason.** A VWAP reclaim in minutes 1 to 4 is followed by a down move 55% of the time over the next five minutes (the pullback) while the window closes up 67% of the time, because reclaiming VWAP early in a window means the window is already well up.
- **What this means for a live view:** show the short-horizon probability per active pattern next to the contract's current level, and keep the window call separate. The short call is where the patterns carry information; the window call is mostly the lead, which the market already prices.

## Each cell as a small meta-analysis

Nine yearly estimates of a cell are nine noisy readings of an effect that may differ by year. A random-effects pooling (DerSimonian-Laird) separates the two: tau is how much the true effect moves from year to year, I-squared is the share of the yearly variation that is real change rather than noise, and the shrunken latest-year value pulls 2026's reading toward the pool by an amount set by the cell's own consistency.

<!-- table:horizons_shrink:start -->
Each cell pooled across years with a random-effects model (DerSimonian-Laird): the pooled deviation in points with its standard error, tau (the between-year standard deviation of the true effect, points), I-squared (the share of the yearly variation that is real change rather than noise), and for the latest year the raw deviation, the shrunken deviation, and the weight the shrunken value puts on that year's own data. The 30 cells with the largest pooled deviation.

| pattern | horizon (min) | pooled (se) | tau | I-squared | latest year | raw | shrunk | weight on own year |
|---|---|---|---|---|---|---|---|---|
| sweep: range position < 0.05 | 30 | +9.9 (1.3) | 3.6 | 92% | 2026 | +7.7 | +7.9 | 0.91 |
| price at 4h low (rangepos <= 0.02) | 30 | +9.8 (1.3) | 3.7 | 90% | 2026 | +7.7 | +7.9 | 0.88 |
| sweep: range position > 0.95 | 30 | -9.5 (1.0) | 2.7 | 88% | 2026 | -8.4 | -8.6 | 0.83 |
| price at 4h high (rangepos >= 0.98) | 30 | -9.4 (0.9) | 2.5 | 82% | 2026 | -8.5 | -8.8 | 0.73 |
| price at 4h low (rangepos <= 0.02) | 15 | +9.4 (1.3) | 3.6 | 91% | 2026 | +7.5 | +7.7 | 0.90 |
| price at 4h low (rangepos <= 0.02) | 10 | +9.3 (1.2) | 3.5 | 92% | 2026 | +6.7 | +6.9 | 0.92 |
| sweep: range position < 0.1 | 30 | +9.2 (1.1) | 3.3 | 93% | 2026 | +8.1 | +8.2 | 0.91 |
| sweep: range position < 0.05 | 15 | +8.8 (1.1) | 3.3 | 93% | 2026 | +6.7 | +6.9 | 0.92 |
| sweep: range position > 0.90 | 30 | -8.6 (0.9) | 2.6 | 91% | 2026 | -7.9 | -8.0 | 0.88 |
| sweep: range position < 0.05 | 10 | +8.5 (1.1) | 3.3 | 94% | 2026 | +6.0 | +6.1 | 0.94 |
| sweep: range position > 0.95 | 15 | -8.4 (0.6) | 1.4 | 76% | 2026 | -8.0 | -8.1 | 0.73 |
| price at 4h high (rangepos >= 0.98) | 15 | -8.3 (0.6) | 1.4 | 64% | 2026 | -8.2 | -8.2 | 0.58 |
| sweep: range position < 0.15 | 30 | +8.2 (1.0) | 2.8 | 93% | 2026 | +7.2 | +7.3 | 0.90 |
| sweep: range position < 0.1 | 15 | +8.1 (0.9) | 2.6 | 92% | 2026 | +7.2 | +7.3 | 0.90 |
| sweep: RSI14 < 25 | 5 | +8.1 (1.2) | 3.4 | 93% | 2026 | +5.1 | +5.3 | 0.91 |
| price at 4h low (rangepos <= 0.02) | 5 | +8.1 (1.2) | 3.4 | 93% | 2026 | +5.1 | +5.3 | 0.93 |
| sweep: RSI14 < 20 | 3 | +8.1 (1.3) | 3.5 | 85% | 2026 | +5.6 | +6.0 | 0.84 |
| sweep: RSI14 < 25 | 3 | +8.0 (1.2) | 3.4 | 95% | 2026 | +5.8 | +5.9 | 0.94 |
| sweep: RSI14 < 25 | 10 | +8.0 (0.9) | 2.4 | 84% | 2026 | +6.4 | +6.7 | 0.83 |
| sweep: range position > 0.85 | 30 | -8.0 (0.8) | 2.4 | 91% | 2026 | -6.9 | -7.0 | 0.90 |
| price at 4h high (rangepos >= 0.98) | 10 | -7.9 (0.7) | 1.7 | 77% | 2026 | -7.9 | -7.9 | 0.69 |
| sweep: 15-min move < -3 sd | 3 | +7.9 (1.0) | 2.1 | 56% | 2026 | +8.0 | +7.9 | 0.46 |
| sweep: RSI60 < 45 | 30 | +7.8 (0.8) | 2.4 | 92% | 2026 | +6.1 | +6.3 | 0.91 |
| RSI14 below 30 | 10 | +7.8 (0.7) | 2.1 | 91% | 2026 | +6.4 | +6.5 | 0.89 |
| sweep: RSI14 < 30 | 10 | +7.8 (0.7) | 2.1 | 91% | 2026 | +6.4 | +6.5 | 0.89 |
| sweep: RSI14 < 30 | 5 | +7.8 (1.0) | 2.8 | 96% | 2026 | +5.0 | +5.2 | 0.95 |
| RSI14 below 30 | 5 | +7.8 (1.0) | 2.8 | 96% | 2026 | +5.0 | +5.2 | 0.95 |
| sweep: RSI60 > 55 | 30 | -7.7 (0.8) | 2.4 | 93% | 2026 | -6.1 | -6.3 | 0.91 |
| sweep: RSI60 < 40 | 30 | +7.6 (1.0) | 2.8 | 83% | 2026 | +8.7 | +8.5 | 0.80 |
| sweep: RSI14 < 20 | 5 | +7.6 (1.2) | 3.0 | 77% | 2026 | +3.9 | +5.0 | 0.71 |

Over all 642 cells: median tau 1.3 points, median I-squared 86%, median weight on the latest year's own data 0.81. A high I-squared with a stable sign (the usual case here) means the size of a cell changes from year to year while its direction does not, so the pooled value is a long-run average and the shrunken latest-year value is the better guide to the present.
<!-- table:horizons_shrink:end -->

The pattern is the same as the eras: I-squared is high (median 86%) with signs that never change, so the size of a cell genuinely differs between years and the pooled value is a long-run average, not a forecast. The weight on 2026's own data is high (median 0.81) because each year's estimate is precise, so the shrunken 2026 values barely move from the raw ones; for the strongest cells they sit at 7 to 9 points, below their nine-year pooled 9 to 10. The shrunken latest-year column is the better guide to the present.

## Regimes

Two questions: when were the bull and bear markets, and does any of the above depend on them? Dating uses the threshold rule of Lunde and Timmermann (a bull ends when the price falls 15% from its peak, a bear when it rises 20% from its trough), which places the turn at the peak or trough and so uses the future; it describes history and cannot drive a live rule. For a label known at the time, a three-state hidden Markov model on daily return and realised volatility is fit on all earlier years and run forward only, and the previous day's state labels every minute of the next day.

<!-- table:regimes:start -->
Bull and bear phases on daily closes, 2017-08 to 2026-08, by the threshold rule: a bull ends when the price falls 15% from its running peak, a bear ends when it rises 20% from its running trough; phases are dated at the peak and trough, so this table uses the future and describes history only.

| start | end | phase | days | return | largest move against |
|---|---|---|---|---|---|
| 2017-08-19 | 2017-09-02 | bull | 14 | +18% | -3% |
| 2017-09-02 | 2017-09-15 | bear | 13 | -34% | +14% |
| 2017-09-15 | 2017-11-05 | bull | 51 | +131% | -11% |
| 2017-11-05 | 2017-11-13 | bear | 8 | -21% | +5% |
| 2017-11-13 | 2017-12-20 | bull | 22 | +198% | -2% |
| 2017-12-20 | 2017-12-31 | bear | 11 | -28% | +18% |
| 2017-12-31 | 2018-01-07 | bull | 7 | +37% | -2% |
| 2018-01-07 | 2018-02-06 | bear | 30 | -59% | +17% |
| 2018-02-06 | 2018-03-05 | bull | 25 | +66% | -14% |
| 2018-03-05 | 2018-04-07 | bear | 33 | -43% | +14% |
| 2018-04-07 | 2018-05-06 | bull | 29 | +49% | -8% |
| 2018-05-06 | 2018-06-29 | bear | 53 | -41% | +9% |
| 2018-06-29 | 2018-07-25 | bull | 25 | +43% | -8% |
| 2018-07-25 | 2018-12-16 | bear | 144 | -62% | +20% |
| 2018-12-16 | 2018-12-21 | bull | 5 | +26% | +0% |
| 2018-12-21 | 2019-02-08 | bear | 49 | -16% | +12% |
| 2019-02-08 | 2019-06-27 | bull | 138 | +285% | -13% |
| 2019-06-27 | 2019-07-17 | bear | 20 | -28% | +18% |
| 2019-07-17 | 2019-08-09 | bull | 23 | +27% | -12% |
| 2019-08-09 | 2019-10-25 | bear | 76 | -38% | +12% |
| 2019-10-25 | 2019-10-28 | bull | 3 | +29% | +0% |
| 2019-10-28 | 2019-12-18 | bear | 51 | -30% | +12% |
| 2019-12-18 | 2020-02-15 | bull | 59 | +56% | -7% |
| 2020-02-15 | 2020-03-13 | bear | 27 | -54% | +7% |
| 2020-03-13 | 2020-08-18 | bull | 158 | +156% | -14% |
| 2020-08-18 | 2020-09-09 | bear | 22 | -18% | +5% |
| 2020-09-09 | 2021-01-09 | bull | 122 | +301% | -11% |
| 2021-01-09 | 2021-01-28 | bear | 19 | -25% | +15% |
| 2021-01-28 | 2021-02-22 | bull | 25 | +89% | -3% |
| 2021-02-22 | 2021-03-01 | bear | 7 | -21% | +2% |
| 2021-03-01 | 2021-03-14 | bull | 13 | +36% | -4% |
| 2021-03-14 | 2021-03-26 | bear | 12 | -16% | +6% |
| 2021-03-26 | 2021-04-14 | bull | 19 | +24% | -5% |
| 2021-04-14 | 2021-06-09 | bear | 56 | -47% | +20% |
| 2021-06-09 | 2021-06-15 | bull | 6 | +21% | -5% |
| 2021-06-15 | 2021-07-21 | bear | 36 | -26% | +14% |
| 2021-07-21 | 2021-09-07 | bull | 48 | +77% | -9% |
| 2021-09-07 | 2021-09-22 | bear | 15 | -23% | +8% |
| 2021-09-22 | 2021-11-09 | bull | 48 | +66% | -11% |
| 2021-11-09 | 2022-01-23 | bear | 75 | -48% | +10% |
| 2022-01-23 | 2022-02-16 | bull | 24 | +27% | -5% |
| 2022-02-16 | 2022-02-22 | bear | 6 | -17% | +0% |
| 2022-02-22 | 2022-03-30 | bull | 36 | +28% | -15% |
| 2022-03-30 | 2022-06-19 | bear | 81 | -60% | +11% |
| 2022-06-19 | 2022-08-14 | bull | 56 | +29% | -11% |
| 2022-08-14 | 2022-11-22 | bear | 100 | -35% | +19% |
| 2022-11-22 | 2023-02-21 | bull | 91 | +57% | -9% |
| 2023-02-21 | 2023-03-11 | bear | 18 | -19% | +2% |
| 2023-03-11 | 2023-04-15 | bull | 35 | +51% | -4% |
| 2023-04-15 | 2023-06-15 | bear | 61 | -18% | +8% |
| 2023-06-15 | 2023-07-14 | bull | 29 | +25% | -4% |
| 2023-07-14 | 2023-09-12 | bear | 60 | -20% | +7% |
| 2023-09-12 | 2024-01-09 | bull | 119 | +87% | -7% |
| 2024-01-09 | 2024-01-23 | bear | 14 | -16% | +3% |
| 2024-01-23 | 2024-03-14 | bull | 51 | +85% | -7% |
| 2024-03-14 | 2024-05-02 | bear | 49 | -20% | +16% |
| 2024-05-02 | 2024-05-21 | bull | 19 | +22% | -5% |
| 2024-05-21 | 2024-07-08 | bear | 48 | -22% | +5% |
| 2024-07-08 | 2024-07-29 | bull | 21 | +22% | -4% |
| 2024-07-29 | 2024-09-07 | bear | 40 | -21% | +19% |
| 2024-09-07 | 2025-01-22 | bull | 137 | +97% | -13% |
| 2025-01-22 | 2025-04-09 | bear | 77 | -28% | +12% |
| 2025-04-09 | 2025-10-07 | bull | 181 | +63% | -12% |
| 2025-10-07 | 2026-02-06 | bear | 122 | -50% | +14% |
| 2026-02-06 | 2026-05-11 | bull | 94 | +31% | -12% |
| 2026-05-11 | 2026-07-01 | bear | 51 | -29% | +9% |
| 2026-07-01 | 2026-09-01 | bull (open) | 62 | +34% | -6% |

The same rule with wider thresholds (a 30% fall ends a bull, a 40% rise ends a bear), for the major cycles.

| start | end | phase | days | return | largest move against |
|---|---|---|---|---|---|
| 2017-08-19 | 2017-09-02 | bull | 14 | +18% | -3% |
| 2017-09-02 | 2017-09-15 | bear | 13 | -34% | +14% |
| 2017-09-15 | 2017-12-20 | bull | 81 | +442% | -21% |
| 2017-12-20 | 2018-02-06 | bear | 48 | -60% | +37% |
| 2018-02-06 | 2018-03-05 | bull | 25 | +66% | -14% |
| 2018-03-05 | 2018-04-07 | bear | 33 | -43% | +14% |
| 2018-04-07 | 2018-05-06 | bull | 29 | +49% | -8% |
| 2018-05-06 | 2018-06-29 | bear | 53 | -41% | +9% |
| 2018-06-29 | 2018-07-25 | bull | 25 | +43% | -8% |
| 2018-07-25 | 2018-12-16 | bear | 144 | -62% | +20% |
| 2018-12-16 | 2019-06-27 | bull | 192 | +308% | -16% |
| 2019-06-27 | 2019-12-18 | bear | 173 | -49% | +29% |
| 2019-12-18 | 2020-02-15 | bull | 59 | +56% | -7% |
| 2020-02-15 | 2020-03-13 | bear | 27 | -54% | +7% |
| 2020-03-13 | 2021-04-14 | bull | 397 | +1224% | -25% |
| 2021-04-14 | 2021-07-21 | bear | 98 | -53% | +21% |
| 2021-07-21 | 2021-11-09 | bull | 111 | +127% | -23% |
| 2021-11-09 | 2022-11-22 | bear | 378 | -77% | +35% |
| 2022-11-22 | 2025-10-07 | bull | 1050 | +690% | -28% |
| 2025-10-07 | 2026-09-01 | bear (open) | 329 | -37% | +37% |

Hidden Markov model with 3 states on daily log return and log realised volatility, fit walk-forward on all earlier years and run forward only (the state of a day uses that day and earlier ones). States are named by their training-year mean return and volatility; the names can differ slightly between years.

| year | state 0 | state 2 | state 1 |
|---|---|---|---|
| 2019 | low vol, flat | mid vol, flat | high vol, down |
| 2020 | high vol, flat | mid vol, flat | low vol, flat |
| 2021 | high vol, flat | mid vol, flat | low vol, flat |
| 2022 | low vol, flat | mid vol, flat | high vol, flat |
| 2023 | low vol, flat | mid vol, flat | high vol, down |
| 2024 | low vol, flat | mid vol, flat | high vol, flat |
| 2025 | low vol, flat | mid vol, flat | high vol, flat |
| 2026 | low vol, flat | mid vol, flat | high vol, flat |

Fingerprint by dated phase (minutes inside bull and bear phases). Tail share is the share of minutes moving more than four of that regime's standard deviations; the reversal rule is 'call the opposite of the previous 15 minutes' on the quarter-hour grid.

| regime | days | 1-min vol (bp) | daily vol (bp) | volume per min | trades per min | taker imbalance | 1-min autocorr | 15-min autocorr | tail share | peak hour (UTC) | weekend/weekday vol | reversal rule [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bull | 1796 | 10.69 | 406 | 40.4 | 1428 | -0.5% | -0.077 | -0.003 | 0.91% | 14:00 | 0.84 | 52.44% [52.20, 52.66] |
| bear | 1484 | 11.54 | 438 | 42.6 | 1382 | -0.9% | -0.020 | -0.018 | 0.90% | 14:00 | 0.81 | 52.46% [52.21, 52.72] |

Fingerprint by HMM state (the previous day's filtered state, known at the time).

| regime | days | 1-min vol (bp) | daily vol (bp) | volume per min | trades per min | taker imbalance | 1-min autocorr | 15-min autocorr | tail share | peak hour (UTC) | weekend/weekday vol | reversal rule [95% CI] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| high vol, down | 11 | 16.60 | 630 | 173.9 | 3641 | -0.3% | +0.029 | -0.061 | 0.74% | 16:00 | 0.94 | 53.09% [51.62, 54.56] |
| high vol, flat | 178 | 18.56 | 704 | 78.4 | 1847 | -1.9% | +0.019 | -0.015 | 0.65% | 13:00 | 0.82 | 52.25% [51.62, 52.87] |
| low vol, flat | 1333 | 6.08 | 231 | 35.3 | 1352 | -0.6% | +0.002 | -0.004 | 0.63% | 15:00 | 0.76 | 52.76% [52.51, 53.02] |
| mid vol, flat | 1276 | 9.49 | 360 | 49.7 | 1867 | -1.1% | -0.003 | -0.007 | 0.59% | 14:00 | 0.83 | 52.31% [52.07, 52.57] |

The 24 strongest conditional cells (from horizons.md) within each HMM state, 2018 onward: deviation of the up-rate from the state's own unconditional rate, points, day-block 95% interval, firings.

| pattern | horizon (min) | all states | high vol, down | high vol, flat | low vol, flat | mid vol, flat |
|---|---|---|---|---|---|---|
| sweep: range position > 0.95 | 30 | -8.7 | -16.0 [-28.6, -9.5] n=335 | -12.4 [-14.9, -10.0] n=8,659 | -7.9 [-8.9, -6.6] n=67,057 | -8.2 [-9.2, -7.2] n=62,732 |
| price at 4h high (rangepos >= 0.98) | 30 | -8.7 |  | -13.1 [-16.4, -9.9] n=3,340 | -7.8 [-9.1, -6.4] n=29,907 | -8.5 [-9.8, -7.3] n=25,839 |
| sweep: range position < 0.05 | 30 | +8.3 |  | +13.0 [+10.8, +15.4] n=6,749 | +7.2 [+6.0, +8.6] n=48,989 | +8.4 [+7.2, +9.6] n=43,402 |
| price at 4h low (rangepos <= 0.02) | 30 | +8.3 |  | +14.5 [+12.0, +17.4] n=2,647 | +7.1 [+5.6, +8.7] n=21,816 | +8.8 [+7.3, +10.2] n=17,286 |
| price at 4h low (rangepos <= 0.02) | 15 | +8.0 |  | +11.3 [+8.6, +14.4] n=2,647 | +7.4 [+6.2, +8.7] n=21,816 | +8.4 [+7.2, +9.7] n=17,286 |
| price at 4h low (rangepos <= 0.02) | 10 | +7.9 |  | +10.7 [+8.2, +13.4] n=2,647 | +7.2 [+6.1, +8.2] n=21,816 | +8.3 [+7.2, +9.4] n=17,286 |
| sweep: range position < 0.1 | 30 | +7.8 | +13.4 [+6.9, +22.8] n=672 | +10.6 [+8.7, +12.5] n=15,284 | +7.0 [+6.0, +8.0] n=107,266 | +7.6 [+6.5, +8.6] n=100,309 |
| sweep: range position > 0.95 | 15 | -7.7 | -11.6 [-22.6, -3.9] n=335 | -9.3 [-11.3, -7.5] n=8,659 | -7.2 [-8.0, -6.3] n=67,057 | -7.6 [-8.5, -6.7] n=62,732 |
| price at 4h high (rangepos >= 0.98) | 15 | -7.7 |  | -10.8 [-13.4, -8.5] n=3,340 | -7.1 [-8.1, -5.9] n=29,907 | -7.8 [-8.9, -6.9] n=25,839 |
| sweep: range position > 0.90 | 30 | -7.7 | -14.7 [-24.8, -8.1] n=816 | -9.3 [-11.6, -7.0] n=20,354 | -7.1 [-8.0, -6.2] n=144,698 | -7.2 [-8.0, -6.3] n=142,633 |
| sweep: 15-min move < -3 sd | 3 | +7.5 |  | +9.8 [+4.8, +15.0] n=619 | +6.8 [+4.8, +8.9] n=5,188 | +8.8 [+6.9, +10.5] n=4,488 |
| sweep: 5-min move < -3 sd | 3 | +7.5 |  | +3.8 [-0.0, +7.5] n=1,166 | +8.2 [+7.0, +9.4] n=10,009 | +8.2 [+6.9, +9.5] n=9,000 |
| sweep: range position < 0.05 | 15 | +7.5 |  | +9.0 [+7.0, +11.5] n=6,749 | +6.9 [+5.9, +8.0] n=48,989 | +7.7 [+6.6, +8.7] n=43,402 |
| sweep: RSI14 < 25 | 10 | +7.4 |  | +7.0 [+3.9, +10.5] n=2,924 | +7.2 [+6.0, +8.2] n=31,862 | +8.3 [+7.3, +9.5] n=21,579 |
| sweep: RSI14 < 25 | 5 | +7.4 |  | +6.5 [+4.0, +9.2] n=2,924 | +6.8 [+5.7, +7.8] n=31,862 | +8.7 [+7.7, +9.7] n=21,579 |
| price at 4h high (rangepos >= 0.98) | 10 | -7.2 |  | -9.7 [-12.3, -7.7] n=3,340 | -6.3 [-7.4, -5.3] n=29,907 | -8.0 [-9.0, -7.1] n=25,839 |
| sweep: RSI14 < 25 | 3 | +7.2 |  | +7.7 [+5.7, +9.9] n=2,924 | +6.5 [+5.5, +7.3] n=31,862 | +8.6 [+7.8, +9.6] n=21,579 |
| sweep: RSI14 < 30 | 10 | +7.2 | +11.3 [+5.0, +18.2] n=519 | +7.5 [+5.7, +9.3] n=8,618 | +6.9 [+6.2, +7.5] n=79,821 | +7.7 [+7.1, +8.5] n=61,010 |
| RSI14 below 30 | 10 | +7.2 | +11.3 [+5.0, +18.2] n=519 | +7.5 [+5.7, +9.3] n=8,618 | +6.9 [+6.2, +7.5] n=79,821 | +7.7 [+7.1, +8.5] n=61,010 |
| RSI14 below 30 | 5 | +7.2 | +7.9 [-1.3, +16.4] n=519 | +6.8 [+5.3, +8.5] n=8,618 | +6.6 [+6.0, +7.2] n=79,821 | +8.0 [+7.5, +8.6] n=61,010 |
| sweep: RSI14 < 30 | 5 | +7.2 | +7.9 [-1.3, +16.4] n=519 | +6.8 [+5.3, +8.5] n=8,618 | +6.6 [+6.0, +7.2] n=79,821 | +8.0 [+7.5, +8.6] n=61,010 |
| sweep: RSI14 < 20 | 3 | +7.1 |  | +8.6 [+5.0, +12.5] n=742 | +6.1 [+4.7, +7.6] n=12,040 | +9.7 [+8.1, +11.3] n=6,444 |
| sweep: range position < 0.05 | 10 | +7.1 |  | +8.8 [+6.8, +10.8] n=6,749 | +6.5 [+5.6, +7.5] n=48,989 | +7.4 [+6.5, +8.3] n=43,402 |
| sweep: RSI60 < 40 | 30 | +7.1 | +16.4 [+10.9, +24.1] n=438 | +11.1 [+7.9, +14.3] n=6,538 | +7.6 [+6.1, +8.8] n=60,809 | +6.8 [+5.4, +8.2] n=49,620 |
<!-- table:regimes:end -->

- **Bitcoin's bull and bear phases are short.** At the standard thresholds there are 67 dated phases in nine years, most of them two to twenty weeks; the wider thresholds (30% and 40%) reduce them to 28 and recover the familiar cycles (the 2018 bear, the March 2020 to April 2021 bull, the 2022 bear).
- **Bull and bear look the same from inside a minute.** Minutes in dated bull and bear phases have nearly identical microstructure: 10.7 against 11.5 basis points of one-minute volatility, the same peak hour (14:00 UTC), the same tail share, the same weekend ratio, and the same reversal-rule accuracy (52.4% in both). Direction at the scale of months leaves almost no fingerprint at the scale of minutes.
- **The states the HMM finds are volatility states, not direction states.** In every year the three states are named by volatility and almost all are "flat" in mean return, which matches the published Bitcoin fits. The low-volatility state covers about 1,330 days and the high-volatility states about 190.
- **The conditional effects appeared to scale with volatility, and the appearance is the era.** Pooled over all years, the 4-hour-extreme reversals are 12 to 16 points in the high-volatility state and 7 to 8 points in the low- and mid-volatility states. But the high-volatility days sit almost entirely in 2020 to 2022 (130 of 189 days), when every cell was larger. Scored inside each era (the table below), the high-over-low ratio falls from 1.38 to 0.93 across the 24 strongest cells, and the 2019 era, with four high-volatility days, has the largest deviations of all (13 to 17 points in the low-volatility state). The sign never changes; the size follows the year, not the day's volatility state. The trailing 60-minute volatility does not scale the cells either (the volatility table in the cells section below). Neither bull and bear nor volatility is a regime variable for these cells; the calendar is.

<!-- table:regimes_era:start -->
The 24 strongest conditional cells by the daily HMM's volatility state inside each era, 2019 to 2026-08 (2019 is the first year the walk-forward HMM scores; 'high vol, down' days are counted as high). Deviation of the up-rate from that state's own rate within the era, points, day-block 95% interval, firings; blank where a state fired fewer than 300 times in the era. The ratio columns divide the high-volatility deviation by the low-volatility one: over all years (the regime study's comparison, which mixes eras) and pooled within eras (each era's two deviations weighted by the smaller firing count).

| pattern | horizon (min) | 2019 low | 2019 mid | 2019 high | 2020-21 low | 2020-21 mid | 2020-21 high | 2022-23 low | 2022-23 mid | 2022-23 high | 2024-26 low | 2024-26 mid | 2024-26 high | high/low, all years | high/low, within eras |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sweep: range position > 0.95 | 30 | -13.8 [-16.2, -11.6] n=10,216 | -9.8 [-14.7, -6.0] n=3,040 | n=187 | -13.2 [-16.2, -10.5] n=6,162 | -8.7 [-10.4, -7.2] n=21,613 | -13.4 [-16.1, -10.6] n=6,766 | -7.2 [-9.2, -5.5] n=14,596 | -8.3 [-10.7, -6.0] n=10,375 | -12.5 [-19.9, -5.0] n=883 | -5.3 [-7.1, -3.7] n=36,083 | -7.6 [-9.2, -6.0] n=27,704 | -8.1 [-15.1, -2.8] n=1,158 | 1.59 | 1.10 |
| price at 4h high (rangepos >= 0.98) | 30 | -14.2 [-17.0, -11.5] n=4,132 | -10.7 [-15.4, -6.3] n=1,333 | n=88 | -12.1 [-15.7, -8.5] n=2,523 | -9.2 [-11.2, -7.1] n=8,733 | -13.8 [-17.1, -10.3] n=2,605 | -7.3 [-9.4, -5.0] n=6,128 | -9.2 [-11.9, -6.4] n=3,420 | n=288 | -5.5 [-7.3, -3.8] n=17,124 | -7.6 [-9.4, -5.8] n=12,353 | -10.7 [-20.3, -3.4] n=504 | 1.69 | 1.21 |
| sweep: range position < 0.05 | 30 | +15.3 [+12.5, +18.1] n=4,661 | +17.9 [+13.4, +22.5] n=1,154 | n=100 | +13.3 [+9.1, +17.3] n=2,831 | +11.8 [+9.7, +13.8] n=11,457 | +15.5 [+12.3, +18.2] n=4,223 | +9.5 [+7.3, +11.9] n=10,856 | +7.1 [+4.4, +10.4] n=9,335 | +9.3 [+5.1, +13.5] n=1,666 | +4.9 [+3.4, +6.4] n=30,641 | +6.7 [+4.8, +8.5] n=21,456 | +9.4 [+3.2, +18.0] n=1,033 | 1.80 | 1.18 |
| price at 4h low (rangepos <= 0.02) | 30 | +16.8 [+13.4, +21.2] n=1,842 | +14.4 [+9.4, +19.3] n=425 | n=40 | +11.3 [+6.6, +15.8] n=1,042 | +12.5 [+10.1, +14.8] n=4,175 | +17.7 [+14.6, +20.9] n=1,622 | +9.7 [+6.9, +12.4] n=4,321 | +7.0 [+3.6, +10.9] n=3,200 | +10.0 [+5.4, +14.6] n=636 | +5.1 [+3.2, +7.0] n=14,611 | +7.5 [+5.2, +9.6] n=9,486 | +10.6 [+5.2, +20.0] n=447 | 2.04 | 1.47 |
| price at 4h low (rangepos <= 0.02) | 15 | +14.0 [+10.5, +18.2] n=1,842 | +9.4 [+4.7, +14.6] n=425 | n=40 | +13.3 [+8.4, +18.0] n=1,042 | +13.1 [+10.8, +15.2] n=4,175 | +15.4 [+12.4, +18.8] n=1,622 | +9.2 [+6.9, +11.3] n=4,321 | +8.6 [+6.0, +11.7] n=3,200 | +5.5 [+0.8, +11.5] n=636 | +6.0 [+4.5, +7.4] n=14,611 | +6.2 [+4.4, +7.9] n=9,486 | +4.2 [-4.7, +15.6] n=447 | 1.50 | 0.96 |
| price at 4h low (rangepos <= 0.02) | 10 | +14.2 [+11.0, +18.1] n=1,842 | +15.5 [+11.0, +20.7] n=425 | n=40 | +14.8 [+11.2, +18.2] n=1,042 | +12.3 [+10.3, +14.5] n=4,175 | +13.3 [+10.9, +16.0] n=1,622 | +8.6 [+6.2, +10.8] n=4,321 | +9.1 [+6.8, +12.0] n=3,200 | +8.5 [+3.3, +14.0] n=636 | +5.6 [+4.2, +6.9] n=14,611 | +6.0 [+4.4, +7.4] n=9,486 | +4.3 [-4.0, +14.1] n=447 | 1.48 | 0.90 |
| sweep: range position < 0.1 | 30 | +13.3 [+11.2, +15.6] n=12,626 | +15.1 [+11.6, +19.1] n=3,199 | n=242 | +12.5 [+8.9, +15.8] n=7,180 | +9.5 [+7.8, +11.3] n=28,745 | +11.8 [+9.5, +14.2] n=9,869 | +8.5 [+6.4, +10.6] n=26,545 | +7.4 [+5.1, +10.0] n=24,030 | +8.4 [+4.7, +12.9] n=3,627 | +4.5 [+3.4, +6.0] n=60,915 | +5.9 [+4.5, +7.4] n=44,335 | +9.3 [+4.6, +15.8] n=2,218 | 1.54 | 1.04 |
| sweep: range position > 0.95 | 15 | -10.7 [-12.6, -8.7] n=10,216 | -7.4 [-12.0, -4.0] n=3,040 | n=187 | -9.8 [-12.1, -7.2] n=6,162 | -7.8 [-9.2, -6.6] n=21,613 | -9.7 [-12.1, -7.7] n=6,766 | -7.2 [-9.1, -5.3] n=14,596 | -9.1 [-11.2, -6.9] n=10,375 | -11.5 [-17.6, -6.7] n=883 | -5.6 [-6.8, -4.3] n=36,083 | -7.0 [-8.4, -5.7] n=27,704 | -7.0 [-13.9, -2.0] n=1,158 | 1.31 | 1.07 |
| price at 4h high (rangepos >= 0.98) | 15 | -11.0 [-13.5, -8.6] n=4,132 | -6.0 [-10.9, -2.3] n=1,333 | n=88 | -8.9 [-12.1, -5.9] n=2,523 | -8.2 [-9.8, -6.5] n=8,733 | -10.9 [-13.9, -8.4] n=2,605 | -6.6 [-8.7, -4.3] n=6,128 | -10.6 [-13.3, -8.0] n=3,420 | n=288 | -5.8 [-7.1, -4.3] n=17,124 | -6.9 [-8.5, -5.3] n=12,353 | -9.8 [-17.3, -3.7] n=504 | 1.50 | 1.29 |
| sweep: range position > 0.90 | 30 | -12.4 [-14.3, -10.6] n=23,966 | -8.1 [-12.0, -4.5] n=6,869 | -10.3 [-19.9, -6.0] n=414 | -12.2 [-14.3, -10.1] n=14,630 | -7.3 [-9.0, -5.9] n=50,921 | -9.8 [-12.1, -7.4] n=15,981 | -6.1 [-7.7, -4.5] n=34,364 | -7.3 [-9.1, -5.5] n=27,199 | -10.6 [-16.9, -4.7] n=2,277 | -4.6 [-5.9, -3.2] n=71,738 | -6.9 [-8.3, -5.6] n=57,644 | -7.0 [-12.7, -2.6] n=2,498 | 1.34 | 0.91 |
| sweep: 15-min move < -3 sd | 3 | +12.8 [+7.8, +18.2] n=746 | n=173 | n=16 | +4.0 [-2.4, +10.6] n=455 | +12.8 [+9.3, +16.9] n=1,207 | +13.1 [+7.1, +19.9] n=363 | +8.3 [+5.4, +11.5] n=1,728 | +4.5 [+1.6, +8.1] n=1,504 | n=172 | +4.3 [+1.1, +7.5] n=2,259 | +9.0 [+5.2, +12.3] n=1,604 | n=111 | 1.41 | 3.28 |
| sweep: 5-min move < -3 sd | 3 | +11.8 [+9.4, +14.4] n=1,843 | +9.6 [+3.8, +15.6] n=435 | n=36 | +10.4 [+6.4, +14.8] n=1,017 | +10.9 [+8.5, +13.1] n=2,889 | +4.7 [+0.7, +8.5] n=821 | +7.2 [+5.2, +9.6] n=3,307 | +8.0 [+5.7, +10.5] n=2,725 | n=250 | +6.9 [+5.0, +8.6] n=3,842 | +5.5 [+3.1, +7.6] n=2,951 | n=150 | 0.52 | 0.45 |
| sweep: range position < 0.05 | 15 | +13.3 [+10.6, +16.0] n=4,661 | +12.1 [+7.8, +16.6] n=1,154 | n=100 | +13.8 [+10.4, +17.5] n=2,831 | +11.3 [+9.6, +12.9] n=11,457 | +11.8 [+9.2, +14.3] n=4,223 | +9.2 [+7.5, +11.0] n=10,856 | +8.0 [+5.8, +10.6] n=9,335 | +4.4 [+0.6, +9.1] n=1,666 | +4.8 [+3.6, +6.2] n=30,641 | +5.4 [+4.0, +6.9] n=21,456 | +4.7 [-1.6, +12.6] n=1,033 | 1.28 | 0.77 |
| sweep: RSI14 < 25 | 10 | +13.6 [+11.3, +16.1] n=3,968 | +8.3 [+2.9, +14.3] n=827 | n=69 | +11.6 [+8.6, +15.1] n=2,415 | +10.0 [+7.9, +11.9] n=6,135 | +8.8 [+5.9, +12.6] n=1,918 | +5.7 [+3.6, +7.5] n=10,691 | +6.6 [+4.4, +8.7] n=6,352 | +7.5 [-0.0, +16.3] n=694 | +6.1 [+4.6, +7.6] n=14,788 | +8.5 [+6.6, +10.2] n=8,265 | -0.9 [-10.5, +11.5] n=417 | 1.03 | 0.76 |
| sweep: RSI14 < 25 | 5 | +15.0 [+12.9, +17.2] n=3,968 | +12.9 [+8.7, +17.3] n=827 | n=69 | +12.4 [+9.7, +15.5] n=2,415 | +11.3 [+9.5, +13.1] n=6,135 | +7.2 [+4.0, +10.3] n=1,918 | +5.3 [+3.6, +7.1] n=10,691 | +6.6 [+4.8, +8.6] n=6,352 | +7.4 [+2.5, +12.5] n=694 | +4.8 [+3.4, +6.1] n=14,788 | +7.9 [+6.3, +9.5] n=8,265 | +1.0 [-7.1, +10.6] n=417 | 0.98 | 0.66 |
| price at 4h high (rangepos >= 0.98) | 10 | -10.4 [-12.9, -8.1] n=4,132 | -7.6 [-11.6, -4.2] n=1,333 | n=88 | -8.7 [-11.9, -5.7] n=2,523 | -8.0 [-9.5, -6.6] n=8,733 | -9.9 [-12.4, -7.7] n=2,605 | -5.7 [-7.9, -3.5] n=6,128 | -12.1 [-14.3, -10.1] n=3,420 | n=288 | -5.0 [-6.2, -3.6] n=17,124 | -6.9 [-8.3, -5.3] n=12,353 | -8.1 [-14.1, -3.7] n=504 | 1.50 | 1.19 |
| sweep: RSI14 < 25 | 3 | +14.6 [+12.7, +16.5] n=3,968 | +14.2 [+10.2, +17.8] n=827 | n=69 | +11.3 [+8.8, +14.2] n=2,415 | +12.0 [+10.4, +13.7] n=6,135 | +8.6 [+5.9, +11.0] n=1,918 | +5.4 [+4.0, +6.9] n=10,691 | +6.9 [+5.5, +8.5] n=6,352 | +6.3 [+2.5, +11.6] n=694 | +4.3 [+3.1, +5.3] n=14,788 | +7.0 [+5.5, +8.3] n=8,265 | +6.3 [-1.4, +15.3] n=417 | 1.24 | 0.86 |
| sweep: RSI14 < 30 | 10 | +11.0 [+9.5, +12.6] n=11,332 | +10.7 [+7.5, +14.3] n=2,497 | n=205 | +11.4 [+9.5, +13.2] n=6,865 | +9.6 [+8.3, +10.8] n=18,548 | +8.4 [+6.6, +10.4] n=5,932 | +5.8 [+4.6, +7.1] n=25,008 | +6.9 [+5.6, +8.3] n=16,596 | +8.7 [+4.1, +13.5] n=1,838 | +5.6 [+4.6, +6.6] n=36,616 | +6.5 [+5.4, +7.5] n=23,369 | +2.3 [-3.1, +8.8] n=1,162 | 1.13 | 0.81 |
| RSI14 below 30 | 10 | +11.0 [+9.5, +12.6] n=11,332 | +10.7 [+7.5, +14.3] n=2,497 | n=205 | +11.4 [+9.5, +13.2] n=6,865 | +9.6 [+8.3, +10.8] n=18,548 | +8.4 [+6.6, +10.4] n=5,932 | +5.8 [+4.6, +7.1] n=25,008 | +6.9 [+5.6, +8.3] n=16,596 | +8.7 [+4.1, +13.5] n=1,838 | +5.6 [+4.6, +6.6] n=36,616 | +6.5 [+5.4, +7.5] n=23,369 | +2.3 [-3.1, +8.8] n=1,162 | 1.13 | 0.81 |
| RSI14 below 30 | 5 | +11.9 [+10.7, +13.3] n=11,332 | +13.9 [+11.0, +16.7] n=2,497 | n=205 | +10.9 [+9.1, +12.6] n=6,865 | +10.7 [+9.5, +11.8] n=18,548 | +7.8 [+6.1, +9.6] n=5,932 | +6.1 [+5.0, +7.2] n=25,008 | +6.6 [+5.6, +7.7] n=16,596 | +5.4 [+2.3, +9.3] n=1,838 | +4.6 [+3.7, +5.4] n=36,616 | +6.3 [+5.3, +7.4] n=23,369 | +3.7 [-1.0, +9.1] n=1,162 | 1.05 | 0.75 |
| sweep: RSI14 < 30 | 5 | +11.9 [+10.7, +13.3] n=11,332 | +13.9 [+11.0, +16.7] n=2,497 | n=205 | +10.9 [+9.1, +12.6] n=6,865 | +10.7 [+9.5, +11.8] n=18,548 | +7.8 [+6.1, +9.6] n=5,932 | +6.1 [+5.0, +7.2] n=25,008 | +6.6 [+5.6, +7.7] n=16,596 | +5.4 [+2.3, +9.3] n=1,838 | +4.6 [+3.7, +5.4] n=36,616 | +6.3 [+5.3, +7.4] n=23,369 | +3.7 [-1.0, +9.1] n=1,162 | 1.05 | 0.75 |
| sweep: RSI14 < 20 | 3 | +15.0 [+11.5, +18.5] n=1,276 | n=275 | n=15 | +10.4 [+6.2, +15.1] n=767 | +12.8 [+9.6, +15.8] n=1,754 | +12.7 [+8.3, +17.5] n=448 | +4.1 [+2.1, +6.8] n=4,404 | +6.9 [+4.0, +10.4] n=2,026 | n=229 | +5.0 [+3.1, +6.9] n=5,593 | +9.4 [+6.8, +12.1] n=2,389 | n=102 | 1.49 | 1.21 |
| sweep: range position < 0.05 | 10 | +13.0 [+10.5, +15.5] n=4,661 | +15.6 [+11.6, +19.7] n=1,154 | n=100 | +13.0 [+10.4, +15.5] n=2,831 | +10.7 [+9.0, +12.4] n=11,457 | +10.6 [+8.4, +12.9] n=4,223 | +8.4 [+6.8, +10.1] n=10,856 | +7.9 [+5.8, +10.1] n=9,335 | +6.0 [+2.3, +11.0] n=1,666 | +4.5 [+3.5, +5.7] n=30,641 | +4.9 [+3.6, +6.1] n=21,456 | +5.8 [-0.2, +13.1] n=1,033 | 1.34 | 0.83 |
| sweep: RSI60 < 40 | 30 | +9.4 [+6.4, +12.4] n=8,715 | +8.5 [+2.8, +15.2] n=2,098 | n=208 | +8.9 [+4.5, +13.9] n=5,122 | +7.4 [+4.6, +10.1] n=14,940 | +12.2 [+8.2, +17.0] n=4,168 | +8.8 [+6.5, +11.7] n=18,604 | +5.2 [+2.5, +8.3] n=14,442 | +12.0 [+5.8, +18.7] n=1,743 | +6.1 [+4.2, +7.8] n=28,368 | +7.3 [+5.0, +9.8] n=18,140 | +8.1 [+0.6, +18.0] n=857 | 1.51 | 1.36 |

Across the 24 cells with both ratios: high over low is 1.38 over all years (range 0.52 to 2.04) and 0.93 within eras (range 0.45 to 3.28).

Days per volatility state in each era, from the regime study's daily table.

| era | low | mid | high |
|---|---|---|---|
| 2019 | 295 | 64 | 4 |
| 2020-21 | 150 | 451 | 130 |
| 2022-23 | 376 | 321 | 33 |
| 2024-26 | 513 | 440 | 22 |
<!-- table:regimes_era:end -->

## One probability per minute from the cells

The cells above are read one at a time. A live view needs one number per minute, so the whole event set of both libraries (0/1 for each event) plus the trailing-hour volatility tercile goes into a logistic regression for the next-h-minute direction, fit on all earlier years and scored on each later year from 2020, at horizons of 5 and 15 minutes. Two baselines on the same minutes: call the opposite of the previous h minutes (the one-bit rule at this horizon), and let the strongest firing cell decide (ranking and direction from the training years). The same run checks whether the cells keep their promises: for every event whose training-years deviation was at least 3 points, the deviation the training years promised against the one the test year delivered.

<!-- table:cells_model_h5:start -->
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
<!-- table:cells_model_h5:end -->

<!-- table:cells_model_h15:start -->
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
<!-- table:cells_model_h15:end -->

- **The model beats the one-bit rule at this horizon by about a point, most years.** At 5 minutes the paired gain over the previous-5-minute reversal is +0.1 to +1.1 points, with the interval above zero in six of seven test years; at 15 minutes +0.2 to +1.0, above zero in five of seven. The rule itself is 50.5 to 52.9% at 5 minutes and 51.4 to 53.2% at 15, so the model lands at 51.3 to 53.0% and 51.7 to 54.2%. Small, but it is out of sample in every row and the direction of the gain never flips.
- **The strongest firing cell is as good as the regression.** "The strongest firing cell decides" is within half a point of the model in every year, above it in four of seven years at 5 minutes and three of seven at 15. With 186 events some cell fires on every minute, so the rule never abstains. A regression over all the cells adds nothing a ranked list of cells does not already carry, which fits the finding that the cells are one effect in several costumes.
- **Where the model is confident, it is right 54 to 58% of the time, and that share is fading.** Probabilities beyond 0.55 either way cover 13 to 22% of minutes at 5 minutes (26 to 37% at 15) and score 58.5% in 2020, 56.6 to 55.7% in 2021 to 2023, and 53.8 to 54.9% in 2024 to 2026 at 5 minutes; at 15 minutes the series goes from 58.5% in 2020 to 53.9 to 55.2% in 2024 to 2026. This is the fading of the cells themselves, measured forward, with the model's threshold held fixed.
- **The cells keep their sign and deliver about nine tenths of their size.** Over 650 cell-years at 5 minutes and 684 at 15, a cell's test-year deviation had the sign the training years promised in 99.8% and 98.7% of cases, and the delivered size was 89% and 90% of the promised size overall. Small promises (3 to 5 points) are delivered in full; large ones (8 to 12 points) deliver 77 to 84%. So the cells can be shown as probabilities, with the understanding that an 8-point cell is a 6- to 7-point cell next year.

## The cells as a few effects: overlap, horizon, volatility

Three questions about the 186 events of both libraries, asked of the same nine years. Which events fire on the same minutes, so that the list can be read as a few effects rather than 186 names; how the deviation builds from one minute to sixty for the strongest cells; and whether the trailing-hour volatility, which a live view knows, changes the size of a cell.

<!-- table:cells_clusters:start -->
Co-firing clusters of the 186 events of both libraries that fire at least 4,500 times over 2018 to 2026-08 ('lib' is the horizons event set, 'pa' the price-action library). Overlap coefficient of firing minutes pooled over years (shared minutes over the rarer event's minutes, so an event nested inside a broader one scores 1), average linkage, cut at 0.5. Each cluster is named by its most frequent member; 'union' is the up-rate deviation when any member fires, points, 95% interval from day-clustered errors, years held out of years with enough firings; 'opposite' counts members whose own 30-minute deviation has the other sign. The 30 clusters (of 55) whose union deviation at 30 minutes held in every year, by absolute deviation; every event's cluster is in cells_clusters.csv.

| cluster (most frequent member) | members | minutes any member fires | union deviation at 5 min | union deviation at 30 min | opposite | other members |
|---|---|---|---|---|---|---|
| pa: doji at a new 1h high | 1 | 0.46% | -5.3 [-6.0, -4.5] 9/9 | -6.8 [-7.6, -6.0] 9/9 | 0 |  |
| pa: wick rejection at the 1h high | 5 | 2.71% | -5.3 [-5.7, -5.0] 9/9 | -6.7 [-7.1, -6.3] 9/9 | 0 | pa: liquidity sweep of the 1h high (took it out, closed back below); pa: pin bar at a new 1h high (long upper wick); pa: wick rejection at the 4h high; pa: wick rejection at the daily high |
| pa: volume climax at a new 1h low (hour's largest volume) | 1 | 0.73% | +6.2 [+5.6, +6.8] 9/9 | +6.5 [+5.9, +7.1] 9/9 | 0 |  |
| pa: wick rejection at the 1h low | 5 | 2.62% | +5.1 [+4.8, +5.5] 9/9 | +6.3 [+5.9, +6.8] 9/9 | 0 | pa: liquidity sweep of the 1h low (took it out, closed back above); pa: pin bar at a new 1h low (long lower wick); pa: wick rejection at the 4h low; pa: wick rejection at the daily low |
| pa: doji at a new 1h low | 1 | 0.43% | +5.1 [+4.3, +5.8] 9/9 | +6.3 [+5.5, +7.2] 9/9 | 0 |  |
| pa: volume climax at a new 1h high (hour's largest volume) | 1 | 0.66% | -5.1 [-5.7, -4.4] 9/9 | -6.2 [-6.8, -5.5] 9/9 | 0 |  |
| pa: retest from above of a 4h high broken in the last hour | 1 | 1.69% | -2.6 [-3.1, -2.1] 9/9 | -5.6 [-6.4, -4.8] 9/9 | 0 |  |
| lib: previous window up | 45 | 78.10% | -3.6 [-3.8, -3.4] 9/9 | -5.4 [-5.6, -5.1] 9/9 | 0 | lib: 4h return above +50 bp; lib: EMA9 above EMA21 by 10 bp; lib: MACD histogram positive; lib: RSI14 above 70; lib: RSI60 above 65; lib: above upper Bollinger band; and 38 more |
| lib: OBV falling over 60 min | 2 | 5.32% | +3.7 [+3.3, +4.0] 9/9 | +5.3 [+4.6, +6.0] 9/9 | 0 | lib: sweep: OBV falling |
| lib: OBV rising over 60 min | 2 | 4.46% | -3.4 [-3.8, -3.0] 9/9 | -5.1 [-5.9, -4.3] 9/9 | 0 | lib: sweep: OBV rising |
| pa: retest from below of a 4h low broken in the last hour | 1 | 1.44% | +1.8 [+1.2, +2.3] 8/9 | +4.9 [+4.0, +5.8] 9/9 | 0 |  |
| lib: MACD histogram negative | 46 | 83.55% | +2.3 [+2.1, +2.5] 9/9 | +4.2 [+3.9, +4.5] 9/9 | 0 | lib: 4h return below -50 bp; lib: ADX14 above 30 (trending); lib: EMA9 below EMA21 by 10 bp; lib: RSI14 below 30; lib: RSI60 below 35; lib: below lower Bollinger band; and 39 more |
| pa: reclaimed the session VWAP in the last 5 minutes after 30+ minutes below | 1 | 0.82% | -4.6 [-5.4, -3.8] 9/9 | -4.1 [-5.0, -3.2] 9/9 | 0 |  |
| pa: resistance held (4h high tested within 3 bp, no close above, price now 3+ bp below) | 1 | 2.93% | -1.4 [-1.8, -0.9] 9/9 | -3.3 [-4.0, -2.5] 9/9 | 0 |  |
| lib: sweep: taker buy share > 0.1 (15 min) | 5 | 24.72% | -2.4 [-2.5, -2.2] 9/9 | -3.2 [-3.5, -2.9] 9/9 | 1 | lib: sweep: taker buy share > 0.2 (15 min); lib: sweep: taker buy share > 0.3 (15 min); lib: taker buying 60 pct+ of last 15 min; pa: absorption: heavy taker buying in the last 5 minutes, price did not rise |
| lib: sweep: taker sell share > 0.1 (15 min) | 5 | 27.38% | +2.5 [+2.3, +2.7] 9/9 | +3.1 [+2.8, +3.4] 9/9 | 1 | lib: sweep: taker sell share > 0.2 (15 min); lib: sweep: taker sell share > 0.3 (15 min); lib: taker selling 60 pct+ of last 15 min; pa: absorption: heavy taker selling in the last 5 minutes, price did not fall |
| pa: failed breakdown below the 1h low | 3 | 8.96% | +0.9 [+0.6, +1.2] 8/9 | +3.0 [+2.6, +3.4] 9/9 | 0 | pa: failed breakdown below the 4h low; pa: failed breakdown below the daily low |
| pa: support held (4h low tested within 3 bp, no close below, price now 3+ bp above) | 1 | 2.50% | +2.1 [+1.5, +2.6] 9/9 | +2.9 [+2.1, +3.8] 9/9 | 0 |  |
| pa: failed breakout above the 1h high | 3 | 9.16% | -1.2 [-1.5, -0.9] 9/9 | -2.9 [-3.3, -2.5] 9/9 | 0 | pa: failed breakout above the 4h high; pa: failed breakout above the daily high |
| pa: crossed a $100 level downward in the last 3 minutes | 2 | 14.08% | +2.3 [+2.1, +2.4] 9/9 | +2.7 [+2.5, +2.9] 9/9 | 0 | pa: crossed a $1,000 level downward in the last 3 minutes |
| pa: lost the session VWAP in the last 5 minutes after 30+ minutes above | 1 | 0.84% | +3.2 [+2.4, +3.9] 9/9 | +2.6 [+1.7, +3.5] 9/9 | 0 |  |
| pa: broke below the previous day's low in the last 5 minutes | 1 | 0.51% | +2.5 [+1.5, +3.5] 8/9 | +2.6 [+1.2, +3.9] 9/9 | 0 |  |
| pa: repeated rejection at the 4h high (2+ touches in 30 minutes, no close above) | 1 | 1.84% | -0.5 [-1.1, +0.1] 5/9 | -2.3 [-3.4, -1.1] 9/9 | 0 |  |
| pa: crossed a $100 level upward in the last 3 minutes | 2 | 14.09% | -2.0 [-2.2, -1.8] 9/9 | -2.1 [-2.3, -1.9] 9/9 | 0 | pa: crossed a $1,000 level upward in the last 3 minutes |
| pa: rejecting the downs (3+ down-minutes undone by the next minute in the last 15) | 1 | 19.56% | -1.8 [-1.9, -1.6] 9/9 | -1.8 [-2.1, -1.5] 9/9 | 0 |  |
| pa: approaching a $100 level from below (within 10 bp, rising) | 2 | 19.62% | -1.3 [-1.5, -1.1] 9/9 | -1.7 [-1.9, -1.5] 9/9 | 0 | pa: approaching a $1,000 level from below (within 10 bp, rising) |
| pa: rejecting the ups (3+ up-minutes undone by the next minute in the last 15) | 1 | 19.37% | +1.4 [+1.2, +1.6] 9/9 | +1.6 [+1.3, +1.9] 9/9 | 0 |  |
| pa: approaching a $100 level from above (within 10 bp, falling) | 2 | 19.46% | +1.0 [+0.8, +1.2] 7/9 | +1.5 [+1.3, +1.7] 9/9 | 1 | pa: approaching a $1,000 level from above (within 10 bp, falling) |
| lib: Asia early (0-3 UTC) | 3 | 16.65% | -0.4 [-0.6, -0.2] 8/9 | -1.3 [-1.8, -0.8] 9/9 | 0 | pa: 10 minutes after funding settlement (00:00 UTC); pa: first hour of the week (Monday 00:00 to 01:00 UTC) |
| pa: taker buying above 70% of the last minute | 1 | 15.33% | -0.2 [-0.3, -0.0] 6/9 | -1.0 [-1.1, -0.8] 9/9 | 0 |  |

How many clusters under each measure and cut: all 186 active events, and the 120 events whose 30-minute cell held its sign in every year.

| measure | cut | clusters, all active events | clusters, events held every year at 30 min |
|---|---|---|---|
| overlap coefficient | 0.5 | 55 | 30 |
| overlap coefficient | 0.7 | 72 | 40 |
| overlap coefficient | 0.9 | 94 | 58 |
| Jaccard | 0.2 | 85 | 44 |
| Jaccard | 0.3 | 108 | 57 |
| Jaccard | 0.5 | 146 | 87 |
<!-- table:cells_clusters:end -->

<!-- table:cells_decay:start -->
The effect by horizon, 2018 to 2026-08: for one cell per cluster among the strongest events held every year at 30 minutes, the pooled deviation at horizons 1 to 60 minutes (points, firing-weighted over years; the number after +/- is half the 95% interval from day-clustered errors pooled as if years were independent; in brackets, years held at that horizon). Every minute to 30, then every five. Below, where each peaks.

| horizon (min) | pa: wick rejection at the daily low | lib: sweep: range position > 0.95 | pa: wick rejection at the 4h high | lib: sweep: range position < 0.05 | pa: doji at a new 1h high | pa: volume climax at a new 1h low (hour's largest volume) | pa: doji at a new 1h low | pa: volume climax at a new 1h high (hour's largest volume) |
|---|---|---|---|---|---|---|---|---|
| 1 | +2.2 +/-0.9 (7/9) | -1.3 +/-0.3 (8/9) | -2.7 +/-0.5 (9/9) | +1.6 +/-0.3 (8/9) | -1.6 +/-0.7 (9/9) | +3.6 +/-0.6 (8/9) | +2.7 +/-0.7 (7/9) | -3.2 +/-0.6 (8/9) |
| 2 | +3.9 +/-0.9 (8/9) | -3.0 +/-0.3 (9/9) | -4.0 +/-0.5 (9/9) | +3.4 +/-0.4 (9/9) | -2.9 +/-0.7 (9/9) | +5.1 +/-0.6 (9/9) | +3.7 +/-0.7 (9/9) | -3.9 +/-0.6 (9/9) |
| 3 | +4.9 +/-0.9 (9/9) | -4.0 +/-0.4 (9/9) | -4.8 +/-0.5 (9/9) | +4.4 +/-0.4 (9/9) | -4.2 +/-0.8 (9/9) | +5.8 +/-0.6 (9/9) | +4.8 +/-0.7 (9/9) | -4.5 +/-0.6 (9/9) |
| 4 | +5.9 +/-1.0 (8/9) | -4.8 +/-0.4 (9/9) | -5.6 +/-0.5 (9/9) | +5.2 +/-0.4 (9/9) | -4.8 +/-0.8 (9/9) | +6.1 +/-0.6 (9/9) | +4.9 +/-0.7 (9/9) | -4.9 +/-0.6 (9/9) |
| 5 | +6.8 +/-1.0 (9/9) | -5.4 +/-0.4 (9/9) | -6.0 +/-0.5 (9/9) | +6.0 +/-0.5 (9/9) | -5.3 +/-0.8 (9/9) | +6.2 +/-0.6 (9/9) | +5.1 +/-0.7 (9/9) | -5.1 +/-0.6 (9/9) |
| 6 | +7.8 +/-1.0 (9/9) | -5.9 +/-0.4 (9/9) | -6.6 +/-0.6 (9/9) | +6.6 +/-0.5 (9/9) | -5.6 +/-0.8 (9/9) | +6.6 +/-0.6 (9/9) | +5.4 +/-0.8 (9/9) | -5.5 +/-0.6 (9/9) |
| 7 | +7.5 +/-1.0 (9/9) | -6.3 +/-0.4 (9/9) | -6.8 +/-0.6 (9/9) | +6.8 +/-0.5 (9/9) | -5.6 +/-0.8 (9/9) | +6.5 +/-0.6 (9/9) | +5.6 +/-0.7 (9/9) | -5.5 +/-0.6 (9/9) |
| 8 | +7.9 +/-1.1 (9/9) | -6.7 +/-0.5 (9/9) | -7.1 +/-0.6 (9/9) | +7.2 +/-0.5 (9/9) | -6.0 +/-0.7 (9/9) | +6.4 +/-0.6 (9/9) | +5.8 +/-0.7 (9/9) | -5.5 +/-0.6 (9/9) |
| 9 | +8.0 +/-1.1 (9/9) | -7.0 +/-0.5 (9/9) | -7.1 +/-0.6 (9/9) | +7.2 +/-0.5 (9/9) | -6.1 +/-0.7 (9/9) | +6.4 +/-0.6 (9/9) | +5.9 +/-0.7 (9/9) | -5.4 +/-0.6 (9/9) |
| 10 | +7.9 +/-1.1 (9/9) | -7.2 +/-0.5 (9/9) | -7.2 +/-0.6 (9/9) | +7.3 +/-0.5 (9/9) | -6.0 +/-0.8 (9/9) | +6.1 +/-0.6 (9/9) | +6.0 +/-0.7 (9/9) | -5.4 +/-0.6 (9/9) |
| 11 | +8.1 +/-1.1 (9/9) | -7.4 +/-0.5 (9/9) | -7.5 +/-0.6 (9/9) | +7.3 +/-0.6 (9/9) | -6.0 +/-0.8 (9/9) | +5.9 +/-0.6 (9/9) | +6.5 +/-0.8 (9/9) | -5.4 +/-0.6 (9/9) |
| 12 | +7.7 +/-1.1 (9/9) | -7.5 +/-0.5 (9/9) | -7.6 +/-0.6 (9/9) | +7.5 +/-0.6 (9/9) | -6.0 +/-0.7 (9/9) | +6.0 +/-0.6 (9/9) | +5.6 +/-0.8 (9/9) | -5.6 +/-0.6 (9/9) |
| 13 | +7.8 +/-1.2 (9/9) | -7.7 +/-0.5 (9/9) | -7.7 +/-0.6 (9/9) | +7.6 +/-0.6 (9/9) | -6.5 +/-0.7 (9/9) | +6.1 +/-0.6 (9/9) | +5.8 +/-0.8 (9/9) | -5.4 +/-0.6 (9/9) |
| 14 | +8.0 +/-1.2 (9/9) | -7.8 +/-0.5 (9/9) | -7.6 +/-0.6 (9/9) | +7.7 +/-0.6 (9/9) | -6.7 +/-0.8 (9/9) | +6.1 +/-0.6 (9/9) | +5.8 +/-0.8 (9/9) | -5.4 +/-0.6 (9/9) |
| 15 | +8.1 +/-1.2 (9/9) | -8.0 +/-0.5 (9/9) | -8.0 +/-0.6 (9/9) | +7.7 +/-0.6 (9/9) | -6.7 +/-0.8 (9/9) | +6.1 +/-0.6 (9/9) | +5.8 +/-0.8 (9/9) | -5.0 +/-0.6 (9/9) |
| 16 | +8.2 +/-1.2 (9/9) | -8.1 +/-0.6 (9/9) | -8.1 +/-0.6 (9/9) | +7.8 +/-0.6 (9/9) | -6.9 +/-0.8 (9/9) | +6.1 +/-0.6 (9/9) | +5.6 +/-0.8 (9/9) | -5.5 +/-0.6 (9/9) |
| 17 | +8.4 +/-1.2 (9/9) | -8.3 +/-0.6 (9/9) | -8.2 +/-0.6 (9/9) | +8.1 +/-0.6 (9/9) | -7.2 +/-0.8 (9/9) | +6.2 +/-0.6 (9/9) | +5.7 +/-0.8 (9/9) | -5.7 +/-0.7 (9/9) |
| 18 | +9.0 +/-1.2 (9/9) | -8.3 +/-0.6 (9/9) | -8.2 +/-0.6 (9/9) | +8.1 +/-0.7 (9/9) | -7.2 +/-0.8 (9/9) | +6.2 +/-0.6 (9/9) | +5.7 +/-0.8 (9/9) | -5.8 +/-0.7 (9/9) |
| 19 | +9.0 +/-1.2 (9/9) | -8.4 +/-0.6 (9/9) | -8.2 +/-0.7 (9/9) | +8.2 +/-0.7 (9/9) | -7.2 +/-0.8 (9/9) | +6.2 +/-0.6 (9/9) | +5.9 +/-0.8 (9/9) | -6.0 +/-0.6 (9/9) |
| 20 | +9.0 +/-1.3 (9/9) | -8.5 +/-0.6 (9/9) | -8.5 +/-0.7 (9/9) | +8.2 +/-0.7 (9/9) | -7.2 +/-0.8 (9/9) | +6.3 +/-0.6 (9/9) | +6.0 +/-0.8 (9/9) | -6.0 +/-0.7 (9/9) |
| 21 | +9.2 +/-1.3 (9/9) | -8.6 +/-0.6 (9/9) | -8.6 +/-0.7 (9/9) | +8.3 +/-0.7 (9/9) | -7.1 +/-0.8 (9/9) | +6.3 +/-0.6 (9/9) | +5.9 +/-0.8 (9/9) | -6.1 +/-0.7 (9/9) |
| 22 | +8.9 +/-1.3 (9/9) | -8.7 +/-0.6 (9/9) | -8.7 +/-0.7 (9/9) | +8.3 +/-0.7 (9/9) | -7.0 +/-0.8 (9/9) | +6.1 +/-0.6 (9/9) | +5.9 +/-0.8 (9/9) | -6.0 +/-0.7 (9/9) |
| 23 | +9.1 +/-1.3 (9/9) | -8.8 +/-0.6 (9/9) | -8.7 +/-0.7 (9/9) | +8.5 +/-0.7 (9/9) | -7.1 +/-0.8 (9/9) | +6.4 +/-0.6 (9/9) | +5.9 +/-0.8 (9/9) | -6.2 +/-0.7 (9/9) |
| 24 | +9.0 +/-1.3 (9/9) | -8.8 +/-0.6 (9/9) | -8.7 +/-0.7 (9/9) | +8.5 +/-0.7 (9/9) | -6.9 +/-0.8 (9/9) | +6.5 +/-0.6 (9/9) | +5.8 +/-0.8 (9/9) | -6.3 +/-0.7 (9/9) |
| 25 | +9.3 +/-1.3 (9/9) | -8.9 +/-0.6 (9/9) | -8.7 +/-0.7 (9/9) | +8.5 +/-0.7 (9/9) | -6.8 +/-0.8 (9/9) | +6.4 +/-0.6 (9/9) | +5.9 +/-0.8 (9/9) | -6.2 +/-0.6 (9/9) |
| 26 | +9.2 +/-1.3 (9/9) | -9.0 +/-0.6 (9/9) | -8.7 +/-0.7 (9/9) | +8.5 +/-0.7 (9/9) | -6.7 +/-0.8 (9/9) | +6.5 +/-0.6 (9/9) | +5.9 +/-0.8 (9/9) | -6.0 +/-0.6 (9/9) |
| 27 | +9.2 +/-1.3 (9/9) | -9.0 +/-0.6 (9/9) | -8.8 +/-0.7 (9/9) | +8.6 +/-0.7 (9/9) | -6.8 +/-0.8 (9/9) | +6.6 +/-0.6 (9/9) | +6.2 +/-0.8 (9/9) | -6.2 +/-0.6 (9/9) |
| 28 | +9.2 +/-1.4 (9/9) | -9.0 +/-0.7 (9/9) | -8.7 +/-0.7 (9/9) | +8.7 +/-0.7 (9/9) | -6.9 +/-0.8 (9/9) | +6.6 +/-0.6 (9/9) | +6.4 +/-0.8 (9/9) | -6.3 +/-0.7 (9/9) |
| 29 | +9.3 +/-1.3 (9/9) | -9.1 +/-0.7 (9/9) | -8.7 +/-0.7 (9/9) | +8.6 +/-0.7 (9/9) | -6.9 +/-0.8 (9/9) | +6.6 +/-0.6 (9/9) | +6.4 +/-0.8 (9/9) | -6.1 +/-0.7 (9/9) |
| 30 | +9.0 +/-1.4 (9/9) | -9.0 +/-0.7 (9/9) | -8.7 +/-0.7 (9/9) | +8.6 +/-0.7 (9/9) | -6.8 +/-0.8 (9/9) | +6.5 +/-0.6 (9/9) | +6.3 +/-0.8 (9/9) | -6.2 +/-0.6 (9/9) |
| 35 | +9.6 +/-1.4 (9/9) | -9.0 +/-0.7 (9/9) | -8.6 +/-0.7 (9/9) | +8.2 +/-0.8 (9/9) | -6.3 +/-0.8 (9/9) | +6.3 +/-0.6 (9/9) | +5.7 +/-0.9 (9/9) | -6.0 +/-0.6 (9/9) |
| 40 | +10.1 +/-1.4 (9/9) | -8.9 +/-0.7 (9/9) | -8.6 +/-0.7 (9/9) | +8.2 +/-0.8 (9/9) | -5.9 +/-0.8 (9/9) | +6.2 +/-0.6 (9/9) | +5.4 +/-0.9 (9/9) | -6.0 +/-0.7 (9/9) |
| 45 | +9.9 +/-1.4 (9/9) | -8.9 +/-0.7 (9/9) | -8.6 +/-0.7 (9/9) | +8.1 +/-0.8 (9/9) | -6.0 +/-0.8 (9/9) | +5.9 +/-0.6 (9/9) | +5.6 +/-0.9 (9/9) | -6.1 +/-0.7 (9/9) |
| 50 | +10.1 +/-1.4 (9/9) | -9.1 +/-0.7 (9/9) | -8.8 +/-0.7 (9/9) | +7.9 +/-0.8 (9/9) | -5.7 +/-0.8 (9/9) | +5.7 +/-0.6 (9/9) | +5.3 +/-0.8 (9/9) | -6.0 +/-0.7 (9/9) |
| 55 | +10.1 +/-1.5 (9/9) | -9.0 +/-0.8 (9/9) | -8.6 +/-0.8 (9/9) | +8.1 +/-0.8 (9/9) | -5.6 +/-0.8 (9/9) | +5.9 +/-0.6 (9/9) | +5.2 +/-0.9 (9/9) | -6.0 +/-0.7 (9/9) |
| 60 | +10.4 +/-1.4 (9/9) | -8.8 +/-0.8 (9/9) | -8.6 +/-0.8 (9/9) | +8.3 +/-0.9 (9/9) | -5.5 +/-0.8 (9/9) | +5.8 +/-0.6 (9/9) | +5.2 +/-0.8 (9/9) | -6.2 +/-0.7 (9/9) |

| event | deviation at 1 min | at 5 min | at 15 min | at 30 min | at 60 min | peak horizon (min) | deviation at peak | horizons of 60 held every year |
|---|---|---|---|---|---|---|---|---|
| pa: wick rejection at the daily low | +2.2 | +6.8 | +8.1 | +9.0 | +10.4 | 60 | +10.4 | 57/60 |
| lib: sweep: range position > 0.95 | -1.3 | -5.4 | -8.0 | -9.0 | -8.8 | 48 | -9.2 | 59/60 |
| pa: wick rejection at the 4h high | -2.7 | -6.0 | -8.0 | -8.7 | -8.6 | 49 | -8.9 | 60/60 |
| lib: sweep: range position < 0.05 | +1.6 | +6.0 | +7.7 | +8.6 | +8.3 | 28 | +8.7 | 59/60 |
| pa: doji at a new 1h high | -1.6 | -5.3 | -6.7 | -6.8 | -5.5 | 17 | -7.2 | 60/60 |
| pa: volume climax at a new 1h low (hour's largest volume) | +3.6 | +6.2 | +6.1 | +6.5 | +5.8 | 27 | +6.6 | 59/60 |
| pa: doji at a new 1h low | +2.7 | +5.1 | +5.8 | +6.3 | +5.2 | 11 | +6.5 | 59/60 |
| pa: volume climax at a new 1h high (hour's largest volume) | -3.2 | -5.1 | -5.0 | -6.2 | -6.2 | 28 | -6.3 | 59/60 |
<!-- table:cells_decay:end -->

<!-- table:cells_volatility:start -->
The strongest cells by tercile of the trailing-hour volatility (vol60; tercile cutoffs from the previous year, so known at the time), 2018 to 2026-08: the 12 largest pooled deviations held every year at each of 5, 30 minutes, one per group of near-identical events (Jaccard 0.3). Because the cutoffs come from the previous year, a calm year after a wild one puts most of its minutes in the low tercile, which is why some terciles have few years with enough firings. Deviation of the up-rate from the tercile's own unconditional rate, points, 95% interval, years held; firings in brackets.

| event | horizon (min) | all minutes | low-volatility third | middle third | high-volatility third |
|---|---|---|---|---|---|
| lib: sweep: RSI14 < 25 | 5 | +7.5 [+6.9, +8.1] 9/9 [64,233] | +6.9 [+5.9, +7.8] 8/8 [30,986] | +8.3 [+7.1, +9.4] 9/9 [14,669] | +8.0 [+6.9, +9.1] 9/9 [18,578] |
| lib: RSI14 below 30 | 5 | +7.4 [+7.0, +7.8] 9/9 [169,065] | +6.8 [+6.2, +7.4] 9/9 [80,102] | +8.3 [+7.5, +9.0] 9/9 [40,735] | +7.8 [+7.1, +8.5] 9/9 [48,228] |
| lib: sweep: 5-min move < -3 sd | 5 | +7.1 [+6.2, +7.9] 9/9 [23,148] | +7.2 [+5.7, +8.6] 6/6 [8,908] | +7.5 [+5.9, +9.2] 8/9 [6,071] | +7.0 [+5.6, +8.5] 7/8 [8,169] |
| lib: sweep: 15-min move < -3 sd | 5 | +6.9 [+5.5, +8.4] 9/9 [12,180] | +5.9 [+3.0, +8.7] 4/4 [3,979] | +3.1 [-1.3, +7.4] 2/2 [3,152] | +7.5 [+4.6, +10.4] 4/4 [5,049] |
| pa: wick rejection at the daily low | 5 | +6.8 [+5.8, +7.8] 9/9 [12,238] | +3.4 [-0.6, +7.5] 1/1 [1,770] | +2.1 [-1.3, +5.6] 1/2 [2,813] | +6.6 [+5.3, +8.0] 7/7 [7,655] |
| lib: sweep: RSI14 < 20 | 5 | +6.8 [+5.7, +8.0] 9/9 [22,141] | +5.6 [+3.8, +7.4] 7/7 [11,191] | +5.4 [+2.9, +7.9] 4/5 [4,583] | +8.3 [+6.4, +10.2] 8/8 [6,367] |
| pa: pin bar at a new 1h high (long upper wick) | 5 | -6.8 [-7.4, -6.1] 9/9 [23,729] | -5.6 [-6.6, -4.7] 7/7 [12,007] | -7.3 [-8.6, -6.0] 8/8 [6,230] | -8.3 [-9.8, -6.7] 4/4 [5,492] |
| lib: price at 4h low (rangepos <= 0.02) | 5 | +6.7 [+6.1, +7.3] 9/9 [46,704] | +5.1 [+4.1, +6.1] 8/8 [17,981] | +8.1 [+6.9, +9.3] 9/9 [11,633] | +7.4 [+6.5, +8.3] 8/8 [17,090] |
| lib: sweep: RSI14 > 75 | 5 | -6.6 [-7.2, -5.9] 9/9 [70,751] | -6.6 [-7.5, -5.7] 8/8 [33,410] | -6.6 [-7.8, -5.4] 9/9 [16,582] | -6.4 [-7.4, -5.4] 9/9 [20,759] |
| lib: RSI14 above 70 | 5 | -6.6 [-7.0, -6.2] 9/9 [179,989] | -6.5 [-7.1, -5.9] 9/9 [83,633] | -6.6 [-7.4, -5.9] 9/9 [44,725] | -6.8 [-7.4, -6.1] 9/9 [51,631] |
| lib: sweep: RSI60 < 35 | 5 | +6.3 [+5.2, +7.4] 9/9 [23,920] | +6.4 [+4.0, +8.7] 5/5 [5,318] | +2.2 [-0.4, +4.9] 3/4 [4,924] | +6.1 [+4.7, +7.6] 8/9 [13,678] |
| pa: wick rejection at the 4h low | 5 | +6.2 [+5.7, +6.7] 9/9 [42,192] | +6.2 [+5.3, +7.2] 7/7 [14,640] | +6.0 [+4.9, +7.0] 9/9 [11,079] | +6.5 [+5.6, +7.3] 9/9 [16,473] |
| pa: wick rejection at the daily low | 30 | +9.0 [+7.6, +10.4] 9/9 [12,238] | +13.3 [+7.9, +18.7] 1/1 [1,770] | +1.2 [-3.5, +6.0] 2/2 [2,813] | +8.6 [+6.7, +10.4] 7/7 [7,655] |
| lib: sweep: range position > 0.95 | 30 | -9.0 [-9.7, -8.3] 9/9 [151,420] | -8.9 [-10.0, -7.8] 9/9 [59,149] | -9.3 [-10.5, -8.2] 9/9 [41,048] | -9.0 [-10.1, -7.9] 9/9 [51,223] |
| pa: wick rejection at the 4h high | 30 | -8.7 [-9.4, -8.0] 9/9 [45,742] | -9.3 [-10.5, -8.2] 7/7 [17,841] | -8.8 [-10.0, -7.6] 9/9 [12,608] | -8.2 [-9.3, -7.0] 9/9 [15,293] |
| lib: sweep: range position < 0.05 | 30 | +8.6 [+7.8, +9.3] 9/9 [110,296] | +8.0 [+6.7, +9.3] 8/8 [40,101] | +8.3 [+7.0, +9.6] 9/9 [28,610] | +9.2 [+8.0, +10.3] 9/9 [41,585] |
| pa: wick rejection at the 4h low | 30 | +8.2 [+7.5, +8.9] 9/9 [42,191] | +8.8 [+7.5, +10.0] 7/7 [14,640] | +7.1 [+5.8, +8.4] 9/9 [11,079] | +8.4 [+7.3, +9.5] 9/9 [16,472] |
| lib: sweep: range position < 0.1 | 30 | +8.2 [+7.6, +8.8] 9/9 [248,062] | +8.4 [+7.4, +9.5] 9/9 [88,631] | +7.9 [+6.8, +9.1] 9/9 [66,754] | +8.1 [+7.1, +9.1] 9/9 [92,677] |
| lib: sweep: range position > 0.90 | 30 | -8.3 [-8.8, -7.7] 9/9 [337,835] | -8.3 [-9.2, -7.4] 9/9 [129,123] | -8.9 [-9.9, -8.0] 9/9 [92,763] | -7.9 [-8.8, -7.0] 9/9 [115,949] |
| lib: sweep: RSI60 < 40 | 30 | +7.3 [+6.4, +8.1] 9/9 [134,567] | +9.6 [+8.0, +11.1] 8/8 [36,555] | +6.0 [+4.4, +7.5] 9/9 [31,996] | +6.3 [+5.0, +7.6] 9/9 [66,016] |
| pa: pin bar at a new 1h high (long upper wick) | 30 | -6.9 [-7.6, -6.2] 9/9 [23,729] | -7.3 [-8.3, -6.2] 7/7 [12,007] | -6.0 [-7.3, -4.6] 8/8 [6,230] | -6.1 [-7.7, -4.4] 4/4 [5,492] |
| pa: wick rejection at the daily high | 30 | -6.9 [-8.1, -5.7] 9/9 [13,898] | -6.1 [-9.6, -2.6] 2/2 [2,810] | -6.5 [-9.7, -3.4] 3/3 [3,777] | -6.8 [-8.5, -5.0] 7/7 [7,311] |
| lib: sweep: RSI14 < 25 | 30 | +6.9 [+6.2, +7.7] 9/9 [64,233] | +8.1 [+6.9, +9.3] 8/8 [30,986] | +6.0 [+4.6, +7.5] 8/9 [14,669] | +5.8 [+4.4, +7.2] 8/9 [18,578] |
| pa: acceptance above the 4h high (last 5 closes all above it) | 30 | -7.0 [-7.8, -6.2] 9/9 [133,621] | -8.4 [-9.8, -7.1] 8/8 [41,533] | -7.6 [-9.0, -6.2] 9/9 [36,607] | -5.9 [-7.0, -4.7] 9/9 [55,481] |

Across the 24 cells, the high-volatility deviation is 1.0 times the low-volatility one (median; range 0.6 to 1.9); the sign agrees between the two terciles in 24 of 24.
<!-- table:cells_volatility:end -->

- **The indicator library is two effects.** Under the nesting measure (an event that fires inside a broader one is a costume of it), 85 of the 107 events of the horizons set fall into two clusters: "price recently rose" (named by its most frequent member, previous window up: 45 members, firing on 78% of minutes) and "price recently fell" (MACD histogram negative: 46 members, 84%). RSI, Bollinger bands, EMA crossings, VWAP distance, 4-hour returns and the window sequence are all ways of saying one of those two things, and no member of either cluster points against its union at 30 minutes.
- **The price-action library adds the probes.** Its holding events form small clusters of their own: wick rejections, liquidity sweeps and pin bars at a low (five members, one effect) and at a high (five, the mirror), dojis and volume climaxes at a new hourly extreme, retests of a broken level, failed breakouts and breakdowns, round-number crossings. These are not nested in the indicator clusters because they describe one candle's shape at an extreme, not where the price sits in its range. Of the 120 events whose 30-minute cell held every year, 30 clusters remain at the nesting cut of 0.5 (40 at 0.7); under Jaccard, which keeps a rare event apart from a broad one, 44 to 87.
- **The deviation builds for half an hour, not five minutes.** For the eight strongest cells, the 1-minute deviation is 28% of the 30-minute one (median), 59% by 3 minutes, 77% by 5 and 91% by 15. The range-position and wick-rejection cells keep rising to a peak at 48 to 60 minutes; the one-candle events (doji, volume climax at an hourly extreme) peak at 11 to 28 minutes and fade a little by 60. The next five minutes carry most of the effect and the rest accrues slowly, so a 5-minute call leaves about a quarter of it on the table.
- **The trailing-hour volatility does not change the size of a cell.** Across the 24 strongest cells, the deviation in the high-volatility third is 1.0 times the deviation in the low third (median; range 0.6 to 1.9), the middle third 0.96 times, and the sign agrees in all 24. The regime section's daily-state doubling turned out to be the era (its within-era table): the high-volatility days are concentrated in 2020 to 2022, when every cell was larger. For the live view the consequence is simple: show the cell's probability without a volatility adjustment, and expect it to shrink with the calendar rather than with the day's volatility.

## What is not yet done

- Derivatives events (funding extremes, open-interest spikes, liquidation signatures) and tick-level events (large-trade bursts) for the library.
- The mechanism of the reversal from the tick data: order-book replenishment and inventory after a sharp move.
- HMM variants not yet tried, after the states lost as predictors (study 29 in [btc_15m.md](btc_15m.md)) and added nothing as features (study 30): an HMM observing order-flow imbalance rather than returns, a non-homogeneous transition matrix driven by time of day, and a hidden semi-Markov model with explicit state durations.

