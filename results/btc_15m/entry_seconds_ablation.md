Which inputs carry the fitted models' gain over the lead-sign rule at 10, 30 and 60 seconds, same windows and same month-by-month walk-forward as the table above (2025-10 to 2026-08, 23328 windows), on CPU. Each model is fitted on three input sets: +lead is the minute-0 feature set plus the lead and the lead scaled by the volatility left in the window (no signed-volume share, trade count or large-trade count); +ticks is the minute-0 set plus all five tick features, the models of the table above; ticks-only is the five tick features with no minute-0 feature. Accuracy has a day-block 95% interval. "vs lead-sign" is accuracy minus the entry's lead-sign rule on the same windows, with a day-block and a month-block 95% interval, the share of days better and the sign-flip p. The month-block interval resamples whole calendar months (the convention of checks.md); with so few test months it is wide.

| entry | model | inputs | accuracy [95% CI] | AUC | log loss | vs lead-sign, day blocks | vs lead-sign, month blocks | days better | sign p |
|---|---|---|---|---|---|---|---|---|---|
| 10 s | lead-sign | rule | 54.15% [53.51, 54.81] | 0.540 | 0.6898 | baseline |  |  |  |
| 10 s | forest | +lead | 54.87% [54.25, 55.52] | 0.570 | 0.6853 | +0.73 [+0.18, +1.30] | +0.73 [+0.20, +1.23] | 57% | 0.0050 |
| 10 s | forest | +ticks | 54.82% [54.22, 55.43] | 0.570 | 0.6854 | +0.68 [+0.12, +1.22] | +0.68 [+0.14, +1.14] | 54% | 0.0090 |
| 10 s | forest | ticks-only | 53.26% [52.63, 53.93] | 0.548 | 0.6908 | -0.88 [-1.40, -0.34] | -0.88 [-1.67, -0.03] | 38% | 0.9995 |
| 10 s | xgb | +lead | 54.91% [54.27, 55.53] | 0.570 | 0.6854 | +0.76 [+0.21, +1.35] | +0.76 [+0.15, +1.29] | 58% | 0.0045 |
| 10 s | xgb | +ticks | 54.85% [54.19, 55.48] | 0.569 | 0.6859 | +0.71 [+0.14, +1.29] | +0.71 [+0.05, +1.33] | 60% | 0.0050 |
| 10 s | xgb | ticks-only | 53.74% [53.15, 54.37] | 0.553 | 0.6892 | -0.40 [-0.83, +0.03] | -0.40 [-0.96, +0.16] | 46% | 0.9645 |
| 30 s | lead-sign | rule | 56.12% [55.48, 56.74] | 0.558 | 0.6857 | baseline |  |  |  |
| 30 s | forest | +lead | 56.75% [56.13, 57.34] | 0.593 | 0.6792 | +0.63 [+0.14, +1.14] | +0.63 [+0.04, +1.20] | 57% | 0.0080 |
| 30 s | forest | +ticks | 56.94% [56.29, 57.57] | 0.596 | 0.6784 | +0.83 [+0.35, +1.33] | +0.83 [+0.16, +1.47] | 61% | < 0.0005 |
| 30 s | forest | ticks-only | 55.88% [55.23, 56.51] | 0.583 | 0.6829 | -0.24 [-0.76, +0.30] | -0.24 [-0.91, +0.36] | 48% | 0.8121 |
| 30 s | xgb | +lead | 56.39% [55.69, 57.06] | 0.592 | 0.6794 | +0.27 [-0.25, +0.83] | +0.27 [-0.52, +1.08] | 54% | 0.1644 |
| 30 s | xgb | +ticks | 56.52% [55.87, 57.14] | 0.593 | 0.6792 | +0.40 [-0.12, +0.95] | +0.40 [-0.28, +1.11] | 54% | 0.0745 |
| 30 s | xgb | ticks-only | 55.42% [54.75, 56.07] | 0.585 | 0.6819 | -0.69 [-1.15, -0.23] | -0.69 [-1.16, -0.26] | 43% | 0.9980 |
| 60 s | lead-sign | rule | 58.85% [58.20, 59.54] | 0.584 | 0.6776 | baseline |  |  |  |
| 60 s | forest | +lead | 59.19% [58.56, 59.84] | 0.630 | 0.6662 | +0.34 [-0.04, +0.75] | +0.34 [-0.11, +0.78] | 58% | 0.0575 |
| 60 s | forest | +ticks | 59.06% [58.45, 59.70] | 0.629 | 0.6663 | +0.21 [-0.20, +0.61] | +0.21 [-0.22, +0.69] | 54% | 0.1649 |
| 60 s | forest | ticks-only | 58.17% [57.57, 58.79] | 0.619 | 0.6707 | -0.68 [-1.11, -0.24] | -0.68 [-1.29, -0.10] | 40% | 0.9985 |
| 60 s | xgb | +lead | 59.02% [58.39, 59.70] | 0.629 | 0.6667 | +0.17 [-0.31, +0.63] | +0.17 [-0.26, +0.60] | 52% | 0.2429 |
| 60 s | xgb | +ticks | 58.97% [58.34, 59.65] | 0.628 | 0.6668 | +0.12 [-0.37, +0.61] | +0.12 [-0.38, +0.58] | 52% | 0.3073 |
| 60 s | xgb | ticks-only | 58.75% [58.10, 59.42] | 0.622 | 0.6694 | -0.10 [-0.44, +0.27] | -0.10 [-0.46, +0.29] | 50% | 0.7056 |

The tick increment proper: accuracy of +ticks minus accuracy of +lead, the same model on the same windows, so the only difference is the signed-volume share, trade count and large-trade count.

| entry | model | +ticks minus +lead, day blocks | +ticks minus +lead, month blocks | days better | sign p |
|---|---|---|---|---|---|
| 10 s | forest | -0.05 [-0.39, +0.29] | -0.05 [-0.37, +0.26] | 50% | 0.5977 |
| 10 s | xgb | -0.06 [-0.42, +0.29] | -0.06 [-0.35, +0.26] | 52% | 0.6007 |
| 30 s | forest | +0.19 [-0.12, +0.52] | +0.19 [+0.02, +0.39] | 52% | 0.1359 |
| 30 s | xgb | +0.12 [-0.23, +0.47] | +0.12 [-0.14, +0.42] | 52% | 0.2454 |
| 60 s | forest | -0.13 [-0.42, +0.15] | -0.13 [-0.30, +0.05] | 45% | 0.8116 |
| 60 s | xgb | -0.05 [-0.31, +0.22] | -0.05 [-0.33, +0.21] | 47% | 0.6412 |

Zero is outside the day-block interval for 9 of the 18 comparisons with the lead-sign rule (forest +lead at 10 s (+0.73); forest +ticks at 10 s (+0.68); forest ticks-only at 10 s (-0.88); xgb +lead at 10 s (+0.76); xgb +ticks at 10 s (+0.71); forest +lead at 30 s (+0.63); forest +ticks at 30 s (+0.83); xgb ticks-only at 30 s (-0.69); forest ticks-only at 60 s (-0.68)) and outside the month-block interval for 9 (forest +lead at 10 s (+0.73); forest +ticks at 10 s (+0.68); forest ticks-only at 10 s (-0.88); xgb +lead at 10 s (+0.76); xgb +ticks at 10 s (+0.71); forest +lead at 30 s (+0.63); forest +ticks at 30 s (+0.83); xgb ticks-only at 30 s (-0.69); forest ticks-only at 60 s (-0.68)). Zero is outside the day-block interval for 0 of the 6 comparisons of +ticks with +lead (none) and outside the month-block interval for 1 (forest at 30 s (+0.19)). The intervals are not adjusted for the number of comparisons.

What these windows could detect: across the rows above a day-block interval on a difference is 0.53 to 1.15 points wide and a month-block interval is 0.35 to 1.65 points wide. A null here is a bound of that width, not a verdict.

The +ticks rows reproduce the forest+ticks and xgb+ticks accuracies of the table above exactly.
