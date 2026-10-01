Acting only when a stable event fires. Stable events are found on 2025-10 to 2026-08 (so the backtest rows are in-sample); the forward rows are 2026-09-01 to 2026-09-30, never seen by the event search. Under a hypothetical cost model (buy the favoured side at 0.5 plus half a 1c spread, pay a 1.75c fee, receive 1 if right) the break-even accuracy is 52.25%. These are sensitivity figures, not a backtest of trades: no venue settles on a Binance last print, and the price model is an assumption. Last column: accuracy minus break-even, in points.

| minute | rule | period | windows acted on | share | accuracy [95% CI] | accuracy minus break-even, points [95% CI] |
|---|---|---|---|---|---|---|
| 0 | any stable event, strongest wins | backtest (in-sample) | 32059 | 100.0% | 53.04% [52.57, 53.52] | +0.79 [+0.32, +1.27] |
| 0 | any stable event, strongest wins | forward | 2880 | 100.0% | 52.40% [50.56, 54.44] | +0.15 [-1.69, +2.19] |
| 0 | events with 5+ point deviation, strongest wins | backtest (in-sample) | 7903 | 24.7% | 56.02% [54.93, 57.05] | +3.77 [+2.68, +4.80] |
| 0 | events with 5+ point deviation, strongest wins | forward | 612 | 21.2% | 54.74% [51.12, 58.51] | +2.49 [-1.13, +6.26] |
| 0 | all firing stable events agree | backtest (in-sample) | 14585 | 45.5% | 54.29% [53.51, 55.05] | +2.04 [+1.26, +2.80] |
| 0 | all firing stable events agree | forward | 1280 | 44.4% | 52.97% [50.23, 55.98] | +0.72 [-2.02, +3.73] |

Each stable event on its own: the deviation of the up-rate from the base rate in the backtest, and the same in the forward period.

| minute | event | direction | backtest deviation (points) | forward fires | forward deviation (points) | held? |
|---|---|---|---|---|---|---|
| 0 | price at 4h high (rangepos >= 0.98) | down | -11.3 | 57 | -4.3 | same |
| 0 | last 15 min up more than 2 sd | down | -8.8 | 76 | +4.1 | flipped |
| 0 | last 15 min down more than 2 sd | up | +8.6 | 85 | +14.8 | same |
| 0 | last 5 min up more than 2 sd | down | -7.7 | 72 | +0.1 | flipped |
| 0 | RSI14 below 30 | up | +7.6 | 121 | +8.0 | same |
| 0 | EMA9 below EMA21 by 10 bp | up | +6.9 | 63 | +15.2 | same |
| 0 | RSI14 above 70 | down | -6.9 | 133 | -1.8 | same |
| 0 | EMA9 above EMA21 by 10 bp | down | -6.4 | 75 | -4.6 | same |
| 0 | price 30 bp+ below 60-min VWAP | up | +6.2 | 114 | +3.6 | same |
| 0 | price at 4h low (rangepos <= 0.02) | up | +5.9 | 36 | +2.9 | same |
| 0 | OBV rising over 60 min | down | -5.8 | 178 | -3.3 | same |
| 0 | taker buying 60 pct+ of last 15 min | down | -4.9 | 566 | -3.3 | same |
| 0 | upper quarter of 4h range | down | -4.9 | 778 | -3.9 | same |
| 0 | last 5 min down more than 2 sd | up | +4.6 | 58 | +8.7 | same |
| 0 | lower quarter of 4h range | up | +4.5 | 630 | +4.1 | same |
| 0 | OBV falling over 60 min | up | +4.5 | 207 | +9.0 | same |
| 0 | three windows up in a row | down | -4.3 | 317 | -4.8 | same |
| 0 | price 30 bp+ above 60-min VWAP | down | -4.0 | 128 | +0.1 | flipped |
| 0 | three windows down in a row | up | +3.9 | 328 | +3.2 | same |
| 0 | two windows down in a row | up | +3.6 | 706 | +3.8 | same |
| 0 | taker selling 60 pct+ of last 15 min | up | +3.5 | 651 | +5.3 | same |
| 0 | two windows up in a row | down | -3.3 | 698 | -4.5 | same |
| 0 | 4h return above +50 bp | down | -3.2 | 499 | -1.8 | same |
| 0 | 4h return below -50 bp | up | +2.7 | 509 | +2.8 | same |
| 0 | volume last 5 min 3x the daily average | down | -2.5 | 149 | +6.5 | flipped |
| 0 | previous window up | down | -2.2 | 1436 | -1.3 | same |
| 0 | previous window down | up | +2.2 | 1444 | +1.3 | same |
| 0 | MACD histogram positive | down | -1.5 | 1428 | -1.4 | same |
| 0 | MACD histogram negative | up | +1.5 | 1452 | +1.3 | same |
| 0 | low volatility (vol60 in bottom decile) | up | +1.1 | 593 | -1.2 | flipped |
