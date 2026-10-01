Magnitude label: the window's close is at least 10 basis points from the entry price (the open at minute 0, the price at entry after it), in either direction.

| minute | model | n | share of windows that move | accuracy [95% CI] | AUC | log loss |
|---|---|---|---|---|---|---|
| 0 | vol60 only | 23328 | 50.7% | 64.70% [63.40, 65.99] | 0.708 | 0.6360 |
| 0 | all features | 23328 | 50.7% | 65.26% [63.98, 66.49] | 0.715 | 0.6165 |
| 3 | vol60 only | 23328 | 45.1% | 65.63% [64.28, 67.02] | 0.719 | 0.6260 |
| 3 | all features | 23328 | 45.1% | 66.85% [65.57, 68.13] | 0.730 | 0.6006 |
