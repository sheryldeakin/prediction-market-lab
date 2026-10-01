Event library: up-rate of the window when the condition holds at the entry minute, against the unconditional rate. Day-block 95% intervals; p compares windows where the event fires with windows where it does not, with day-clustered errors; 'survives FDR' marks events that pass Benjamini-Hochberg at a 10% false discovery rate across all events tested at that minute. Events that fire fewer than 300 times are omitted.

| minute | if | fires | share | up-rate [95% CI] | vs base (points) | p | survives FDR |
|---|---|---|---|---|---|---|---|
| 0 | upper quarter of 4h range | 7948 | 24.8% | 44.9% [43.9, 45.8] | -4.9 | 0.000 | yes |
| 0 | lower quarter of 4h range | 7388 | 23.0% | 54.3% [53.1, 55.6] | +4.5 | 0.000 | yes |
| 0 | previous window up | 15922 | 49.7% | 47.5% [46.8, 48.2] | -2.2 | 0.000 | yes |
| 0 | previous window down | 16137 | 50.3% | 51.9% [51.2, 52.6] | +2.2 | 0.000 | yes |
| 0 | taker buying 60 pct+ of last 15 min | 6289 | 19.6% | 44.8% [43.8, 46.0] | -4.9 | 0.000 | yes |
| 0 | two windows down in a row | 7770 | 24.2% | 53.3% [52.4, 54.4] | +3.6 | 0.000 | yes |
| 0 | two windows up in a row | 7555 | 23.6% | 46.4% [45.4, 47.4] | -3.3 | 0.000 | yes |
| 0 | taker selling 60 pct+ of last 15 min | 7496 | 23.4% | 53.2% [52.1, 54.3] | +3.5 | 0.000 | yes |
| 0 | 4h return above +50 bp | 6792 | 21.2% | 46.6% [45.4, 47.6] | -3.2 | 0.000 | yes |
| 0 | OBV rising over 60 min | 2366 | 7.4% | 44.0% [42.1, 45.9] | -5.8 | 0.000 | yes |
| 0 | price 30 bp+ below 60-min VWAP | 2105 | 6.6% | 56.0% [53.7, 58.2] | +6.2 | 0.000 | yes |
| 0 | three windows up in a row | 3501 | 10.9% | 45.4% [43.9, 46.9] | -4.3 | 0.000 | yes |
| 0 | RSI14 below 30 | 1391 | 4.3% | 57.3% [54.7, 59.9] | +7.6 | 0.000 | yes |
| 0 | price at 4h high (rangepos >= 0.98) | 539 | 1.7% | 38.4% [34.3, 42.5] | -11.3 | 0.000 | yes |
| 0 | MACD histogram positive | 15925 | 49.7% | 48.2% [47.6, 48.9] | -1.5 | 0.000 | yes |
| 0 | MACD histogram negative | 16134 | 50.3% | 51.2% [50.5, 51.9] | +1.5 | 0.000 | yes |
| 0 | EMA9 below EMA21 by 10 bp | 1610 | 5.0% | 56.6% [54.3, 59.1] | +6.9 | 0.000 | yes |
| 0 | RSI14 above 70 | 1295 | 4.0% | 42.9% [40.4, 45.3] | -6.9 | 0.000 | yes |
| 0 | OBV falling over 60 min | 2884 | 9.0% | 54.2% [52.6, 56.0] | +4.5 | 0.000 | yes |
| 0 | 4h return below -50 bp | 6941 | 21.7% | 52.4% [51.2, 53.7] | +2.7 | 0.000 | yes |
| 0 | last 15 min up more than 2 sd | 718 | 2.2% | 40.9% [37.7, 44.5] | -8.8 | 0.000 | yes |
| 0 | three windows down in a row | 3635 | 11.3% | 53.7% [52.0, 55.3] | +3.9 | 0.000 | yes |
| 0 | EMA9 above EMA21 by 10 bp | 1515 | 4.7% | 43.3% [40.7, 46.0] | -6.4 | 0.000 | yes |
| 0 | last 15 min down more than 2 sd | 812 | 2.5% | 58.4% [54.7, 62.0] | +8.6 | 0.000 | yes |
| 0 | last 5 min up more than 2 sd | 688 | 2.1% | 42.0% [38.3, 45.6] | -7.7 | 0.000 | yes |
| 0 | price 30 bp+ above 60-min VWAP | 2190 | 6.8% | 45.7% [43.6, 47.9] | -4.0 | 0.000 | yes |
| 0 | below lower Bollinger band | 1271 | 4.0% | 54.5% [51.8, 57.4] | +4.8 | 0.001 | yes |
| 0 | price at 4h low (rangepos <= 0.02) | 521 | 1.6% | 55.7% [51.3, 59.6] | +5.9 | 0.006 | yes |
| 0 | last 5 min down more than 2 sd | 688 | 2.1% | 54.4% [50.6, 58.2] | +4.6 | 0.012 | yes |
| 0 | above upper Bollinger band | 1224 | 3.8% | 46.7% [44.1, 49.6] | -3.0 | 0.033 | yes |
| 0 | volume last 5 min 3x the daily average | 1524 | 4.8% | 47.2% [44.8, 49.6] | -2.5 | 0.042 | yes |
| 0 | low volatility (vol60 in bottom decile) | 4407 | 13.7% | 50.8% [49.7, 52.0] | +1.1 | 0.059 | yes |
| 0 | weekend | 9216 | 28.7% | 50.3% [49.6, 51.1] | +0.6 | 0.088 |  |
| 0 | US afternoon (14-17 UTC) | 5344 | 16.7% | 50.7% [49.4, 52.0] | +1.0 | 0.106 |  |
| 0 | Asia early (0-3 UTC) | 5339 | 16.7% | 48.9% [47.7, 50.0] | -0.8 | 0.132 |  |
| 0 | ADX14 below 15 (ranging) | 3962 | 12.4% | 48.8% [47.1, 50.5] | -1.0 | 0.217 |  |
| 0 | high volatility (vol60 in top decile) | 3029 | 9.4% | 50.4% [48.6, 52.3] | +0.7 | 0.424 |  |
| 0 | ADX14 above 30 (trending) | 9570 | 29.9% | 50.1% [49.1, 50.9] | +0.3 | 0.451 |  |
| 0 | trade count last 5 min 3x average | 808 | 2.5% | 48.8% [45.9, 51.8] | -1.0 | 0.525 |  |
| 3 | price at 4h high (rangepos >= 0.98) | 513 | 1.6% | 68.8% [64.9, 72.5] | +19.1 | 0.000 | yes |
| 3 | price at 4h low (rangepos <= 0.02) | 571 | 1.8% | 29.4% [25.8, 33.2] | -20.3 | 0.000 | yes |
| 3 | last 5 min up more than 2 sd | 864 | 2.7% | 81.9% [79.3, 84.4] | +32.2 | 0.000 | yes |
| 3 | last 5 min down more than 2 sd | 895 | 2.8% | 18.8% [16.2, 21.4] | -31.0 | 0.000 | yes |
| 3 | last 15 min up more than 2 sd | 692 | 2.2% | 67.2% [63.8, 70.7] | +17.5 | 0.000 | yes |
| 3 | previous window up | 15922 | 49.7% | 47.5% [46.8, 48.2] | -2.2 | 0.000 | yes |
| 3 | previous window down | 16137 | 50.3% | 51.9% [51.2, 52.6] | +2.2 | 0.000 | yes |
| 3 | RSI14 above 70 | 1361 | 4.2% | 73.3% [71.1, 75.5] | +23.5 | 0.000 | yes |
| 3 | RSI14 below 30 | 1508 | 4.7% | 28.6% [26.2, 31.1] | -21.2 | 0.000 | yes |
| 3 | MACD histogram positive | 15631 | 48.8% | 57.7% [57.0, 58.4] | +8.0 | 0.000 | yes |
| 3 | MACD histogram negative | 16428 | 51.2% | 42.2% [41.5, 42.8] | -7.6 | 0.000 | yes |
| 3 | above upper Bollinger band | 1827 | 5.7% | 79.5% [77.6, 81.3] | +29.7 | 0.000 | yes |
| 3 | below lower Bollinger band | 1956 | 6.1% | 20.0% [18.2, 21.6] | -29.7 | 0.000 | yes |
| 3 | price 30 bp+ above 60-min VWAP | 2177 | 6.8% | 59.8% [58.0, 61.7] | +10.1 | 0.000 | yes |
| 3 | price 30 bp+ below 60-min VWAP | 2169 | 6.8% | 41.2% [39.3, 43.1] | -8.5 | 0.000 | yes |
| 3 | leading by 10 bp+ at entry | 3760 | 11.7% | 78.6% [77.2, 79.9] | +28.9 | 0.000 | yes |
| 3 | trailing by 10 bp+ at entry | 4039 | 12.6% | 22.8% [21.4, 24.2] | -26.9 | 0.000 | yes |
| 3 | last 15 min down more than 2 sd | 703 | 2.2% | 35.6% [32.2, 39.0] | -14.2 | 0.000 | yes |
| 3 | two windows down in a row | 7770 | 24.2% | 53.3% [52.4, 54.4] | +3.6 | 0.000 | yes |
| 3 | two windows up in a row | 7555 | 23.6% | 46.4% [45.4, 47.4] | -3.3 | 0.000 | yes |
| 3 | three windows up in a row | 3501 | 10.9% | 45.4% [43.9, 46.9] | -4.3 | 0.000 | yes |
| 3 | upper quarter of 4h range | 7947 | 24.8% | 52.0% [51.1, 52.9] | +2.2 | 0.000 | yes |
| 3 | three windows down in a row | 3635 | 11.3% | 53.7% [52.0, 55.3] | +3.9 | 0.000 | yes |
| 3 | taker selling 60 pct+ of last 15 min | 7439 | 23.2% | 47.4% [46.3, 48.5] | -2.3 | 0.000 | yes |
| 3 | lower quarter of 4h range | 7398 | 23.1% | 47.6% [46.6, 48.7] | -2.2 | 0.000 | yes |
| 3 | taker buying 60 pct+ of last 15 min | 6139 | 19.1% | 51.9% [50.7, 53.2] | +2.2 | 0.000 | yes |
| 3 | EMA9 below EMA21 by 10 bp | 1553 | 4.8% | 45.9% [43.7, 48.3] | -3.8 | 0.001 | yes |
| 3 | EMA9 above EMA21 by 10 bp | 1484 | 4.6% | 53.6% [51.0, 56.2] | +3.9 | 0.002 | yes |
| 3 | weekend | 9216 | 28.7% | 50.3% [49.6, 51.1] | +0.6 | 0.088 |  |
| 3 | US afternoon (14-17 UTC) | 5344 | 16.7% | 50.7% [49.4, 52.0] | +1.0 | 0.106 |  |
| 3 | Asia early (0-3 UTC) | 5339 | 16.7% | 48.9% [47.7, 50.0] | -0.8 | 0.132 |  |
| 3 | ADX14 below 15 (ranging) | 3886 | 12.1% | 48.7% [47.1, 50.3] | -1.1 | 0.157 |  |
| 3 | ADX14 above 30 (trending) | 9535 | 29.7% | 50.2% [49.3, 51.1] | +0.5 | 0.211 |  |
| 3 | high volatility (vol60 in top decile) | 3025 | 9.4% | 50.8% [49.0, 52.8] | +1.1 | 0.231 |  |
| 3 | low volatility (vol60 in bottom decile) | 4454 | 13.9% | 50.3% [49.1, 51.5] | +0.6 | 0.306 |  |
| 3 | OBV rising over 60 min | 2281 | 7.1% | 50.7% [48.7, 52.6] | +0.9 | 0.331 |  |
| 3 | volume last 5 min 3x the daily average | 1795 | 5.6% | 48.7% [46.7, 50.9] | -1.0 | 0.362 |  |
| 3 | 4h return below -50 bp | 6935 | 21.6% | 49.4% [48.4, 50.6] | -0.3 | 0.557 |  |
| 3 | trade count last 5 min 3x average | 1136 | 3.5% | 50.5% [48.0, 53.2] | +0.8 | 0.562 |  |
| 3 | within 2 bp of the open at entry | 7520 | 23.5% | 49.9% [48.8, 51.0] | +0.2 | 0.667 |  |
| 3 | OBV falling over 60 min | 2858 | 8.9% | 49.5% [47.8, 51.3] | -0.2 | 0.823 |  |
| 3 | 4h return above +50 bp | 6762 | 21.1% | 49.7% [48.6, 50.8] | -0.0 | 0.953 |  |

Stability of the survivors: the deviation of the up-rate from that month's base rate, month by month after the three reference months, and how many of those months agree with the direction the event had in the reference months. Stable means at least three quarters agree.

| minute | if | overall | direction in reference months | months agreeing | deviation by month (points) | verdict |
|---|---|---|---|---|---|---|
| 0 | price at 4h high (rangepos >= 0.98) | down by 11.3 points overall | down | 7/7 | -4.9 - -12.8 -12.2 -17.6 -13.3 -21.7 -15.3 | stable |
| 0 | price at 4h low (rangepos <= 0.02) | up by 5.9 points overall | up | 6/8 | +12.5 +7.6 +6.7 -4.3 +4.2 +17.1 +2.3 -0.3 | stable |
| 0 | upper quarter of 4h range | down by 4.9 points overall | down | 8/8 | -7.1 -2.9 -7.7 -4.6 -5.4 -5.1 -4.6 -3.7 | stable |
| 0 | lower quarter of 4h range | up by 4.5 points overall | up | 8/8 | +5.4 +5.5 +6.9 +6.2 +4.7 +5.3 +3.9 +1.2 | stable |
| 0 | last 5 min up more than 2 sd | down by 7.7 points overall | down | 8/8 | -15.5 -2.4 -10.8 -3.8 -18.0 -12.0 -2.6 -7.0 | stable |
| 0 | last 5 min down more than 2 sd | up by 4.6 points overall | up | 6/8 | +10.4 -1.2 +0.1 +8.2 +3.0 +11.7 -5.3 +9.1 | stable |
| 0 | last 15 min up more than 2 sd | down by 8.8 points overall | down | 6/8 | -11.4 -14.7 -18.0 +0.6 -7.6 +3.4 -1.2 -14.4 | stable |
| 0 | last 15 min down more than 2 sd | up by 8.6 points overall | up | 8/8 | +0.7 +12.3 +9.4 +15.7 +3.0 +11.1 +1.8 +15.5 | stable |
| 0 | 4h return above +50 bp | down by 3.2 points overall | down | 7/8 | -6.3 -2.7 -2.9 -3.4 -5.4 -3.0 -5.7 +0.0 | stable |
| 0 | 4h return below -50 bp | up by 2.7 points overall | up | 8/8 | +1.6 +2.3 +4.8 +4.6 +6.8 +1.6 +5.9 +1.4 | stable |
| 0 | previous window up | down by 2.2 points overall | down | 8/8 | -3.3 -3.0 -1.1 -3.0 -2.0 -2.9 -1.8 -1.1 | stable |
| 0 | previous window down | up by 2.2 points overall | up | 8/8 | +3.2 +3.0 +1.1 +3.1 +1.9 +2.6 +1.8 +1.1 | stable |
| 0 | two windows up in a row | down by 3.3 points overall | down | 8/8 | -6.4 -3.6 -3.6 -3.8 -3.6 -4.3 -2.3 -3.3 | stable |
| 0 | two windows down in a row | up by 3.6 points overall | up | 8/8 | +4.6 +5.2 +4.9 +3.6 +3.1 +2.2 +4.8 +3.3 | stable |
| 0 | three windows up in a row | down by 4.3 points overall | down | 7/8 | -10.2 -4.4 -7.8 -1.9 -1.3 -8.3 +0.3 -5.1 | stable |
| 0 | three windows down in a row | up by 3.9 points overall | up | 8/8 | +5.6 +7.0 +2.5 +3.9 +2.6 +3.9 +5.9 +4.6 | stable |
| 0 | RSI14 above 70 | down by 6.9 points overall | down | 8/8 | -8.9 -11.9 -5.4 -5.3 -7.4 -1.2 -5.6 -2.2 | stable |
| 0 | RSI14 below 30 | up by 7.6 points overall | up | 8/8 | +9.9 +5.4 +1.9 +10.1 +1.9 +8.4 +9.0 +11.8 | stable |
| 0 | MACD histogram positive | down by 1.5 points overall | down | 7/8 | -2.2 -2.0 +0.6 -1.7 -2.0 -0.9 -0.6 -1.0 | stable |
| 0 | MACD histogram negative | up by 1.5 points overall | up | 7/8 | +2.3 +1.9 -0.6 +1.8 +1.9 +0.9 +0.6 +0.9 | stable |
| 0 | above upper Bollinger band | down by 3.0 points overall | down | 5/8 | -6.8 +8.1 +0.5 -10.8 -6.4 +1.4 -4.6 -1.0 | not stable |
| 0 | below lower Bollinger band | up by 4.8 points overall | up | 5/8 | +6.5 -1.7 -2.1 +6.2 +6.8 -1.1 +6.1 +9.5 | not stable |
| 0 | EMA9 above EMA21 by 10 bp | down by 6.4 points overall | down | 8/8 | -11.3 -8.2 -10.3 -1.8 -8.0 -7.2 -1.0 -4.3 | stable |
| 0 | EMA9 below EMA21 by 10 bp | up by 6.9 points overall | up | 8/8 | +4.7 +9.9 +9.7 +5.7 +7.2 +8.6 +12.3 +15.3 | stable |
| 0 | taker buying 60 pct+ of last 15 min | down by 4.9 points overall | down | 8/8 | -5.0 -1.0 -4.9 -6.6 -3.7 -4.9 -2.9 -3.8 | stable |
| 0 | taker selling 60 pct+ of last 15 min | up by 3.5 points overall | up | 7/8 | +5.0 -0.1 +1.7 +6.5 +2.3 +3.1 +2.3 +4.5 | stable |
| 0 | volume last 5 min 3x the daily average | down by 2.5 points overall | down | 6/8 | -4.6 +1.9 -0.3 -1.7 -5.4 +3.2 -4.2 -6.1 | stable |
| 0 | OBV rising over 60 min | down by 5.8 points overall | down | 7/8 | -9.0 +0.3 -7.3 -5.4 -8.0 -7.7 -8.2 -1.9 | stable |
| 0 | OBV falling over 60 min | up by 4.5 points overall | up | 8/8 | +5.1 +8.6 +3.6 +3.7 +4.1 +8.6 +5.9 +8.7 | stable |
| 0 | price 30 bp+ above 60-min VWAP | down by 4.0 points overall | down | 7/8 | -6.3 -4.7 -4.2 -4.0 -2.7 -1.9 +3.8 -2.9 | stable |
| 0 | price 30 bp+ below 60-min VWAP | up by 6.2 points overall | up | 7/8 | +7.6 +4.9 +9.3 -2.9 +2.7 +8.5 +10.8 +14.4 | stable |
| 0 | low volatility (vol60 in bottom decile) | up by 1.1 points overall | up | 6/8 | +0.4 +9.6 -2.8 -1.1 +1.2 +6.4 +0.7 +1.9 | stable |
| 3 | price at 4h high (rangepos >= 0.98) | up by 19.1 points overall | up | 8/8 | +16.0 +12.7 +30.1 +16.5 +17.4 +23.4 +13.9 +21.8 | stable |
| 3 | price at 4h low (rangepos <= 0.02) | down by 20.3 points overall | down | 7/7 | -10.3 -19.1 -15.8 - -24.8 -14.8 -20.1 -14.7 | stable |
| 3 | upper quarter of 4h range | up by 2.2 points overall | up | 8/8 | +0.5 +3.4 +0.7 +1.5 +1.5 +2.9 +1.9 +2.2 | stable |
| 3 | lower quarter of 4h range | down by 2.2 points overall | down | 7/8 | -1.0 -0.8 +0.6 -1.2 -2.9 -3.8 -2.3 -5.4 | stable |
| 3 | last 5 min up more than 2 sd | up by 32.2 points overall | up | 8/8 | +21.3 +40.3 +33.2 +33.9 +35.1 +36.0 +31.4 +24.4 | stable |
| 3 | last 5 min down more than 2 sd | down by 31.0 points overall | down | 8/8 | -31.4 -32.9 -29.4 -37.7 -29.5 -31.3 -29.4 -33.1 | stable |
| 3 | last 15 min up more than 2 sd | up by 17.5 points overall | up | 8/8 | +10.3 +23.2 +8.7 +18.1 +15.6 +28.5 +21.7 +16.4 | stable |
| 3 | last 15 min down more than 2 sd | down by 14.2 points overall | down | 8/8 | -17.3 -19.6 -9.6 -9.6 -21.4 -11.1 -10.4 -5.9 | stable |
| 3 | previous window up | down by 2.2 points overall | down | 8/8 | -3.3 -3.0 -1.1 -3.0 -2.0 -2.9 -1.8 -1.1 | stable |
| 3 | previous window down | up by 2.2 points overall | up | 8/8 | +3.2 +3.0 +1.1 +3.1 +1.9 +2.6 +1.8 +1.1 | stable |
| 3 | two windows up in a row | down by 3.3 points overall | down | 8/8 | -6.4 -3.6 -3.6 -3.8 -3.6 -4.3 -2.3 -3.3 | stable |
| 3 | two windows down in a row | up by 3.6 points overall | up | 8/8 | +4.6 +5.2 +4.9 +3.6 +3.1 +2.2 +4.8 +3.3 | stable |
| 3 | three windows up in a row | down by 4.3 points overall | down | 7/8 | -10.2 -4.4 -7.8 -1.9 -1.3 -8.3 +0.3 -5.1 | stable |
| 3 | three windows down in a row | up by 3.9 points overall | up | 8/8 | +5.6 +7.0 +2.5 +3.9 +2.6 +3.9 +5.9 +4.6 | stable |
| 3 | RSI14 above 70 | up by 23.5 points overall | up | 8/8 | +17.1 +25.8 +24.8 +22.4 +24.6 +27.7 +27.5 +23.2 | stable |
| 3 | RSI14 below 30 | down by 21.2 points overall | down | 8/8 | -21.0 -23.4 -21.4 -27.4 -27.6 -19.3 -19.2 -9.5 | stable |
| 3 | MACD histogram positive | up by 8.0 points overall | up | 8/8 | +8.3 +5.9 +10.5 +7.4 +8.1 +8.4 +8.6 +8.4 | stable |
| 3 | MACD histogram negative | down by 7.6 points overall | down | 8/8 | -8.2 -5.6 -10.1 -7.2 -7.8 -8.2 -8.4 -7.5 | stable |
| 3 | above upper Bollinger band | up by 29.7 points overall | up | 8/8 | +26.0 +31.4 +30.3 +29.4 +31.0 +31.7 +33.7 +24.6 | stable |
| 3 | below lower Bollinger band | down by 29.7 points overall | down | 8/8 | -30.2 -27.3 -27.8 -36.9 -30.6 -27.3 -28.5 -28.4 | stable |
| 3 | EMA9 above EMA21 by 10 bp | up by 3.9 points overall | up | 6/8 | -0.4 +2.3 +1.0 +8.8 -0.4 +8.2 +10.7 +4.0 | stable |
| 3 | EMA9 below EMA21 by 10 bp | down by 3.8 points overall | down | 7/8 | -4.6 -0.4 -3.3 -5.4 -11.8 -5.1 +3.8 -0.3 | stable |
| 3 | taker buying 60 pct+ of last 15 min | up by 2.2 points overall | up | 8/8 | +2.1 +3.0 +0.8 +1.7 +3.4 +2.5 +3.3 +3.4 | stable |
| 3 | taker selling 60 pct+ of last 15 min | down by 2.3 points overall | down | 7/8 | -2.7 -3.8 -2.9 +0.4 -3.2 -3.2 -4.7 -1.6 | stable |
| 3 | price 30 bp+ above 60-min VWAP | up by 10.1 points overall | up | 8/8 | +6.8 +6.5 +6.9 +12.1 +7.7 +13.1 +14.4 +13.3 | stable |
| 3 | price 30 bp+ below 60-min VWAP | down by 8.5 points overall | down | 7/8 | -3.5 -7.4 -7.5 -18.1 -16.8 -7.9 -11.6 +0.8 | stable |
| 3 | leading by 10 bp+ at entry | up by 28.9 points overall | up | 8/8 | +26.5 +24.2 +30.0 +29.0 +32.7 +30.4 +37.6 +28.7 | stable |
| 3 | trailing by 10 bp+ at entry | down by 26.9 points overall | down | 8/8 | -29.3 -23.0 -26.5 -29.8 -30.7 -26.9 -28.6 -26.1 | stable |

Learned rules: a depth-2 decision tree per test month (leaves of at least 500 windows), trained on earlier months, and its accuracy on the test month. The same root split in most months is a stable rule; a different root each month means there is none.

| minute | month | accuracy | tree |
|---|---|---|---|
| 0 | 2026-01 | 52.22% | &#124;--- flow15 <= 0.2<br>&#124;   &#124;--- rsi14 <= 36.9<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- rsi14 >  36.9<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;--- flow15 >  0.2<br>&#124;   &#124;--- rsi14 <= 59.6<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- rsi14 >  59.6<br>&#124;   &#124;   &#124;--- class: 0<br> |
| 0 | 2026-02 | 51.00% | &#124;--- rsi60 <= 56.0<br>&#124;   &#124;--- flow15 <= -0.1<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- flow15 >  -0.1<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- rsi60 >  56.0<br>&#124;   &#124;--- flow15 <= 0.1<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- flow15 >  0.1<br>&#124;   &#124;   &#124;--- class: 0<br> |
| 0 | 2026-03 | 51.41% | &#124;--- bb_pctb <= 0.6<br>&#124;   &#124;--- rsi14 <= 32.9<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- rsi14 >  32.9<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;--- bb_pctb >  0.6<br>&#124;   &#124;--- rsi60 <= 56.0<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- rsi60 >  56.0<br>&#124;   &#124;   &#124;--- class: 0<br> |
| 0 | 2026-04 | 51.18% | &#124;--- rsi60 <= 56.0<br>&#124;   &#124;--- rsi60 <= 47.5<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- rsi60 >  47.5<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- rsi60 >  56.0<br>&#124;   &#124;--- size5 <= 1.0<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- size5 >  1.0<br>&#124;   &#124;   &#124;--- class: 0<br> |
| 0 | 2026-05 | 51.28% | &#124;--- rsi60 <= 55.9<br>&#124;   &#124;--- rsi60 <= 45.4<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- rsi60 >  45.4<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;--- rsi60 >  55.9<br>&#124;   &#124;--- size5 <= 1.1<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- size5 >  1.1<br>&#124;   &#124;   &#124;--- class: 0<br> |
| 0 | 2026-06 | 53.33% | &#124;--- rsi60 <= 55.0<br>&#124;   &#124;--- rangepos <= 0.3<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- rangepos >  0.3<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- rsi60 >  55.0<br>&#124;   &#124;--- flow15 <= 0.1<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- flow15 >  0.1<br>&#124;   &#124;   &#124;--- class: 0<br> |
| 0 | 2026-07 | 52.65% | &#124;--- rsi60 <= 51.5<br>&#124;   &#124;--- rsi14 <= 33.9<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- rsi14 >  33.9<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;--- rsi60 >  51.5<br>&#124;   &#124;--- rsi60 <= 55.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- rsi60 >  55.9<br>&#124;   &#124;   &#124;--- class: 0<br> |
| 0 | 2026-08 | 51.58% | &#124;--- rsi60 <= 51.5<br>&#124;   &#124;--- rsi14 <= 33.9<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- rsi14 >  33.9<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;--- rsi60 >  51.5<br>&#124;   &#124;--- rsi60 <= 56.3<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- rsi60 >  56.3<br>&#124;   &#124;   &#124;--- class: 0<br> |
| 3 | 2026-01 | 65.73% | &#124;--- lead <= -0.8<br>&#124;   &#124;--- lead <= -5.5<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- lead >  -5.5<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- lead >  -0.8<br>&#124;   &#124;--- lead <= 5.5<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- lead >  5.5<br>&#124;   &#124;   &#124;--- class: 1<br> |
| 3 | 2026-02 | 64.88% | &#124;--- lead <= -0.8<br>&#124;   &#124;--- lead <= -5.5<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- lead >  -5.5<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- lead >  -0.8<br>&#124;   &#124;--- lead <= 5.5<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- lead >  5.5<br>&#124;   &#124;   &#124;--- class: 1<br> |
| 3 | 2026-03 | 65.15% | &#124;--- lead <= -0.8<br>&#124;   &#124;--- lead <= -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- lead >  -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- lead >  -0.8<br>&#124;   &#124;--- lead <= 4.3<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- lead >  4.3<br>&#124;   &#124;   &#124;--- class: 1<br> |
| 3 | 2026-04 | 66.32% | &#124;--- lead <= -0.8<br>&#124;   &#124;--- lead <= -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- lead >  -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- lead >  -0.8<br>&#124;   &#124;--- lead <= 5.5<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- lead >  5.5<br>&#124;   &#124;   &#124;--- class: 1<br> |
| 3 | 2026-05 | 66.20% | &#124;--- lead <= -0.8<br>&#124;   &#124;--- lead <= -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- lead >  -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- lead >  -0.8<br>&#124;   &#124;--- lead <= 5.8<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- lead >  5.8<br>&#124;   &#124;   &#124;--- class: 1<br> |
| 3 | 2026-06 | 66.53% | &#124;--- lead <= -0.8<br>&#124;   &#124;--- lead <= -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- lead >  -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- lead >  -0.8<br>&#124;   &#124;--- lead <= 4.3<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- lead >  4.3<br>&#124;   &#124;   &#124;--- class: 1<br> |
| 3 | 2026-07 | 66.16% | &#124;--- lead <= -0.8<br>&#124;   &#124;--- lead <= -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- lead >  -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- lead >  -0.8<br>&#124;   &#124;--- lead <= 4.6<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- lead >  4.6<br>&#124;   &#124;   &#124;--- class: 1<br> |
| 3 | 2026-08 | 67.61% | &#124;--- lead <= -0.1<br>&#124;   &#124;--- lead <= -4.8<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- lead >  -4.8<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- lead >  -0.1<br>&#124;   &#124;--- lead <= 4.6<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- lead >  4.6<br>&#124;   &#124;   &#124;--- class: 1<br> |
