The conditional cells under two labels, 2018 to 2026-08, every minute as a decision time: the last print (close of the horizon's last minute against the open of the decision minute) and 60-second VWAPs (the decision minute's VWAP against the last minute's VWAP). Deviation from the unconditional up-rate in points, firing-weighted over the years; 'retained' is the VWAP deviation as a share of the last-print one; the last column is the number of years in which the VWAP deviation had the pooled last-print sign. At horizon 1 the VWAP label compares the decision minute's first and second 30 seconds, so it is a different (shorter) question from the last-print label there. The 30 cells with the largest last-print deviation.

| pattern | horizon (min) | deviation, last print | deviation, VWAP | retained | years same sign under VWAP |
|---|---|---|---|---|---|
| sweep: range position > 0.95 | 30 | -9.0 | -9.6 | 106% | 9/9 |
| price at 4h high (rangepos >= 0.98) | 30 | -8.8 | -9.5 | 108% | 9/9 |
| sweep: range position < 0.05 | 30 | +8.6 | +9.1 | 107% | 9/9 |
| price at 4h low (rangepos <= 0.02) | 30 | +8.4 | +9.0 | 107% | 9/9 |
| sweep: range position > 0.90 | 30 | -8.3 | -8.7 | 105% | 9/9 |
| sweep: range position < 0.1 | 30 | +8.2 | +8.6 | 105% | 9/9 |
| price at 4h low (rangepos <= 0.02) | 15 | +8.1 | +8.9 | 110% | 9/9 |
| sweep: range position > 0.95 | 15 | -8.0 | -8.5 | 106% | 9/9 |
| price at 4h low (rangepos <= 0.02) | 10 | +7.9 | +8.7 | 109% | 9/9 |
| price at 4h high (rangepos >= 0.98) | 15 | -7.8 | -8.3 | 107% | 9/9 |
| sweep: range position > 0.85 | 30 | -7.7 | -8.0 | 103% | 9/9 |
| sweep: range position < 0.05 | 15 | +7.7 | +8.4 | 110% | 9/9 |
| sweep: RSI60 < 45 | 30 | +7.6 | +7.9 | 104% | 9/9 |
| sweep: RSI60 > 55 | 30 | -7.6 | -7.8 | 103% | 9/9 |
| sweep: range position < 0.15 | 30 | +7.6 | +7.9 | 105% | 9/9 |
| sweep: 15-min move < -3 sd | 3 | +7.5 | +7.8 | 104% | 9/9 |
| sweep: 5-min move < -3 sd | 3 | +7.5 | +7.9 | 105% | 9/9 |
| sweep: RSI14 < 25 | 10 | +7.5 | +7.8 | 104% | 9/9 |
| RSI14 below 30 | 10 | +7.5 | +7.9 | 105% | 9/9 |
| sweep: RSI14 < 30 | 10 | +7.5 | +7.9 | 105% | 9/9 |
| sweep: RSI14 < 25 | 5 | +7.5 | +7.8 | 104% | 9/9 |
| RSI14 below 30 | 5 | +7.4 | +7.8 | 105% | 9/9 |
| sweep: RSI14 < 30 | 5 | +7.4 | +7.8 | 105% | 9/9 |
| sweep: range position < 0.1 | 15 | +7.4 | +7.9 | 108% | 9/9 |
| price at 4h high (rangepos >= 0.98) | 10 | -7.3 | -8.1 | 110% | 9/9 |
| sweep: RSI14 < 25 | 3 | +7.3 | +7.0 | 96% | 9/9 |
| sweep: range position < 0.05 | 10 | +7.3 | +8.2 | 112% | 9/9 |
| sweep: RSI60 < 40 | 30 | +7.3 | +7.6 | 104% | 9/9 |
| sweep: range position > 0.90 | 15 | -7.3 | -7.6 | 105% | 9/9 |
| sweep: RSI14 < 20 | 3 | +7.2 | +6.7 | 94% | 9/9 |

By horizon, over all cells: the median share of the last-print deviation retained under the VWAP label, and the share of cells whose sign is unchanged.

| horizon (min) | cells | median retained | sign unchanged |
|---|---|---|---|
| 1 | 107 | 110% | 93% |
| 3 | 107 | 103% | 99% |
| 5 | 107 | 105% | 100% |
| 10 | 107 | 108% | 100% |
| 15 | 107 | 106% | 99% |
| 30 | 107 | 106% | 100% |
