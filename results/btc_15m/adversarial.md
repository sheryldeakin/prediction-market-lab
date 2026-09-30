Adversarial validation: a classifier trained to tell a test month's windows from all earlier months, scored on a held-out half. AUC 0.5 means the month is indistinguishable; higher means the feature distribution moved, and the top features say where.

| minute | month | AUC | top features |
|---|---|---|---|
| 0 | 2026-01 | 0.772 | vol240, atr14, vol60 |
| 0 | 2026-02 | 0.843 | vol240, atr14, nratio5 |
| 0 | 2026-03 | 0.768 | wday, atr14, vol240 |
| 0 | 2026-04 | 0.746 | vol240, flow15, nratio5 |
| 0 | 2026-05 | 0.844 | atr14, vol240, nratio5 |
| 0 | 2026-06 | 0.679 | vol240, wday, vol60 |
| 0 | 2026-07 | 0.759 | atr14, nratio5, vol240 |
| 0 | 2026-08 | 0.792 | vol240, atr14, wday |
| 3 | 2026-01 | 0.768 | vol240, atr14, wday |
| 3 | 2026-02 | 0.841 | vol240, atr14, nratio5 |
| 3 | 2026-03 | 0.770 | atr14, wday, vol240 |
| 3 | 2026-04 | 0.740 | vol240, atr14, nratio5 |
| 3 | 2026-05 | 0.843 | atr14, vol240, nratio5 |
| 3 | 2026-06 | 0.676 | vol60, atr14, vol240 |
| 3 | 2026-07 | 0.756 | atr14, vol240, nratio5 |
| 3 | 2026-08 | 0.791 | vol240, atr14, wday |
