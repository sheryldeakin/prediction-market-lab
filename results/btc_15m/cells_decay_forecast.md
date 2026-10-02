Fading as a forecast: the 16 strongest cells held in every year (both libraries, one horizon per event), their yearly deviation fitted with a straight line in the year (weights 1/se^2). Slope in points per year; the 2027 forecast with a 95% interval from the fitted line's uncertainty; the year the line reaches zero if the trend continued ('none' when the trend points away from zero). Record: mean absolute error, in points, of forecasting each year from 2022 with the line fitted on earlier years, against 'same as last year' and 'mean of earlier years'.

| library | pattern | horizon (min) | 2018 | 2026 | slope (points/year) | 2027 forecast [95%] | line reaches zero | record: line | same as last year | mean so far |
|---|---|---|---|---|---|---|---|---|---|---|
| lib | sweep: range position > 0.95 | 30 | -13.5 | -8.4 | +0.99 | -4.5 [-6.6, -2.3] | 2032 | 1.4 | 1.6 | 3.4 |
| pa | wick rejection at the daily low | 30 | +9.9 | +6.9 | -0.98 | +4.4 [-1.6, +10.4] | 2031 | 4.2 | 5.2 | 4.7 |
| lib | price at 4h high (rangepos >= 0.98) | 30 | -11.8 | -8.5 | +0.90 | -4.8 [-7.1, -2.4] | 2032 | 1.2 | 1.1 | 3.0 |
| pa | wick rejection at the 4h high | 30 | -11.2 | -6.4 | +0.88 | -4.2 [-6.1, -2.3] | 2032 | 0.9 | 0.9 | 3.0 |
| lib | sweep: range position < 0.05 | 30 | +9.3 | +7.7 | -0.81 | +5.4 [-0.0, +10.9] | 2034 | 3.7 | 4.0 | 4.3 |
| lib | price at 4h low (rangepos <= 0.02) | 30 | +7.5 | +7.7 | -0.62 | +6.3 [+0.0, +12.5] | 2037 | 4.4 | 4.8 | 3.8 |
| lib | sweep: range position > 0.90 | 30 | -12.6 | -7.9 | +0.89 | -4.2 [-6.7, -1.6] | 2032 | 1.6 | 1.5 | 3.0 |
| lib | sweep: range position < 0.1 | 30 | +9.8 | +8.1 | -0.85 | +4.6 [+0.0, +9.1] | 2032 | 2.9 | 3.1 | 3.6 |
| pa | wick rejection at the 4h low | 30 | +9.0 | +6.8 | -0.92 | +3.7 [-0.4, +7.9] | 2031 | 2.9 | 3.2 | 3.9 |
| lib | sweep: range position > 0.85 | 30 | -11.7 | -6.9 | +0.78 | -4.1 [-6.3, -1.8] | 2032 | 1.6 | 1.1 | 2.5 |
| lib | sweep: RSI60 < 45 | 30 | +8.8 | +6.1 | -0.61 | +4.7 [+1.3, +8.0] | 2035 | 1.9 | 2.2 | 2.2 |
| lib | sweep: RSI60 > 55 | 30 | -11.7 | -6.1 | +0.83 | -3.5 [-5.6, -1.5] | 2031 | 1.5 | 1.2 | 2.5 |
| lib | sweep: range position < 0.15 | 30 | +9.1 | +7.2 | -0.76 | +4.2 [+0.3, +8.1] | 2032 | 2.2 | 2.4 | 2.8 |
| lib | sweep: 15-min move < -3 sd | 3 | +5.6 | +8.0 | -0.28 | +6.2 [+0.8, +11.5] | 2049 | 3.0 | 3.4 | 2.5 |
| lib | sweep: 5-min move < -3 sd | 3 | +4.0 | +5.6 | -0.15 | +6.7 [+1.2, +12.1] | 2071 | 3.4 | 3.0 | 2.5 |
| lib | sweep: RSI14 < 25 | 10 | +5.3 | +6.4 | -0.34 | +6.1 [+1.7, +10.6] | 2045 | 2.4 | 1.7 | 2.2 |

Across the 16 cells: the line beats 'same as last year' in 9 and 'mean so far' in 12; 16 trend toward zero, reaching it between 2031 and 2071 (median 2032); the 2027 forecasts are 3.5 to 6.7 points in size against 5.6 to 8.5 in 2026.
