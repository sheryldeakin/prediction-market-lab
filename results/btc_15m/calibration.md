Calibration of the XGBoost probabilities (price + flow + indicators), walk-forward. Platt and isotonic recalibration are fit on earlier months' out-of-fold probabilities only. Brier = reliability - resolution + uncertainty; lower reliability is better calibration, higher resolution is more information. ECE is the expected calibration error over ten bins.

| minute | probabilities | n | Brier | reliability | resolution | ECE |
|---|---|---|---|---|---|---|
| 0 | raw | 20351 | 0.2491 | 0.00042 | 0.00103 | 1.55% |
| 0 | platt | 20351 | 0.2488 | 0.00001 | 0.00072 | 0.16% |
| 0 | isotonic | 20351 | 0.2491 | 0.00024 | 0.00073 | 0.56% |
| 3 | raw | 20351 | 0.2135 | 0.00015 | 0.03568 | 0.92% |
| 3 | platt | 20351 | 0.2136 | 0.00019 | 0.03566 | 1.20% |
| 3 | isotonic | 20351 | 0.2139 | 0.00022 | 0.03557 | 1.21% |

Reliability by month (raw probabilities): ECE, mean predicted, observed rate of up.

| minute | month | n | ECE | mean predicted | observed |
|---|---|---|---|---|---|
| 0 | 2026-01 | 2976 | 1.64% | 50.0% | 49.3% |
| 0 | 2026-02 | 2688 | 2.55% | 49.5% | 50.4% |
| 0 | 2026-03 | 2976 | 2.17% | 50.3% | 49.9% |
| 0 | 2026-04 | 2880 | 1.29% | 49.7% | 51.0% |
| 0 | 2026-05 | 2976 | 1.98% | 50.0% | 49.3% |
| 0 | 2026-06 | 2880 | 2.90% | 50.0% | 47.6% |
| 0 | 2026-07 | 2976 | 0.54% | 49.7% | 49.7% |
| 0 | 2026-08 | 2975 | 1.84% | 49.9% | 50.3% |
| 3 | 2026-01 | 2976 | 1.97% | 49.9% | 49.3% |
| 3 | 2026-02 | 2688 | 3.30% | 50.0% | 50.4% |
| 3 | 2026-03 | 2976 | 2.63% | 50.6% | 49.9% |
| 3 | 2026-04 | 2880 | 1.58% | 50.0% | 51.0% |
| 3 | 2026-05 | 2976 | 2.57% | 50.3% | 49.3% |
| 3 | 2026-06 | 2880 | 3.62% | 49.5% | 47.6% |
| 3 | 2026-07 | 2976 | 2.46% | 49.0% | 49.7% |
| 3 | 2026-08 | 2975 | 2.82% | 49.9% | 50.3% |
