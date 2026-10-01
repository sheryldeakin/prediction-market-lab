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
- **The conditional effects scale with volatility.** The 4-hour-extreme reversals are 12 to 16 points in the high-volatility state and 7 to 8 points in the low- and mid-volatility states, with intervals that separate. The sign never changes; the size does. So the useful regime variable for these cells is the volatility state known at the time, not whether the market is bull or bear, and the simplest form of it, the trailing 60-minute volatility, is already a feature.

## What is not yet done

- Derivatives events (funding extremes, open-interest spikes, liquidation signatures) and tick-level events (large-trade bursts) for the library.
- The mechanism of the reversal from the tick data: order-book replenishment and inventory after a sharp move.

