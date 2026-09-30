GRU over the last 120 minutes (return, volume ratio, taker-buy share) plus lead and hour, walk-forward by month, early stopping on the last 10% of training months.

| minute | model | n | accuracy [95% CI] | AUC | log loss | vs baseline |
|---|---|---|---|---|---|---|
| 0 | gru-sequence | 23327 | 51.16% [50.57, 51.76] | 0.520 | 0.6924 | +0.84 [+0.09, +1.61] vs majority |
| 3 | gru-sequence | 23327 | 65.89% [65.28, 66.54] | 0.715 | 0.6203 | -0.43 [-0.76, -0.10] vs lead-only |
