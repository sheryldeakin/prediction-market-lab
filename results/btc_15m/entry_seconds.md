The window call by entry time, walk-forward by month, 2025-10 to 2026-08, test months after the first three (the windows of the main table). Open and minute 3 are the stored out-of-fold predictions of the main table on the same windows. Entries at 10, 30 and 60 seconds: lead-sign calls up when the lead at that second is above the open, down when below, and the previous-window rule when exactly zero (its AUC and log loss use the training up-rate of each call); lead-z is the one-feature logistic on the lead scaled by the volatility left in the window; forest+ticks and xgb+ticks are the minute-0 feature set plus the tick features at that second (lead, signed-volume share, trades, large trades, lead-z), on CPU. Accuracy has a day-block 95% interval. The last columns are accuracy minus the entry's one-bit rule on the same windows (named in the cell; at minute 3 it is the lead z-score, as in checks.md), day-block interval, share of days better, sign-flip p.

| entry | model | n | accuracy [95% CI] | AUC | log loss | vs one-bit rule | days better | sign p |
|---|---|---|---|---|---|---|---|---|
| open | prev-window | 23328 | 52.21% [51.63, 52.82] | 0.519 | 0.6922 | baseline |  |  |
| open | forest | 23328 | 52.65% [52.01, 53.33] | 0.539 | 0.6910 | +0.44 [-0.25, +1.18] vs prev-window | 54% | 0.1044 |
| 10 s | lead-sign | 23328 | 54.15% [53.51, 54.81] | 0.540 | 0.6898 | baseline |  |  |
| 10 s | lead-z | 23328 | 53.95% [53.31, 54.60] | 0.562 | 0.6872 | -0.20 [-0.63, +0.24] vs lead-sign | 47% | 0.8186 |
| 10 s | forest+ticks | 23328 | 54.82% [54.22, 55.43] | 0.570 | 0.6854 | +0.68 [+0.12, +1.22] vs lead-sign | 54% | 0.0090 |
| 10 s | xgb+ticks | 23328 | 54.85% [54.19, 55.48] | 0.569 | 0.6859 | +0.71 [+0.14, +1.29] vs lead-sign | 60% | 0.0050 |
| 30 s | lead-sign | 23328 | 56.12% [55.48, 56.74] | 0.558 | 0.6857 | baseline |  |  |
| 30 s | lead-z | 23328 | 56.00% [55.37, 56.63] | 0.590 | 0.6804 | -0.12 [-0.40, +0.15] vs lead-sign | 51% | 0.7856 |
| 30 s | forest+ticks | 23328 | 56.94% [56.29, 57.57] | 0.596 | 0.6784 | +0.83 [+0.35, +1.33] vs lead-sign | 61% | < 0.0005 |
| 30 s | xgb+ticks | 23328 | 56.52% [55.87, 57.14] | 0.593 | 0.6792 | +0.40 [-0.12, +0.95] vs lead-sign | 54% | 0.0745 |
| 60 s | lead-sign | 23328 | 58.85% [58.20, 59.54] | 0.584 | 0.6776 | baseline |  |  |
| 60 s | lead-z | 23328 | 58.81% [58.15, 59.48] | 0.628 | 0.6670 | -0.04 [-0.27, +0.17] vs lead-sign | 50% | 0.6392 |
| 60 s | forest+ticks | 23328 | 59.06% [58.45, 59.70] | 0.629 | 0.6663 | +0.21 [-0.20, +0.61] vs lead-sign | 54% | 0.1649 |
| 60 s | xgb+ticks | 23328 | 58.97% [58.34, 59.65] | 0.628 | 0.6668 | +0.12 [-0.37, +0.61] vs lead-sign | 52% | 0.3073 |
| minute 3 | lead-z | 23328 | 66.35% [65.73, 66.98] | 0.721 | 0.6150 | baseline |  |  |
| minute 3 | lead-sign | 23328 | 66.29% [65.69, 66.91] | 0.661 | 0.6391 | -0.05 [-0.19, +0.09] vs lead-z | 47% | 0.7526 |
| minute 3 | xgb-all | 23328 | 66.28% [65.66, 66.92] | 0.719 | 0.6169 | -0.07 [-0.42, +0.27] vs lead-z | 50% | 0.6492 |

What these windows could detect: the day-block interval on a difference from the entry's rule is 0.28 to 1.43 points wide across the rows above, so an increment smaller than about 0.14 to 0.72 points could not be told from zero. A null here is a bound of that width, not a verdict.

Of the 9 comparisons with the lead-sign rule at 10, 30 and 60 seconds, 3 have a day-block interval that excludes zero: forest+ticks at 10 s (+0.68); xgb+ticks at 10 s (+0.71); forest+ticks at 30 s (+0.83). The intervals are not adjusted for the number of comparisons. The fitted models differ from the rule in two ways at once, they use the tick features and they use the minute-0 features, and no row separates the two.

Tick coverage at each entry over the scored windows: the share whose second [t+N-1, t+N) had no trade (the last earlier VWAP was used), the share with no trade at all in [t, t+N), the share whose lead is exactly zero, and the share whose lead has a different sign when measured against the candle open instead of the first traded second's VWAP.

| entry | windows | fallback used | no trade in [t, t+N) | lead exactly zero | sign differs from candle-open lead |
|---|---|---|---|---|---|
| 10 s | 23328 | 8.42% | 0.00% | 1.74% | 7.75% |
| 30 s | 23328 | 8.97% | 0.00% | 0.98% | 3.88% |
| 60 s | 23328 | 11.90% | 0.00% | 0.55% | 2.43% |
