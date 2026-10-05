The same slices for the six strongest any-minute cells at the 15-minute horizon, 2018 to 2026, all times UTC: every minute is a decision time, the call is the reversal the cell implies (up after a drop, a low or RSI14 below 25; down after the mirror), and a slice is the cell's firings inside it. Deviation, pooling, years held and the family-wise adjusted p are as in calendar_rules.md (500 rotated-label runs per year; a slice-year is scored when at least 100 firings fall inside and outside the slice).

The cells over all firings: firings per year (mean) and the accuracy of the call, firing-weighted over the years.

| cell | firings per year | accuracy |
|---|---|---|
| 3-sd drop (5-min move < -3 sd) | 2,572 | 55.5% |
| 3-sd rise (5-min move > +3 sd) | 2,649 | 53.6% |
| 4-hour low (rangepos <= 0.02) | 5,189 | 58.2% |
| 4-hour high (rangepos >= 0.98) | 7,188 | 57.4% |
| RSI14 below 25 | 7,137 | 57.0% |
| RSI14 above 75 | 7,861 | 55.7% |

By cell and family: slices scored, how many clear the family's 5% adjusted line and how many of those hold the sign in at least 8 years, the smallest pooled deviation that would clear the line (median over slices), and the slice with the largest pooled |z|.

| cell | family | slices scored | clear the null | clear and hold | smallest clearing deviation (points) | largest |z| slice | its deviation (points), years held, adjusted p |
|---|---|---|---|---|---|---|---|
| 3-sd drop (5-min move < -3 sd) | hour | 21 | 0 | 0 | 9.2 | 12:00 | +4.2 (1.9) 7/9, p 0.455 |
| 3-sd drop (5-min move < -3 sd) | weekday | 7 | 1 | 0 | 3.0 | Sat | +4.5 (1.7) 7/9, p 0.040 |
| 3-sd drop (5-min move < -3 sd) | session | 5 | 0 | 0 | 2.5 | Europe 08-13 | -0.6 (0.9) 5/9, p 0.924 |
| 3-sd drop (5-min move < -3 sd) | month | 12 | 0 | 0 | 5.8 | Oct | +3.4 (2.0) 7/8, p 0.675 |
| 3-sd drop (5-min move < -3 sd) | event slot | 3 | 0 | 0 | 3.3 | weekend (Sat, Sun) | +2.1 (0.9) 7/9, p 0.066 |
| 3-sd rise (5-min move > +3 sd) | hour | 20 | 0 | 0 | 8.6 | 07:00 | -5.3 (2.2) 7/8, p 0.319 |
| 3-sd rise (5-min move > +3 sd) | weekday | 7 | 1 | 1 | 3.1 | Sat | +4.5 (1.2) 8/9, p 0.006 |
| 3-sd rise (5-min move > +3 sd) | session | 5 | 0 | 0 | 3.3 | Asia 00-08 | -1.6 (0.7) 6/9, p 0.100 |
| 3-sd rise (5-min move > +3 sd) | month | 12 | 0 | 0 | 6.2 | Oct | -3.8 (1.5) 7/8, p 0.172 |
| 3-sd rise (5-min move > +3 sd) | event slot | 3 | 0 | 0 | 2.5 | weekend (Sat, Sun) | +1.6 (0.7) 8/9, p 0.072 |
| 4-hour low (rangepos <= 0.02) | hour | 24 | 0 | 0 | 6.3 | 11:00 | +4.3 (1.9) 6/7, p 0.441 |
| 4-hour low (rangepos <= 0.02) | weekday | 7 | 0 | 0 | 2.6 | Sat | +3.0 (1.2) 8/9, p 0.084 |
| 4-hour low (rangepos <= 0.02) | session | 5 | 0 | 0 | 2.2 | Europe 08-13 | +1.0 (0.9) 5/9, p 0.693 |
| 4-hour low (rangepos <= 0.02) | month | 12 | 0 | 0 | 3.8 | Sep | +1.5 (1.2) 8/8, p 0.940 |
| 4-hour low (rangepos <= 0.02) | event slot | 3 | 0 | 0 | 2.5 | weekend (Sat, Sun) | +2.2 (1.0) 7/9, p 0.102 |
| 4-hour high (rangepos >= 0.98) | hour | 24 | 0 | 0 | 5.1 | 07:00 | +2.3 (1.5) 4/9, p 0.958 |
| 4-hour high (rangepos >= 0.98) | weekday | 7 | 0 | 0 | 2.6 | Sat | +2.1 (1.0) 7/9, p 0.180 |
| 4-hour high (rangepos >= 0.98) | session | 5 | 0 | 0 | 2.0 | overlap 13-17 | -1.2 (1.0) 5/9, p 0.671 |
| 4-hour high (rangepos >= 0.98) | month | 12 | 0 | 0 | 4.4 | Mar | +2.0 (1.3) 7/9, p 0.778 |
| 4-hour high (rangepos >= 0.98) | event slot | 4 | 0 | 0 | 4.0 | weekend (Sat, Sun) | +0.9 (0.7) 6/9, p 0.513 |
| RSI14 below 25 | hour | 24 | 0 | 0 | 5.6 | 22:00 | +3.7 (1.6) 7/9, p 0.385 |
| RSI14 below 25 | weekday | 7 | 1 | 1 | 2.7 | Sat | +4.7 (1.3) 8/9, p 0.010 |
| RSI14 below 25 | session | 5 | 0 | 0 | 2.2 | late 21-24 | +0.9 (1.0) 5/9, p 0.850 |
| RSI14 below 25 | month | 12 | 0 | 0 | 4.6 | Oct | +3.0 (1.2) 6/8, p 0.172 |
| RSI14 below 25 | event slot | 3 | 1 | 0 | 2.6 | weekend (Sat, Sun) | +2.0 (0.7) 7/9, p 0.012 |
| RSI14 above 75 | hour | 24 | 0 | 0 | 5.7 | 12:00 | +4.6 (1.6) 8/9, p 0.118 |
| RSI14 above 75 | weekday | 7 | 1 | 1 | 2.6 | Sat | +3.4 (0.8) 9/9, p 0.002 |
| RSI14 above 75 | session | 5 | 0 | 0 | 2.2 | late 21-24 | +2.0 (0.9) 9/9, p 0.086 |
| RSI14 above 75 | month | 12 | 0 | 0 | 4.3 | Aug | -1.7 (1.1) 5/9, p 0.792 |
| RSI14 above 75 | event slot | 5 | 1 | 1 | 4.6 | weekend (Sat, Sun) | +1.7 (0.6) 9/9, p 0.024 |
