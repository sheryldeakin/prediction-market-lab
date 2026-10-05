Derivatives events for the price-action library: definitions and the coverage of the futures files held. Every cutoff is a percentile (decile) of the previous calendar year, so an event can be scored in year Y only if the files cover all of year Y-1. The events are defined and tested in models/btc_15m/library_events.py (`deriv_events`).

| series | first stamp | last stamp | files |
|---|---|---|---|
| funding rate (monthly files) | 2025-10 | 2026-08 | 11 |
| open interest and positioning metrics (daily files) | 2025-10-01 | 2026-09-29 | 364 |
| perpetual 1-minute klines (monthly files) | 2025-10 | 2026-08 | 11 |
| perpetual 1-minute klines (daily files) | 2026-09-01 | 2026-09-29 | 29 |

| event |
|---|
| funding rate in the top decile of the previous year |
| funding rate in the bottom decile of the previous year |
| open interest up over 15 minutes (top decile) |
| open interest down over 15 minutes (bottom decile) |
| open interest up over 60 minutes (top decile) |
| open interest down over 60 minutes (bottom decile) |
| long liquidation signature (open interest down, price down hard, perp volume heavy) |
| short liquidation signature (open interest down, price up hard, perp volume heavy) |

The files cover 335 days in total and no calendar year in full, so no event has a previous year to take its cutoffs from and none is scored.
