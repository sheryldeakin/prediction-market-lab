Co-firing clusters of the 186 events of both libraries that fire at least 4,500 times over 2018 to 2026-08 ('lib' is the horizons event set, 'pa' the price-action library). Overlap coefficient of firing minutes pooled over years (shared minutes over the rarer event's minutes, so an event nested inside a broader one scores 1), average linkage, cut at 0.5. Each cluster is named by its most frequent member; 'union' is the up-rate deviation when any member fires, points, 95% interval from day-clustered errors, years held out of years with enough firings; 'opposite' counts members whose own 30-minute deviation has the other sign. The 30 clusters (of 55) whose union deviation at 30 minutes held in every year, by absolute deviation; every event's cluster is in cells_clusters.csv.

| cluster (most frequent member) | members | minutes any member fires | union deviation at 5 min | union deviation at 30 min | opposite | other members |
|---|---|---|---|---|---|---|
| pa: doji at a new 1h high | 1 | 0.46% | -5.3 [-6.0, -4.5] 9/9 | -6.8 [-7.6, -6.0] 9/9 | 0 |  |
| pa: wick rejection at the 1h high | 5 | 2.71% | -5.3 [-5.7, -5.0] 9/9 | -6.7 [-7.1, -6.3] 9/9 | 0 | pa: liquidity sweep of the 1h high (took it out, closed back below); pa: pin bar at a new 1h high (long upper wick); pa: wick rejection at the 4h high; pa: wick rejection at the daily high |
| pa: volume climax at a new 1h low (hour's largest volume) | 1 | 0.73% | +6.2 [+5.6, +6.8] 9/9 | +6.5 [+5.9, +7.1] 9/9 | 0 |  |
| pa: wick rejection at the 1h low | 5 | 2.62% | +5.1 [+4.8, +5.5] 9/9 | +6.3 [+5.9, +6.8] 9/9 | 0 | pa: liquidity sweep of the 1h low (took it out, closed back above); pa: pin bar at a new 1h low (long lower wick); pa: wick rejection at the 4h low; pa: wick rejection at the daily low |
| pa: doji at a new 1h low | 1 | 0.43% | +5.1 [+4.3, +5.8] 9/9 | +6.3 [+5.5, +7.2] 9/9 | 0 |  |
| pa: volume climax at a new 1h high (hour's largest volume) | 1 | 0.66% | -5.1 [-5.7, -4.4] 9/9 | -6.2 [-6.8, -5.5] 9/9 | 0 |  |
| pa: retest from above of a 4h high broken in the last hour | 1 | 1.69% | -2.6 [-3.1, -2.1] 9/9 | -5.6 [-6.4, -4.8] 9/9 | 0 |  |
| lib: previous window up | 45 | 78.10% | -3.6 [-3.8, -3.4] 9/9 | -5.4 [-5.6, -5.1] 9/9 | 0 | lib: 4h return above +50 bp; lib: EMA9 above EMA21 by 10 bp; lib: MACD histogram positive; lib: RSI14 above 70; lib: RSI60 above 65; lib: above upper Bollinger band; and 38 more |
| lib: OBV falling over 60 min | 2 | 5.32% | +3.7 [+3.3, +4.0] 9/9 | +5.3 [+4.6, +6.0] 9/9 | 0 | lib: sweep: OBV falling |
| lib: OBV rising over 60 min | 2 | 4.46% | -3.4 [-3.8, -3.0] 9/9 | -5.1 [-5.9, -4.3] 9/9 | 0 | lib: sweep: OBV rising |
| pa: retest from below of a 4h low broken in the last hour | 1 | 1.44% | +1.8 [+1.2, +2.3] 8/9 | +4.9 [+4.0, +5.8] 9/9 | 0 |  |
| lib: MACD histogram negative | 46 | 83.55% | +2.3 [+2.1, +2.5] 9/9 | +4.2 [+3.9, +4.5] 9/9 | 0 | lib: 4h return below -50 bp; lib: ADX14 above 30 (trending); lib: EMA9 below EMA21 by 10 bp; lib: RSI14 below 30; lib: RSI60 below 35; lib: below lower Bollinger band; and 39 more |
| pa: reclaimed the session VWAP in the last 5 minutes after 30+ minutes below | 1 | 0.82% | -4.6 [-5.4, -3.8] 9/9 | -4.1 [-5.0, -3.2] 9/9 | 0 |  |
| pa: resistance held (4h high tested within 3 bp, no close above, price now 3+ bp below) | 1 | 2.93% | -1.4 [-1.8, -0.9] 9/9 | -3.3 [-4.0, -2.5] 9/9 | 0 |  |
| lib: sweep: taker buy share > 0.1 (15 min) | 5 | 24.72% | -2.4 [-2.5, -2.2] 9/9 | -3.2 [-3.5, -2.9] 9/9 | 1 | lib: sweep: taker buy share > 0.2 (15 min); lib: sweep: taker buy share > 0.3 (15 min); lib: taker buying 60 pct+ of last 15 min; pa: absorption: heavy taker buying in the last 5 minutes, price did not rise |
| lib: sweep: taker sell share > 0.1 (15 min) | 5 | 27.38% | +2.5 [+2.3, +2.7] 9/9 | +3.1 [+2.8, +3.4] 9/9 | 1 | lib: sweep: taker sell share > 0.2 (15 min); lib: sweep: taker sell share > 0.3 (15 min); lib: taker selling 60 pct+ of last 15 min; pa: absorption: heavy taker selling in the last 5 minutes, price did not fall |
| pa: failed breakdown below the 1h low | 3 | 8.96% | +0.9 [+0.6, +1.2] 8/9 | +3.0 [+2.6, +3.4] 9/9 | 0 | pa: failed breakdown below the 4h low; pa: failed breakdown below the daily low |
| pa: support held (4h low tested within 3 bp, no close below, price now 3+ bp above) | 1 | 2.50% | +2.1 [+1.5, +2.6] 9/9 | +2.9 [+2.1, +3.8] 9/9 | 0 |  |
| pa: failed breakout above the 1h high | 3 | 9.16% | -1.2 [-1.5, -0.9] 9/9 | -2.9 [-3.3, -2.5] 9/9 | 0 | pa: failed breakout above the 4h high; pa: failed breakout above the daily high |
| pa: crossed a $100 level downward in the last 3 minutes | 2 | 14.08% | +2.3 [+2.1, +2.4] 9/9 | +2.7 [+2.5, +2.9] 9/9 | 0 | pa: crossed a $1,000 level downward in the last 3 minutes |
| pa: lost the session VWAP in the last 5 minutes after 30+ minutes above | 1 | 0.84% | +3.2 [+2.4, +3.9] 9/9 | +2.6 [+1.7, +3.5] 9/9 | 0 |  |
| pa: broke below the previous day's low in the last 5 minutes | 1 | 0.51% | +2.5 [+1.5, +3.5] 8/9 | +2.6 [+1.2, +3.9] 9/9 | 0 |  |
| pa: repeated rejection at the 4h high (2+ touches in 30 minutes, no close above) | 1 | 1.84% | -0.5 [-1.1, +0.1] 5/9 | -2.3 [-3.4, -1.1] 9/9 | 0 |  |
| pa: crossed a $100 level upward in the last 3 minutes | 2 | 14.09% | -2.0 [-2.2, -1.8] 9/9 | -2.1 [-2.3, -1.9] 9/9 | 0 | pa: crossed a $1,000 level upward in the last 3 minutes |
| pa: rejecting the downs (3+ down-minutes undone by the next minute in the last 15) | 1 | 19.56% | -1.8 [-1.9, -1.6] 9/9 | -1.8 [-2.1, -1.5] 9/9 | 0 |  |
| pa: approaching a $100 level from below (within 10 bp, rising) | 2 | 19.62% | -1.3 [-1.5, -1.1] 9/9 | -1.7 [-1.9, -1.5] 9/9 | 0 | pa: approaching a $1,000 level from below (within 10 bp, rising) |
| pa: rejecting the ups (3+ up-minutes undone by the next minute in the last 15) | 1 | 19.37% | +1.4 [+1.2, +1.6] 9/9 | +1.6 [+1.3, +1.9] 9/9 | 0 |  |
| pa: approaching a $100 level from above (within 10 bp, falling) | 2 | 19.46% | +1.0 [+0.8, +1.2] 7/9 | +1.5 [+1.3, +1.7] 9/9 | 1 | pa: approaching a $1,000 level from above (within 10 bp, falling) |
| lib: Asia early (0-3 UTC) | 3 | 16.65% | -0.4 [-0.6, -0.2] 8/9 | -1.3 [-1.8, -0.8] 9/9 | 0 | pa: 10 minutes after funding settlement (00:00 UTC); pa: first hour of the week (Monday 00:00 to 01:00 UTC) |
| pa: taker buying above 70% of the last minute | 1 | 15.33% | -0.2 [-0.3, -0.0] 6/9 | -1.0 [-1.1, -0.8] 9/9 | 0 |  |

How many clusters under each measure and cut: all 186 active events, and the 120 events whose 30-minute cell held its sign in every year.

| measure | cut | clusters, all active events | clusters, events held every year at 30 min |
|---|---|---|---|
| overlap coefficient | 0.5 | 55 | 30 |
| overlap coefficient | 0.7 | 72 | 40 |
| overlap coefficient | 0.9 | 94 | 58 |
| Jaccard | 0.2 | 85 | 44 |
| Jaccard | 0.3 | 108 | 57 |
| Jaccard | 0.5 | 146 | 87 |
