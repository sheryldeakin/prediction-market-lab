Is an early confident call worth more than the window's own move? Out-of-fold probabilities of the walk-forward, 2026-01-01 to 2026-08-31, 23,328 windows on 243 days, entry minutes 0 to 14. For each predictor and threshold, a window's call is made at the first minute at which the probability of the called side (the larger of p and 1 - p; exactly 0.5 is not a call) reaches the threshold, on that minute's side. The comparison is the one-feature rule's call at the same minute (prev-window at minute 0, lead-z after), on the same windows. A window that never reaches the threshold makes no call: it counts in the share called and is left out of both accuracies. Difference = accuracy of the predictor's calls minus accuracy of the rule's calls, in points, paired by window, with a 95% interval from resampling whole days (2,000 resamples). The p is a two-sided sign-flip test on whole-day sums of the paired differences (20,000 draws; a Holm-adjusted p printed with "<" comes from a raw p at the test's floor), adjusted by Holm over the 48 cells. The rows named "rule" are the rule scored against itself and must show exactly zero; majority never reaches a threshold. "other one-feature" is win1-logistic at minute 0 and lead-only after. The last two columns count only calls made at minutes 1 to 3 (descriptive, not adjusted).

| predictor | threshold | share called | crossing minute, mean / median | accuracy, predictor | accuracy, rule | difference (points) [95% interval] | Holm p | calls at minutes 1 to 3 | difference at minutes 1 to 3 (points) [95% interval] |
|---|---|---|---|---|---|---|---|---|---|
| majority | 0.55 | 0.0% | - | - | - | - | - | 0 | - |
| majority | 0.60 | 0.0% | - | - | - | - | - | 0 | - |
| majority | 0.65 | 0.0% | - | - | - | - | - | 0 | - |
| majority | 0.70 | 0.0% | - | - | - | - | - | 0 | - |
| majority | 0.75 | 0.0% | - | - | - | - | - | 0 | - |
| majority | 0.80 | 0.0% | - | - | - | - | - | 0 | - |
| rule | 0.55 | 99.9% | 1.6 / 1 | 63.45% | 63.45% | +0.00 [+0.00, +0.00] | 1.0000 | 21,851 | +0.00 [+0.00, +0.00] |
| rule | 0.60 | 99.9% | 2.6 / 2 | 67.55% | 67.55% | +0.00 [+0.00, +0.00] | 1.0000 | 17,856 | +0.00 [+0.00, +0.00] |
| rule | 0.65 | 99.6% | 3.8 / 3 | 72.61% | 72.61% | +0.00 [+0.00, +0.00] | 1.0000 | 13,017 | +0.00 [+0.00, +0.00] |
| rule | 0.70 | 98.8% | 5.1 / 4 | 77.14% | 77.14% | +0.00 [+0.00, +0.00] | 1.0000 | 8,703 | +0.00 [+0.00, +0.00] |
| rule | 0.75 | 96.6% | 6.3 / 6 | 81.70% | 81.70% | +0.00 [+0.00, +0.00] | 1.0000 | 5,565 | +0.00 [+0.00, +0.00] |
| rule | 0.80 | 93.0% | 7.5 / 7 | 85.80% | 85.80% | +0.00 [+0.00, +0.00] | 1.0000 | 3,268 | +0.00 [+0.00, +0.00] |
| other one-feature | 0.55 | 99.6% | 2.3 / 2 | 66.14% | 66.14% | +0.00 [+0.00, +0.00] | 1.0000 | 17,788 | +0.00 [+0.00, +0.00] |
| other one-feature | 0.60 | 98.7% | 4.0 / 3 | 72.71% | 72.71% | +0.00 [+0.00, +0.00] | 1.0000 | 12,804 | +0.00 [+0.00, +0.00] |
| other one-feature | 0.65 | 96.4% | 5.4 / 5 | 77.81% | 77.81% | +0.00 [+0.00, +0.00] | 1.0000 | 8,385 | +0.00 [+0.00, +0.00] |
| other one-feature | 0.70 | 92.8% | 6.6 / 6 | 81.99% | 81.99% | +0.00 [+0.00, +0.00] | 1.0000 | 5,458 | +0.00 [+0.00, +0.00] |
| other one-feature | 0.75 | 88.4% | 7.6 / 8 | 85.10% | 85.10% | +0.00 [+0.00, +0.00] | 1.0000 | 3,532 | +0.00 [+0.00, +0.00] |
| other one-feature | 0.80 | 83.0% | 8.4 / 9 | 88.48% | 88.48% | +0.00 [+0.00, +0.00] | 1.0000 | 2,239 | +0.00 [+0.00, +0.00] |
| logistic-all | 0.55 | 100.0% | 1.2 / 1 | 60.87% | 60.69% | +0.18 [-0.11, +0.45] | 1.0000 | 15,619 | -0.02 [-0.34, +0.29] |
| logistic-all | 0.60 | 99.7% | 2.9 / 2 | 68.55% | 68.54% | +0.00 [-0.10, +0.12] | 1.0000 | 16,107 | +0.11 [-0.01, +0.24] |
| logistic-all | 0.65 | 98.0% | 4.6 / 4 | 74.80% | 74.79% | +0.02 [-0.03, +0.07] | 1.0000 | 10,802 | +0.03 [-0.03, +0.09] |
| logistic-all | 0.70 | 94.7% | 6.1 / 6 | 80.10% | 80.11% | -0.01 [-0.02, +0.00] | 1.0000 | 6,543 | +0.00 [+0.00, +0.00] |
| logistic-all | 0.75 | 90.4% | 7.3 / 7 | 84.22% | 84.23% | -0.00 [-0.02, +0.01] | 1.0000 | 3,940 | -0.03 [-0.08, +0.00] |
| logistic-all | 0.80 | 85.4% | 8.3 / 8 | 87.83% | 87.83% | +0.00 [-0.01, +0.01] | 1.0000 | 2,336 | +0.00 [+0.00, +0.00] |
| forest | 0.55 | 100.0% | 1.0 / 1 | 60.01% | 59.52% | +0.49 [+0.18, +0.80] | 0.0840 | 15,515 | +0.24 [+0.05, +0.45] |
| forest | 0.60 | 100.0% | 2.1 / 2 | 65.65% | 65.58% | +0.07 [-0.00, +0.15] | 1.0000 | 18,455 | +0.03 [-0.03, +0.09] |
| forest | 0.65 | 99.9% | 3.4 / 3 | 70.37% | 70.36% | +0.00 [+0.00, +0.01] | 1.0000 | 14,727 | +0.00 [+0.00, +0.00] |
| forest | 0.70 | 99.7% | 4.7 / 4 | 75.22% | 75.22% | +0.00 [+0.00, +0.00] | 1.0000 | 10,061 | +0.00 [+0.00, +0.00] |
| forest | 0.75 | 98.8% | 6.1 / 6 | 79.93% | 79.93% | +0.00 [+0.00, +0.00] | 1.0000 | 5,797 | +0.00 [+0.00, +0.00] |
| forest | 0.80 | 95.9% | 7.4 / 7 | 84.39% | 84.39% | +0.00 [+0.00, +0.00] | 1.0000 | 2,556 | +0.00 [+0.00, +0.00] |
| hgb-all | 0.55 | 100.0% | 1.3 / 1 | 61.23% | 61.09% | +0.14 [-0.07, +0.36] | 1.0000 | 19,172 | +0.05 [-0.12, +0.22] |
| hgb-all | 0.60 | 100.0% | 2.3 / 2 | 66.15% | 66.15% | -0.00 [-0.08, +0.08] | 1.0000 | 18,853 | -0.04 [-0.09, +0.02] |
| hgb-all | 0.65 | 99.8% | 3.4 / 3 | 70.61% | 70.63% | -0.01 [-0.05, +0.02] | 1.0000 | 14,413 | -0.01 [-0.04, +0.01] |
| hgb-all | 0.70 | 99.6% | 4.8 / 4 | 75.30% | 75.31% | -0.00 [-0.02, +0.01] | 1.0000 | 9,739 | +0.00 [+0.00, +0.00] |
| hgb-all | 0.75 | 98.5% | 6.3 / 6 | 80.31% | 80.31% | +0.00 [+0.00, +0.00] | 1.0000 | 4,980 | +0.00 [+0.00, +0.00] |
| hgb-all | 0.80 | 95.8% | 7.7 / 7 | 84.76% | 84.76% | +0.00 [+0.00, +0.00] | 1.0000 | 1,700 | +0.00 [+0.00, +0.00] |
| xgb-price | 0.55 | 100.0% | 1.0 / 1 | 59.53% | 59.11% | +0.42 [+0.09, +0.74] | 0.7291 | 14,864 | +0.03 [-0.14, +0.20] |
| xgb-price | 0.60 | 100.0% | 2.1 / 2 | 65.34% | 65.24% | +0.09 [-0.01, +0.20] | 1.0000 | 18,283 | +0.05 [-0.02, +0.11] |
| xgb-price | 0.65 | 99.8% | 3.3 / 3 | 70.45% | 70.44% | +0.00 [-0.02, +0.03] | 1.0000 | 14,789 | +0.01 [-0.02, +0.04] |
| xgb-price | 0.70 | 99.5% | 4.6 / 4 | 74.88% | 74.87% | +0.01 [+0.00, +0.02] | 1.0000 | 10,392 | +0.00 [+0.00, +0.00] |
| xgb-price | 0.75 | 98.6% | 6.0 / 6 | 79.74% | 79.74% | +0.00 [+0.00, +0.00] | 1.0000 | 6,184 | +0.00 [+0.00, +0.00] |
| xgb-price | 0.80 | 96.2% | 7.4 / 7 | 84.19% | 84.19% | +0.00 [+0.00, +0.00] | 1.0000 | 2,689 | +0.00 [+0.00, +0.00] |
| xgb-all | 0.55 | 100.0% | 1.0 / 1 | 59.62% | 59.12% | +0.50 [+0.15, +0.86] | 0.3196 | 14,744 | +0.10 [-0.13, +0.34] |
| xgb-all | 0.60 | 100.0% | 2.1 / 2 | 65.17% | 65.10% | +0.07 [-0.06, +0.20] | 1.0000 | 18,235 | -0.07 [-0.15, +0.02] |
| xgb-all | 0.65 | 99.9% | 3.3 / 3 | 70.01% | 70.00% | +0.00 [-0.03, +0.04] | 1.0000 | 14,837 | +0.03 [+0.00, +0.06] |
| xgb-all | 0.70 | 99.6% | 4.6 / 4 | 74.49% | 74.49% | +0.00 [+0.00, +0.00] | 1.0000 | 10,394 | +0.00 [+0.00, +0.00] |
| xgb-all | 0.75 | 98.6% | 6.0 / 6 | 79.48% | 79.48% | +0.00 [+0.00, +0.00] | 1.0000 | 6,127 | +0.00 [+0.00, +0.00] |
| xgb-all | 0.80 | 96.3% | 7.4 / 7 | 83.97% | 83.97% | +0.00 [+0.00, +0.00] | 1.0000 | 2,682 | +0.00 [+0.00, +0.00] |

The largest paired difference among the cells with at least 200 calls is +0.50 [+0.15, +0.86] points for xgb-all at 0.55 (23,328 calls); its Holm-adjusted p is 0.3196, not under 0.05.

The smallest paired difference among the cells with at least 200 calls is -0.01 [-0.05, +0.02] points for hgb-all at 0.65 (23,286 calls); its Holm-adjusted p is 1.0000, not under 0.05.

0 of the 48 cells have a Holm-adjusted p under 0.05: 0 with the predictor ahead of the rule and 0 behind it.

3 cells have an unadjusted interval entirely above zero (forest at 0.55, xgb-price at 0.55, xgb-all at 0.55) and 0 have one entirely below zero (none); their Holm-adjusted p is 0.0840, 0.7291, 0.3196 (above) and not applicable (below).

Among the cells at thresholds of 0.65 and above, the largest absolute paired difference is 0.02 points (logistic-all at 0.65).

The rule scored against itself differs by exactly zero in all 6 of its cells that make a call, and the constant predictor (majority) makes no call at any threshold; the run stops if either fails.

6 cells make fewer than 200 calls; they are listed above and left out of the two sentences that name the largest and smallest difference.
