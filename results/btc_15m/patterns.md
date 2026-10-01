Rules mined from a random forest fit on 2025-10 to 2026-02, scored on 2026-03 to 2026-08 (never seen by the forest). Up-rate when the rule fires, day-block 95% interval, p for firing against non-firing windows with day-clustered errors, false-discovery correction across all 419 candidate rules, and month-by-month stability (at least three quarters of months agreeing). Only rules that survive the correction are listed.

Of 419 candidates, 262 survive the correction and 244 are also stable month by month. The 25 stable rules with the largest deviation are listed; every candidate is in patterns_rules.csv.

| rule | fires | share | up-rate [95% CI] | vs base (points) | p | survives FDR | months agreeing | by month | verdict |
|---|---|---|---|---|---|---|---|---|---|
| bb_pctb > 0.623 and flow15 > 0.139 and rsi60 > 55.1 and size5 > 1.16 | 537 | 3.0% | 34.8% [31.2, 38.3] | -14.8 | 0.000 | yes | 6/6 | -14.0 -15.6 -13.8 -18.1 -15.1 -13.0 | stable |
| rsi60 > 56.2 and size5 > 1.03 and win1 > 9.29 | 663 | 3.8% | 35.9% [32.6, 39.1] | -13.7 | 0.000 | yes | 6/6 | -16.3 -10.5 -19.3 -13.0 -9.2 -14.8 | stable |
| flow5 > 0.0168 and rsi14 > 53.5 and rsi60 > 56 and size5 > 1.01 | 746 | 4.2% | 36.1% [32.7, 39.3] | -13.6 | 0.000 | yes | 6/6 | -17.6 -14.1 -13.1 -11.0 -13.1 -13.3 | stable |
| flow15 <= -0.149 and nratio5 > 0.946 and rsi60 <= 47.6 and size5 > 1.06 | 426 | 2.4% | 61.5% [56.7, 65.7] | +11.9 | 0.000 | yes | 6/6 | +13.6 +16.3 +12.8 +12.0 +6.2 +11.8 | stable |
| ema_cross > 2.11 and rsi60 > 55.9 and size5 > 1.01 | 927 | 5.2% | 38.1% [35.0, 41.0] | -11.6 | 0.000 | yes | 6/6 | -16.6 -11.7 -12.4 -9.3 -7.7 -11.3 | stable |
| flow15 <= 0.141 and ret60 <= -74.3 and size5 <= 1.96 | 561 | 3.2% | 60.8% [56.6, 65.3] | +11.1 | 0.000 | yes | 6/6 | +11.6 +9.3 +0.7 +13.1 +6.9 +23.2 | stable |
| rangepos > 0.93 and rsi60 > 56.4 and vol60 <= 6.99 | 584 | 3.3% | 39.0% [35.5, 42.7] | -10.6 | 0.000 | yes | 6/6 | -13.9 -9.5 -8.0 -9.5 -12.9 -10.6 | stable |
| flow1 > -0.365 and rsi60 > 55.9 and size5 > 0.988 | 976 | 5.5% | 39.0% [35.9, 42.0] | -10.6 | 0.000 | yes | 6/6 | -11.9 -13.2 -9.8 -10.2 -11.5 -7.7 | stable |
| flow3 <= -0.171 and rsi14 <= 54.1 and vratio15 > 0.635 and vwap_dev60 <= -28.1 | 442 | 2.5% | 60.2% [55.5, 64.7] | +10.5 | 0.000 | yes | 6/6 | +12.1 +13.9 +0.7 +10.6 +14.1 +6.8 | stable |
| flow3 > 0.341 and rangepos > 0.892 | 539 | 3.1% | 39.5% [35.8, 43.0] | -10.1 | 0.000 | yes | 6/6 | -9.1 -7.8 -5.1 -11.3 -14.6 -13.3 | stable |
| bb_pctb <= 0.626 and ret60 <= -38.3 and rsi14 <= 32.6 | 516 | 2.9% | 59.7% [55.3, 63.9] | +10.1 | 0.000 | yes | 6/6 | +6.9 +9.0 +2.9 +15.5 +14.4 +10.8 | stable |
| ret60 <= -37.2 and rsi14 <= 32.7 | 537 | 3.0% | 59.6% [55.3, 63.4] | +10.0 | 0.000 | yes | 6/6 | +7.4 +8.8 +2.8 +14.9 +13.7 +11.5 | stable |
| flow15 <= 0.157 and ret60 <= -36.6 and rsi14 <= 32.6 | 525 | 3.0% | 59.6% [55.4, 63.8] | +10.0 | 0.000 | yes | 6/6 | +8.1 +8.8 +2.2 +14.6 +12.8 +12.7 | stable |
| bb_pctb > 0.627 and flow15 > 0.153 and rsi60 > 54.8 and vratio5 > 1.06 | 689 | 3.9% | 39.6% [36.1, 43.1] | -10.0 | 0.000 | yes | 6/6 | -10.1 -12.9 -8.3 -9.6 -7.0 -11.9 | stable |
| ema_cross > 0.0295 and hour <= 6.5 and rsi60 > 55.9 | 655 | 3.7% | 39.7% [35.7, 43.5] | -9.9 | 0.000 | yes | 6/6 | -11.9 -19.2 -8.1 -13.6 -6.9 -3.2 | stable |
| rsi14 <= 36.8 and rsi60 <= 44.5 and vol240 > 3.7 | 871 | 4.9% | 59.6% [56.8, 62.5] | +9.9 | 0.000 | yes | 6/6 | +11.9 +6.0 +9.5 +10.5 +10.7 +11.4 | stable |
| flow3 > 0.00848 and flow60 > -0.0749 and rsi14 > 59.6 and size5 > 1.16 | 766 | 4.3% | 39.9% [36.6, 43.3] | -9.7 | 0.000 | yes | 6/6 | -12.4 -10.3 -12.4 -2.3 -9.1 -9.9 | stable |
| ema_cross > -2.17 and flow60 > 0.182 and rsi60 > 55.9 | 812 | 4.6% | 40.1% [36.7, 43.2] | -9.5 | 0.000 | yes | 6/6 | -14.2 -10.5 -10.0 -9.4 -8.3 -6.4 | stable |
| flow15 > 0.166 and obv_slope60 > 0.218 | 1224 | 6.9% | 40.1% [37.4, 42.7] | -9.5 | 0.000 | yes | 6/6 | -10.3 -5.7 -9.3 -15.4 -8.6 -9.4 | stable |
| adx14 > 34.1 and rangepos <= 0.892 and stoch14 <= 0.436 and vratio5 > 1.17 | 608 | 3.4% | 59.0% [55.3, 63.0] | +9.4 | 0.000 | yes | 6/6 | +9.3 +5.1 +1.6 +13.2 +15.4 +12.4 | stable |
| bb_pctb > 0.836 and rsi14 > 36.9 and rsi60 > 56.9 | 750 | 4.2% | 40.3% [37.0, 43.4] | -9.4 | 0.000 | yes | 6/6 | -14.4 -6.3 -8.0 -1.3 -14.6 -10.6 | stable |
| flow15 <= 0.134 and rsi60 <= 55.9 and vol15 > 8.81 and win4 <= -9.51 | 347 | 2.0% | 58.8% [53.7, 64.0] | +9.2 | 0.001 | yes | 3/3 | +12.6 - - +7.8 - +13.6 | stable |
| rangepos <= 0.133 and rsi14 <= 36.9 and vol240 > 3.62 | 623 | 3.5% | 58.6% [54.9, 62.2] | +8.9 | 0.000 | yes | 6/6 | +7.6 +9.7 +5.6 +12.4 +9.5 +7.4 | stable |
| rsi14 <= 33.9 and rsi60 <= 51.5 and win2 <= -3.14 | 880 | 5.0% | 58.4% [55.1, 61.5] | +8.8 | 0.000 | yes | 6/6 | +15.4 +2.7 +3.1 +10.1 +6.3 +13.2 | stable |
| ema_cross > -0.768 and flow15 > 0.16 and macd_hist > 0.185 and rsi60 > 55.9 | 869 | 4.9% | 41.0% [37.7, 44.1] | -8.7 | 0.000 | yes | 6/6 | -8.6 -9.0 -7.8 -6.9 -11.0 -8.9 | stable |

Shapes of the last 60 minutes before the open (24 clusters found on the search months, scored on the later months). Each shape is described by its cumulative path in standard-deviation units.

| shape | fires | share | up-rate [95% CI] | vs base (points) | p | survives FDR | months agreeing | by month | verdict |
|---|---|---|---|---|---|---|---|---|---|
| shape 6: net +1.6 sd; first quarter up, second flat, third up, last quarter down | 659 | 3.7% | 43.2% [39.6, 46.9] | -6.4 | 0.001 | yes | 0/6 | -4.4 -11.5 -8.2 -3.9 -7.4 -3.0 |  |
| shape 20: net -2.6 sd; first quarter flat, second flat, third flat, last quarter down | 575 | 3.3% | 53.6% [49.9, 57.2] | +3.9 | 0.036 |  | 3/6 | -0.4 +14.6 +9.2 -5.3 +7.1 -0.3 |  |
| shape 10: net +0.6 sd; first quarter flat, second up, third flat, last quarter flat | 763 | 4.3% | 45.7% [41.9, 49.4] | -3.9 | 0.040 |  | 0/6 | -3.6 -2.8 -1.1 -3.3 -5.3 -7.6 |  |
| shape 19: net +2.0 sd; first quarter flat, second up, third flat, last quarter flat | 756 | 4.3% | 46.7% [43.4, 50.1] | -2.9 | 0.077 |  | 5/6 | -7.7 -8.0 +1.9 -0.7 -0.9 -1.3 |  |
| shape 16: net +2.0 sd; first quarter flat, second flat, third flat, last quarter up | 631 | 3.6% | 46.6% [42.9, 50.2] | -3.0 | 0.103 |  | 5/6 | -0.4 -7.2 -4.1 -7.4 +2.9 -3.0 |  |
| shape 4: net -1.1 sd; first quarter flat, second down, third flat, last quarter flat | 744 | 4.2% | 52.0% [48.7, 55.5] | +2.4 | 0.159 |  | 3/6 | -0.3 +7.5 -0.6 +9.5 +1.0 -2.0 |  |
| shape 21: net -2.5 sd; first quarter down, second flat, third flat, last quarter down | 798 | 4.5% | 51.6% [48.4, 54.9] | +2.0 | 0.242 |  | 4/6 | +4.9 -1.4 +4.4 +6.2 -7.5 +5.0 |  |
| shape 1: net -0.7 sd; first quarter down, second up, third flat, last quarter flat | 662 | 3.7% | 51.7% [48.1, 55.1] | +2.0 | 0.248 |  | 4/6 | +5.2 -0.5 +0.7 +2.4 -1.9 +5.8 |  |
| shape 12: net -2.3 sd; first quarter flat, second down, third flat, last quarter down | 741 | 4.2% | 51.7% [47.6, 55.6] | +2.0 | 0.290 |  | 4/6 | +5.9 +1.7 +7.6 -5.1 -0.5 +4.0 |  |
| shape 9: net +0.4 sd; first quarter up, second down, third flat, last quarter down | 658 | 3.7% | 51.5% [47.5, 55.5] | +1.9 | 0.343 |  | 2/6 | +8.0 -0.5 -2.2 +2.9 +2.4 +1.4 |  |
| shape 7: net -0.4 sd; first quarter flat, second down, third down, last quarter up | 832 | 4.7% | 48.2% [44.8, 51.7] | -1.4 | 0.402 |  | 4/6 | -7.0 -1.0 -2.7 -6.3 +3.0 +5.6 |  |
| shape 13: net -0.9 sd; first quarter up, second flat, third down, last quarter flat | 812 | 4.6% | 51.1% [47.6, 54.8] | +1.5 | 0.409 |  | 2/6 | +0.9 +1.5 -2.7 -0.3 +6.0 +2.3 |  |
| shape 3: net +1.4 sd; first quarter up, second down, third flat, last quarter flat | 705 | 4.0% | 48.4% [44.9, 52.1] | -1.3 | 0.495 |  | 4/6 | +9.2 -5.8 -7.1 +1.5 -4.2 -0.3 |  |
| shape 2: net +0.9 sd; first quarter flat, second up, third up, last quarter down | 797 | 4.5% | 48.6% [45.3, 51.8] | -1.1 | 0.502 |  | 2/6 | +1.1 -0.6 +0.7 -3.5 -3.1 -1.4 |  |
| shape 11: net -0.1 sd; first quarter flat, second up, third down, last quarter flat | 788 | 4.5% | 50.8% [47.4, 54.1] | +1.1 | 0.506 |  | 4/6 | -2.3 -0.6 +1.8 +0.9 +3.8 +2.3 |  |
| shape 18: net +1.9 sd; first quarter down, second up, third up, last quarter flat | 718 | 4.1% | 50.7% [47.2, 54.2] | +1.1 | 0.559 |  | 4/6 | +3.6 +7.1 +0.3 -6.1 -5.0 +3.8 |  |
| shape 14: net -2.8 sd; first quarter down, second down, third down, last quarter up | 789 | 4.5% | 48.7% [45.0, 52.6] | -1.0 | 0.598 |  | 3/6 | +0.8 -1.7 -9.8 -1.0 +6.2 +0.1 |  |
| shape 17: net +1.3 sd; first quarter up, second up, third down, last quarter down | 908 | 5.1% | 50.6% [47.0, 54.1] | +0.9 | 0.600 |  | 4/6 | -5.2 +2.1 +4.3 +5.3 +0.3 -2.8 |  |
| shape 22: net +1.8 sd; first quarter down, second up, third flat, last quarter up | 759 | 4.3% | 50.5% [46.5, 54.3] | +0.8 | 0.670 |  | 3/6 | -2.4 +5.1 +4.7 +3.8 -0.9 -3.5 |  |
| shape 5: net -1.3 sd; first quarter flat, second down, third flat, last quarter flat | 786 | 4.4% | 50.1% [46.3, 53.8] | +0.5 | 0.784 |  | 3/6 | +1.3 -1.3 -1.7 +5.4 +1.0 -1.0 |  |
| shape 0: net -0.7 sd; first quarter down, second down, third up, last quarter flat | 733 | 4.1% | 50.1% [46.8, 53.4] | +0.4 | 0.803 |  | 2/6 | -4.2 +5.6 -0.5 -5.6 +7.3 -3.5 |  |
| shape 15: net -1.3 sd; first quarter flat, second down, third up, last quarter flat | 662 | 3.7% | 50.0% [46.2, 53.6] | +0.4 | 0.851 |  | 3/6 | -1.0 -5.1 +3.0 +5.4 +0.8 -1.3 |  |
| shape 23: net +1.8 sd; first quarter down, second up, third up, last quarter flat | 763 | 4.3% | 49.8% [46.1, 53.4] | +0.2 | 0.927 |  | 4/6 | +3.9 +7.5 -3.1 -3.5 -3.9 -1.1 |  |
| shape 8: net -0.6 sd; first quarter down, second up, third flat, last quarter flat | 625 | 3.5% | 49.6% [45.7, 53.4] | -0.0 | 0.985 |  | 3/6 | -3.3 -7.2 +4.4 +5.2 +0.3 -0.3 |  |
