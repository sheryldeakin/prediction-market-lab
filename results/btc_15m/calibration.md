Calibration of the XGBoost probabilities (price + flow + indicators), walk-forward. Platt and isotonic recalibration are fit on earlier months' out-of-fold probabilities only. Binned decomposition over ten quantile bins of the predicted probability: Brier is approximately reliability - resolution + uncertainty, and the residual column is the part the binning does not account for. Lower reliability is better calibration, higher resolution is more information. ECE is the expected calibration error over the same quantile bins. The calibration slope is the coefficient of a logistic regression of the outcome on the logit of the probability, with a day-block interval: 1 is calibrated, below 1 means the probabilities are too extreme, above 1 too timid.

| minute | probabilities | n | Brier | reliability | resolution | uncertainty | residual | ECE | calibration slope [95% CI] |
|---|---|---|---|---|---|---|---|---|---|
| 0 | raw | 20352 | 0.2491 | 0.00050 | 0.00132 | 0.24999 | -0.00010 | 1.75% | 0.63 [0.52, 0.76] |
| 0 | platt | 20352 | 0.2487 | 0.00008 | 0.00126 | 0.24999 | -0.00007 | 0.82% | 1.02 [0.83, 1.22] |
| 0 | isotonic | 20352 | 0.2489 | 0.00012 | 0.00122 | 0.24999 | +0.00004 | 0.94% | 0.72 [0.50, 0.98] |
| 3 | raw | 20352 | 0.2135 | 0.00022 | 0.03627 | 0.24999 | -0.00045 | 1.09% | 0.99 [0.95, 1.03] |
| 3 | platt | 20352 | 0.2136 | 0.00019 | 0.03602 | 0.24999 | -0.00060 | 1.26% | 1.05 [1.01, 1.09] |
| 3 | isotonic | 20352 | 0.2140 | 0.00022 | 0.03562 | 0.24999 | -0.00060 | 1.09% | 0.96 [0.90, 1.02] |

Reliability by month (raw probabilities): ECE, mean predicted, observed rate of up.

| minute | month | n | ECE | mean predicted | observed |
|---|---|---|---|---|---|
| 0 | 2026-01 | 2976 | 2.97% | 49.9% | 49.3% |
| 0 | 2026-02 | 2688 | 4.03% | 49.4% | 50.4% |
| 0 | 2026-03 | 2976 | 3.31% | 50.2% | 49.9% |
| 0 | 2026-04 | 2880 | 2.47% | 49.7% | 51.0% |
| 0 | 2026-05 | 2976 | 2.41% | 49.9% | 49.3% |
| 0 | 2026-06 | 2880 | 5.32% | 49.9% | 47.6% |
| 0 | 2026-07 | 2976 | 2.52% | 49.6% | 49.7% |
| 0 | 2026-08 | 2976 | 1.89% | 49.8% | 50.3% |
| 3 | 2026-01 | 2976 | 2.15% | 49.8% | 49.3% |
| 3 | 2026-02 | 2688 | 3.20% | 50.1% | 50.4% |
| 3 | 2026-03 | 2976 | 2.37% | 50.5% | 49.9% |
| 3 | 2026-04 | 2880 | 1.71% | 49.9% | 51.0% |
| 3 | 2026-05 | 2976 | 2.99% | 50.4% | 49.3% |
| 3 | 2026-06 | 2880 | 2.68% | 49.4% | 47.6% |
| 3 | 2026-07 | 2976 | 2.93% | 49.0% | 49.7% |
| 3 | 2026-08 | 2976 | 2.81% | 49.8% | 50.3% |
