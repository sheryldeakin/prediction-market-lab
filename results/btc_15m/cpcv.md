Combinatorial purged cross-validation at minute 0: 6 contiguous blocks, every pair as the test set, training rows within 25 hours of a test block dropped (the longest feature lookback). Forest, price + flow. Unlike walk-forward, some paths train on data from after the test block.

| test blocks | train rows | test rows | accuracy |
|---|---|---|---|
| (0, 1) | 21271 | 10687 | 52.38% |
| (0, 2) | 21070 | 10687 | 52.51% |
| (0, 3) | 21070 | 10687 | 53.03% |
| (0, 4) | 21070 | 10687 | 52.18% |
| (0, 5) | 21171 | 10687 | 52.59% |
| (1, 2) | 21172 | 10686 | 53.55% |
| (1, 3) | 20971 | 10686 | 53.41% |
| (1, 4) | 20971 | 10686 | 53.18% |
| (1, 5) | 21072 | 10686 | 52.98% |
| (2, 3) | 21172 | 10686 | 52.98% |
| (2, 4) | 20971 | 10686 | 52.73% |
| (2, 5) | 21072 | 10686 | 52.52% |
| (3, 4) | 21172 | 10686 | 52.92% |
| (3, 5) | 21072 | 10686 | 52.94% |
| (4, 5) | 21273 | 10686 | 52.48% |
| all 15 paths |  |  | mean 52.82%, min 52.18%, max 53.55% |
