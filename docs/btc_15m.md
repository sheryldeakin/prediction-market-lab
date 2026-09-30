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

## What remains open

- The forward log is the arbiter. If the open-of-window accuracy stays near 50% for another two months, the backtest signal was regime-specific and the README will say so. The drift study makes that outcome more puzzling, not less: nothing in the eleven months suggested the signal decays.
- Tick-level flow was tested at 5 to 300 seconds before entry. The published quarter-hour result concerns horizons of hours, which this model does not target.
- Nothing here uses information from outside the exchange: funding rates, open interest, other venues, or the calendar of scheduled news. Those are the next inputs worth an ablation.

Reported accuracies of 80% or more for Bitcoin direction in the literature are almost always at daily or longer horizons, use overlapping labels, or leak information at decision time; a diagnostic study that toggles one evaluation convention at a time finds that centred features and same-day execution alone produce large, stable inflation. Nothing here should be compared with those numbers.

