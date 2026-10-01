Multi-asset results (xgb, price + flow features), walk-forward by month, 2025-10 to 2026-08. Last column: accuracy minus the coin's own-history model on the same windows, day-block 95% interval.

| minute | setup | n | accuracy [95% CI] | AUC | log loss | vs own |
|---|---|---|---|---|---|---|
| 0 | BTC own | 23328 | 52.52% [51.92, 53.18] | 0.537 | 0.6917 | baseline |
| 0 | ETH own | 23328 | 53.48% [52.88, 54.08] | 0.545 | 0.6911 | baseline |
| 0 | SOL own | 23328 | 52.49% [51.87, 53.14] | 0.531 | 0.6930 | baseline |
| 0 | DOGE own | 23328 | 52.83% [52.14, 53.49] | 0.540 | 0.6924 | baseline |
| 0 | BTC one-feature baseline (prev-window) | 23328 | 52.21% [51.63, 52.82] | 0.519 | 0.6922 | -0.32 [-1.03, +0.38] |
| 0 | ETH one-feature baseline (prev-window) | 23328 | 52.76% [52.16, 53.33] | 0.528 | 0.6917 | -0.71 [-1.33, -0.07] |
| 0 | SOL one-feature baseline (prev-window) | 23328 | 51.99% [51.38, 52.64] | 0.520 | 0.6922 | -0.50 [-1.19, +0.18] |
| 0 | DOGE one-feature baseline (prev-window) | 23328 | 52.82% [52.18, 53.47] | 0.531 | 0.6917 | -0.01 [-0.70, +0.67] |
| 0 | BTC pooled (4 coins) | 23328 | 52.85% [52.25, 53.44] | 0.541 | 0.6908 | +0.33 [-0.25, +0.90] |
| 0 | ETH pooled (4 coins) | 23328 | 53.55% [52.99, 54.15] | 0.547 | 0.6898 | +0.08 [-0.44, +0.60] |
| 0 | SOL pooled (4 coins) | 23328 | 52.65% [52.01, 53.27] | 0.536 | 0.6920 | +0.15 [-0.46, +0.74] |
| 0 | DOGE pooled (4 coins) | 23328 | 52.85% [52.18, 53.50] | 0.540 | 0.6912 | +0.02 [-0.50, +0.56] |
| 0 | BTC own (cross-joined rows) | 23328 | 52.52% [51.92, 53.18] | 0.537 | 0.6917 | baseline |
| 0 | BTC + ETH and SOL features | 23328 | 52.31% [51.71, 52.95] | 0.536 | 0.6919 | -0.22 [-0.72, +0.25] |
| 3 | BTC own | 23328 | 66.22% [65.61, 66.86] | 0.718 | 0.6168 | baseline |
| 3 | ETH own | 23328 | 66.82% [66.21, 67.45] | 0.728 | 0.6095 | baseline |
| 3 | SOL own | 23328 | 66.26% [65.65, 66.88] | 0.726 | 0.6104 | baseline |
| 3 | DOGE own | 23328 | 66.96% [66.40, 67.50] | 0.731 | 0.6072 | baseline |
| 3 | BTC one-feature baseline (lead-z) | 23328 | 66.35% [65.73, 66.98] | 0.721 | 0.6150 | +0.13 [-0.21, +0.48] |
| 3 | ETH one-feature baseline (lead-z) | 23328 | 66.72% [66.13, 67.34] | 0.727 | 0.6093 | -0.10 [-0.45, +0.23] |
| 3 | SOL one-feature baseline (lead-z) | 23328 | 66.55% [65.98, 67.16] | 0.728 | 0.6089 | +0.28 [-0.03, +0.60] |
| 3 | DOGE one-feature baseline (lead-z) | 23328 | 66.97% [66.40, 67.53] | 0.732 | 0.6065 | +0.01 [-0.38, +0.41] |
| 3 | BTC pooled (4 coins) | 23328 | 66.32% [65.72, 66.90] | 0.720 | 0.6155 | +0.10 [-0.18, +0.38] |
| 3 | ETH pooled (4 coins) | 23328 | 67.00% [66.44, 67.59] | 0.730 | 0.6080 | +0.18 [-0.09, +0.44] |
| 3 | SOL pooled (4 coins) | 23328 | 66.56% [65.99, 67.16] | 0.730 | 0.6078 | +0.29 [+0.03, +0.57] |
| 3 | DOGE pooled (4 coins) | 23328 | 67.21% [66.65, 67.73] | 0.735 | 0.6043 | +0.24 [-0.02, +0.51] |
| 3 | BTC own (cross-joined rows) | 23328 | 66.22% [65.61, 66.86] | 0.718 | 0.6168 | baseline |
| 3 | BTC + ETH and SOL features | 23328 | 66.27% [65.68, 66.91] | 0.718 | 0.6169 | +0.05 [-0.16, +0.28] |
