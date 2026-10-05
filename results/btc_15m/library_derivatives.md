Derivatives events for the price-action library: definitions and the coverage of the futures files held. Every cutoff is a percentile (decile) of the previous calendar year, so an event can be scored in year Y only if the files cover all of year Y-1. The events are defined and tested in models/btc_15m/library_events.py (`deriv_events`).

| series | first stamp | last stamp | files |
|---|---|---|---|
| funding rate (monthly files) | 2020-01 | 2026-08 | 80 |
| open interest and positioning metrics (daily files) | 2020-09-01 | 2026-09-29 | 2220 |
| perpetual 1-minute klines (monthly files) | 2020-01 | 2026-08 | 80 |
| perpetual 1-minute klines (daily files) | 2026-09-01 | 2026-09-29 | 29 |

Calendar years fully covered by funding, metrics and perp klines together: 2021, 2022, 2023, 2024, 2025; the events can be scored in 2022, 2023, 2024, 2025, 2026.

Derivatives events for the price-action library, scored in 2022 to 2026-08, every minute as a decision time. Every cutoff is a decile of the previous calendar year of the futures series themselves, so a year never defines its own extreme. The columns are the same as in the tick table; the share is the share of minutes the event fires on over the years in which it was scored (an event with fewer than 500 firings in a year is not scored in it, and the years columns count the scored years). The null covers these 8 events at the 6 horizons only (50 rotated-label runs per year; the smallest possible adjusted p is 0.0040). The comparison at each cut is strict, because the funding rate sits at the exchange default on a large share of minutes, so the previous year's upper decile can be the default itself; this was set after the one-year smoke run and is the only thing that run changed. The orientation of the funding and liquidation groups below was fixed before the run.

| family | event | horizon (min) | fires | share (scored years) | up-rate | deviation (points) [95% interval] | min adjusted p | years held | years p<=0.05 | VWAP retained |
|---|---|---|---|---|---|---|---|---|---|---|
| funding | funding rate in the top decile of the previous year | 1 | 135,360 | 12.88% | 50.9% | -0.6 [-1.0, -0.3] | 0.5578 | 2/2 | 0/2 | -10% |
| funding | funding rate in the top decile of the previous year | 3 | 135,358 | 12.88% | 50.3% | -0.2 [-0.6, +0.1] | 0.9562 | 2/2 | 0/2 | - |
| funding | funding rate in the top decile of the previous year | 5 | 135,356 | 12.88% | 50.3% | -0.1 [-0.5, +0.3] | 1.0000 | 2/2 | 0/2 | - |
| funding | funding rate in the top decile of the previous year | 10 | 135,351 | 12.88% | 50.5% | +0.2 [-0.4, +0.7] | 1.0000 | 1/2 | 0/2 | - |
| funding | funding rate in the top decile of the previous year | 15 | 135,346 | 12.88% | 50.7% | +0.2 [-0.5, +0.9] | 1.0000 | 1/2 | 0/2 | - |
| funding | funding rate in the top decile of the previous year | 30 | 135,331 | 12.88% | 50.9% | +0.3 [-0.6, +1.2] | 1.0000 | 1/2 | 0/2 | - |
| funding | funding rate in the bottom decile of the previous year | 1 | 445,440 | 18.17% | 50.6% | -0.2 [-0.4, -0.1] | 0.1833 | 3/5 | 0/5 | 15% |
| funding | funding rate in the bottom decile of the previous year | 3 | 445,440 | 18.17% | 50.2% | +0.0 [-0.1, +0.2] | 1.0000 | 3/5 | 0/5 | - |
| funding | funding rate in the bottom decile of the previous year | 5 | 445,440 | 18.17% | 50.1% | +0.1 [-0.1, +0.3] | 0.9960 | 3/5 | 0/5 | - |
| funding | funding rate in the bottom decile of the previous year | 10 | 445,440 | 18.17% | 50.2% | +0.2 [-0.1, +0.5] | 0.9522 | 3/5 | 0/5 | - |
| funding | funding rate in the bottom decile of the previous year | 15 | 445,440 | 18.17% | 50.4% | +0.3 [-0.0, +0.7] | 0.9841 | 4/5 | 0/5 | - |
| funding | funding rate in the bottom decile of the previous year | 30 | 445,440 | 18.17% | 50.4% | +0.2 [-0.2, +0.7] | 1.0000 | 4/5 | 0/5 | - |
| open interest | open interest up over 15 minutes (top decile) | 1 | 173,710 | 7.08% | 50.2% | -1.3 [-1.6, -1.1] | 0.0040 | 5/5 | 3/5 | 20% |
| open interest | open interest up over 15 minutes (top decile) | 3 | 173,710 | 7.08% | 49.9% | -0.5 [-0.8, -0.2] | 0.3187 | 3/5 | 0/5 | 52% |
| open interest | open interest up over 15 minutes (top decile) | 5 | 173,710 | 7.08% | 49.8% | -0.4 [-0.8, -0.0] | 0.4422 | 3/5 | 0/5 | 57% |
| open interest | open interest up over 15 minutes (top decile) | 10 | 173,710 | 7.08% | 49.8% | -0.3 [-0.8, +0.2] | 0.9641 | 4/5 | 0/5 | - |
| open interest | open interest up over 15 minutes (top decile) | 15 | 173,710 | 7.08% | 50.0% | -0.2 [-0.7, +0.4] | 0.6693 | 3/5 | 0/5 | - |
| open interest | open interest up over 15 minutes (top decile) | 30 | 173,710 | 7.08% | 50.0% | -0.3 [-1.0, +0.4] | 0.5219 | 3/5 | 0/5 | - |
| open interest | open interest down over 15 minutes (bottom decile) | 1 | 183,796 | 7.50% | 50.6% | -0.9 [-1.1, -0.7] | 0.0040 | 5/5 | 1/5 | 1% |
| open interest | open interest down over 15 minutes (bottom decile) | 3 | 183,796 | 7.50% | 50.5% | +0.1 [-0.2, +0.4] | 0.9522 | 4/5 | 0/5 | - |
| open interest | open interest down over 15 minutes (bottom decile) | 5 | 183,796 | 7.50% | 50.7% | +0.5 [+0.2, +0.9] | 0.3785 | 4/5 | 0/5 | 107% |
| open interest | open interest down over 15 minutes (bottom decile) | 10 | 183,796 | 7.50% | 51.2% | +1.1 [+0.6, +1.6] | 0.5737 | 4/5 | 0/5 | 95% |
| open interest | open interest down over 15 minutes (bottom decile) | 15 | 183,796 | 7.50% | 51.6% | +1.4 [+0.9, +2.0] | 0.1315 | 4/5 | 0/5 | 95% |
| open interest | open interest down over 15 minutes (bottom decile) | 30 | 183,787 | 7.50% | 52.0% | +1.7 [+1.0, +2.3] | 0.1394 | 5/5 | 0/5 | 105% |
| open interest | open interest up over 60 minutes (top decile) | 1 | 179,385 | 7.32% | 50.5% | -1.0 [-1.3, -0.8] | 0.0040 | 5/5 | 3/5 | 1% |
| open interest | open interest up over 60 minutes (top decile) | 3 | 179,385 | 7.32% | 50.1% | -0.3 [-0.7, -0.0] | 0.1036 | 3/5 | 0/5 | 34% |
| open interest | open interest up over 60 minutes (top decile) | 5 | 179,385 | 7.32% | 50.0% | -0.1 [-0.5, +0.2] | 0.5299 | 2/5 | 0/5 | - |
| open interest | open interest up over 60 minutes (top decile) | 10 | 179,385 | 7.32% | 50.1% | +0.0 [-0.5, +0.5] | 0.8725 | 3/5 | 0/5 | - |
| open interest | open interest up over 60 minutes (top decile) | 15 | 179,385 | 7.32% | 50.0% | -0.2 [-0.8, +0.5] | 0.9841 | 2/5 | 0/5 | - |
| open interest | open interest up over 60 minutes (top decile) | 30 | 179,385 | 7.32% | 49.6% | -0.7 [-1.6, +0.1] | 0.4183 | 2/5 | 0/5 | - |
| open interest | open interest down over 60 minutes (bottom decile) | 1 | 184,261 | 7.51% | 50.5% | -1.0 [-1.2, -0.7] | 0.0159 | 5/5 | 2/5 | -0% |
| open interest | open interest down over 60 minutes (bottom decile) | 3 | 184,259 | 7.51% | 50.3% | -0.1 [-0.4, +0.2] | 0.3705 | 3/5 | 0/5 | - |
| open interest | open interest down over 60 minutes (bottom decile) | 5 | 184,257 | 7.51% | 50.6% | +0.4 [-0.0, +0.7] | 0.4821 | 3/5 | 0/5 | - |
| open interest | open interest down over 60 minutes (bottom decile) | 10 | 184,252 | 7.51% | 50.9% | +0.7 [+0.2, +1.2] | 0.4024 | 4/5 | 0/5 | 95% |
| open interest | open interest down over 60 minutes (bottom decile) | 15 | 184,247 | 7.51% | 51.2% | +1.0 [+0.4, +1.6] | 0.5060 | 4/5 | 0/5 | 100% |
| open interest | open interest down over 60 minutes (bottom decile) | 30 | 184,232 | 7.51% | 51.5% | +1.2 [+0.4, +2.0] | 0.6175 | 3/5 | 0/5 | 98% |
| liquidation signature | long liquidation signature (open interest down, price down hard, perp volume heavy) | 1 | 23,526 | 0.96% | 51.8% | +0.4 [-0.2, +1.0] | 1.0000 | 4/5 | 0/5 | - |
| liquidation signature | long liquidation signature (open interest down, price down hard, perp volume heavy) | 3 | 23,526 | 0.96% | 52.6% | +2.2 [+1.3, +3.1] | 0.0159 | 5/5 | 1/5 | 119% |
| liquidation signature | long liquidation signature (open interest down, price down hard, perp volume heavy) | 5 | 23,526 | 0.96% | 53.4% | +3.2 [+2.1, +4.2] | 0.0040 | 4/5 | 2/5 | 108% |
| liquidation signature | long liquidation signature (open interest down, price down hard, perp volume heavy) | 10 | 23,526 | 0.96% | 53.6% | +3.5 [+2.2, +4.8] | 0.0159 | 4/5 | 1/5 | 119% |
| liquidation signature | long liquidation signature (open interest down, price down hard, perp volume heavy) | 15 | 23,526 | 0.96% | 54.3% | +4.1 [+2.7, +5.5] | 0.0040 | 4/5 | 1/5 | 112% |
| liquidation signature | long liquidation signature (open interest down, price down hard, perp volume heavy) | 30 | 23,526 | 0.96% | 55.5% | +5.1 [+3.6, +6.7] | 0.0159 | 4/5 | 1/5 | 106% |
| liquidation signature | short liquidation signature (open interest down, price up hard, perp volume heavy) | 1 | 17,395 | 0.71% | 47.0% | -4.4 [-5.2, -3.7] | 0.0040 | 5/5 | 5/5 | 90% |
| liquidation signature | short liquidation signature (open interest down, price up hard, perp volume heavy) | 3 | 17,395 | 0.71% | 46.6% | -3.8 [-4.8, -2.8] | 0.0080 | 5/5 | 2/5 | 98% |
| liquidation signature | short liquidation signature (open interest down, price up hard, perp volume heavy) | 5 | 17,395 | 0.71% | 45.9% | -4.3 [-5.5, -3.2] | 0.0159 | 5/5 | 1/5 | 89% |
| liquidation signature | short liquidation signature (open interest down, price up hard, perp volume heavy) | 10 | 17,395 | 0.71% | 46.5% | -3.7 [-5.0, -2.3] | 0.3546 | 5/5 | 0/5 | 109% |
| liquidation signature | short liquidation signature (open interest down, price up hard, perp volume heavy) | 15 | 17,395 | 0.71% | 45.8% | -4.4 [-5.9, -2.9] | 0.2390 | 5/5 | 0/5 | 107% |
| liquidation signature | short liquidation signature (open interest down, price up hard, perp volume heavy) | 30 | 17,395 | 0.71% | 47.3% | -3.1 [-4.7, -1.4] | 0.9203 | 5/5 | 0/5 | 98% |

Of 48 cells (8 events at 6 horizons), 15 hold their sign in every year. A search-wide adjusted p of at most 0.05 is reached in every scored year by 1 cells, in at least half of the scored years by 3 and in at least one year by 12; 3 cells hold their sign in every year and clear the null in at least half of the years.

Events with at least one cell that holds its sign in every year and clears the null in at least half of the years: open interest up over 15 minutes (top decile), open interest up over 60 minutes (top decile), short liquidation signature (open interest down, price up hard, perp volume heavy).

Events with at least one cell that holds its sign in every year: funding rate in the top decile of the previous year, open interest up over 15 minutes (top decile), open interest down over 15 minutes (bottom decile), open interest up over 60 minutes (top decile), open interest down over 60 minutes (bottom decile), long liquidation signature (open interest down, price down hard, perp volume heavy), short liquidation signature (open interest down, price up hard, perp volume heavy).

Among those 3 cells (interval excludes zero), the VWAP label keeps a median of 20% of the last-print deviation (range 1% to 90%).

The largest absolute pooled deviation is 5.1 points (long liquidation signature (open interest down, price down hard, perp volume heavy), 30 minutes); 27 of the 48 pooled 95% intervals exclude zero.

'funding rate in the top decile of the previous year' was scored in 2 of 5 years (fewer than 500 firings in the others).

Of the 3 cells that hold their sign in every year and clear the null in at least half of the years, 2 are at the 1-minute horizon and keep less than half of their deviation under the VWAP label: open interest up over 15 minutes (top decile) (retained 20%), open interest up over 60 minutes (top decile) (retained 1%).

'funding rate in the top decile of the previous year' fires on 0.00% of minutes in its quietest year (2022) and 19.40% in its busiest (2024).

'long liquidation signature (open interest down, price down hard, perp volume heavy)' fires on 0.58% of minutes in its quietest year (2022) and 1.44% in its busiest (2024).

Null: the largest |z| across all events and horizons on rotated labels has median 2.73 and 95th percentile 3.94; the real search's largest |z| is 7.34.

Funding at an extreme, read against the crowd (top decile: down is the reversal): at 5, 10, 15 and 30 minutes the pooled deviation runs from -0.3 to +0.3 points (reversal positive); 0 of 8 cells have an interval that excludes zero; cells holding their sign in every year: 1. Per year at 15 minutes, the oriented deviation runs from -0.6 to +0.7 points over 7 year-cells, 5 of them positive.

Liquidation signatures, a reversal of the forced move: at 5, 10, 15 and 30 minutes the pooled deviation runs from +3.1 to +5.1 points (reversal positive); 8 of 8 cells have an interval that excludes zero; cells holding their sign in every year: 4. Per year at 15 minutes, the oriented deviation runs from -4.1 to +9.1 points over 10 year-cells, 9 of them positive.

Open interest up over 15 or 60 minutes, top decile (deviation signed up): at 5, 10, 15 and 30 minutes the pooled deviation runs from -0.7 to +0.0 points (up positive); 1 of 8 cells have an interval that excludes zero; cells holding their sign in every year: 0. Per year at 15 minutes, the oriented deviation runs from -1.5 to +2.5 points over 10 year-cells, 5 of them positive.

Open interest down over 15 or 60 minutes, bottom decile (deviation signed up): at 5, 10, 15 and 30 minutes the pooled deviation runs from +0.4 to +1.7 points (up positive); 7 of 8 cells have an interval that excludes zero; cells holding their sign in every year: 1. Per year at 15 minutes, the oriented deviation runs from -0.5 to +2.4 points over 10 year-cells, 8 of them positive.

For scale, the largest deviation among the price-action library's cells that hold their sign in every year is 9.0 points (price_action_summary.csv).
