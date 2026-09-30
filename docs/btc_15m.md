# BTC 15-minute direction: full report

Everything the model was tested on, in the order it was done. Every table is generated into `results/btc_15m/` and spliced here by `scripts/update_readme.py`; the prose is written against those tables and checked before each commit. Bugs found on the way, and the decisions behind each study, are in [process.md](process.md).

## The problem

Predicts whether Bitcoin closes a 15-minute window (aligned to the quarter hour) at or above where it opened. Data is free public 1-minute candles from Binance, including the taker-buy volume that gives a per-minute measure of order flow.

The question is asked at several points inside the window: at the open (minute 0, nothing of the window seen yet) and 1, 3, 5 and 8 minutes in. Later entries are easier because the current lead over the open is known, so every model is compared with a logistic regression that sees only that lead. A model that cannot beat the lead-only baseline has found nothing the current price does not already say.

Evaluation is walk-forward by calendar month: each test month is predicted by a model trained only on earlier months. The first three months are training only.

## Models compared

| name | what it is | features |
|---|---|---|
| majority | predicts the more common class in the training data | none |
| lead-only | logistic regression | current lead over the open (minutes 1+) |
| logistic-all | logistic regression, standardised inputs | all 24 |
| forest | random forest, 300 trees, leaves of 50+ windows, 4 threads | all 24 |
| hgb-all | histogram gradient boosting (scikit-learn) | all 24 |
| xgb-price | XGBoost, depth 3 (GPU when available) | 15 price features |
| xgb-all | XGBoost, depth 3 | 15 price + 9 order-flow features |

Price features: lead over the open, returns over the prior 5/15/60/240 minutes, the last four windows' returns, realised volatility at three horizons, position in the 4-hour range, hour and weekday. Order-flow features: taker-buy share of volume over 1/3/5/15/60 minutes, volume and trade-count ratios to the 24-hour average, mean trade size ratio.

## Main results

<!-- table:walk_forward:start -->
Walk-forward results, 2025-10 to 2026-08, test months after the first three.

| minute | model | n test | accuracy | AUC | log loss |
|---|---|---|---|---|---|
| 0 | majority | 23,327 | 50.14% | 0.494 | 0.6932 |
| 0 | logistic-all | 23,327 | 52.79% | 0.542 | 0.6906 |
| 0 | forest | 23,327 | 52.98% | 0.540 | 0.6909 |
| 0 | hgb-all | 23,327 | 52.94% | 0.539 | 0.6911 |
| 0 | xgb-price | 23,327 | 52.28% | 0.534 | 0.6924 |
| 0 | xgb-all | 23,327 | 52.54% | 0.536 | 0.6920 |
| 0 | xgb-all, label from 1 min in | 23,327 | 51.89% | 0.525 | 0.6936 |
| 1 | majority | 23,327 | 50.14% | 0.494 | 0.6932 |
| 1 | lead-only | 23,327 | 58.91% | 0.623 | 0.6727 |
| 1 | logistic-all | 23,327 | 59.19% | 0.627 | 0.6692 |
| 1 | forest | 23,327 | 59.09% | 0.629 | 0.6666 |
| 1 | hgb-all | 23,327 | 59.39% | 0.627 | 0.6678 |
| 1 | xgb-price | 23,327 | 59.15% | 0.629 | 0.6671 |
| 1 | xgb-all | 23,327 | 59.09% | 0.628 | 0.6674 |
| 3 | majority | 23,327 | 50.14% | 0.494 | 0.6932 |
| 3 | lead-only | 23,327 | 66.32% | 0.713 | 0.6304 |
| 3 | logistic-all | 23,327 | 65.69% | 0.712 | 0.6253 |
| 3 | forest | 23,327 | 66.20% | 0.719 | 0.6161 |
| 3 | hgb-all | 23,327 | 66.36% | 0.719 | 0.6165 |
| 3 | xgb-price | 23,327 | 66.22% | 0.718 | 0.6170 |
| 3 | xgb-all | 23,327 | 66.17% | 0.718 | 0.6172 |
| 5 | majority | 23,327 | 50.14% | 0.494 | 0.6932 |
| 5 | lead-only | 23,327 | 70.00% | 0.762 | 0.5916 |
| 5 | logistic-all | 23,327 | 69.14% | 0.761 | 0.5863 |
| 5 | forest | 23,327 | 70.15% | 0.774 | 0.5682 |
| 5 | hgb-all | 23,327 | 69.88% | 0.772 | 0.5713 |
| 5 | xgb-price | 23,327 | 69.90% | 0.773 | 0.5702 |
| 5 | xgb-all | 23,327 | 69.96% | 0.772 | 0.5707 |
| 8 | majority | 23,327 | 50.14% | 0.494 | 0.6932 |
| 8 | lead-only | 23,327 | 77.40% | 0.846 | 0.5009 |
| 8 | logistic-all | 23,327 | 76.85% | 0.845 | 0.4976 |
| 8 | forest | 23,327 | 77.48% | 0.856 | 0.4723 |
| 8 | hgb-all | 23,327 | 77.41% | 0.855 | 0.4742 |
| 8 | xgb-price | 23,327 | 77.32% | 0.856 | 0.4722 |
| 8 | xgb-all | 23,327 | 77.36% | 0.855 | 0.4733 |
<!-- table:walk_forward:end -->

![accuracy by entry minute](../results/btc_15m/by_minute.png)

![accuracy at the open by test month](../results/btc_15m/monthly_k0.png)

![calibration at the open](../results/btc_15m/calibration_k0.png)

What the tables and charts say:

- At the open there is a small, repeatable signal in the backtest: about 53% against a 50.1% majority baseline, above 50% in every one of the eight test months. The 95% day-block bootstrap interval on the best model's gain over majority is +2.0 to +3.7 points, and a within-day label permutation test gives p = 0.002 (`results/btc_15m/checks.md`).
- The signal is simple. Logistic regression on the same features does as well as the tree models, so it is not an interaction the linear model misses.
- Part of it comes from the shared boundary price between back-to-back windows. Measuring the label from one minute after the open, which removes the shared price, leaves 51.9%.
- Once the window is under way, the current lead explains almost all of the accuracy. No model beats the lead-only baseline by more than half a point, and most intervals on the difference include zero. The tree models improve the probabilities (lower log loss, from accounting for volatility) but not the direction calls.
- Minute-level order flow adds about a quarter of a point at the open and nothing later.
- Predicted probabilities at the open are calibrated across deciles (chart above), so 0.55 means about 55%.

## Forward log

The backtest above can be re-run and tuned; the forward log cannot. `models/btc_15m/log.py` freezes models trained through a cutoff month and scores every later window as Binance publishes its daily files, appending each window once to `results/btc_15m/predictions.csv`.

![forward log](../results/btc_15m/forward_log.png)

<!-- forward:start -->
Trained through 2026-08, scored on 2026-09-01 to 2026-09-29.

| minute | model | windows | accuracy |
|---|---|---|---|
| 0 | forest | 2,783 | 50.41% |
| 3 | xgb-all | 2,783 | 66.69% |
<!-- forward:end -->

So far the open-of-window signal has not shown up in the forward period: 50.4% on September's 2,783 windows, against 53% in the backtest. One month is too little to call it dead (the backtest's worst month for that model was 51.6%), but it is the number to watch, and it is the reason the log exists. The minute-3 model is where the backtest said it would be.

## Checks the numbers pass

- **No lookahead.** Features are pure functions of past candles. `tests/test_features.py` multiplies every candle from the entry minute onward by three and asserts the features do not change, at five different entry minutes.
- **Day-clustered uncertainty.** Windows in one day share conditions, so every interval resamples whole days and the permutation test shuffles labels within days. `tests/test_stats.py` checks that the bootstrap widens correctly when a day's windows are identical, and that a model which only knows each day's drift gets no credit.
- **Baselines at the same moment.** Every model is reported next to the strongest simple predictor available at that minute.
- **Shared-boundary check.** The label is re-measured from one minute in to see how much of the open-of-window signal is boundary noise.
- **Numbers come from scripts.** The tables in this file are spliced from `results/` by `scripts/update_readme.py`; the charts are drawn from the same CSVs.

## Follow-up experiments

Six follow-ups, each with the reason it was worth running and what it found. Tables are generated into `results/btc_15m/` and spliced here.

**1. Feature sets, including an indicator bank and tick-level order flow.** Classic indicators (RSI, MACD, Bollinger %b, ATR, EMA cross, stochastic, OBV slope, VWAP deviation, ADX) are deterministic transforms of the same prices, so the expectation was little gain. Tick-level flow (Binance aggregated trades reduced to one-second bins: signed volume imbalance over the 5 to 300 seconds before the entry, large-trade share, trade-rate ratio) is the one input the minute candles cannot express; published work on Binance futures reports that order imbalance at quarter-hour openings carries information over hours, so the question was whether any of it shows at 15 minutes.

<!-- table:ablation:start -->
Feature-set ablation, walk-forward by month. Last column: accuracy minus the price-only forest on the same windows, day-block 95% interval.

| minute | features | model | n | accuracy | AUC | log loss | vs price-only forest |
|---|---|---|---|---|---|---|---|
| 0 | price | forest | 23327 | 52.72% | 0.536 | 0.6917 | +0.00 [+0.00, +0.00] |
| 0 | price | xgb | 23327 | 52.28% | 0.534 | 0.6924 | -0.44 [-0.93, +0.06] |
| 0 | price + flow | forest | 23327 | 52.98% | 0.540 | 0.6909 | +0.26 [-0.30, +0.87] |
| 0 | price + flow | xgb | 23327 | 52.54% | 0.536 | 0.6920 | -0.18 [-0.80, +0.41] |
| 0 | price + flow + indicators | forest | 23327 | 53.40% | 0.546 | 0.6900 | +0.68 [+0.14, +1.25] |
| 0 | price + flow + indicators | xgb | 23327 | 53.29% | 0.544 | 0.6908 | +0.57 [-0.05, +1.20] |
| 0 | price + flow + tick flow | forest | 23327 | 53.01% | 0.544 | 0.6902 | +0.29 [-0.31, +0.93] |
| 0 | price + flow + tick flow | xgb | 23327 | 52.92% | 0.540 | 0.6915 | +0.20 [-0.43, +0.84] |
| 0 | everything | forest | 23327 | 53.18% | 0.546 | 0.6900 | +0.46 [-0.19, +1.15] |
| 0 | everything | xgb | 23327 | 53.19% | 0.545 | 0.6908 | +0.47 [-0.17, +1.10] |
| 3 | price | forest | 23327 | 66.00% | 0.719 | 0.6166 | +0.00 [+0.00, +0.00] |
| 3 | price | xgb | 23327 | 66.22% | 0.718 | 0.6170 | +0.22 [-0.07, +0.50] |
| 3 | price + flow | forest | 23327 | 66.20% | 0.719 | 0.6161 | +0.20 [-0.04, +0.45] |
| 3 | price + flow | xgb | 23327 | 66.17% | 0.718 | 0.6172 | +0.18 [-0.13, +0.48] |
| 3 | price + flow + indicators | forest | 23327 | 66.15% | 0.720 | 0.6156 | +0.15 [-0.11, +0.41] |
| 3 | price + flow + indicators | xgb | 23327 | 66.34% | 0.720 | 0.6157 | +0.35 [+0.03, +0.68] |
| 3 | price + flow + tick flow | forest | 23327 | 66.29% | 0.720 | 0.6160 | +0.29 [+0.03, +0.54] |
| 3 | price + flow + tick flow | xgb | 23327 | 66.32% | 0.719 | 0.6168 | +0.33 [+0.02, +0.63] |
| 3 | everything | forest | 23327 | 66.29% | 0.720 | 0.6155 | +0.29 [+0.05, +0.54] |
| 3 | everything | xgb | 23327 | 66.32% | 0.720 | 0.6159 | +0.33 [+0.03, +0.63] |
<!-- table:ablation:end -->

At the open, the indicator bank is the only addition whose interval excludes zero (+0.68 points for the forest), and it is one of ten comparisons in the table, so it should be read as "worth keeping", not as a discovery. Tick-level flow adds +0.29 at the open with an interval that includes zero: the imbalance in the seconds before a quarter-hour open does not predict the next 15 minutes here. Three minutes in, every addition is worth about +0.3 points, which is real but small.

**2. A sequence model on the raw minute series.** A GRU over the last 120 minutes of returns, volume ratios and taker-buy share, with the lead and hour as side inputs, trained walk-forward with early stopping (runs on the GPU when one is present).

<!-- table:sequence:start -->
GRU over the last 120 minutes (return, volume ratio, taker-buy share) plus lead and hour, walk-forward by month, early stopping on the last 10% of training months.

| minute | model | n | accuracy [95% CI] | AUC | log loss | vs baseline |
|---|---|---|---|---|---|---|
| 0 | gru-sequence | 23327 | 51.16% [50.57, 51.76] | 0.520 | 0.6924 | +0.84 [+0.09, +1.61] vs majority |
| 3 | gru-sequence | 23327 | 65.89% [65.28, 66.54] | 0.715 | 0.6203 | -0.43 [-0.76, -0.10] vs lead-only |
<!-- table:sequence:end -->

It underperforms the hand-built features at the open (51.2% vs 53.0%) and loses to the lead-only logistic model three minutes in. With 23,000 training windows the sequence model does not find anything the features miss.

**3. A magnitude label.** Instead of up or down: does the window move at least 10 basis points from its open in either direction? That is the question that decides whether a window is worth acting on at all. The baseline is logistic regression on the trailing 60-minute volatility alone.

<!-- table:magnitude:start -->
Magnitude label: the window moves at least 10 basis points from its open, in either direction.

| minute | model | n | share of windows that move | accuracy [95% CI] | AUC | log loss |
|---|---|---|---|---|---|---|
| 0 | vol60 only | 23327 | 50.7% | 64.70% [63.39, 65.99] | 0.708 | 0.6361 |
| 0 | all features | 23327 | 50.7% | 65.35% [64.08, 66.57] | 0.715 | 0.6167 |
| 3 | vol60 only | 23327 | 50.7% | 65.17% [63.87, 66.43] | 0.715 | 0.6320 |
| 3 | all features | 23327 | 50.7% | 67.27% [66.10, 68.42] | 0.741 | 0.5970 |
<!-- table:magnitude:end -->

Magnitude is far more predictable than direction (65% at the open against a 50.7% base rate), and most of it is volatility clustering: the volatility-only baseline gets 64.7%.

**4. Where the direction signal lives.** Accuracy at the open by session, volatility tercile and 4-hour trend tercile.

<!-- table:regime:start -->
Accuracy at the open (forest, price + flow) by regime, walk-forward predictions. Volatility is the trailing 60-minute realised volatility; trend is the absolute 4-hour return.

| split | group | windows | accuracy [95% CI] |
|---|---|---|---|
| session | Asia 00-07 | 7776 | 53.36% [52.25, 54.57] |
| session | Europe 08-13 | 5832 | 52.30% [51.01, 53.72] |
| session | US 14-21 | 7776 | 53.14% [52.07, 54.26] |
| session | late 22-23 | 1943 | 52.86% [50.82, 54.97] |
| volatility | low | 7776 | 52.83% [51.78, 53.89] |
| volatility | mid | 7775 | 53.25% [52.14, 54.28] |
| volatility | high | 7776 | 52.85% [51.75, 54.00] |
| trend | flat | 7776 | 52.25% [51.27, 53.34] |
| trend | mid | 7775 | 52.59% [51.44, 53.78] |
| trend | strong | 7776 | 54.09% [53.09, 55.12] |
<!-- table:regime:end -->

The signal is spread evenly. The only group that stands out is windows following a strong 4-hour move (54.1%), and the intervals of the three trend groups overlap.

**5. Combinatorial purged cross-validation as a second estimate.** Six contiguous blocks, every pair as the test set (15 paths), training rows within four hours of a test block dropped. Unlike walk-forward, some paths train on data from after the test block, so agreement between the two is a check that the walk-forward estimate is not an artefact of the particular month order.

<!-- table:cpcv:start -->
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
<!-- table:cpcv:end -->

The 15 paths give 52.2% to 53.4% with a mean of 52.8%, in line with the walk-forward 53.0%.

**6. A cost-aware score.** Expected value per traded window in cents on a $1 binary contract, buying the favoured side at 0.5 plus half a 1-cent spread and paying a 1.75-cent fee, trading only when the model's probability is far enough from 0.5.

<!-- table:cost:start -->
Expected value per traded window, cents per $1 contract, buying the favoured side at 0.5 + half a 1c spread and paying a 1.75c fee. Forest, price + flow features, walk-forward. Note: after the open a real market would not be priced at 0.5, so only the minute-0 rows describe a real trade.

| minute | trade when probability | windows | share traded | accuracy | EV cents [95% CI] |
|---|---|---|---|---|---|
| 0 | >= 0.50 or <= 0.50 | 23327 | 100% | 52.98% | +0.73 [+0.11, +1.39] |
| 0 | >= 0.53 or <= 0.47 | 12605 | 54% | 54.09% | +1.84 [+0.99, +2.74] |
| 0 | >= 0.55 or <= 0.45 | 7283 | 31% | 55.06% | +2.81 [+1.65, +4.02] |
| 0 | >= 0.58 or <= 0.42 | 2687 | 12% | 58.02% | +5.77 [+4.00, +7.49] |
| 3 | >= 0.50 or <= 0.50 | 23327 | 100% | 66.20% | +13.95 [+13.33, +14.59] |
| 3 | >= 0.53 or <= 0.47 | 21139 | 91% | 67.63% | +15.38 [+14.77, +16.00] |
| 3 | >= 0.55 or <= 0.45 | 19618 | 84% | 68.78% | +16.53 [+15.89, +17.18] |
| 3 | >= 0.58 or <= 0.42 | 17326 | 74% | 70.35% | +18.10 [+17.43, +18.77] |
<!-- table:cost:end -->

In the backtest, trading every window at the open is worth +0.7 cents, and the most confident 12% of windows +5.8 cents. The forward log above is the reason to distrust these numbers until more months are in: September scored 50.4%, which at these costs is a loss. After the open the rows describe a contract that a real market would not price at 0.5, so they are upper bounds, not trades.

## Going deeper

Four more studies, chosen because they are the questions a careful reader asks next. Each uses the same walk-forward harness, day-clustered intervals and README splice.

**7. Four coins, and what one coin says about another.** The features are scale-free (basis points, ratios, shares), so the same pipeline runs on ETH, SOL and DOGE, and their earlier months can be pooled to train one model that is tested on each coin. A second question is cross-asset lead-lag: does ETH's or SOL's last few minutes say anything about BTC's next window?

<!-- table:multi_asset:start -->
Multi-asset results (xgb, price + flow features), walk-forward by month, 2025-10 to 2026-08. Last column: accuracy minus the coin's own-history model on the same windows, day-block 95% interval.

| minute | setup | n | accuracy [95% CI] | AUC | log loss | vs own |
|---|---|---|---|---|---|---|
| 0 | BTC own | 23327 | 52.36% [51.77, 52.97] | 0.537 | 0.6918 | baseline |
| 0 | ETH own | 23327 | 53.47% [52.85, 54.08] | 0.545 | 0.6912 | baseline |
| 0 | SOL own | 23327 | 52.54% [51.94, 53.17] | 0.532 | 0.6931 | baseline |
| 0 | DOGE own | 23327 | 53.02% [52.34, 53.65] | 0.541 | 0.6921 | baseline |
| 0 | BTC pooled (4 coins) | 23327 | 52.72% [52.08, 53.34] | 0.540 | 0.6911 | +0.36 [-0.23, +0.90] |
| 0 | ETH pooled (4 coins) | 23327 | 53.85% [53.25, 54.49] | 0.549 | 0.6896 | +0.38 [-0.18, +0.96] |
| 0 | SOL pooled (4 coins) | 23327 | 52.71% [52.10, 53.36] | 0.535 | 0.6920 | +0.17 [-0.39, +0.71] |
| 0 | DOGE pooled (4 coins) | 23327 | 53.08% [52.42, 53.72] | 0.541 | 0.6910 | +0.06 [-0.48, +0.58] |
| 0 | BTC own (cross-joined rows) | 23327 | 52.36% [51.77, 52.97] | 0.537 | 0.6918 | baseline |
| 0 | BTC + ETH and SOL features | 23327 | 52.09% [51.47, 52.74] | 0.534 | 0.6924 | -0.27 [-0.72, +0.20] |
| 3 | BTC own | 23327 | 66.22% [65.61, 66.85] | 0.719 | 0.6169 | baseline |
| 3 | ETH own | 23327 | 66.84% [66.24, 67.44] | 0.728 | 0.6097 | baseline |
| 3 | SOL own | 23327 | 66.36% [65.75, 66.98] | 0.726 | 0.6103 | baseline |
| 3 | DOGE own | 23327 | 67.15% [66.57, 67.71] | 0.731 | 0.6071 | baseline |
| 3 | BTC pooled (4 coins) | 23327 | 66.34% [65.72, 66.93] | 0.720 | 0.6156 | +0.11 [-0.17, +0.39] |
| 3 | ETH pooled (4 coins) | 23327 | 67.05% [66.49, 67.64] | 0.730 | 0.6081 | +0.21 [-0.06, +0.47] |
| 3 | SOL pooled (4 coins) | 23327 | 66.51% [65.90, 67.13] | 0.729 | 0.6080 | +0.15 [-0.13, +0.42] |
| 3 | DOGE pooled (4 coins) | 23327 | 67.21% [66.64, 67.73] | 0.735 | 0.6043 | +0.06 [-0.23, +0.33] |
| 3 | BTC own (cross-joined rows) | 23327 | 66.22% [65.61, 66.85] | 0.719 | 0.6169 | baseline |
| 3 | BTC + ETH and SOL features | 23327 | 66.22% [65.64, 66.83] | 0.718 | 0.6174 | -0.01 [-0.24, +0.22] |
<!-- table:multi_asset:end -->

All four coins show the same small signal at the open (52.4% to 53.5%) and the same lead-driven accuracy three minutes in. Pooling four coins' history adds +0.1 to +0.4 points, with every interval including zero: four times the data does not find more than the same simple effect. ETH's and SOL's last minutes add nothing to BTC (-0.27 at the open, 0.00 at minute 3). This table is also where a caching bug was caught: a first run showed four identical rows because the feature cache was keyed on the time span alone, which the coins share; the key now includes the price content and a test covers it.

**8. Hyperparameter search, honest and dishonest.** For each test month, Optuna picks XGBoost parameters two ways: validated on the month before the test month (honest), and validated on the test month itself, which is what happens when a notebook tunes and reports on the same split. The gap between the two rows is the optimism to subtract from any tuned result that does not name its validation split.

<!-- table:tuning:start -->
XGBoost with default parameters vs Optuna search (30 trials per month) validated honestly (on the month before the test month) and validated on the test month itself. Walk-forward, price + flow + indicator features. Last column: accuracy minus default on the same windows, day-block 95% interval.

| minute | variant | n | accuracy [95% CI] | AUC | log loss | vs default |
|---|---|---|---|---|---|---|
| 0 | default | 23327 | 52.96% [52.36, 53.58] | 0.542 | 0.6913 | baseline |
| 0 | tuned-honest | 23327 | 53.41% [52.82, 54.03] | 0.547 | 0.6898 | +0.45 [+0.00, +0.87] |
| 0 | tuned-on-test | 23327 | 53.45% [52.85, 54.09] | 0.550 | 0.6890 | +0.49 [+0.03, +0.94] |
| 3 | default | 23327 | 66.34% [65.71, 66.96] | 0.720 | 0.6162 | baseline |
| 3 | tuned-honest | 23327 | 66.21% [65.59, 66.84] | 0.720 | 0.6158 | -0.13 [-0.35, +0.09] |
| 3 | tuned-on-test | 23327 | 66.29% [65.67, 66.89] | 0.722 | 0.6148 | -0.05 [-0.27, +0.17] |
<!-- table:tuning:end -->

Honest tuning adds +0.45 points at the open (interval touching zero) and nothing at minute 3. The leaky variant is only +0.04 above honest here, which is itself informative: with 30 trials over a small space and a weak signal there is little room to overfit the test month. The gap grows with the number of trials and the flexibility of the space, which is the usual setting of a tuned notebook.

**9. How much history, and how often to retrain.** Training on only the last few months beats training on everything when the relationship drifts. The second table keeps one model without retraining and reports accuracy by months since it was fit.

<!-- table:drift:start -->
Training window: for each test month, train on the last W months only or on every earlier month. XGBoost, price + flow + indicators, walk-forward. Last column: accuracy minus expanding on the same windows, day-block 95% interval.

| minute | training window | n | accuracy [95% CI] | log loss | vs expanding |
|---|---|---|---|---|---|
| 0 | last 2 months | 23327 | 52.98% [52.35, 53.63] | 0.6945 | +0.02 [-0.63, +0.65] |
| 0 | last 3 months | 23327 | 52.99% [52.40, 53.62] | 0.6932 | +0.03 [-0.56, +0.61] |
| 0 | last 4 months | 23327 | 52.97% [52.38, 53.59] | 0.6920 | +0.01 [-0.49, +0.50] |
| 0 | last 6 months | 23327 | 52.91% [52.36, 53.52] | 0.6915 | -0.05 [-0.40, +0.30] |
| 0 | expanding | 23327 | 52.96% [52.36, 53.58] | 0.6913 | baseline |
| 3 | last 2 months | 23327 | 66.18% [65.57, 66.83] | 0.6208 | -0.16 [-0.45, +0.16] |
| 3 | last 3 months | 23327 | 66.11% [65.50, 66.79] | 0.6189 | -0.23 [-0.50, +0.06] |
| 3 | last 4 months | 23327 | 66.35% [65.74, 67.00] | 0.6172 | +0.01 [-0.24, +0.29] |
| 3 | last 6 months | 23327 | 66.37% [65.75, 67.00] | 0.6165 | +0.03 [-0.12, +0.18] |
| 3 | expanding | 23327 | 66.34% [65.71, 66.96] | 0.6162 | baseline |

Retrain frequency: a model trained at the start of a month and kept without retraining. Accuracy by months since the last retrain, pooled over all start months (later ages have fewer start months).

| minute | months since retrain | start months | n | accuracy [95% CI] |
|---|---|---|---|---|
| 0 | 0 | 8 | 23327 | 52.96% [52.36, 53.58] |
| 0 | 1 | 7 | 20351 | 53.07% [52.42, 53.79] |
| 0 | 2 | 6 | 17663 | 52.71% [52.02, 53.38] |
| 0 | 3 | 5 | 14687 | 52.94% [52.16, 53.71] |
| 3 | 0 | 8 | 23327 | 66.34% [65.71, 66.96] |
| 3 | 1 | 7 | 20351 | 66.23% [65.59, 66.87] |
| 3 | 2 | 6 | 17663 | 66.29% [65.59, 66.93] |
| 3 | 3 | 5 | 14687 | 66.83% [66.09, 67.56] |
<!-- table:drift:end -->

Training on the last two to six months does no better or worse than training on everything, and a model kept for three months without retraining is as accurate as a fresh one. Whatever the open-of-window signal is, it is not drifting within this year, which makes the September forward result (50.4%) harder to explain as staleness.

**10. Triple-barrier labels and meta-labelling.** Instead of "close above open", a window is labelled by which barrier the price touches first inside its remaining minutes: an upper barrier, a lower one, or the time limit. At entry minute k the barriers are measured from the entry price over the remaining minutes only; measuring them from the open lets a barrier touched in minutes the model has already seen decide the label, which produced a false 74% at minute 3 before a test caught it. Meta-labelling trains a second model to predict whether the first model's direction call will be right, using only first-model predictions that were made out of sample, and uses it to decide when to act.

<!-- table:meta:start -->
Triple-barrier labels: which comes first in the 15 minutes, the upper barrier, the lower barrier, or the time limit (then the sign of the final move). XGBoost, price + flow + indicators, walk-forward.

| minute | label | how windows resolved | share up | accuracy [95% CI] | AUC |
|---|---|---|---|---|---|
| 0 | close >= open (plain) |  | 49.7% | 52.96% [52.36, 53.58] | 0.542 |
| 0 | fixed 10 bp barriers | upper 37%, lower 38%, time 25% | 49.3% | 52.98% [52.31, 53.60] | 0.540 |
| 0 | 1.0 x volatility barriers | upper 22%, lower 22%, time 56% | 49.5% | 52.72% [52.11, 53.35] | 0.538 |
| 0 | 2.0 x volatility barriers | upper 5%, lower 5%, time 90% | 49.7% | 52.87% [52.30, 53.49] | 0.542 |
| 3 | close >= open (plain) |  | 49.7% | 66.34% [65.71, 66.96] | 0.720 |
| 3 | fixed 10 bp barriers | upper 34%, lower 34%, time 33% | 50.0% | 50.84% [50.27, 51.39] | 0.512 |
| 3 | 1.0 x volatility barriers | upper 21%, lower 21%, time 58% | 50.1% | 51.10% [50.47, 51.73] | 0.517 |
| 3 | 2.0 x volatility barriers | upper 5%, lower 5%, time 91% | 50.1% | 51.01% [50.38, 51.62] | 0.517 |

Meta-labelling: a second model predicts whether the primary direction call is right, trained only on out-of-sample primary predictions from earlier months. EV in cents per $1 contract at a 1c spread and 1.75c fee, priced at 0.5 (only meaningful at minute 0). The AUC is the secondary model's ability to rank right calls above wrong ones.

| minute | rule | windows | share acted on | accuracy of primary [95% CI] | EV cents [95% CI] | meta AUC |
|---|---|---|---|---|---|---|
| 0 | act always | 20351 | 100% | 52.83% [52.22, 53.46] | +0.58 [-0.03, +1.21] | 0.513 |
| 0 | act when meta >= 0.5 | 14919 | 73% | 53.21% [52.50, 53.92] | +0.96 [+0.25, +1.67] |  |
| 0 | act when meta >= 0.55 | 6997 | 34% | 54.01% [52.92, 55.16] | +1.76 [+0.67, +2.91] |  |
| 0 | act when meta >= 0.6 | 2340 | 11% | 55.34% [53.35, 57.52] | +3.09 [+1.10, +5.27] |  |
| 3 | act always | 20351 | 100% | 66.38% [65.74, 67.06] | +14.13 [+13.49, +14.81] | 0.614 |
| 3 | act when meta >= 0.5 | 19159 | 94% | 66.98% [66.31, 67.67] | +14.73 [+14.06, +15.42] |  |
| 3 | act when meta >= 0.55 | 16420 | 81% | 68.98% [68.27, 69.69] | +16.73 [+16.02, +17.44] |  |
| 3 | act when meta >= 0.6 | 13002 | 64% | 71.64% [70.88, 72.40] | +19.39 [+18.63, +20.15] |  |
<!-- table:meta:end -->

At the open, the barrier labels behave like the plain label (52.7% to 53.0%). Three minutes in, predicting which barrier the remaining path touches first from the entry price is a coin flip (50.8% to 51.1%): the 66% accuracy of the plain label at minute 3 is entirely the lead already in hand, and the direction of the rest of the window is not predictable. The meta model ranks right calls above wrong ones with an AUC of 0.51 at the open and 0.61 at minute 3. Acting only when it is confident raises the primary's accuracy at the open from 52.8% to 55.3% on the 11% of windows it selects, at the cost of skipping the rest; this is the sizing rule the cost table lacked, and it carries the same forward-log caveat.

**11. Ensembles and stacking.** The four base models' out-of-fold probabilities averaged, and a logistic stacker fit on earlier months' out-of-fold probabilities only (so it never sees a base prediction that was fit on the month it scores).

<!-- table:ensemble:start -->
Ensembles: the mean of four base models' out-of-fold probabilities, and a logistic stacker fit on earlier months' out-of-fold probabilities only. Scored on the months where every variant exists (the stacker needs one month of base predictions to start). Last column: accuracy minus the best single base model on the same windows, day-block 95% interval.

| minute | model | n | accuracy [95% CI] | AUC | log loss | vs best single |
|---|---|---|---|---|---|---|
| 0 | logistic-all | 20351 | 52.88% [52.18, 53.59] | 0.544 | 0.6905 | -0.37 [-1.02, +0.25] vs forest |
| 0 | forest | 20351 | 53.26% [52.62, 53.91] | 0.543 | 0.6906 | best single |
| 0 | hgb-all | 20351 | 52.91% [52.25, 53.57] | 0.540 | 0.6904 | -0.34 [-0.89, +0.18] vs forest |
| 0 | xgb-all | 20351 | 52.83% [52.22, 53.46] | 0.541 | 0.6914 | -0.43 [-0.93, +0.08] vs forest |
| 0 | average | 20351 | 53.26% [52.61, 53.93] | 0.545 | 0.6899 | +0.00 [-0.45, +0.45] vs forest |
| 0 | stacking | 20351 | 53.16% [52.53, 53.81] | 0.543 | 0.6902 | -0.09 [-0.51, +0.29] vs forest |
| 3 | logistic-all | 20351 | 65.74% [65.11, 66.38] | 0.715 | 0.6208 | -0.65 [-1.05, -0.23] vs xgb-all |
| 3 | forest | 20351 | 66.19% [65.54, 66.89] | 0.720 | 0.6155 | -0.20 [-0.46, +0.10] vs xgb-all |
| 3 | hgb-all | 20351 | 66.23% [65.61, 66.87] | 0.720 | 0.6157 | -0.16 [-0.41, +0.09] vs xgb-all |
| 3 | xgb-all | 20351 | 66.38% [65.74, 67.06] | 0.720 | 0.6158 | best single |
| 3 | average | 20351 | 66.32% [65.67, 67.00] | 0.722 | 0.6143 | -0.06 [-0.29, +0.17] vs xgb-all |
| 3 | stacking | 20351 | 66.14% [65.49, 66.82] | 0.721 | 0.6146 | -0.24 [-0.52, +0.06] vs xgb-all |
<!-- table:ensemble:end -->

Neither helps. The average matches the best single model at the open (+0.00) and the stacker is slightly behind at both entry points, with every interval including zero. The four base models make the same calls on the same windows; there is nothing to combine.

**12. Calibration.** Are the probabilities honest numbers? Platt and isotonic recalibration fit on earlier months' out-of-fold probabilities, the Brier score split into reliability (calibration error) and resolution (information), and the expected calibration error month by month.

<!-- table:calibration:start -->
Calibration of the XGBoost probabilities (price + flow + indicators), walk-forward. Platt and isotonic recalibration are fit on earlier months' out-of-fold probabilities only. Brier = reliability - resolution + uncertainty; lower reliability is better calibration, higher resolution is more information. ECE is the expected calibration error over ten bins.

| minute | probabilities | n | Brier | reliability | resolution | ECE |
|---|---|---|---|---|---|---|
| 0 | raw | 20351 | 0.2491 | 0.00042 | 0.00103 | 1.55% |
| 0 | platt | 20351 | 0.2488 | 0.00001 | 0.00072 | 0.16% |
| 0 | isotonic | 20351 | 0.2491 | 0.00024 | 0.00073 | 0.56% |
| 3 | raw | 20351 | 0.2135 | 0.00015 | 0.03568 | 0.92% |
| 3 | platt | 20351 | 0.2136 | 0.00019 | 0.03566 | 1.20% |
| 3 | isotonic | 20351 | 0.2139 | 0.00022 | 0.03557 | 1.21% |

Reliability by month (raw probabilities): ECE, mean predicted, observed rate of up.

| minute | month | n | ECE | mean predicted | observed |
|---|---|---|---|---|---|
| 0 | 2026-01 | 2976 | 1.64% | 50.0% | 49.3% |
| 0 | 2026-02 | 2688 | 2.55% | 49.5% | 50.4% |
| 0 | 2026-03 | 2976 | 2.17% | 50.3% | 49.9% |
| 0 | 2026-04 | 2880 | 1.29% | 49.7% | 51.0% |
| 0 | 2026-05 | 2976 | 1.98% | 50.0% | 49.3% |
| 0 | 2026-06 | 2880 | 2.90% | 50.0% | 47.6% |
| 0 | 2026-07 | 2976 | 0.54% | 49.7% | 49.7% |
| 0 | 2026-08 | 2975 | 1.84% | 49.9% | 50.3% |
| 3 | 2026-01 | 2976 | 1.97% | 49.9% | 49.3% |
| 3 | 2026-02 | 2688 | 3.30% | 50.0% | 50.4% |
| 3 | 2026-03 | 2976 | 2.63% | 50.6% | 49.9% |
| 3 | 2026-04 | 2880 | 1.58% | 50.0% | 51.0% |
| 3 | 2026-05 | 2976 | 2.57% | 50.3% | 49.3% |
| 3 | 2026-06 | 2880 | 3.62% | 49.5% | 47.6% |
| 3 | 2026-07 | 2976 | 2.46% | 49.0% | 49.7% |
| 3 | 2026-08 | 2975 | 2.82% | 49.9% | 50.3% |
<!-- table:calibration:end -->

The raw probabilities are already close to calibrated (ECE 1.6% at the open, 0.9% at minute 3; a 0.55 means about 55%). Platt scaling removes most of the remaining error at the open but also flattens the probabilities (lower resolution), so the Brier score barely moves. Month by month, the mean predicted probability tracks the observed rate within about two points; June 2026, when only 47.6% of windows closed up, is the largest miss.

**13. Abstention with conformal prediction.** Instead of a fixed confidence cutoff, split conformal prediction uses the previous month to set a threshold that guarantees a coverage rate, and issues a set: {up}, {down}, or both. A two-class set is an abstention.

<!-- table:conformal:start -->
Split conformal prediction sets: the previous month calibrates the threshold, the current month is scored. Coverage is how often the set contains the truth (should be at least the target). A single-class set is a call; a two-class set is an abstention.

| minute | target coverage | n | coverage | share with a single-class set | accuracy when a call is made |
|---|---|---|---|---|---|
| 0 | 90% | 20351 | 90.9% | 21.1% | 56.60% |
| 0 | 80% | 20351 | 81.0% | 42.4% | 55.11% |
| 0 | 70% | 20351 | 70.8% | 63.5% | 53.98% |
| 0 | 60% | 20351 | 60.2% | 85.0% | 53.18% |
| 3 | 90% | 20351 | 90.1% | 41.3% | 76.15% |
| 3 | 80% | 20351 | 80.6% | 68.2% | 71.61% |
| 3 | 70% | 20351 | 70.6% | 91.3% | 67.82% |
| 3 | 60% | 20351 | 60.1% | 87.9% | 68.35% |
<!-- table:conformal:end -->

The coverage guarantee holds at every target (90.9% delivered for 90% promised, and so on down). At the open, asking for 90% coverage makes a call on 21% of windows, and those calls are right 56.6% of the time; this is the same trade as the meta-labelling rule (55.3% on 11%) reached by a different route, with a guarantee attached. Three minutes in, 90% coverage yields calls on 41% of windows at 76% accuracy.

**14. Adversarial validation.** For each test month, a classifier tries to tell that month's windows from all earlier months. AUC 0.5 would mean nothing moved.

<!-- table:adversarial:start -->
Adversarial validation: a classifier trained to tell a test month's windows from all earlier months, scored on a held-out half. AUC 0.5 means the month is indistinguishable; higher means the feature distribution moved, and the top features say where.

| minute | month | AUC | top features |
|---|---|---|---|
| 0 | 2026-01 | 0.772 | vol240, atr14, vol60 |
| 0 | 2026-02 | 0.843 | vol240, atr14, nratio5 |
| 0 | 2026-03 | 0.768 | wday, atr14, vol240 |
| 0 | 2026-04 | 0.746 | vol240, flow15, nratio5 |
| 0 | 2026-05 | 0.844 | atr14, vol240, nratio5 |
| 0 | 2026-06 | 0.679 | vol240, wday, vol60 |
| 0 | 2026-07 | 0.759 | atr14, nratio5, vol240 |
| 0 | 2026-08 | 0.792 | vol240, atr14, wday |
| 3 | 2026-01 | 0.768 | vol240, atr14, wday |
| 3 | 2026-02 | 0.841 | vol240, atr14, nratio5 |
| 3 | 2026-03 | 0.770 | atr14, wday, vol240 |
| 3 | 2026-04 | 0.740 | vol240, atr14, nratio5 |
| 3 | 2026-05 | 0.843 | atr14, vol240, nratio5 |
| 3 | 2026-06 | 0.676 | vol60, atr14, vol240 |
| 3 | 2026-07 | 0.756 | atr14, vol240, nratio5 |
| 3 | 2026-08 | 0.791 | vol240, atr14, wday |
<!-- table:adversarial:end -->

Every month is distinguishable (AUC 0.68 to 0.84), and the features that give it away are always the volatility measures (`vol240`, `atr14`) and the trade-rate ratio. So the inputs drift month to month, in their volatility level, while the direction signal does not (study 9): the model's decision depends on the shape of the recent path, not its scale. This is the argument for the volatility-normalised features already in the set, and a caution for any feature that is not scale-free.

**15. Feature importance over time.** Permutation importance (accuracy lost when a feature is shuffled) and mean absolute SHAP contribution, on each held-out month.

<!-- table:importance:start -->
Feature importance on each held-out month. Permutation importance is the accuracy drop (points) when the feature is shuffled; SHAP is the mean absolute contribution from the booster. Top five of each.

| minute | month | permutation importance (points) | mean |SHAP| |
|---|---|---|---|
| 0 | 2026-01 | rsi60 +1.11, flow15 +0.94, macd_hist +0.87, flow1 +0.71, flow5 +0.57 | flow15 0.080, vratio15 0.056, atr14 0.049, obv_slope60 0.041, bb_pctb 0.038 |
| 0 | 2026-02 | macd_hist +0.89, rsi14 +0.63, win2 +0.56, win1 +0.48, rsi60 +0.48 | flow15 0.072, rsi60 0.052, obv_slope60 0.044, vratio15 0.037, rangepos 0.036 |
| 0 | 2026-03 | rsi60 +1.08, obv_slope60 +0.91, flow1 +0.67, vol240 +0.44, hour +0.44 | flow15 0.053, rsi60 0.052, obv_slope60 0.048, bb_pctb 0.048, vratio15 0.034 |
| 0 | 2026-04 | rsi60 +1.39, ret5 +1.01, rangepos +1.01, bb_pctb +0.83, rsi14 +0.76 | rsi60 0.063, flow15 0.042, rangepos 0.041, obv_slope60 0.041, bb_pctb 0.028 |
| 0 | 2026-05 | flow1 +0.57, vratio15 +0.44, rsi60 +0.34, flow3 +0.17, lead +0.00 | rsi60 0.063, rangepos 0.053, flow15 0.052, obv_slope60 0.046, bb_pctb 0.033 |
| 0 | 2026-06 | rangepos +1.01, ret240 +0.69, atr14 +0.63, ret5 +0.45, ret15 +0.45 | rangepos 0.065, rsi60 0.056, flow15 0.041, obv_slope60 0.038, ret5 0.037 |
| 0 | 2026-07 | obv_slope60 +1.48, atr14 +1.24, rsi60 +0.94, nratio5 +0.87, adx14 +0.81 | rangepos 0.055, rsi60 0.048, obv_slope60 0.044, bb_pctb 0.040, flow15 0.039 |
| 0 | 2026-08 | win3 +0.67, win4 +0.34, obv_slope60 +0.27, vratio5 +0.24, size5 +0.24 | rangepos 0.057, rsi60 0.054, obv_slope60 0.052, bb_pctb 0.041, flow15 0.037 |
| 3 | 2026-01 | lead +14.05, vol240 +0.60, vol15 +0.47, ret5 +0.44, flow1 +0.44 | lead 0.571, win1 0.085, flow15 0.068, stoch14 0.065, rangepos 0.054 |
| 3 | 2026-02 | lead +12.61, vol15 +0.63, win1 +0.60, flow3 +0.30, flow60 +0.30 | lead 0.736, win1 0.102, stoch14 0.062, flow15 0.053, obv_slope60 0.049 |
| 3 | 2026-03 | lead +11.32, win1 +0.40, ret5 +0.34, vratio15 +0.30, adx14 +0.30 | lead 0.632, win1 0.099, flow3 0.071, stoch14 0.056, obv_slope60 0.048 |
| 3 | 2026-04 | lead +14.44, win1 +0.56, stoch14 +0.45, obv_slope60 +0.35, vratio5 +0.21 | lead 0.556, win1 0.071, ret5 0.056, flow3 0.051, stoch14 0.050 |
| 3 | 2026-05 | lead +14.52, win1 +0.24, ret5 +0.07, vol15 +0.07, wday +0.03 | lead 0.530, win1 0.068, stoch14 0.058, flow3 0.053, ret5 0.052 |
| 3 | 2026-06 | lead +15.83, flow15 +0.49, ret5 +0.45, ret240 +0.35, rsi60 +0.31 | lead 0.663, win1 0.069, ret5 0.060, rangepos 0.053, flow3 0.052 |
| 3 | 2026-07 | lead +13.41, win1 +0.27, bb_pctb +0.20, rangepos +0.10, win2 +0.07 | lead 0.530, win1 0.067, flow3 0.056, ret5 0.054, stoch14 0.046 |
| 3 | 2026-08 | lead +12.24, win1 +0.67, rangepos +0.57, flow3 +0.44, vol60 +0.27 | lead 0.510, win1 0.066, flow3 0.065, ret5 0.049, stoch14 0.046 |
<!-- table:importance:end -->

Three minutes in, the lead is worth 11 to 16 points every month and nothing else is worth more than one, which is the numerical form of "the current lead explains almost all of it". At the open there is no stable leader: the top permutation feature changes every month and no single feature is worth more than 1.5 points. The SHAP ranking is steadier (`flow15`, `rsi60`, `rangepos`, `obv_slope60` recur), which says the model spreads a small signal over several correlated inputs rather than finding one that matters.

**16. Event rules: "if X happens, then up or down".** Forty-odd conditions of the kind a chart reader would name (price breaks the 4-hour high, RSI is oversold, three windows down in a row, taker buying dominates, a two-standard-deviation spike in the last five minutes), each scored by the up-rate of the next window when it holds. Because forty tests produce a few false positives by chance, p-values are corrected for the false discovery rate, and every survivor is re-checked month by month: it counts as stable only if its direction holds in at least three quarters of the test months. A depth-2 decision tree per month then shows what a learned rule looks like.

<!-- table:rules:start -->
Event library: up-rate of the window when the condition holds at the entry minute, against the unconditional rate. Day-block 95% intervals; p-values use a day-clustered standard error; 'survives FDR' marks events that pass Benjamini-Hochberg at a 10% false discovery rate across all events tested at that minute. Events that fire fewer than 300 times are omitted.

| minute | if | fires | share | up-rate [95% CI] | vs base (points) | p | survives FDR |
|---|---|---|---|---|---|---|---|
| 0 | upper quarter of 4h range | 7948 | 24.8% | 44.9% [43.9, 45.8] | -4.9 | 0.000 | yes |
| 0 | taker buying 60 pct+ of last 15 min | 6289 | 19.6% | 44.8% [43.8, 46.0] | -4.9 | 0.000 | yes |
| 0 | lower quarter of 4h range | 7387 | 23.0% | 54.3% [53.1, 55.6] | +4.5 | 0.000 | yes |
| 0 | two windows down in a row | 7770 | 24.2% | 53.3% [52.4, 54.4] | +3.6 | 0.000 | yes |
| 0 | taker selling 60 pct+ of last 15 min | 7496 | 23.4% | 53.2% [52.1, 54.3] | +3.5 | 0.000 | yes |
| 0 | previous window up | 15922 | 49.7% | 47.5% [46.8, 48.2] | -2.2 | 0.000 | yes |
| 0 | two windows up in a row | 7555 | 23.6% | 46.4% [45.4, 47.4] | -3.3 | 0.000 | yes |
| 0 | previous window down | 16136 | 50.3% | 51.9% [51.2, 52.6] | +2.2 | 0.000 | yes |
| 0 | OBV rising over 60 min | 2366 | 7.4% | 44.0% [42.1, 45.9] | -5.8 | 0.000 | yes |
| 0 | price 30 bp+ below 60-min VWAP | 2105 | 6.6% | 56.0% [53.7, 58.2] | +6.2 | 0.000 | yes |
| 0 | price at 4h high (rangepos >= 0.98) | 539 | 1.7% | 38.4% [34.3, 42.5] | -11.3 | 0.000 | yes |
| 0 | RSI14 below 30 | 1391 | 4.3% | 57.3% [54.7, 59.9] | +7.6 | 0.000 | yes |
| 0 | three windows up in a row | 3501 | 10.9% | 45.4% [43.9, 46.9] | -4.3 | 0.000 | yes |
| 0 | 4h return above +50 bp | 6792 | 21.2% | 46.6% [45.4, 47.6] | -3.2 | 0.000 | yes |
| 0 | EMA9 below EMA21 by 10 bp | 1610 | 5.0% | 56.6% [54.3, 59.1] | +6.9 | 0.000 | yes |
| 0 | RSI14 above 70 | 1295 | 4.0% | 42.9% [40.4, 45.3] | -6.9 | 0.000 | yes |
| 0 | OBV falling over 60 min | 2884 | 9.0% | 54.2% [52.6, 56.0] | +4.5 | 0.000 | yes |
| 0 | last 15 min up more than 2 sd | 718 | 2.2% | 40.9% [37.7, 44.5] | -8.8 | 0.000 | yes |
| 0 | EMA9 above EMA21 by 10 bp | 1515 | 4.7% | 43.3% [40.7, 46.0] | -6.4 | 0.000 | yes |
| 0 | three windows down in a row | 3635 | 11.3% | 53.7% [52.0, 55.3] | +3.9 | 0.000 | yes |
| 0 | last 15 min down more than 2 sd | 812 | 2.5% | 58.4% [54.7, 62.0] | +8.6 | 0.000 | yes |
| 0 | 4h return below -50 bp | 6940 | 21.6% | 52.4% [51.2, 53.6] | +2.7 | 0.000 | yes |
| 0 | MACD histogram negative | 16134 | 50.3% | 51.2% [50.5, 51.9] | +1.5 | 0.000 | yes |
| 0 | MACD histogram positive | 15924 | 49.7% | 48.2% [47.6, 48.9] | -1.5 | 0.000 | yes |
| 0 | last 5 min up more than 2 sd | 688 | 2.1% | 42.0% [38.3, 45.6] | -7.7 | 0.000 | yes |
| 0 | price 30 bp+ above 60-min VWAP | 2190 | 6.8% | 45.7% [43.6, 47.9] | -4.0 | 0.000 | yes |
| 0 | below lower Bollinger band | 1271 | 4.0% | 54.5% [51.8, 57.4] | +4.8 | 0.001 | yes |
| 0 | price at 4h low (rangepos <= 0.02) | 521 | 1.6% | 55.7% [51.3, 59.6] | +5.9 | 0.006 | yes |
| 0 | last 5 min down more than 2 sd | 688 | 2.1% | 54.4% [50.6, 58.2] | +4.6 | 0.014 | yes |
| 0 | above upper Bollinger band | 1224 | 3.8% | 46.7% [44.1, 49.6] | -3.0 | 0.034 | yes |
| 0 | volume last 5 min 3x the daily average | 1524 | 4.8% | 47.2% [44.8, 49.6] | -2.5 | 0.043 | yes |
| 0 | US afternoon (14-17 UTC) | 5344 | 16.7% | 50.7% [49.4, 52.0] | +1.0 | 0.140 |  |
| 0 | Asia early (0-3 UTC) | 5339 | 16.7% | 48.9% [47.7, 50.0] | -0.8 | 0.162 |  |
| 0 | ADX14 below 15 (ranging) | 3962 | 12.4% | 48.8% [47.1, 50.5] | -1.0 | 0.242 |  |
| 0 | low volatility (vol60 in bottom decile) | 3206 | 10.0% | 50.3% [48.9, 51.7] | +0.6 | 0.391 |  |
| 0 | high volatility (vol60 in top decile) | 3206 | 10.0% | 50.5% [48.7, 52.3] | +0.8 | 0.393 |  |
| 0 | weekend | 9216 | 28.7% | 50.1% [49.3, 51.0] | +0.4 | 0.401 |  |
| 0 | ADX14 above 30 (trending) | 9570 | 29.9% | 50.1% [49.1, 50.9] | +0.3 | 0.495 |  |
| 0 | trade count last 5 min 3x average | 808 | 2.5% | 48.8% [45.9, 51.8] | -1.0 | 0.523 |  |
| 3 | price at 4h high (rangepos >= 0.98) | 513 | 1.6% | 68.8% [64.9, 72.5] | +19.1 | 0.000 | yes |
| 3 | price at 4h low (rangepos <= 0.02) | 571 | 1.8% | 29.4% [25.8, 33.2] | -20.3 | 0.000 | yes |
| 3 | last 5 min up more than 2 sd | 864 | 2.7% | 81.9% [79.3, 84.4] | +32.2 | 0.000 | yes |
| 3 | last 5 min down more than 2 sd | 895 | 2.8% | 18.8% [16.2, 21.4] | -31.0 | 0.000 | yes |
| 3 | last 15 min up more than 2 sd | 692 | 2.2% | 67.2% [63.8, 70.7] | +17.5 | 0.000 | yes |
| 3 | RSI14 above 70 | 1361 | 4.2% | 73.3% [71.1, 75.5] | +23.5 | 0.000 | yes |
| 3 | RSI14 below 30 | 1508 | 4.7% | 28.6% [26.2, 31.1] | -21.2 | 0.000 | yes |
| 3 | MACD histogram positive | 15631 | 48.8% | 57.7% [57.0, 58.4] | +8.0 | 0.000 | yes |
| 3 | MACD histogram negative | 16427 | 51.2% | 42.2% [41.5, 42.8] | -7.6 | 0.000 | yes |
| 3 | above upper Bollinger band | 1827 | 5.7% | 79.5% [77.6, 81.3] | +29.7 | 0.000 | yes |
| 3 | below lower Bollinger band | 1956 | 6.1% | 20.0% [18.2, 21.6] | -29.7 | 0.000 | yes |
| 3 | price 30 bp+ above 60-min VWAP | 2177 | 6.8% | 59.8% [58.0, 61.7] | +10.1 | 0.000 | yes |
| 3 | price 30 bp+ below 60-min VWAP | 2169 | 6.8% | 41.2% [39.3, 43.1] | -8.5 | 0.000 | yes |
| 3 | leading by 10 bp+ at entry | 3760 | 11.7% | 78.6% [77.2, 79.9] | +28.9 | 0.000 | yes |
| 3 | trailing by 10 bp+ at entry | 4039 | 12.6% | 22.8% [21.4, 24.2] | -26.9 | 0.000 | yes |
| 3 | last 15 min down more than 2 sd | 703 | 2.2% | 35.6% [32.2, 39.0] | -14.2 | 0.000 | yes |
| 3 | two windows down in a row | 7770 | 24.2% | 53.3% [52.4, 54.4] | +3.6 | 0.000 | yes |
| 3 | previous window up | 15922 | 49.7% | 47.5% [46.8, 48.2] | -2.2 | 0.000 | yes |
| 3 | two windows up in a row | 7555 | 23.6% | 46.4% [45.4, 47.4] | -3.3 | 0.000 | yes |
| 3 | previous window down | 16136 | 50.3% | 51.9% [51.2, 52.6] | +2.2 | 0.000 | yes |
| 3 | three windows up in a row | 3501 | 10.9% | 45.4% [43.9, 46.9] | -4.3 | 0.000 | yes |
| 3 | upper quarter of 4h range | 7947 | 24.8% | 52.0% [51.1, 52.9] | +2.3 | 0.000 | yes |
| 3 | three windows down in a row | 3635 | 11.3% | 53.7% [52.0, 55.3] | +3.9 | 0.000 | yes |
| 3 | taker selling 60 pct+ of last 15 min | 7439 | 23.2% | 47.4% [46.3, 48.5] | -2.3 | 0.000 | yes |
| 3 | lower quarter of 4h range | 7397 | 23.1% | 47.6% [46.5, 48.7] | -2.2 | 0.000 | yes |
| 3 | taker buying 60 pct+ of last 15 min | 6139 | 19.1% | 51.9% [50.7, 53.2] | +2.2 | 0.000 | yes |
| 3 | EMA9 below EMA21 by 10 bp | 1553 | 4.8% | 45.9% [43.7, 48.3] | -3.8 | 0.001 | yes |
| 3 | EMA9 above EMA21 by 10 bp | 1484 | 4.6% | 53.6% [51.0, 56.2] | +3.9 | 0.003 | yes |
| 3 | US afternoon (14-17 UTC) | 5344 | 16.7% | 50.7% [49.4, 52.0] | +1.0 | 0.140 |  |
| 3 | high volatility (vol60 in top decile) | 3206 | 10.0% | 51.1% [49.3, 52.9] | +1.4 | 0.144 |  |
| 3 | low volatility (vol60 in bottom decile) | 3206 | 10.0% | 50.8% [49.4, 52.2] | +1.0 | 0.153 |  |
| 3 | Asia early (0-3 UTC) | 5339 | 16.7% | 48.9% [47.7, 50.0] | -0.8 | 0.162 |  |
| 3 | ADX14 below 15 (ranging) | 3885 | 12.1% | 48.6% [47.0, 50.2] | -1.1 | 0.177 |  |
| 3 | ADX14 above 30 (trending) | 9535 | 29.7% | 50.2% [49.3, 51.1] | +0.5 | 0.266 |  |
| 3 | OBV rising over 60 min | 2281 | 7.1% | 50.7% [48.7, 52.6] | +0.9 | 0.341 |  |
| 3 | volume last 5 min 3x the daily average | 1795 | 5.6% | 48.7% [46.7, 50.9] | -1.0 | 0.361 |  |
| 3 | weekend | 9216 | 28.7% | 50.1% [49.3, 51.0] | +0.4 | 0.401 |  |
| 3 | trade count last 5 min 3x average | 1136 | 3.5% | 50.5% [48.0, 53.2] | +0.8 | 0.559 |  |
| 3 | 4h return below -50 bp | 6934 | 21.6% | 49.4% [48.4, 50.6] | -0.3 | 0.599 |  |
| 3 | within 2 bp of the open at entry | 7519 | 23.5% | 49.9% [48.8, 51.0] | +0.2 | 0.708 |  |
| 3 | OBV falling over 60 min | 2858 | 8.9% | 49.5% [47.8, 51.3] | -0.2 | 0.832 |  |
| 3 | 4h return above +50 bp | 6762 | 21.1% | 49.7% [48.6, 50.8] | -0.0 | 0.961 |  |

Stability of the survivors: the deviation of the up-rate from that month's base rate, month by month, and how many months agree with the overall direction. Stable means at least three quarters of the months agree.

| minute | if | overall | months agreeing | deviation by month (points) | verdict |
|---|---|---|---|---|---|
| 0 | price at 4h high (rangepos >= 0.98) | down by 11.3 points overall | 7/7 | -4.9 - -12.8 -12.2 -17.6 -13.3 -21.7 -15.3 | stable |
| 0 | price at 4h low (rangepos <= 0.02) | up by 5.9 points overall | 6/8 | +12.5 +7.6 +6.7 -4.3 +4.2 +17.1 +2.3 -0.3 | stable |
| 0 | upper quarter of 4h range | down by 4.9 points overall | 8/8 | -7.1 -2.9 -7.7 -4.6 -5.4 -5.1 -4.6 -3.7 | stable |
| 0 | lower quarter of 4h range | up by 4.5 points overall | 8/8 | +5.4 +5.5 +6.9 +6.2 +4.7 +5.3 +3.9 +1.1 | stable |
| 0 | last 5 min up more than 2 sd | down by 7.7 points overall | 8/8 | -15.5 -2.4 -10.8 -3.8 -18.0 -12.0 -2.6 -7.0 | stable |
| 0 | last 5 min down more than 2 sd | up by 4.6 points overall | 6/8 | +10.4 -1.2 +0.1 +8.2 +3.0 +11.7 -5.3 +9.1 | stable |
| 0 | last 15 min up more than 2 sd | down by 8.8 points overall | 6/8 | -11.4 -14.7 -18.0 +0.6 -7.6 +3.4 -1.2 -14.4 | stable |
| 0 | last 15 min down more than 2 sd | up by 8.6 points overall | 8/8 | +0.7 +12.3 +9.4 +15.7 +3.0 +11.1 +1.8 +15.5 | stable |
| 0 | 4h return above +50 bp | down by 3.2 points overall | 7/8 | -6.3 -2.7 -2.9 -3.4 -5.4 -3.0 -5.7 +0.1 | stable |
| 0 | 4h return below -50 bp | up by 2.7 points overall | 8/8 | +1.6 +2.3 +4.8 +4.6 +6.8 +1.6 +5.9 +1.3 | stable |
| 0 | previous window up | down by 2.2 points overall | 8/8 | -3.3 -3.0 -1.1 -3.0 -2.0 -2.9 -1.8 -1.1 | stable |
| 0 | previous window down | up by 2.2 points overall | 8/8 | +3.2 +3.0 +1.1 +3.1 +1.9 +2.6 +1.8 +1.1 | stable |
| 0 | two windows up in a row | down by 3.3 points overall | 8/8 | -6.4 -3.6 -3.6 -3.8 -3.6 -4.3 -2.3 -3.2 | stable |
| 0 | two windows down in a row | up by 3.6 points overall | 8/8 | +4.6 +5.2 +4.9 +3.6 +3.1 +2.2 +4.8 +3.3 | stable |
| 0 | three windows up in a row | down by 4.3 points overall | 7/8 | -10.2 -4.4 -7.8 -1.9 -1.3 -8.3 +0.3 -5.1 | stable |
| 0 | three windows down in a row | up by 3.9 points overall | 8/8 | +5.6 +7.0 +2.5 +3.9 +2.6 +3.9 +5.9 +4.6 | stable |
| 0 | RSI14 above 70 | down by 6.9 points overall | 8/8 | -8.9 -11.9 -5.4 -5.3 -7.4 -1.2 -5.6 -2.2 | stable |
| 0 | RSI14 below 30 | up by 7.6 points overall | 8/8 | +9.9 +5.4 +1.9 +10.1 +1.9 +8.4 +9.0 +11.8 | stable |
| 0 | MACD histogram positive | down by 1.5 points overall | 7/8 | -2.2 -2.0 +0.6 -1.7 -2.0 -0.9 -0.6 -1.0 | stable |
| 0 | MACD histogram negative | up by 1.5 points overall | 7/8 | +2.3 +1.9 -0.6 +1.8 +1.9 +0.9 +0.6 +0.9 | stable |
| 0 | above upper Bollinger band | down by 3.0 points overall | 5/8 | -6.8 +8.1 +0.5 -10.8 -6.4 +1.4 -4.6 -1.0 | not stable |
| 0 | below lower Bollinger band | up by 4.8 points overall | 5/8 | +6.5 -1.7 -2.1 +6.2 +6.8 -1.1 +6.1 +9.6 | not stable |
| 0 | EMA9 above EMA21 by 10 bp | down by 6.4 points overall | 8/8 | -11.3 -8.2 -10.3 -1.8 -8.0 -7.2 -1.0 -4.3 | stable |
| 0 | EMA9 below EMA21 by 10 bp | up by 6.9 points overall | 8/8 | +4.7 +9.9 +9.7 +5.7 +7.2 +8.6 +12.3 +15.3 | stable |
| 0 | taker buying 60 pct+ of last 15 min | down by 4.9 points overall | 8/8 | -5.0 -1.0 -4.9 -6.6 -3.7 -4.9 -2.9 -3.8 | stable |
| 0 | taker selling 60 pct+ of last 15 min | up by 3.5 points overall | 7/8 | +5.0 -0.1 +1.7 +6.5 +2.3 +3.1 +2.3 +4.5 | stable |
| 0 | volume last 5 min 3x the daily average | down by 2.5 points overall | 6/8 | -4.6 +1.9 -0.3 -1.7 -5.4 +3.2 -4.2 -6.0 | stable |
| 0 | OBV rising over 60 min | down by 5.8 points overall | 7/8 | -9.0 +0.3 -7.3 -5.4 -8.0 -7.7 -8.2 -1.9 | stable |
| 0 | OBV falling over 60 min | up by 4.5 points overall | 8/8 | +5.1 +8.6 +3.6 +3.7 +4.1 +8.6 +5.9 +8.7 | stable |
| 0 | price 30 bp+ above 60-min VWAP | down by 4.0 points overall | 7/8 | -6.3 -4.7 -4.2 -4.0 -2.7 -1.9 +3.8 -2.9 | stable |
| 0 | price 30 bp+ below 60-min VWAP | up by 6.2 points overall | 7/8 | +7.6 +4.9 +9.3 -2.9 +2.7 +8.5 +10.8 +14.4 | stable |
| 3 | price at 4h high (rangepos >= 0.98) | up by 19.1 points overall | 8/8 | +16.0 +12.7 +30.1 +16.5 +17.4 +23.4 +13.9 +21.8 | stable |
| 3 | price at 4h low (rangepos <= 0.02) | down by 20.3 points overall | 7/7 | -10.3 -19.1 -15.8 - -24.8 -14.8 -20.1 -14.7 | stable |
| 3 | upper quarter of 4h range | up by 2.3 points overall | 8/8 | +0.5 +3.4 +0.7 +1.5 +1.5 +2.9 +1.9 +2.3 | stable |
| 3 | lower quarter of 4h range | down by 2.2 points overall | 7/8 | -1.0 -0.8 +0.6 -1.2 -2.9 -3.8 -2.3 -5.5 | stable |
| 3 | last 5 min up more than 2 sd | up by 32.2 points overall | 8/8 | +21.3 +40.3 +33.2 +33.9 +35.1 +36.0 +31.4 +24.5 | stable |
| 3 | last 5 min down more than 2 sd | down by 31.0 points overall | 8/8 | -31.4 -32.9 -29.4 -37.7 -29.5 -31.3 -29.4 -33.1 | stable |
| 3 | last 15 min up more than 2 sd | up by 17.5 points overall | 8/8 | +10.3 +23.2 +8.7 +18.1 +15.6 +28.5 +21.7 +16.4 | stable |
| 3 | last 15 min down more than 2 sd | down by 14.2 points overall | 8/8 | -17.3 -19.6 -9.6 -9.6 -21.4 -11.1 -10.4 -5.8 | stable |
| 3 | previous window up | down by 2.2 points overall | 8/8 | -3.3 -3.0 -1.1 -3.0 -2.0 -2.9 -1.8 -1.1 | stable |
| 3 | previous window down | up by 2.2 points overall | 8/8 | +3.2 +3.0 +1.1 +3.1 +1.9 +2.6 +1.8 +1.1 | stable |
| 3 | two windows up in a row | down by 3.3 points overall | 8/8 | -6.4 -3.6 -3.6 -3.8 -3.6 -4.3 -2.3 -3.2 | stable |
| 3 | two windows down in a row | up by 3.6 points overall | 8/8 | +4.6 +5.2 +4.9 +3.6 +3.1 +2.2 +4.8 +3.3 | stable |
| 3 | three windows up in a row | down by 4.3 points overall | 7/8 | -10.2 -4.4 -7.8 -1.9 -1.3 -8.3 +0.3 -5.1 | stable |
| 3 | three windows down in a row | up by 3.9 points overall | 8/8 | +5.6 +7.0 +2.5 +3.9 +2.6 +3.9 +5.9 +4.6 | stable |
| 3 | RSI14 above 70 | up by 23.5 points overall | 8/8 | +17.1 +25.8 +24.8 +22.4 +24.6 +27.7 +27.5 +23.2 | stable |
| 3 | RSI14 below 30 | down by 21.2 points overall | 8/8 | -21.0 -23.4 -21.4 -27.4 -27.6 -19.3 -19.2 -9.5 | stable |
| 3 | MACD histogram positive | up by 8.0 points overall | 8/8 | +8.3 +5.9 +10.5 +7.4 +8.1 +8.4 +8.6 +8.4 | stable |
| 3 | MACD histogram negative | down by 7.6 points overall | 8/8 | -8.2 -5.6 -10.1 -7.2 -7.8 -8.2 -8.4 -7.5 | stable |
| 3 | above upper Bollinger band | up by 29.7 points overall | 8/8 | +26.0 +31.4 +30.3 +29.4 +31.0 +31.7 +33.7 +24.6 | stable |
| 3 | below lower Bollinger band | down by 29.7 points overall | 8/8 | -30.2 -27.3 -27.8 -36.9 -30.6 -27.3 -28.5 -28.4 | stable |
| 3 | EMA9 above EMA21 by 10 bp | up by 3.9 points overall | 6/8 | -0.4 +2.3 +1.0 +8.8 -0.4 +8.2 +10.7 +4.0 | stable |
| 3 | EMA9 below EMA21 by 10 bp | down by 3.8 points overall | 7/8 | -4.6 -0.4 -3.3 -5.4 -11.8 -5.1 +3.8 -0.3 | stable |
| 3 | taker buying 60 pct+ of last 15 min | up by 2.2 points overall | 8/8 | +2.1 +3.0 +0.8 +1.7 +3.4 +2.5 +3.3 +3.4 | stable |
| 3 | taker selling 60 pct+ of last 15 min | down by 2.3 points overall | 7/8 | -2.7 -3.8 -2.9 +0.4 -3.2 -3.2 -4.7 -1.5 | stable |
| 3 | price 30 bp+ above 60-min VWAP | up by 10.1 points overall | 8/8 | +6.8 +6.5 +6.9 +12.1 +7.7 +13.1 +14.4 +13.3 | stable |
| 3 | price 30 bp+ below 60-min VWAP | down by 8.5 points overall | 7/8 | -3.5 -7.4 -7.5 -18.1 -16.8 -7.9 -11.6 +0.8 | stable |
| 3 | leading by 10 bp+ at entry | up by 28.9 points overall | 8/8 | +26.5 +24.2 +30.0 +29.0 +32.7 +30.4 +37.6 +28.7 | stable |
| 3 | trailing by 10 bp+ at entry | down by 26.9 points overall | 8/8 | -29.3 -23.0 -26.5 -29.8 -30.7 -26.9 -28.6 -26.1 | stable |

Learned rules: a depth-2 decision tree per test month (leaves of at least 500 windows), trained on earlier months, and its accuracy on the test month. The same root split in most months is a stable rule; a different root each month means there is none.

| minute | month | accuracy | tree |
|---|---|---|---|
| 0 | 2026-01 | 52.22% | &#124;--- flow15 <= 0.2<br>&#124;   &#124;--- rsi14 <= 36.9<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- rsi14 >  36.9<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;--- flow15 >  0.2<br>&#124;   &#124;--- rsi14 <= 59.6<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- rsi14 >  59.6<br>&#124;   &#124;   &#124;--- class: 0<br> |
| 0 | 2026-02 | 51.00% | &#124;--- rsi60 <= 56.0<br>&#124;   &#124;--- flow15 <= -0.1<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- flow15 >  -0.1<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- rsi60 >  56.0<br>&#124;   &#124;--- flow15 <= 0.1<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- flow15 >  0.1<br>&#124;   &#124;   &#124;--- class: 0<br> |
| 0 | 2026-03 | 51.41% | &#124;--- bb_pctb <= 0.6<br>&#124;   &#124;--- rsi14 <= 32.9<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- rsi14 >  32.9<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;--- bb_pctb >  0.6<br>&#124;   &#124;--- rsi60 <= 56.0<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- rsi60 >  56.0<br>&#124;   &#124;   &#124;--- class: 0<br> |
| 0 | 2026-04 | 51.18% | &#124;--- rsi60 <= 56.0<br>&#124;   &#124;--- rsi60 <= 47.5<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- rsi60 >  47.5<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- rsi60 >  56.0<br>&#124;   &#124;--- size5 <= 1.0<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- size5 >  1.0<br>&#124;   &#124;   &#124;--- class: 0<br> |
| 0 | 2026-05 | 51.28% | &#124;--- rsi60 <= 55.9<br>&#124;   &#124;--- rsi60 <= 45.4<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- rsi60 >  45.4<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;--- rsi60 >  55.9<br>&#124;   &#124;--- size5 <= 1.1<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- size5 >  1.1<br>&#124;   &#124;   &#124;--- class: 0<br> |
| 0 | 2026-06 | 53.33% | &#124;--- rsi60 <= 55.0<br>&#124;   &#124;--- rangepos <= 0.3<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- rangepos >  0.3<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- rsi60 >  55.0<br>&#124;   &#124;--- flow15 <= 0.1<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- flow15 >  0.1<br>&#124;   &#124;   &#124;--- class: 0<br> |
| 0 | 2026-07 | 52.65% | &#124;--- rsi60 <= 51.5<br>&#124;   &#124;--- rsi14 <= 33.9<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- rsi14 >  33.9<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;--- rsi60 >  51.5<br>&#124;   &#124;--- rsi60 <= 55.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- rsi60 >  55.9<br>&#124;   &#124;   &#124;--- class: 0<br> |
| 0 | 2026-08 | 51.56% | &#124;--- rsi60 <= 51.5<br>&#124;   &#124;--- rsi14 <= 33.9<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- rsi14 >  33.9<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;--- rsi60 >  51.5<br>&#124;   &#124;--- rsi60 <= 56.3<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- rsi60 >  56.3<br>&#124;   &#124;   &#124;--- class: 0<br> |
| 3 | 2026-01 | 65.73% | &#124;--- lead <= -0.8<br>&#124;   &#124;--- lead <= -5.5<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- lead >  -5.5<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- lead >  -0.8<br>&#124;   &#124;--- lead <= 5.5<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- lead >  5.5<br>&#124;   &#124;   &#124;--- class: 1<br> |
| 3 | 2026-02 | 64.88% | &#124;--- lead <= -0.8<br>&#124;   &#124;--- lead <= -5.5<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- lead >  -5.5<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- lead >  -0.8<br>&#124;   &#124;--- lead <= 5.5<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- lead >  5.5<br>&#124;   &#124;   &#124;--- class: 1<br> |
| 3 | 2026-03 | 65.15% | &#124;--- lead <= -0.8<br>&#124;   &#124;--- lead <= -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- lead >  -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- lead >  -0.8<br>&#124;   &#124;--- lead <= 4.3<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- lead >  4.3<br>&#124;   &#124;   &#124;--- class: 1<br> |
| 3 | 2026-04 | 66.32% | &#124;--- lead <= -0.8<br>&#124;   &#124;--- lead <= -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- lead >  -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- lead >  -0.8<br>&#124;   &#124;--- lead <= 5.5<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- lead >  5.5<br>&#124;   &#124;   &#124;--- class: 1<br> |
| 3 | 2026-05 | 66.20% | &#124;--- lead <= -0.8<br>&#124;   &#124;--- lead <= -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- lead >  -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- lead >  -0.8<br>&#124;   &#124;--- lead <= 5.8<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- lead >  5.8<br>&#124;   &#124;   &#124;--- class: 1<br> |
| 3 | 2026-06 | 66.53% | &#124;--- lead <= -0.8<br>&#124;   &#124;--- lead <= -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- lead >  -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- lead >  -0.8<br>&#124;   &#124;--- lead <= 4.3<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- lead >  4.3<br>&#124;   &#124;   &#124;--- class: 1<br> |
| 3 | 2026-07 | 66.16% | &#124;--- lead <= -0.8<br>&#124;   &#124;--- lead <= -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- lead >  -4.9<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- lead >  -0.8<br>&#124;   &#124;--- lead <= 4.6<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- lead >  4.6<br>&#124;   &#124;   &#124;--- class: 1<br> |
| 3 | 2026-08 | 67.63% | &#124;--- lead <= -0.1<br>&#124;   &#124;--- lead <= -4.8<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;   &#124;--- lead >  -4.8<br>&#124;   &#124;   &#124;--- class: 0<br>&#124;--- lead >  -0.1<br>&#124;   &#124;--- lead <= 4.6<br>&#124;   &#124;   &#124;--- class: 1<br>&#124;   &#124;--- lead >  4.6<br>&#124;   &#124;   &#124;--- class: 1<br> |
<!-- table:rules:end -->

Two things come out of it. First, at the open every stable event points the same way: **whatever just went up tends to go down in the next window, and vice versa**. Price at the 4-hour high is followed by an up window only 38% of the time (down by 11 points, in 7 of 7 months); price in the upper quarter of its range, 45%; RSI14 above 70, 43%; a two-standard-deviation spike up in the last five minutes, 42%; taker buying dominating the last 15 minutes, 45%. The mirror images hold for the down versions (RSI14 below 30 is followed by an up window 57% of the time, 8 of 8 months). So "if the price breaks X, then up" is backwards at this horizon: a break is followed by a pull-back more often than by a continuation. Second, the learned trees say the same thing in one line: the root split in six of eight months is RSI over the last 60 minutes at about 55, with "below, up; above, down", and that single rule scores 51 to 53% out of sample, about what the full models score. The events are individually stronger than the model's overall 53% because each fires on a slice of windows (2% to 25%) and the slices overlap heavily; they are one effect seen through many indicators, and the model already has it.

Three minutes in, the strongest "events" are just the lead in disguise (leading by 10 bp, 79% up), and the conditions that were reversal signals at the open have flipped sign because the last five minutes are now inside the window. Part of the open-of-window reversal is the shared-boundary effect noted in the checks (a spike into the open lifts the open price itself), which the one-minute-in check earlier put at roughly a third of the signal.

**17. Acting only when a strong event fires, and the September check.** The stable events from study 16 turned into three rules (act on any stable event with the strongest deciding; only events with a 5-point deviation or more; only when every firing event agrees), scored in-sample on the backtest and then on September 2026, which the event search never saw.

<!-- table:event_portfolio:start -->
Acting only when a stable event fires. Stable events are found on 2025-10 to 2026-08 (so the backtest rows are in-sample); the forward rows are 2026-09-01 to 2026-09-29, never seen by the event search. EV in cents per $1 contract at a 1c spread and 1.75c fee, priced at 0.5.

| minute | rule | period | windows acted on | share | accuracy [95% CI] | EV cents [95% CI] |
|---|---|---|---|---|---|---|
| 0 | any stable event, strongest wins | backtest (in-sample) | 32058 | 100.0% | 53.04% [52.57, 53.52] | +0.79 [+0.32, +1.27] |
| 0 | any stable event, strongest wins | forward | 2783 | 100.0% | 52.46% [50.61, 54.55] | +0.21 [-1.64, +2.30] |
| 0 | events with 5+ point deviation, strongest wins | backtest (in-sample) | 7903 | 24.7% | 56.02% [54.93, 57.05] | +3.77 [+2.68, +4.80] |
| 0 | events with 5+ point deviation, strongest wins | forward | 590 | 21.2% | 55.08% [51.42, 58.87] | +2.83 [-0.83, +6.62] |
| 0 | all firing stable events agree | backtest (in-sample) | 15868 | 49.5% | 54.08% [53.33, 54.80] | +1.83 [+1.08, +2.55] |
| 0 | all firing stable events agree | forward | 1421 | 51.1% | 53.62% [50.82, 56.63] | +1.37 [-1.43, +4.38] |

Each stable event on its own: the deviation of the up-rate from the base rate in the backtest, and the same in the forward period.

| minute | event | direction | backtest deviation (points) | forward fires | forward deviation (points) | held? |
|---|---|---|---|---|---|---|
| 0 | price at 4h high (rangepos >= 0.98) | down | -11.3 | 57 | -4.3 | same |
| 0 | last 15 min up more than 2 sd | down | -8.8 | 74 | +2.8 | flipped |
| 0 | last 15 min down more than 2 sd | up | +8.6 | 84 | +14.3 | same |
| 0 | last 5 min up more than 2 sd | down | -7.7 | 71 | -0.7 | same |
| 0 | RSI14 below 30 | up | +7.6 | 118 | +6.8 | same |
| 0 | EMA9 below EMA21 by 10 bp | up | +6.9 | 60 | +15.1 | same |
| 0 | RSI14 above 70 | down | -6.9 | 129 | -1.9 | same |
| 0 | EMA9 above EMA21 by 10 bp | down | -6.4 | 72 | -5.5 | same |
| 0 | price 30 bp+ below 60-min VWAP | up | +6.2 | 109 | +4.2 | same |
| 0 | price at 4h low (rangepos <= 0.02) | up | +5.9 | 36 | +2.8 | same |
| 0 | OBV rising over 60 min | down | -5.8 | 170 | -4.1 | same |
| 0 | taker buying 60 pct+ of last 15 min | down | -4.9 | 553 | -3.1 | same |
| 0 | upper quarter of 4h range | down | -4.9 | 761 | -4.3 | same |
| 0 | last 5 min down more than 2 sd | up | +4.6 | 56 | +9.0 | same |
| 0 | lower quarter of 4h range | up | +4.5 | 597 | +4.0 | same |
| 0 | OBV falling over 60 min | up | +4.5 | 204 | +8.9 | same |
| 0 | three windows up in a row | down | -4.3 | 305 | -5.4 | same |
| 0 | price 30 bp+ above 60-min VWAP | down | -4.0 | 125 | -0.3 | same |
| 0 | three windows down in a row | up | +3.9 | 319 | +2.7 | same |
| 0 | two windows down in a row | up | +3.6 | 679 | +3.2 | same |
| 0 | taker selling 60 pct+ of last 15 min | up | +3.5 | 631 | +5.4 | same |
| 0 | two windows up in a row | down | -3.3 | 676 | -4.8 | same |
| 0 | 4h return above +50 bp | down | -3.2 | 481 | -2.1 | same |
| 0 | 4h return below -50 bp | up | +2.7 | 494 | +3.3 | same |
| 0 | volume last 5 min 3x the daily average | down | -2.5 | 145 | +5.9 | flipped |
| 0 | previous window up | down | -2.2 | 1390 | -1.3 | same |
| 0 | previous window down | up | +2.2 | 1393 | +1.3 | same |
| 0 | MACD histogram positive | down | -1.5 | 1382 | -1.5 | same |
| 0 | MACD histogram negative | up | +1.5 | 1401 | +1.4 | same |
<!-- table:event_portfolio:end -->

Two results. First, **the reversal structure held in September**: 27 of the 29 stable events kept their direction in the forward month (the two that flipped were the weakest and the noisiest), and the rule that acts only on events with a 5-point deviation scored 55.1% on the 21% of September windows it selected, against 56.0% in-sample. Second, and this is the finding that matters for the forward log: the plain "act on every window, strongest event decides" rule scored 52.5% on all of September, while the frozen random forest scored 50.4% on the same windows. A rule with no fitted parameters carried the signal through a month where the fitted model did not. The likeliest reading is that the forest's September miss is model instability, not the signal disappearing; the next forward month will separate those. The September intervals are wide (590 windows for the strong-event rule), so none of this is settled.

**18. Patterns a person would not name: rules mined from a forest, and shapes of the recent path.** A random forest fit on the first five months is read leaf by leaf: each leaf is a rule of two to four conditions. Leaves with at least 300 training windows and a lift of three points become candidates and are scored on the last six months, which the forest never saw, with the same correction and stability check as the event library. Separately, the last 60 minutes before each open are scaled by their own volatility and clustered into 24 shapes on the first five months, and each shape is scored on the last six.

<!-- table:patterns:start -->
Rules mined from a random forest fit on 2025-10 to 2026-02, scored on 2026-03 to 2026-08 (never seen by the forest). Up-rate when the rule fires, day-block 95% interval, day-clustered p against the scoring period's base rate, false-discovery correction across all 423 candidate rules, and month-by-month stability (at least three quarters of months agreeing). Only rules that survive the correction are listed.

Of 423 candidates, 261 survive the correction and 248 are also stable month by month. The 25 stable rules with the largest deviation are listed; every candidate is in patterns_rules.csv.

| rule | fires | share | up-rate [95% CI] | vs base (points) | p | survives FDR | months agreeing | by month | verdict |
|---|---|---|---|---|---|---|---|---|---|
| bb_pctb > 0.623 and flow15 > 0.139 and rsi60 > 55.1 and size5 > 1.16 | 537 | 3.0% | 34.8% [31.2, 38.3] | -14.8 | 0.000 | yes | 6/6 | -14.0 -15.6 -13.8 -18.1 -15.1 -12.9 | stable |
| rsi60 > 56.2 and size5 > 1.03 and win1 > 9.29 | 663 | 3.8% | 35.9% [32.6, 39.1] | -13.7 | 0.000 | yes | 6/6 | -16.3 -10.5 -19.3 -13.0 -9.2 -14.8 | stable |
| flow5 > 0.0168 and rsi14 > 53.5 and rsi60 > 56 and size5 > 1.01 | 746 | 4.2% | 36.1% [32.7, 39.3] | -13.6 | 0.000 | yes | 6/6 | -17.6 -14.1 -13.1 -11.0 -13.1 -13.3 | stable |
| flow15 <= -0.149 and nratio5 > 0.946 and rsi60 <= 47.6 and size5 > 1.06 | 426 | 2.4% | 61.5% [56.7, 65.7] | +11.9 | 0.000 | yes | 6/6 | +13.6 +16.3 +12.8 +12.0 +6.2 +11.8 | stable |
| ema_cross > 2.11 and rsi60 > 55.9 and size5 > 1.01 | 927 | 5.2% | 38.1% [35.0, 41.0] | -11.6 | 0.000 | yes | 6/6 | -16.6 -11.7 -12.4 -9.3 -7.7 -11.3 | stable |
| flow15 <= 0.141 and ret60 <= -74.3 and size5 <= 1.96 | 561 | 3.2% | 60.8% [56.6, 65.3] | +11.1 | 0.000 | yes | 6/6 | +11.6 +9.3 +0.7 +13.1 +6.9 +23.2 | stable |
| rangepos > 0.93 and rsi60 > 56.4 and vol60 <= 6.99 | 584 | 3.3% | 39.0% [35.5, 42.7] | -10.6 | 0.000 | yes | 6/6 | -13.9 -9.5 -8.0 -9.5 -12.9 -10.6 | stable |
| flow1 > -0.365 and rsi60 > 55.9 and size5 > 0.988 | 976 | 5.5% | 39.0% [35.9, 42.0] | -10.6 | 0.000 | yes | 6/6 | -11.9 -13.2 -9.8 -10.2 -11.5 -7.7 | stable |
| flow3 <= -0.171 and rsi14 <= 54.1 and vratio15 > 0.635 and vwap_dev60 <= -28.1 | 442 | 2.5% | 60.2% [55.5, 64.7] | +10.5 | 0.000 | yes | 6/6 | +12.1 +13.9 +0.7 +10.6 +14.1 +6.9 | stable |
| flow3 > 0.341 and rangepos > 0.892 | 539 | 3.1% | 39.5% [35.8, 43.0] | -10.1 | 0.000 | yes | 6/6 | -9.1 -7.8 -5.1 -11.3 -14.6 -13.3 | stable |
| bb_pctb <= 0.626 and ret60 <= -38.3 and rsi14 <= 32.6 | 516 | 2.9% | 59.7% [55.3, 63.9] | +10.1 | 0.000 | yes | 6/6 | +6.9 +9.0 +2.9 +15.5 +14.4 +10.8 | stable |
| ret60 <= -37.2 and rsi14 <= 32.7 | 537 | 3.0% | 59.6% [55.3, 63.4] | +10.0 | 0.000 | yes | 6/6 | +7.4 +8.8 +2.8 +14.9 +13.7 +11.5 | stable |
| flow15 <= 0.157 and ret60 <= -36.6 and rsi14 <= 32.6 | 525 | 3.0% | 59.6% [55.4, 63.8] | +10.0 | 0.000 | yes | 6/6 | +8.1 +8.8 +2.2 +14.6 +12.8 +12.7 | stable |
| bb_pctb > 0.627 and flow15 > 0.153 and rsi60 > 54.8 and vratio5 > 1.06 | 689 | 3.9% | 39.6% [36.1, 43.1] | -10.0 | 0.000 | yes | 6/6 | -10.1 -12.9 -8.3 -9.6 -7.0 -11.9 | stable |
| rsi14 <= 36.8 and rsi60 <= 44.5 and vol240 > 3.7 | 871 | 4.9% | 59.6% [56.8, 62.5] | +10.0 | 0.000 | yes | 6/6 | +11.9 +6.0 +9.5 +10.5 +10.7 +11.4 | stable |
| ema_cross > 0.0295 and hour <= 6.5 and rsi60 > 55.9 | 655 | 3.7% | 39.7% [35.7, 43.5] | -9.9 | 0.000 | yes | 6/6 | -11.9 -19.2 -8.1 -13.6 -6.9 -3.2 | stable |
| flow3 > 0.00848 and flow60 > -0.0749 and rsi14 > 59.6 and size5 > 1.16 | 766 | 4.3% | 39.9% [36.6, 43.3] | -9.7 | 0.000 | yes | 6/6 | -12.4 -10.3 -12.4 -2.3 -9.1 -9.8 | stable |
| ema_cross > -2.17 and flow60 > 0.182 and rsi60 > 55.9 | 812 | 4.6% | 40.1% [36.7, 43.2] | -9.5 | 0.000 | yes | 6/6 | -14.2 -10.5 -10.0 -9.4 -8.3 -6.4 | stable |
| flow15 > 0.166 and obv_slope60 > 0.218 | 1224 | 6.9% | 40.1% [37.4, 42.7] | -9.5 | 0.000 | yes | 6/6 | -10.3 -5.7 -9.3 -15.4 -8.6 -9.4 | stable |
| adx14 > 34.1 and rangepos <= 0.892 and stoch14 <= 0.436 and vratio5 > 1.17 | 608 | 3.4% | 59.0% [55.3, 63.0] | +9.4 | 0.000 | yes | 6/6 | +9.3 +5.1 +1.6 +13.2 +15.4 +12.4 | stable |
| bb_pctb > 0.836 and rsi14 > 36.9 and rsi60 > 56.9 | 750 | 4.2% | 40.3% [37.0, 43.4] | -9.4 | 0.000 | yes | 6/6 | -14.4 -6.3 -8.0 -1.3 -14.6 -10.6 | stable |
| flow15 <= 0.134 and rsi60 <= 55.9 and vol15 > 8.81 and win4 <= -9.51 | 347 | 2.0% | 58.8% [53.7, 64.0] | +9.2 | 0.001 | yes | 3/3 | +12.6 - - +7.8 - +13.6 | stable |
| rangepos <= 0.133 and rsi14 <= 36.9 and vol240 > 3.62 | 623 | 3.5% | 58.6% [54.9, 62.2] | +9.0 | 0.000 | yes | 6/6 | +7.6 +9.7 +5.6 +12.4 +9.5 +7.4 | stable |
| rsi14 <= 33.9 and rsi60 <= 51.5 and win2 <= -3.14 | 880 | 5.0% | 58.4% [55.1, 61.5] | +8.8 | 0.000 | yes | 6/6 | +15.4 +2.7 +3.1 +10.1 +6.3 +13.2 | stable |
| ema_cross > -0.768 and flow15 > 0.16 and macd_hist > 0.185 and rsi60 > 55.9 | 869 | 4.9% | 41.0% [37.7, 44.1] | -8.7 | 0.000 | yes | 6/6 | -8.6 -9.0 -7.8 -6.9 -11.0 -8.8 | stable |

Shapes of the last 60 minutes before the open (24 clusters found on the search months, scored on the later months). Each shape is described by its cumulative path in standard-deviation units.

| shape | fires | share | up-rate [95% CI] | vs base (points) | p | survives FDR | months agreeing | by month | verdict |
|---|---|---|---|---|---|---|---|---|---|
| shape 6: net +1.6 sd; first quarter up, second flat, third up, last quarter down | 659 | 3.7% | 43.2% [39.6, 46.9] | -6.4 | 0.001 | yes | 6/6 | -4.4 -11.5 -8.2 -3.9 -7.4 -3.0 | stable |
| shape 20: net -2.6 sd; first quarter flat, second flat, third flat, last quarter down | 575 | 3.3% | 53.6% [49.9, 57.2] | +3.9 | 0.039 |  | 3/6 | -0.4 +14.6 +9.2 -5.3 +7.1 -0.3 |  |
| shape 10: net +0.6 sd; first quarter flat, second up, third flat, last quarter flat | 763 | 4.3% | 45.7% [41.9, 49.4] | -3.9 | 0.042 |  | 6/6 | -3.6 -2.8 -1.1 -3.3 -5.3 -7.6 |  |
| shape 19: net +2.0 sd; first quarter flat, second up, third flat, last quarter flat | 756 | 4.3% | 46.7% [43.4, 50.1] | -2.9 | 0.082 |  | 5/6 | -7.7 -8.0 +1.9 -0.7 -0.9 -1.3 |  |
| shape 16: net +2.0 sd; first quarter flat, second flat, third flat, last quarter up | 631 | 3.6% | 46.6% [42.9, 50.2] | -3.0 | 0.111 |  | 5/6 | -0.4 -7.2 -4.1 -7.4 +2.9 -3.0 |  |
| shape 4: net -1.1 sd; first quarter flat, second down, third flat, last quarter flat | 744 | 4.2% | 52.0% [48.7, 55.5] | +2.4 | 0.162 |  | 3/6 | -0.3 +7.5 -0.6 +9.5 +1.0 -2.0 |  |
| shape 21: net -2.5 sd; first quarter down, second flat, third flat, last quarter down | 798 | 4.5% | 51.6% [48.4, 54.9] | +2.0 | 0.238 |  | 4/6 | +4.9 -1.4 +4.4 +6.2 -7.5 +5.0 |  |
| shape 1: net -0.7 sd; first quarter down, second up, third flat, last quarter flat | 662 | 3.7% | 51.7% [48.1, 55.1] | +2.0 | 0.253 |  | 4/6 | +5.2 -0.5 +0.7 +2.4 -1.9 +5.9 |  |
| shape 12: net -2.3 sd; first quarter flat, second down, third flat, last quarter down | 741 | 4.2% | 51.7% [47.6, 55.6] | +2.1 | 0.297 |  | 4/6 | +5.9 +1.7 +7.6 -5.1 -0.5 +4.0 |  |
| shape 9: net +0.4 sd; first quarter up, second down, third flat, last quarter down | 658 | 3.7% | 51.5% [47.5, 55.5] | +1.9 | 0.352 |  | 4/6 | +8.0 -0.5 -2.2 +2.9 +2.4 +1.4 |  |
| shape 13: net -0.9 sd; first quarter up, second flat, third down, last quarter flat | 812 | 4.6% | 51.1% [47.6, 54.8] | +1.5 | 0.414 |  | 4/6 | +0.9 +1.5 -2.7 -0.3 +6.0 +2.3 |  |
| shape 7: net -0.4 sd; first quarter flat, second down, third down, last quarter up | 832 | 4.7% | 48.2% [44.8, 51.7] | -1.4 | 0.415 |  | 4/6 | -7.0 -1.0 -2.7 -6.3 +3.0 +5.6 |  |
| shape 3: net +1.4 sd; first quarter up, second down, third flat, last quarter flat | 705 | 4.0% | 48.4% [44.9, 52.1] | -1.3 | 0.490 |  | 4/6 | +9.2 -5.8 -7.1 +1.5 -4.2 -0.3 |  |
| shape 2: net +0.9 sd; first quarter flat, second up, third up, last quarter down | 797 | 4.5% | 48.6% [45.3, 51.8] | -1.1 | 0.516 |  | 4/6 | +1.1 -0.6 +0.7 -3.5 -3.1 -1.4 |  |
| shape 11: net -0.1 sd; first quarter flat, second up, third down, last quarter flat | 788 | 4.5% | 50.8% [47.4, 54.1] | +1.1 | 0.520 |  | 4/6 | -2.3 -0.6 +1.8 +0.9 +3.8 +2.3 |  |
| shape 18: net +1.9 sd; first quarter down, second up, third up, last quarter flat | 718 | 4.1% | 50.7% [47.2, 54.2] | +1.1 | 0.567 |  | 4/6 | +3.6 +7.1 +0.3 -6.1 -5.0 +3.8 |  |
| shape 14: net -2.8 sd; first quarter down, second down, third down, last quarter up | 789 | 4.5% | 48.7% [45.0, 52.6] | -1.0 | 0.601 |  | 3/6 | +0.8 -1.7 -9.8 -1.0 +6.2 +0.1 |  |
| shape 17: net +1.3 sd; first quarter up, second up, third down, last quarter down | 908 | 5.1% | 50.6% [47.0, 54.1] | +0.9 | 0.601 |  | 4/6 | -5.2 +2.1 +4.3 +5.3 +0.3 -2.8 |  |
| shape 22: net +1.8 sd; first quarter down, second up, third flat, last quarter up | 759 | 4.3% | 50.5% [46.5, 54.3] | +0.8 | 0.674 |  | 3/6 | -2.4 +5.1 +4.7 +3.8 -0.9 -3.5 |  |
| shape 0: net -0.7 sd; first quarter down, second down, third up, last quarter flat | 733 | 4.1% | 50.1% [46.8, 53.4] | +0.4 | 0.802 |  | 2/6 | -4.2 +5.6 -0.5 -5.6 +7.3 -3.5 |  |
| shape 5: net -1.3 sd; first quarter flat, second down, third flat, last quarter flat | 785 | 4.4% | 50.1% [46.3, 53.7] | +0.4 | 0.814 |  | 3/6 | +1.3 -1.3 -1.7 +5.4 +1.0 -1.4 |  |
| shape 15: net -1.3 sd; first quarter flat, second down, third up, last quarter flat | 662 | 3.7% | 50.0% [46.2, 53.6] | +0.4 | 0.849 |  | 3/6 | -1.0 -5.1 +3.0 +5.4 +0.8 -1.3 |  |
| shape 23: net +1.8 sd; first quarter down, second up, third up, last quarter flat | 763 | 4.3% | 49.8% [46.1, 53.4] | +0.2 | 0.928 |  | 2/6 | +3.9 +7.5 -3.1 -3.5 -3.9 -1.0 |  |
| shape 8: net -0.6 sd; first quarter down, second up, third flat, last quarter flat | 625 | 3.5% | 49.6% [45.7, 53.4] | -0.0 | 0.986 |  | 3/6 | -3.3 -7.2 +4.4 +5.2 +0.3 -0.3 |  |
<!-- table:patterns:end -->

The mined rules are sharper than any single event. Of 423 candidates, 261 survive the correction and 248 hold their direction month by month; the strongest, "price above its Bollinger midline, taker buying dominant, hour-RSI above 55 and trades larger than usual", is followed by an up window only 35% of the time on the 3% of windows it selects, and its mirror ("taker selling, hour-RSI below 48, trades larger than usual") by an up window 61.5% of the time. Half the stable rules mention the hour-RSI and more than half mention order flow: they are the reversal effect of study 16 sharpened by requiring two or three of its signs at once, which is what a forest is for. They come at a cost the table shows: each fires on 2% to 8% of windows, and 248 overlapping rules are not 248 independent chances.

The shapes found almost nothing. One of 24 survives and is stable (a path that rose, paused, rose again and fell in the last quarter, followed by fewer up windows), and it is the same "just went up" pattern in another costume. The shape of the last hour on its own carries less than the indicators built from it.

## What remains open

- The forward log is the arbiter. If the open-of-window accuracy stays near 50% for another two months, the backtest signal was regime-specific and the README will say so. The drift study makes that outcome more puzzling, not less: nothing in the eleven months suggested the signal decays.
- Tick-level flow was tested at 5 to 300 seconds before entry. The published quarter-hour result concerns horizons of hours, which this model does not target.
- Nothing here uses information from outside the exchange: funding rates, open interest, other venues, or the calendar of scheduled news. Those are the next inputs worth an ablation.

Reported accuracies of 80% or more for Bitcoin direction in the literature are almost always at daily or longer horizons, use overlapping labels, or leak information at decision time; a diagnostic study that toggles one evaluation convention at a time finds that centred features and same-day execution alone produce large, stable inflation. Nothing here should be compared with those numbers.

