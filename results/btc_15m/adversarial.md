Adversarial validation: a classifier trained to tell a test month's windows from all earlier months, scored on a held-out half. AUC 0.5 means the month is indistinguishable; higher means the feature distribution moved, and the top features say where.

| minute | month | AUC | top features |
|---|---|---|---|
| 0 | 2026-01 | 0.771 | vol240, atr14, wday |
| 0 | 2026-02 | 0.838 | vol240, atr14, nratio5 |
| 0 | 2026-03 | 0.760 | wday, atr14, vol240 |
| 0 | 2026-04 | 0.746 | vol240, nratio5, flow15 |
| 0 | 2026-05 | 0.846 | atr14, vol240, nratio5 |
| 0 | 2026-06 | 0.681 | vol240, vol60, wday |
| 0 | 2026-07 | 0.754 | vol240, atr14, nratio5 |
| 0 | 2026-08 | 0.788 | vol240, atr14, wday |
| 3 | 2026-01 | 0.770 | vol240, atr14, wday |
| 3 | 2026-02 | 0.837 | vol240, atr14, nratio5 |
| 3 | 2026-03 | 0.758 | atr14, wday, vol240 |
| 3 | 2026-04 | 0.742 | vol240, atr14, nratio5 |
| 3 | 2026-05 | 0.843 | vol240, nratio5, atr14 |
| 3 | 2026-06 | 0.678 | vol240, vol60, atr14 |
| 3 | 2026-07 | 0.756 | atr14, vol240, nratio5 |
| 3 | 2026-08 | 0.786 | vol240, atr14, wday |
