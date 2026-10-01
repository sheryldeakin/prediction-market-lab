Each cell pooled across years with a random-effects model (DerSimonian-Laird): the pooled deviation in points with its standard error, tau (the between-year standard deviation of the true effect, points), I-squared (the share of the yearly variation that is real change rather than noise), and for the latest year the raw deviation, the shrunken deviation, and the weight the shrunken value puts on that year's own data. The 30 cells with the largest pooled deviation.

| pattern | horizon (min) | pooled (se) | tau | I-squared | latest year | raw | shrunk | weight on own year |
|---|---|---|---|---|---|---|---|---|
| sweep: range position < 0.05 | 30 | +9.9 (1.3) | 3.6 | 92% | 2026 | +7.7 | +7.9 | 0.91 |
| price at 4h low (rangepos <= 0.02) | 30 | +9.8 (1.3) | 3.7 | 90% | 2026 | +7.7 | +7.9 | 0.88 |
| sweep: range position > 0.95 | 30 | -9.5 (1.0) | 2.7 | 88% | 2026 | -8.4 | -8.6 | 0.83 |
| price at 4h high (rangepos >= 0.98) | 30 | -9.4 (0.9) | 2.5 | 82% | 2026 | -8.5 | -8.8 | 0.73 |
| price at 4h low (rangepos <= 0.02) | 15 | +9.4 (1.3) | 3.6 | 91% | 2026 | +7.5 | +7.7 | 0.90 |
| price at 4h low (rangepos <= 0.02) | 10 | +9.3 (1.2) | 3.5 | 92% | 2026 | +6.7 | +6.9 | 0.92 |
| sweep: range position < 0.1 | 30 | +9.2 (1.1) | 3.3 | 93% | 2026 | +8.1 | +8.2 | 0.91 |
| sweep: range position < 0.05 | 15 | +8.8 (1.1) | 3.3 | 93% | 2026 | +6.7 | +6.9 | 0.92 |
| sweep: range position > 0.90 | 30 | -8.6 (0.9) | 2.6 | 91% | 2026 | -7.9 | -8.0 | 0.88 |
| sweep: range position < 0.05 | 10 | +8.5 (1.1) | 3.3 | 94% | 2026 | +6.0 | +6.1 | 0.94 |
| sweep: range position > 0.95 | 15 | -8.4 (0.6) | 1.4 | 76% | 2026 | -8.0 | -8.1 | 0.73 |
| price at 4h high (rangepos >= 0.98) | 15 | -8.3 (0.6) | 1.4 | 64% | 2026 | -8.2 | -8.2 | 0.58 |
| sweep: range position < 0.15 | 30 | +8.2 (1.0) | 2.8 | 93% | 2026 | +7.2 | +7.3 | 0.90 |
| sweep: range position < 0.1 | 15 | +8.1 (0.9) | 2.6 | 92% | 2026 | +7.2 | +7.3 | 0.90 |
| sweep: RSI14 < 25 | 5 | +8.1 (1.2) | 3.4 | 93% | 2026 | +5.1 | +5.3 | 0.91 |
| price at 4h low (rangepos <= 0.02) | 5 | +8.1 (1.2) | 3.4 | 93% | 2026 | +5.1 | +5.3 | 0.93 |
| sweep: RSI14 < 20 | 3 | +8.1 (1.3) | 3.5 | 85% | 2026 | +5.6 | +6.0 | 0.84 |
| sweep: RSI14 < 25 | 3 | +8.0 (1.2) | 3.4 | 95% | 2026 | +5.8 | +5.9 | 0.94 |
| sweep: RSI14 < 25 | 10 | +8.0 (0.9) | 2.4 | 84% | 2026 | +6.4 | +6.7 | 0.83 |
| sweep: range position > 0.85 | 30 | -8.0 (0.8) | 2.4 | 91% | 2026 | -6.9 | -7.0 | 0.90 |
| price at 4h high (rangepos >= 0.98) | 10 | -7.9 (0.7) | 1.7 | 77% | 2026 | -7.9 | -7.9 | 0.69 |
| sweep: 15-min move < -3 sd | 3 | +7.9 (1.0) | 2.1 | 56% | 2026 | +8.0 | +7.9 | 0.46 |
| sweep: RSI60 < 45 | 30 | +7.8 (0.8) | 2.4 | 92% | 2026 | +6.1 | +6.3 | 0.91 |
| RSI14 below 30 | 10 | +7.8 (0.7) | 2.1 | 91% | 2026 | +6.4 | +6.5 | 0.89 |
| sweep: RSI14 < 30 | 10 | +7.8 (0.7) | 2.1 | 91% | 2026 | +6.4 | +6.5 | 0.89 |
| sweep: RSI14 < 30 | 5 | +7.8 (1.0) | 2.8 | 96% | 2026 | +5.0 | +5.2 | 0.95 |
| RSI14 below 30 | 5 | +7.8 (1.0) | 2.8 | 96% | 2026 | +5.0 | +5.2 | 0.95 |
| sweep: RSI60 > 55 | 30 | -7.7 (0.8) | 2.4 | 93% | 2026 | -6.1 | -6.3 | 0.91 |
| sweep: RSI60 < 40 | 30 | +7.6 (1.0) | 2.8 | 83% | 2026 | +8.7 | +8.5 | 0.80 |
| sweep: RSI14 < 20 | 5 | +7.6 (1.2) | 3.0 | 77% | 2026 | +3.9 | +5.0 | 0.71 |

Over all 642 cells: median tau 1.3 points, median I-squared 86%, median weight on the latest year's own data 0.81. A high I-squared with a stable sign (the usual case here) means the size of a cell changes from year to year while its direction does not, so the pooled value is a long-run average and the shrunken latest-year value is the better guide to the present.
