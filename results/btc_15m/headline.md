| where | one-bit rule | its accuracy | fitted model | its accuracy | model minus rule, points [day CI] | more |
|---|---|---|---|---|---|---|
| backtest 2025-10 to 2026-08, open | previous window reversed | 52.21% | forest (price + flow) | 52.65% | +0.44 [-0.25, +1.18] | [-0.30, +1.04], days better 54%, sign p 0.104 |
| backtest, open, richest feature set | previous window reversed | 52.21% | forest (price + flow + indicators) | 53.48% | +1.27 [+0.58, +1.95] | day-block interval only |
| backtest, minute 3 | lead z-score | 66.35% | xgb-all | 66.28% | -0.07 [-0.42, +0.27] | [-0.33, +0.21], days better 50%, sign p 0.649 |
| holdout 2025-01 to 2025-09, open (two declared runs; see the process log) | previous window reversed | 51.56% | forest (frozen forward model) | 51.64% | +0.08 [-0.58, +0.72] | days better 50%, p 0.3948 |
| holdout 2025-01 to 2025-09, open (two declared runs; see the process log) | previous window reversed | 51.56% | forest (price + flow + indicators) | 51.96% | +0.40 [-0.22, +1.02] | days better 54%, p 0.1129 |
| holdout September 2026, minute 0 (re-fitted frozen models) |  |  | forest | 50.94% |  | 2,880 windows; see the event rules row for the reversal in September |
| holdout September 2026, minute 3 (re-fitted frozen models) |  |  | xgb-all | 66.67% |  | 2,880 windows; see the event rules row for the reversal in September |
| backtest on Coinbase BTC-USD | previous window reversed | 51.95% | forest (price only) | 52.27% | +0.32 [-0.31, +0.98] | day-block interval |
| backtest on Bitstamp BTC-USD | previous window reversed | 52.06% | forest (price only) | 52.06% | -0.00 [-0.66, +0.70] | day-block interval |
| backtest, label from 60-second VWAPs inside the window (no shared prints) | previous window reversed (same label) | 52.54% | forest | 53.18% | +0.63 [-0.06, +1.37] | days better 53% |
| backtest, windows shifted 0 to 14 minutes off the quarter hour | previous window reversed | 51.31% to 52.67% | forest (price + flow) |  | -0.39 to +1.03 across the 15 offsets | an effect of any 15-minute boundary, not of the clock |
| event rules: stable survivors of the wide search | 745 real | null median 0, null maximum 147 |  |  |  | labels rotated within months, 200 runs |
| event rules: kept their direction in September 2026 | 562 of 666 | null median 330, 95th percentile 492 |  |  |  |  |
| event rules: kept their direction in 2025 | 737 of 745 |  |  |  |  | scored once |
