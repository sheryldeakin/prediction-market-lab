The best model's accuracy increment over the one-feature baseline, corrected for having picked the best of several models. Selection bias is estimated by resampling days, re-picking the best model in each resample, and measuring how far that winner sits above its own original increment. Points of accuracy; the interval is day-block bootstrap on the corrected value.

| minute | baseline | models compared | best model | observed increment | selection bias | corrected increment [95% CI] |
|---|---|---|---|---|---|---|
| 0 | prev-window | 5 | logistic-all | +0.69 | 0.16 | +0.52 [-0.17, +1.21] |
| 3 | lead-z | 5 | hgb-all | +0.00 | 0.05 | -0.05 [-0.34, +0.24] |
