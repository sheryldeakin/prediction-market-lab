The wide event search at minute 0 (913 candidates with at least 300 firings, 2025-10 to 2026-08) re-run 200 times on labels rotated within each month, which keeps each month's base rate and runs but breaks the link to the features. The rows compare the real search with that null distribution.

| quantity | real | null median | null 95th percentile | null maximum | share of null runs at or above real |
|---|---|---|---|---|---|
| survive the false-discovery correction | 823 | 0 | 3 | 640 | 0.0% |
| also stable month by month | 745 | 0 | 3 | 147 | 0.0% |
| largest abs(z) across candidates | 10.46 | 3.22 | 4.15 | 6.27 | 0.0% |

Adjusted for the whole search (single-step max-T over 200 null runs, valid under any dependence between candidates): 490 candidates have an adjusted p at or below 0.05 and 575 at or below 0.10. The smallest adjusted p possible with 200 runs is 0.0050. Every candidate's z and adjusted p are in search_null_candidates.csv.

September (2026-09-01 to 2026-09-30): of the 745 stable survivors, 666 fired at least 30 times and 562 kept their direction. With September's labels rotated within the month (effects gone, overlap between candidates kept) the held count has median 330 and 95th percentile 492 over 1000 draws; 0.4% of draws reach 562. If every effect had kept its backtest size, about 604 would hold (this expectation treats windows as independent, so it is approximate).
