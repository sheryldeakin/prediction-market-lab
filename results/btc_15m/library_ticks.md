Tick-level events for the price-action library, 2018 to 2026-08, every minute as a decision time (definitions in models/btc_15m/library_events.py; every cutoff is a percentile of the previous year). For each event and horizon: minutes it fires on in all years, the share of minutes it fires on over the years in which it was scored (an event with fewer than 500 firings in a year is not scored in it, and the years columns count the scored years), the pooled up-rate of the next h minutes, the deviation from the unconditional up-rate in points with a 95% interval (day-clustered errors, years combined as independent), the smallest search-wide adjusted p across years (50 rotated-label runs per year; the smallest possible value is 0.0022), the years in which the sign matched the pooled sign out of years with at least 500 firings, the years with an adjusted p of at most 0.05, and the share of the last-print deviation kept under the 60-second VWAP label, shown only where the interval excludes zero because a ratio of two near-zero deviations means nothing (at 1 minute the VWAP label compares the two halves of the decision minute, a shorter question). Every cell is listed.

| family | event | horizon (min) | fires | share (scored years) | up-rate | deviation (points) [95% interval] | min adjusted p | years held | years p<=0.05 | VWAP retained |
|---|---|---|---|---|---|---|---|---|---|---|
| large trades | large-trade burst | 1 | 38,904 | 1.12% | 51.8% | +0.4 [-0.1, +0.9] | 0.8914 | 4/7 | 0/7 | - |
| large trades | large-trade burst | 3 | 38,904 | 1.12% | 51.1% | +0.8 [+0.3, +1.3] | 0.4390 | 6/7 | 0/7 | 50% |
| large trades | large-trade burst | 5 | 38,904 | 1.12% | 50.7% | +0.5 [-0.0, +1.1] | 0.9401 | 7/7 | 0/7 | - |
| large trades | large-trade burst | 10 | 38,904 | 1.12% | 50.6% | +0.5 [-0.1, +1.0] | 0.7738 | 5/7 | 0/7 | - |
| large trades | large-trade burst | 15 | 38,903 | 1.12% | 50.6% | +0.4 [-0.3, +1.0] | 0.7672 | 4/7 | 0/7 | - |
| large trades | large-trade burst | 30 | 38,903 | 1.12% | 50.4% | +0.0 [-0.7, +0.8] | 0.3592 | 3/7 | 0/7 | - |
| large trades | large-trade burst with net large buying | 1 | 18,384 | 0.53% | 50.6% | -0.8 [-1.5, +0.0] | 0.0266 | 4/7 | 1/7 | - |
| large trades | large-trade burst with net large buying | 3 | 18,384 | 0.53% | 49.7% | -0.7 [-1.5, +0.1] | 0.0222 | 4/7 | 1/7 | - |
| large trades | large-trade burst with net large buying | 5 | 18,384 | 0.53% | 49.0% | -1.2 [-2.0, -0.5] | 0.0133 | 5/7 | 1/7 | 98% |
| large trades | large-trade burst with net large buying | 10 | 18,384 | 0.53% | 48.9% | -1.2 [-2.1, -0.4] | 0.0155 | 6/7 | 1/7 | 101% |
| large trades | large-trade burst with net large buying | 15 | 18,383 | 0.53% | 48.6% | -1.6 [-2.4, -0.7] | 0.0333 | 5/7 | 1/7 | 119% |
| large trades | large-trade burst with net large buying | 30 | 18,383 | 0.53% | 49.1% | -1.3 [-2.2, -0.4] | 0.3193 | 5/7 | 0/7 | 95% |
| large trades | large-trade burst with net large selling | 1 | 20,520 | 0.59% | 52.8% | +1.5 [+0.8, +2.1] | 0.0177 | 5/7 | 1/7 | 76% |
| large trades | large-trade burst with net large selling | 3 | 20,520 | 0.59% | 52.4% | +2.1 [+1.4, +2.8] | 0.0266 | 7/7 | 1/7 | 79% |
| large trades | large-trade burst with net large selling | 5 | 20,520 | 0.59% | 52.3% | +2.1 [+1.3, +2.8] | 0.0266 | 5/7 | 1/7 | 93% |
| large trades | large-trade burst with net large selling | 10 | 20,520 | 0.59% | 52.1% | +2.0 [+1.2, +2.8] | 0.2993 | 7/7 | 0/7 | 122% |
| large trades | large-trade burst with net large selling | 15 | 20,520 | 0.59% | 52.3% | +2.1 [+1.2, +3.0] | 0.2350 | 7/7 | 0/7 | 91% |
| large trades | large-trade burst with net large selling | 30 | 20,520 | 0.59% | 51.6% | +1.2 [+0.2, +2.2] | 0.3902 | 7/7 | 0/7 | 77% |
| imbalance persistence | net taker buying in each of the last 3 minutes | 1 | 681,134 | 15.12% | 50.9% | +0.0 [-0.1, +0.2] | 0.0022 | 4/9 | 5/9 | - |
| imbalance persistence | net taker buying in each of the last 3 minutes | 3 | 681,129 | 15.12% | 49.4% | -0.9 [-1.0, -0.7] | 0.0022 | 8/9 | 5/9 | 135% |
| imbalance persistence | net taker buying in each of the last 3 minutes | 5 | 681,128 | 15.12% | 49.1% | -1.1 [-1.3, -1.0] | 0.0022 | 8/9 | 6/9 | 136% |
| imbalance persistence | net taker buying in each of the last 3 minutes | 10 | 681,126 | 15.12% | 49.0% | -1.3 [-1.4, -1.1] | 0.0022 | 9/9 | 5/9 | 130% |
| imbalance persistence | net taker buying in each of the last 3 minutes | 15 | 681,114 | 15.12% | 49.1% | -1.3 [-1.4, -1.1] | 0.0044 | 9/9 | 6/9 | 127% |
| imbalance persistence | net taker buying in each of the last 3 minutes | 30 | 681,090 | 15.12% | 49.1% | -1.4 [-1.6, -1.3] | 0.0022 | 9/9 | 7/9 | 116% |
| imbalance persistence | net taker selling in each of the last 3 minutes | 1 | 703,770 | 15.62% | 51.2% | +0.2 [+0.1, +0.4] | 0.0022 | 5/9 | 3/9 | 83% |
| imbalance persistence | net taker selling in each of the last 3 minutes | 3 | 703,767 | 15.62% | 51.4% | +1.1 [+1.0, +1.3] | 0.0022 | 8/9 | 6/9 | 129% |
| imbalance persistence | net taker selling in each of the last 3 minutes | 5 | 703,767 | 15.62% | 51.5% | +1.3 [+1.2, +1.5] | 0.0022 | 9/9 | 7/9 | 125% |
| imbalance persistence | net taker selling in each of the last 3 minutes | 10 | 703,763 | 15.62% | 51.8% | +1.5 [+1.4, +1.7] | 0.0022 | 9/9 | 7/9 | 118% |
| imbalance persistence | net taker selling in each of the last 3 minutes | 15 | 703,762 | 15.62% | 51.8% | +1.5 [+1.3, +1.7] | 0.0022 | 9/9 | 8/9 | 115% |
| imbalance persistence | net taker selling in each of the last 3 minutes | 30 | 703,748 | 15.62% | 52.2% | +1.7 [+1.5, +1.8] | 0.0022 | 9/9 | 8/9 | 111% |
| imbalance persistence | net taker buying in each of the last 5 minutes | 1 | 237,980 | 5.28% | 50.9% | +0.0 [-0.2, +0.2] | 0.0067 | 3/9 | 2/9 | - |
| imbalance persistence | net taker buying in each of the last 5 minutes | 3 | 237,980 | 5.28% | 49.1% | -1.2 [-1.4, -0.9] | 0.0200 | 8/9 | 4/9 | 127% |
| imbalance persistence | net taker buying in each of the last 5 minutes | 5 | 237,980 | 5.28% | 48.6% | -1.6 [-1.9, -1.3] | 0.0133 | 8/9 | 5/9 | 132% |
| imbalance persistence | net taker buying in each of the last 5 minutes | 10 | 237,979 | 5.28% | 48.5% | -1.8 [-2.1, -1.4] | 0.0067 | 9/9 | 4/9 | 125% |
| imbalance persistence | net taker buying in each of the last 5 minutes | 15 | 237,974 | 5.28% | 48.6% | -1.7 [-2.0, -1.4] | 0.0200 | 9/9 | 3/9 | 124% |
| imbalance persistence | net taker buying in each of the last 5 minutes | 30 | 237,965 | 5.28% | 48.8% | -1.8 [-2.1, -1.4] | 0.0067 | 9/9 | 4/9 | 114% |
| imbalance persistence | net taker selling in each of the last 5 minutes | 1 | 248,348 | 5.51% | 51.3% | +0.4 [+0.2, +0.6] | 0.0022 | 5/9 | 2/9 | 97% |
| imbalance persistence | net taker selling in each of the last 5 minutes | 3 | 248,348 | 5.51% | 51.9% | +1.6 [+1.4, +1.9] | 0.0022 | 8/9 | 4/9 | 112% |
| imbalance persistence | net taker selling in each of the last 5 minutes | 5 | 248,348 | 5.51% | 52.0% | +1.8 [+1.6, +2.1] | 0.0044 | 9/9 | 5/9 | 118% |
| imbalance persistence | net taker selling in each of the last 5 minutes | 10 | 248,348 | 5.51% | 52.2% | +2.0 [+1.6, +2.3] | 0.0089 | 9/9 | 5/9 | 113% |
| imbalance persistence | net taker selling in each of the last 5 minutes | 15 | 248,347 | 5.51% | 52.2% | +1.9 [+1.6, +2.3] | 0.0067 | 9/9 | 2/9 | 114% |
| imbalance persistence | net taker selling in each of the last 5 minutes | 30 | 248,341 | 5.51% | 52.6% | +2.1 [+1.8, +2.5] | 0.0067 | 9/9 | 4/9 | 107% |
| trade count | trade-count climax | 1 | 234,701 | 5.21% | 50.5% | -0.1 [-0.3, +0.1] | 0.0067 | 4/9 | 3/9 | - |
| trade count | trade-count climax | 3 | 234,699 | 5.21% | 50.4% | +0.2 [-0.0, +0.5] | 0.0288 | 6/9 | 2/9 | - |
| trade count | trade-count climax | 5 | 234,699 | 5.21% | 50.7% | +0.5 [+0.2, +0.7] | 0.0200 | 6/9 | 2/9 | 121% |
| trade count | trade-count climax | 10 | 234,699 | 5.21% | 51.1% | +0.8 [+0.5, +1.1] | 0.0067 | 7/9 | 2/9 | 116% |
| trade count | trade-count climax | 15 | 234,698 | 5.21% | 51.3% | +0.9 [+0.5, +1.3] | 0.0067 | 8/9 | 2/9 | 102% |
| trade count | trade-count climax | 30 | 234,694 | 5.21% | 51.6% | +1.0 [+0.5, +1.5] | 0.0222 | 8/9 | 1/9 | 109% |
| trade count | trade-count climax at a new 1h high | 1 | 36,486 | 0.92% | 48.1% | -2.4 [-3.0, -1.9] | 0.0067 | 7/8 | 2/8 | 119% |
| trade count | trade-count climax at a new 1h high | 3 | 36,484 | 0.92% | 44.9% | -5.3 [-5.9, -4.7] | 0.0022 | 7/8 | 5/8 | 113% |
| trade count | trade-count climax at a new 1h high | 5 | 36,484 | 0.92% | 44.0% | -6.3 [-6.9, -5.6] | 0.0022 | 7/8 | 5/8 | 115% |
| trade count | trade-count climax at a new 1h high | 10 | 36,484 | 0.92% | 43.4% | -6.9 [-7.6, -6.2] | 0.0022 | 8/8 | 5/8 | 114% |
| trade count | trade-count climax at a new 1h high | 15 | 36,484 | 0.92% | 43.9% | -6.5 [-7.2, -5.8] | 0.0022 | 8/8 | 4/8 | 110% |
| trade count | trade-count climax at a new 1h high | 30 | 36,484 | 0.92% | 43.7% | -7.0 [-7.8, -6.2] | 0.0022 | 8/8 | 5/8 | 109% |
| trade count | trade-count climax at a new 1h low | 1 | 40,113 | 1.01% | 53.8% | +3.3 [+2.7, +3.8] | 0.0022 | 6/8 | 4/8 | 114% |
| trade count | trade-count climax at a new 1h low | 3 | 40,113 | 1.01% | 56.7% | +6.5 [+6.0, +7.1] | 0.0022 | 8/8 | 6/8 | 108% |
| trade count | trade-count climax at a new 1h low | 5 | 40,113 | 1.01% | 57.8% | +7.6 [+7.0, +8.2] | 0.0022 | 8/8 | 6/8 | 112% |
| trade count | trade-count climax at a new 1h low | 10 | 40,113 | 1.01% | 58.7% | +8.4 [+7.8, +9.1] | 0.0022 | 8/8 | 6/8 | 112% |
| trade count | trade-count climax at a new 1h low | 15 | 40,112 | 1.01% | 58.4% | +8.0 [+7.3, +8.7] | 0.0022 | 8/8 | 6/8 | 107% |
| trade count | trade-count climax at a new 1h low | 30 | 40,110 | 1.01% | 59.1% | +8.5 [+7.7, +9.2] | 0.0022 | 8/8 | 5/8 | 107% |
| trade count | trade-count climax with no new 1h high or low | 1 | 157,126 | 3.95% | 50.2% | -0.4 [-0.6, -0.2] | 0.0266 | 5/8 | 1/8 | 10% |
| trade count | trade-count climax with no new 1h high or low | 3 | 157,126 | 3.95% | 50.1% | -0.1 [-0.4, +0.2] | 0.1308 | 3/8 | 0/8 | - |
| trade count | trade-count climax with no new 1h high or low | 5 | 157,126 | 3.95% | 50.4% | +0.2 [-0.2, +0.5] | 0.0754 | 5/8 | 0/8 | - |
| trade count | trade-count climax with no new 1h high or low | 10 | 157,126 | 3.95% | 51.0% | +0.6 [+0.2, +1.0] | 0.0599 | 6/8 | 0/8 | 124% |
| trade count | trade-count climax with no new 1h high or low | 15 | 157,126 | 3.95% | 51.2% | +0.8 [+0.3, +1.3] | 0.0355 | 7/8 | 1/8 | 104% |
| trade count | trade-count climax with no new 1h high or low | 30 | 157,124 | 3.95% | 51.5% | +0.9 [+0.3, +1.5] | 0.1020 | 6/8 | 0/8 | 113% |

Of 66 cells (11 events at 6 horizons), 27 hold their sign in every year. A search-wide adjusted p of at most 0.05 is reached in every scored year by 0 cells, in at least half of the scored years by 25 and in at least one year by 52; 17 cells hold their sign in every year and clear the null in at least half of the years.

Events with at least one cell that holds its sign in every year and clears the null in at least half of the years: net taker buying in each of the last 3 minutes, net taker selling in each of the last 3 minutes, net taker selling in each of the last 5 minutes, trade-count climax at a new 1h high, trade-count climax at a new 1h low.

Events with at least one cell that holds its sign in every year: large-trade burst, large-trade burst with net large selling, net taker buying in each of the last 3 minutes, net taker selling in each of the last 3 minutes, net taker buying in each of the last 5 minutes, net taker selling in each of the last 5 minutes, trade-count climax at a new 1h high, trade-count climax at a new 1h low.

Among those 17 cells (interval excludes zero), the VWAP label keeps a median of 113% of the last-print deviation (range 107% to 130%).

The largest absolute pooled deviation is 8.5 points (trade-count climax at a new 1h low, 30 minutes); 53 of the 66 pooled 95% intervals exclude zero.

'large-trade burst' was scored in 7 of 9 years (fewer than 500 firings in the others).

'large-trade burst with net large buying' was scored in 7 of 9 years (fewer than 500 firings in the others).

'large-trade burst with net large selling' was scored in 7 of 9 years (fewer than 500 firings in the others).

'trade-count climax at a new 1h high' was scored in 8 of 9 years (fewer than 500 firings in the others).

'trade-count climax at a new 1h low' was scored in 8 of 9 years (fewer than 500 firings in the others).

'trade-count climax with no new 1h high or low' was scored in 8 of 9 years (fewer than 500 firings in the others).

Of the 17 cells that hold their sign in every year and clear the null in at least half of the years, 0 are at the 1-minute horizon and keep less than half of their deviation under the VWAP label: none.

'trade-count climax' fires on 0.19% of minutes in its quietest year (2024) and 22.23% in its busiest (2018).

'large-trade burst' fires on 0.02% of minutes in its quietest year (2018) and 1.75% in its busiest (2023).

Null: the largest |z| across all events and horizons on rotated labels has median 2.64 and 95th percentile 4.30; the real search's largest |z| is 15.12.

A reversal from a price extreme on heavy trading: at 5, 10, 15 and 30 minutes the pooled deviation runs from +6.3 to +8.5 points (reversal positive); 8 of 8 cells have an interval that excludes zero; cells holding their sign in every year: 7. Per year at 15 minutes, the oriented deviation runs from +1.1 to +11.4 points over 16 year-cells, 16 of them positive.

The same side of the flow for several minutes: at 5, 10, 15 and 30 minutes the pooled deviation runs from +1.1 to +2.1 points (reversal positive); 16 of 16 cells have an interval that excludes zero; cells holding their sign in every year: 14. Per year at 15 minutes, the oriented deviation runs from +0.5 to +3.8 points over 36 year-cells, 36 of them positive.

Large-trade bursts split by the side of the large trades: at 5, 10, 15 and 30 minutes the pooled deviation runs from +1.2 to +2.1 points (reversal positive); 8 of 8 cells have an interval that excludes zero; cells holding their sign in every year: 3. Per year at 15 minutes, the oriented deviation runs from -0.9 to +5.3 points over 14 year-cells, 12 of them positive.

Events with no side (deviation signed up): at 5, 10, 15 and 30 minutes the pooled deviation runs from +0.0 to +1.0 points (up positive); 7 of 12 cells have an interval that excludes zero; cells holding their sign in every year: 1. Per year at 15 minutes, the oriented deviation runs from -1.0 to +4.0 points over 24 year-cells, 19 of them positive.

For scale, the largest deviation among the price-action library's cells that hold their sign in every year is 9.0 points (price_action_summary.csv).
