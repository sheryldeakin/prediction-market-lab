Hidden Markov models as predictors, walk-forward by month, 2025-10 to 2026-08. hmm-state: a 3-state Gaussian HMM on the minute series (return, log volume ratio, taker share) fit on the training months, filtered forward, each state's training up-rate mixed by the filtered probabilities at the last closed minute. ms-baseline: the one-feature baseline refit per state and mixed the same way. Direction label and the magnitude label (window moves at least 10 bp). Last column: accuracy minus the baseline on the same windows, day-block 95% interval, share of days better.

| minute | label | model | n | accuracy [95% CI] | AUC | log loss | vs baseline |
|---|---|---|---|---|---|---|---|
| 0 | direction | prev-window | 23328 | 52.21% [51.63, 52.82] | 0.519 | 0.6922 | baseline |
| 0 | direction | hmm-state | 23328 | 50.11% [49.45, 50.74] | 0.502 | 0.6932 | -2.10 [-2.94, -1.27], days better 37% |
| 0 | direction | ms-baseline | 23328 | 52.21% [51.63, 52.82] | 0.524 | 0.6921 | +0.00 [+0.00, +0.00], days better 50% |
| 0 | magnitude (>= 10 bp) | vol60 logistic | 23328 | 64.70% [63.40, 65.99] | 0.708 | 0.6360 | baseline |
| 0 | magnitude (>= 10 bp) | hmm-state | 23328 | 58.17% [57.00, 59.30] | 0.593 | 0.6762 | -6.53 [-7.56, -5.51], days better 18% |
| 0 | magnitude (>= 10 bp) | ms-baseline | 23328 | 57.79% [56.70, 58.86] | 0.595 | 0.6757 | -6.91 [-7.97, -5.82], days better 19% |
| 3 | direction | lead-z | 23328 | 66.35% [65.73, 66.98] | 0.721 | 0.6150 | baseline |
| 3 | direction | hmm-state | 23328 | 55.83% [55.18, 56.47] | 0.578 | 0.6849 | -10.51 [-11.24, -9.76], days better 2% |
| 3 | direction | ms-baseline | 23328 | 66.21% [65.60, 66.84] | 0.721 | 0.6148 | -0.13 [-0.36, +0.06], days better 48% |
| 3 | magnitude (>= 10 bp) | vol60 logistic | 23328 | 65.17% [63.88, 66.43] | 0.715 | 0.6320 | baseline |
| 3 | magnitude (>= 10 bp) | hmm-state | 23328 | 62.83% [61.63, 64.03] | 0.643 | 0.6585 | -2.34 [-3.19, -1.43], days better 36% |
| 3 | magnitude (>= 10 bp) | ms-baseline | 23328 | 62.82% [61.77, 63.82] | 0.651 | 0.6561 | -2.35 [-3.28, -1.41], days better 39% |

Markov-switching baseline: the baseline feature's logistic coefficient in each state per test month (states ordered by the HMM's internal index, which can change between months; 'vol' is the state's return standard deviation in standardised units and 'share' its share of training windows).

| label | month | minute | state 0 coef | state 0 share | state 0 vol | state 1 coef | state 1 share | state 1 vol | state 2 coef | state 2 share | state 2 vol |
|---|---|---|---|---|---|---|---|---|---|---|---|
| direction | 2026-01 | 0 | -0.165 | 0.380 | 0.453 | -0.304 | 0.248 | 1.623 | -0.090 | 0.371 | 0.459 |
| direction | 2026-02 | 0 | -0.148 | 0.376 | 0.438 | -0.302 | 0.251 | 1.644 | -0.173 | 0.373 | 0.434 |
| direction | 2026-03 | 0 | -0.314 | 0.254 | 1.656 | -0.149 | 0.374 | 0.428 | -0.191 | 0.372 | 0.421 |
| direction | 2026-04 | 0 | -0.138 | 0.376 | 0.441 | -0.339 | 0.250 | 1.659 | -0.133 | 0.374 | 0.433 |
| direction | 2026-05 | 0 | -0.145 | 0.381 | 0.436 | -0.324 | 0.246 | 1.670 | -0.157 | 0.373 | 0.443 |
| direction | 2026-06 | 0 | -0.150 | 0.373 | 0.436 | -0.301 | 0.241 | 1.684 | -0.143 | 0.386 | 0.428 |
| direction | 2026-07 | 0 | -0.169 | 0.386 | 0.432 | -0.299 | 0.240 | 1.681 | -0.135 | 0.374 | 0.439 |
| direction | 2026-08 | 0 | -0.165 | 0.388 | 0.431 | -0.309 | 0.237 | 1.684 | -0.123 | 0.375 | 0.438 |
| direction | 2026-01 | 3 | 1.754 | 0.354 | 0.459 | 1.619 | 0.306 | 1.622 | 1.810 | 0.340 | 0.453 |
| direction | 2026-02 | 3 | 1.572 | 0.310 | 1.644 | 1.835 | 0.344 | 0.434 | 1.749 | 0.347 | 0.438 |
| direction | 2026-03 | 3 | 1.800 | 0.343 | 0.421 | 1.542 | 0.312 | 1.656 | 1.721 | 0.344 | 0.428 |
| direction | 2026-04 | 3 | 1.704 | 0.346 | 0.441 | 1.553 | 0.304 | 1.659 | 1.805 | 0.349 | 0.433 |
| direction | 2026-05 | 3 | 1.812 | 0.354 | 0.436 | 1.574 | 0.299 | 1.670 | 1.721 | 0.347 | 0.443 |
| direction | 2026-06 | 3 | 1.581 | 0.297 | 1.684 | 1.701 | 0.348 | 0.436 | 1.799 | 0.356 | 0.428 |
| direction | 2026-07 | 3 | 1.675 | 0.349 | 0.439 | 1.600 | 0.297 | 1.681 | 1.827 | 0.354 | 0.432 |
| direction | 2026-08 | 3 | 1.618 | 0.295 | 1.684 | 1.831 | 0.354 | 0.431 | 1.655 | 0.351 | 0.438 |
