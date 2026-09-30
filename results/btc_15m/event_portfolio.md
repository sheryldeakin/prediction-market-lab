Acting only when a stable event fires. Stable events are found on 2025-10 to 2026-08 (so the backtest rows are in-sample); the forward rows are 2026-09-01 to 2026-09-29, never seen by the event search. EV in cents per $1 contract at a 1c spread and 1.75c fee, priced at 0.5.

| minute | rule | period | windows acted on | share | accuracy [95% CI] | EV cents [95% CI] |
|---|---|---|---|---|---|---|
| 0 | any stable event, strongest wins | backtest (in-sample) | 32058 | 100.0% | 53.04% [52.57, 53.52] | +0.79 [+0.32, +1.27] |
| 0 | any stable event, strongest wins | forward | 2783 | 100.0% | 52.46% [50.61, 54.55] | +0.21 [-1.64, +2.30] |
| 0 | events with 5+ point deviation, strongest wins | backtest (in-sample) | 7903 | 24.7% | 56.02% [54.93, 57.05] | +3.77 [+2.68, +4.80] |
| 0 | events with 5+ point deviation, strongest wins | forward | 590 | 21.2% | 55.08% [51.42, 58.87] | +2.83 [-0.83, +6.62] |
| 0 | all firing stable events agree | backtest (in-sample) | 15868 | 49.5% | 54.08% [53.33, 54.80] | +1.83 [+1.08, +2.55] |
| 0 | all firing stable events agree | forward | 1421 | 51.1% | 53.62% [50.82, 56.63] | +1.37 [-1.43, +4.38] |

Each stable event on its own: the deviation of the up-rate from the base rate in the backtest, and the same in the forward period.

| minute | event | direction | backtest deviation (points) | forward fires | forward deviation (points) | held? |
|---|---|---|---|---|---|---|
| 0 | price at 4h high (rangepos >= 0.98) | down | -11.3 | 57 | -4.3 | same |
| 0 | last 15 min up more than 2 sd | down | -8.8 | 74 | +2.8 | flipped |
| 0 | last 15 min down more than 2 sd | up | +8.6 | 84 | +14.3 | same |
| 0 | last 5 min up more than 2 sd | down | -7.7 | 71 | -0.7 | same |
| 0 | RSI14 below 30 | up | +7.6 | 118 | +6.8 | same |
| 0 | EMA9 below EMA21 by 10 bp | up | +6.9 | 60 | +15.1 | same |
| 0 | RSI14 above 70 | down | -6.9 | 129 | -1.9 | same |
| 0 | EMA9 above EMA21 by 10 bp | down | -6.4 | 72 | -5.5 | same |
| 0 | price 30 bp+ below 60-min VWAP | up | +6.2 | 109 | +4.2 | same |
| 0 | price at 4h low (rangepos <= 0.02) | up | +5.9 | 36 | +2.8 | same |
| 0 | OBV rising over 60 min | down | -5.8 | 170 | -4.1 | same |
| 0 | taker buying 60 pct+ of last 15 min | down | -4.9 | 553 | -3.1 | same |
| 0 | upper quarter of 4h range | down | -4.9 | 761 | -4.3 | same |
| 0 | last 5 min down more than 2 sd | up | +4.6 | 56 | +9.0 | same |
| 0 | lower quarter of 4h range | up | +4.5 | 597 | +4.0 | same |
| 0 | OBV falling over 60 min | up | +4.5 | 204 | +8.9 | same |
| 0 | three windows up in a row | down | -4.3 | 305 | -5.4 | same |
| 0 | price 30 bp+ above 60-min VWAP | down | -4.0 | 125 | -0.3 | same |
| 0 | three windows down in a row | up | +3.9 | 319 | +2.7 | same |
| 0 | two windows down in a row | up | +3.6 | 679 | +3.2 | same |
| 0 | taker selling 60 pct+ of last 15 min | up | +3.5 | 631 | +5.4 | same |
| 0 | two windows up in a row | down | -3.3 | 676 | -4.8 | same |
| 0 | 4h return above +50 bp | down | -3.2 | 481 | -2.1 | same |
| 0 | 4h return below -50 bp | up | +2.7 | 494 | +3.3 | same |
| 0 | volume last 5 min 3x the daily average | down | -2.5 | 145 | +5.9 | flipped |
| 0 | previous window up | down | -2.2 | 1390 | -1.3 | same |
| 0 | previous window down | up | +2.2 | 1393 | +1.3 | same |
| 0 | MACD histogram positive | down | -1.5 | 1382 | -1.5 | same |
| 0 | MACD histogram negative | up | +1.5 | 1401 | +1.4 | same |
