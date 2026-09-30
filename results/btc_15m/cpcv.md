Combinatorial purged cross-validation at minute 0: 6 contiguous blocks, every pair as the test set, training rows within 4 hours of a test block dropped. Forest, price + flow. Unlike walk-forward, some paths train on data from after the test block.

| test blocks | train rows | test rows | accuracy |
|---|---|---|---|
| (0, 1) | 21355 | 10686 | 52.35% |
| (0, 2) | 21322 | 10686 | 52.77% |
| (0, 3) | 21322 | 10686 | 52.54% |
| (0, 4) | 21322 | 10686 | 52.32% |
| (0, 5) | 21339 | 10686 | 52.64% |
| (1, 2) | 21339 | 10686 | 52.95% |
| (1, 3) | 21306 | 10686 | 53.39% |
| (1, 4) | 21306 | 10686 | 53.41% |
| (1, 5) | 21323 | 10686 | 53.04% |
| (2, 3) | 21339 | 10686 | 52.78% |
| (2, 4) | 21306 | 10686 | 52.99% |
| (2, 5) | 21323 | 10686 | 52.77% |
| (3, 4) | 21339 | 10686 | 52.91% |
| (3, 5) | 21323 | 10686 | 53.26% |
| (4, 5) | 21356 | 10686 | 52.22% |
| all 15 paths |  |  | mean 52.82%, min 52.22%, max 53.41% |
