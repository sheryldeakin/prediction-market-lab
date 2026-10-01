The price-action library, 2018 to 2026-08, every minute as a decision time: trader vernacular written as events that read only earlier candles (definitions in models/btc_15m/price_action.py), scored like the conditional tables in horizons.md. Pooled up-rate of the next h minutes when the event holds, deviation from the unconditional rate in points, share of minutes it fires on, years in which the sign matched the pooled sign out of years with at least 500 firings, and the smallest search-wide adjusted p across years (30 rotated-label runs per year). Top 40 cells by absolute deviation that held in every year.

| family | event | horizon (min) | up-rate | deviation (points) | fires on | years held | min adjusted p |
|---|---|---|---|---|---|---|---|
| levels | wick rejection at the daily low | 30 | 59.4% | +9.0 | 0.27% | 9/9 | 0.0074 |
| volume and flow | delta divergence: new 4h low with net taker buying over the hour | 30 | 59.2% | +8.7 | 0.27% | 8/8 | 0.0037 |
| levels | wick rejection at the 4h high | 30 | 41.9% | -8.6 | 1.01% | 9/9 | 0.0037 |
| levels | wick rejection at the 4h low | 30 | 58.6% | +8.1 | 0.94% | 9/9 | 0.0037 |
| levels | wick rejection at the daily low | 15 | 58.3% | +8.0 | 0.27% | 9/9 | 0.0074 |
| levels | wick rejection at the daily low | 10 | 58.1% | +7.9 | 0.27% | 9/9 | 0.0037 |
| levels | wick rejection at the 4h high | 15 | 42.4% | -7.9 | 1.01% | 9/9 | 0.0037 |
| levels | wick rejection at the 4h low | 15 | 57.9% | +7.7 | 0.94% | 9/9 | 0.0037 |
| volume and flow | delta divergence: new 4h high with net taker selling over the hour | 15 | 42.9% | -7.4 | 0.42% | 9/9 | 0.0074 |
| volume and flow | delta divergence: new 4h low with net taker buying over the hour | 15 | 57.7% | +7.4 | 0.27% | 8/8 | 0.0074 |
| levels | wick rejection at the 4h low | 10 | 57.5% | +7.3 | 0.94% | 9/9 | 0.0037 |
| levels | wick rejection at the 4h high | 10 | 43.1% | -7.1 | 1.01% | 9/9 | 0.0037 |
| candles | pin bar at a new 1h high (long upper wick) | 15 | 43.3% | -7.1 | 0.53% | 9/9 | 0.0037 |
| candles | pin bar at a new 1h high (long upper wick) | 30 | 43.6% | -6.9 | 0.53% | 9/9 | 0.0037 |
| levels | wick rejection at the daily high | 30 | 43.7% | -6.9 | 0.31% | 9/9 | 0.0295 |
| levels | wick rejection at the daily low | 5 | 57.0% | +6.8 | 0.27% | 9/9 | 0.0074 |
| levels | acceptance above the 4h high (last 5 closes all above it) | 30 | 43.7% | -6.8 | 2.97% | 9/9 | 0.0037 |
| volume and flow | delta divergence: new 4h high with net taker selling over the hour | 10 | 43.4% | -6.8 | 0.42% | 9/9 | 0.0074 |
| volume and flow | delta divergence: new 4h low with net taker buying over the hour | 10 | 57.0% | +6.8 | 0.27% | 8/8 | 0.0037 |
| candles | doji at a new 1h high | 30 | 43.8% | -6.8 | 0.46% | 9/9 | 0.0037 |
| candles | pin bar at a new 1h high (long upper wick) | 5 | 43.5% | -6.7 | 0.53% | 9/9 | 0.0037 |
| candles | doji at a new 1h high | 15 | 43.7% | -6.6 | 0.46% | 9/9 | 0.0037 |
| candles | pin bar at a new 1h low (long lower wick) | 10 | 56.9% | +6.6 | 0.56% | 9/9 | 0.0037 |
| candles | pin bar at a new 1h low (long lower wick) | 30 | 57.1% | +6.6 | 0.56% | 9/9 | 0.0037 |
| levels | liquidity sweep of the 1h high (took it out, closed back below) | 30 | 44.0% | -6.5 | 2.03% | 9/9 | 0.0037 |
| candles | pin bar at a new 1h high (long upper wick) | 10 | 43.7% | -6.5 | 0.53% | 9/9 | 0.0037 |
| volume and flow | volume climax at a new 1h low (hour's largest volume) | 30 | 57.0% | +6.5 | 0.72% | 9/9 | 0.0037 |
| levels | wick rejection at the 1h high | 30 | 44.1% | -6.5 | 2.57% | 9/9 | 0.0037 |
| levels | acceptance below the 4h low (last 5 closes all below it) | 30 | 56.9% | +6.4 | 2.54% | 9/9 | 0.0074 |
| levels | liquidity sweep of the 1h high (took it out, closed back below) | 15 | 44.0% | -6.3 | 2.03% | 9/9 | 0.0037 |
| candles | pin bar at a new 1h low (long lower wick) | 15 | 56.6% | +6.3 | 0.56% | 9/9 | 0.0037 |
| candles | doji at a new 1h low | 30 | 56.8% | +6.3 | 0.43% | 9/9 | 0.0037 |
| levels | liquidity sweep of the 1h low (took it out, closed back above) | 30 | 56.7% | +6.2 | 2.01% | 9/9 | 0.0037 |
| levels | wick rejection at the 1h high | 15 | 44.1% | -6.2 | 2.57% | 9/9 | 0.0037 |
| levels | liquidity sweep of the 1h low (took it out, closed back above) | 10 | 56.4% | +6.2 | 2.01% | 9/9 | 0.0037 |
| levels | wick rejection at the 4h low | 5 | 56.3% | +6.1 | 0.94% | 9/9 | 0.0037 |
| volume and flow | volume climax at a new 1h high (hour's largest volume) | 30 | 44.4% | -6.1 | 0.66% | 9/9 | 0.0037 |
| volume and flow | volume climax at a new 1h low (hour's largest volume) | 5 | 56.3% | +6.1 | 0.72% | 9/9 | 0.0037 |
| levels | wick rejection at the 1h low | 30 | 56.6% | +6.1 | 2.48% | 9/9 | 0.0037 |
| levels | liquidity sweep of the 1h low (took it out, closed back above) | 15 | 56.4% | +6.1 | 2.01% | 9/9 | 0.0037 |

By family: events defined, cells (event by horizon) that held their sign in every year, and the largest absolute deviation among them.

| family | events | cells tested | held every year | largest deviation among those (points) |
|---|---|---|---|---|
| candles | 7 | 42 | 23 | 7.1 |
| levels | 38 | 228 | 132 | 9.0 |
| round numbers | 8 | 48 | 24 | 3.1 |
| time | 17 | 102 | 2 | 1.3 |
| volatility | 1 | 6 | 0 | nan |
| volume and flow | 8 | 48 | 20 | 8.7 |

Every event at the 15-minute horizon, held or not, so that the null results are visible too.

| family | event | up-rate | deviation (points) | fires on | years held | min adjusted p |
|---|---|---|---|---|---|---|
| candles | pin bar at a new 1h high (long upper wick) | 43.3% | -7.1 | 0.53% | 9/9 | 0.0037 |
| candles | doji at a new 1h high | 43.7% | -6.6 | 0.46% | 9/9 | 0.0037 |
| candles | pin bar at a new 1h low (long lower wick) | 56.6% | +6.3 | 0.56% | 9/9 | 0.0037 |
| candles | doji at a new 1h low | 56.1% | +5.8 | 0.43% | 9/9 | 0.0037 |
| candles | bullish engulfing | 49.8% | -0.5 | 7.84% | 8/9 | 0.1033 |
| candles | bearish engulfing | 50.7% | +0.4 | 7.84% | 7/9 | 0.1993 |
| candles | inside bar (last minute inside the previous one) | 50.3% | -0.1 | 22.21% | 6/9 | 1.0000 |
| levels | wick rejection at the daily low | 58.3% | +8.0 | 0.27% | 9/9 | 0.0074 |
| levels | wick rejection at the 4h high | 42.4% | -7.9 | 1.01% | 9/9 | 0.0037 |
| levels | wick rejection at the 4h low | 57.9% | +7.7 | 0.94% | 9/9 | 0.0037 |
| levels | liquidity sweep of the 1h high (took it out, closed back below) | 44.0% | -6.3 | 2.03% | 9/9 | 0.0037 |
| levels | wick rejection at the 1h high | 44.1% | -6.2 | 2.57% | 9/9 | 0.0037 |
| levels | liquidity sweep of the 1h low (took it out, closed back above) | 56.4% | +6.1 | 2.01% | 9/9 | 0.0037 |
| levels | wick rejection at the daily high | 44.2% | -6.1 | 0.31% | 9/9 | 0.0295 |
| levels | acceptance below the 4h low (last 5 closes all below it) | 56.3% | +6.1 | 2.54% | 9/9 | 0.0037 |
| levels | acceptance above the 4h high (last 5 closes all above it) | 44.3% | -6.0 | 2.97% | 9/9 | 0.0074 |
| levels | wick rejection at the 1h low | 56.2% | +5.9 | 2.48% | 9/9 | 0.0037 |
| levels | failed breakdown below the daily low | 55.3% | +5.0 | 0.97% | 9/9 | 0.1033 |
| levels | retest from above of a 4h high broken in the last hour | 45.9% | -4.4 | 1.70% | 9/9 | 0.0332 |
| levels | range breakdown downward (prior hour under 15 bp) | 54.5% | +4.3 | 0.47% | 5/5 | 0.1587 |
| levels | failed breakout above the daily high | 46.0% | -4.3 | 1.08% | 9/9 | 0.2214 |
| levels | failed breakdown below the 4h low | 54.4% | +4.2 | 3.40% | 9/9 | 0.0074 |
| levels | failed breakout above the 4h high | 46.2% | -4.1 | 3.65% | 9/9 | 0.0037 |
| levels | reclaimed the session VWAP in the last 5 minutes after 30+ minutes below | 46.2% | -4.1 | 0.82% | 9/9 | 0.0923 |
| levels | retest from below of a 4h low broken in the last hour | 53.8% | +3.6 | 1.45% | 9/9 | 0.0590 |
| levels | lower highs (three successive 10-minute highs declining) | 53.8% | +3.5 | 29.33% | 9/9 | 0.0037 |
| levels | higher lows (three successive 10-minute lows rising) | 46.9% | -3.4 | 29.80% | 9/9 | 0.0037 |
| levels | resistance flipped to support (4h high broken, retested within 5 bp, last 3 closes above) | 46.9% | -3.3 | 0.36% | 5/5 | 1.0000 |
| levels | range breakout upward (prior hour under 15 bp) | 46.9% | -3.3 | 0.47% | 4/5 | 0.9705 |
| levels | lost the session VWAP in the last 5 minutes after 30+ minutes above | 53.4% | +3.1 | 0.84% | 9/9 | 0.1439 |
| levels | support held (4h low tested within 3 bp, no close below, price now 3+ bp above) | 53.0% | +2.7 | 2.52% | 8/9 | 0.0923 |
| levels | broke below the previous day's low in the last 5 minutes | 52.8% | +2.5 | 0.51% | 9/9 | 0.8266 |
| levels | support flipped to resistance (4h low broken, retested within 5 bp, last 3 closes below) | 52.5% | +2.4 | 0.33% | 3/4 | 1.0000 |
| levels | approaching the previous day's low from above (within 10 bp) | 52.6% | +2.3 | 0.93% | 5/9 | 0.1218 |
| levels | failed breakdown below the 1h low | 52.6% | +2.3 | 8.43% | 9/9 | 0.0037 |
| levels | failed breakout above the 1h high | 48.2% | -2.2 | 8.59% | 9/9 | 0.0037 |
| levels | broke above the previous day's high in the last 5 minutes | 48.2% | -2.1 | 0.60% | 9/9 | 0.6421 |
| levels | resistance held (4h high tested within 3 bp, no close above, price now 3+ bp below) | 48.2% | -2.1 | 2.94% | 9/9 | 0.3137 |
| levels | crossed above the daily open in the last 5 minutes | 48.2% | -2.1 | 1.80% | 8/9 | 0.1771 |
| levels | repeated rejection at the 4h high (2+ touches in 30 minutes, no close above) | 48.7% | -1.7 | 1.85% | 9/9 | 1.0000 |
| levels | repeated rejection at the 4h low (2+ touches in 30 minutes, no close below) | 52.0% | +1.7 | 1.56% | 7/9 | 0.9926 |
| levels | rejecting the downs (3+ down-minutes undone by the next minute in the last 15) | 48.7% | -1.6 | 19.51% | 9/9 | 0.0221 |
| levels | rejecting the ups (3+ up-minutes undone by the next minute in the last 15) | 51.5% | +1.2 | 19.34% | 9/9 | 0.0480 |
| levels | approaching the previous day's high from below (within 10 bp) | 49.2% | -1.1 | 1.21% | 5/9 | 1.0000 |
| levels | crossed below the daily open in the last 5 minutes | 50.9% | +0.6 | 1.80% | 6/9 | 1.0000 |
| round numbers | crossed a $1,000 level downward in the last 3 minutes | 52.8% | +2.7 | 1.76% | 9/9 | 0.1550 |
| round numbers | crossed a $100 level downward in the last 3 minutes | 52.2% | +2.0 | 14.25% | 9/9 | 0.0037 |
| round numbers | crossed a $1,000 level upward in the last 3 minutes | 48.4% | -1.7 | 1.76% | 9/9 | 0.2214 |
| round numbers | crossed a $100 level upward in the last 3 minutes | 48.6% | -1.6 | 14.25% | 9/9 | 0.0037 |
| round numbers | approaching a $100 level from below (within 10 bp, rising) | 49.0% | -1.1 | 20.08% | 9/9 | 0.0037 |
| round numbers | approaching a $1,000 level from above (within 10 bp, falling) | 49.1% | -1.0 | 1.95% | 8/9 | 0.9926 |
| round numbers | approaching a $100 level from above (within 10 bp, falling) | 51.0% | +0.9 | 19.95% | 7/9 | 0.0074 |
| round numbers | approaching a $1,000 level from below (within 10 bp, rising) | 49.7% | -0.4 | 2.09% | 6/9 | 1.0000 |
| time | 10 minutes after the US equity open (13:30 UTC) | 48.9% | -1.4 | 0.69% | 7/9 | 1.0000 |
| time | 10 minutes before funding settlement (00:00 UTC) | 49.0% | -1.3 | 0.69% | 6/9 | 0.9926 |
| time | last 5 minutes of the UTC day | 49.2% | -1.1 | 0.35% | 4/9 | 0.9926 |
| time | 10 minutes after funding settlement (16:00 UTC) | 49.3% | -1.0 | 0.70% | 7/9 | 1.0000 |
| time | first hour of the week (Monday 00:00 to 01:00 UTC) | 49.4% | -0.9 | 0.60% | 6/9 | 1.0000 |
| time | 10 minutes before funding settlement (16:00 UTC) | 51.2% | +0.9 | 0.70% | 6/9 | 1.0000 |
| time | 10 minutes after the US equity close (20:00 UTC) | 51.2% | +0.9 | 0.70% | 5/9 | 1.0000 |
| time | 10 minutes before funding settlement (08:00 UTC) | 50.9% | +0.6 | 0.69% | 6/9 | 1.0000 |
| time | first 5 minutes of the UTC day | 49.8% | -0.5 | 0.35% | 4/9 | 1.0000 |
| time | first 5 minutes of a 4-hour block | 49.9% | -0.4 | 2.08% | 6/9 | 1.0000 |
| time | 10 minutes after funding settlement (00:00 UTC) | 50.0% | -0.3 | 0.70% | 5/9 | 1.0000 |
| time | first 5 minutes of the hour | 50.1% | -0.3 | 8.33% | 7/9 | 1.0000 |
| time | 10 minutes after the London open (07:00 UTC) | 50.2% | -0.1 | 0.69% | 5/9 | 1.0000 |
| time | 10 minutes after funding settlement (08:00 UTC) | 50.3% | -0.0 | 0.69% | 5/9 | 1.0000 |
| time | last 5 minutes of the hour | 50.3% | -0.0 | 8.33% | 4/9 | 1.0000 |
| time | Saturday or Sunday | 50.3% | -0.0 | 28.60% | 4/9 | 1.0000 |
| time | last 5 minutes of a 4-hour block | 50.3% | +0.0 | 2.08% | 4/9 | 1.0000 |
| volatility | squeeze: last hour's range under 40% of the previous day's median hourly range | 50.0% | -0.2 | 1.63% | 6/9 | 1.0000 |
| volume and flow | delta divergence: new 4h high with net taker selling over the hour | 42.9% | -7.4 | 0.42% | 9/9 | 0.0074 |
| volume and flow | delta divergence: new 4h low with net taker buying over the hour | 57.7% | +7.4 | 0.27% | 8/8 | 0.0074 |
| volume and flow | volume climax at a new 1h low (hour's largest volume) | 56.4% | +6.1 | 0.72% | 9/9 | 0.0037 |
| volume and flow | volume climax at a new 1h high (hour's largest volume) | 45.4% | -5.0 | 0.66% | 9/9 | 0.0074 |
| volume and flow | taker buying above 70% of the last minute | 49.7% | -0.6 | 15.64% | 8/9 | 0.0111 |
| volume and flow | taker selling above 70% of the last minute | 50.8% | +0.5 | 16.20% | 7/9 | 0.1144 |
| volume and flow | absorption: heavy taker buying in the last 5 minutes, price did not rise | 50.2% | -0.1 | 1.86% | 5/9 | 0.5683 |
| volume and flow | absorption: heavy taker selling in the last 5 minutes, price did not fall | 50.2% | -0.1 | 1.89% | 4/9 | 0.9852 |

Null: the largest |z| across all events and horizons on rotated labels has median 3.47 and 95th percentile 5.68; the real search's largest |z| is 23.82.
