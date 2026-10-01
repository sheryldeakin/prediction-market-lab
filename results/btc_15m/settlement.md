Minute-0 accuracy under three labels, 2025-10 to 2026-08, walk-forward by month. 'Last print' is the main label; the VWAP labels use 60-second volume-weighted prices from the tick data, either ending at each boundary or inside the window's first and last minute. 'Own previous label' calls the opposite of (or the same as, whichever the training months favour) the previous window's label under the same definition. Intervals: day blocks, then month blocks. The last column is the forest minus the own-previous-label baseline, day-block interval, and the share of days the forest wins.

| label | agrees with last print | share up | model | n | accuracy [day CI] [month CI] | forest vs own previous label |
|---|---|---|---|---|---|---|
| last print | 100.0% | 49.7% | own previous label | 23328 | 52.21% [51.63, 52.82] [51.67, 52.77] |  |
| last print | 100.0% | 49.7% | prev-window (candles) | 23328 | 52.21% [51.63, 52.82] [51.67, 52.77] |  |
| last print | 100.0% | 49.7% | forest | 23328 | 52.83% [52.21, 53.47] [52.58, 53.09] | +0.62 [-0.04, +1.29], days better 55% |
| vwap_end | 94.3% | 49.8% | own previous label | 23328 | 52.12% [51.49, 52.75] [51.46, 52.81] |  |
| vwap_end | 94.3% | 49.8% | prev-window (candles) | 23328 | 51.53% [50.90, 52.18] [50.95, 52.17] |  |
| vwap_end | 94.3% | 49.8% | forest | 23328 | 52.86% [52.22, 53.51] [52.32, 53.35] | +0.74 [+0.04, +1.47], days better 54% |
| vwap_in | 93.0% | 49.7% | own previous label | 23328 | 52.54% [51.90, 53.19] [51.80, 53.34] |  |
| vwap_in | 93.0% | 49.7% | prev-window (candles) | 23328 | 52.68% [52.07, 53.30] [52.00, 53.41] |  |
| vwap_in | 93.0% | 49.7% | forest | 23328 | 53.18% [52.51, 53.82] [52.57, 53.82] | +0.63 [-0.06, +1.37], days better 53% |
