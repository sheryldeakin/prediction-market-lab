# prediction-market-lab

Models, prediction logs and tracking tools for prediction markets. Each model lives in its own folder under `models/`, is evaluated walk-forward against honest baselines, and reports numbers that a script generated.

## Models

### BTC 15-minute direction (`models/btc_15m`)

Predicts whether Bitcoin closes a 15-minute window (aligned to the quarter hour) at or above where it opened. Data is free public 1-minute candles from Binance, including the taker-buy volume that gives a per-minute measure of order flow.

The question is asked at several points inside the window: at the open (minute 0, nothing of the window seen yet) and 1, 3, 5 and 8 minutes in. Later entries are easier because the current lead over the open is known, so every model is compared with a logistic regression that sees only that lead. A model that cannot beat the lead-only baseline has found nothing the current price does not already say.

Evaluation is walk-forward by calendar month: each test month is predicted by a model trained only on earlier months. The first three months are training only.

#### Models compared

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

#### Results

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

![accuracy by entry minute](results/btc_15m/by_minute.png)

![accuracy at the open by test month](results/btc_15m/monthly_k0.png)

![calibration at the open](results/btc_15m/calibration_k0.png)

What the tables and charts say:

- At the open there is a small, repeatable signal in the backtest: about 53% against a 50.1% majority baseline, above 50% in every one of the eight test months. The 95% day-block bootstrap interval on the best model's gain over majority is +2.0 to +3.7 points, and a within-day label permutation test gives p = 0.002 (`results/btc_15m/checks.md`).
- The signal is simple. Logistic regression on the same features does as well as the tree models, so it is not an interaction the linear model misses.
- Part of it comes from the shared boundary price between back-to-back windows. Measuring the label from one minute after the open, which removes the shared price, leaves 51.9%.
- Once the window is under way, the current lead explains almost all of the accuracy. No model beats the lead-only baseline by more than half a point, and most intervals on the difference include zero. The tree models improve the probabilities (lower log loss, from accounting for volatility) but not the direction calls.
- Minute-level order flow adds about a quarter of a point at the open and nothing later.
- Predicted probabilities at the open are calibrated across deciles (chart above), so 0.55 means about 55%.

#### Forward log

The backtest above can be re-run and tuned; the forward log cannot. `models/btc_15m/log.py` freezes models trained through a cutoff month and scores every later window as Binance publishes its daily files, appending each window once to `results/btc_15m/predictions.csv`.

![forward log](results/btc_15m/forward_log.png)

<!-- forward:start -->
Trained through 2026-08, scored on 2026-09-01 to 2026-09-29.

| minute | model | windows | accuracy |
|---|---|---|---|
| 0 | forest | 2,783 | 50.41% |
| 3 | xgb-all | 2,783 | 66.69% |
<!-- forward:end -->

So far the open-of-window signal has not shown up in the forward period: 50.4% on September's 2,783 windows, against 53% in the backtest. One month is too little to call it dead (the backtest's worst month for that model was 51.6%), but it is the number to watch, and it is the reason the log exists. The minute-3 model is where the backtest said it would be.

#### Checks the numbers pass

- **No lookahead.** Features are pure functions of past candles. `tests/test_features.py` multiplies every candle from the entry minute onward by three and asserts the features do not change, at five different entry minutes.
- **Day-clustered uncertainty.** Windows in one day share conditions, so every interval resamples whole days and the permutation test shuffles labels within days. `tests/test_stats.py` checks that the bootstrap widens correctly when a day's windows are identical, and that a model which only knows each day's drift gets no credit.
- **Baselines at the same moment.** Every model is reported next to the strongest simple predictor available at that minute.
- **Shared-boundary check.** The label is re-measured from one minute in to see how much of the open-of-window signal is boundary noise.
- **Numbers come from scripts.** The tables in this file are spliced from `results/` by `scripts/update_readme.py`; the charts are drawn from the same CSVs.

#### Follow-up experiments

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

#### What remains open

- The forward log is the arbiter. If the open-of-window accuracy stays near 50% for another two months, the backtest signal was regime-specific and the README will say so.
- Tick-level flow was tested at 5 to 300 seconds before entry. The published quarter-hour result concerns horizons of hours, which this model does not target.
- Nothing here uses information from outside the exchange: funding rates, open interest, other venues, or the calendar of scheduled news. Those are the next inputs worth an ablation.

Reported accuracies of 80% or more for Bitcoin direction in the literature are almost always at daily or longer horizons, use overlapping labels, or leak information at decision time; a diagnostic study that toggles one evaluation convention at a time finds that centred features and same-day execution alone produce large, stable inflation. Nothing here should be compared with those numbers.

## Setup

```
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
python -m models.btc_15m.data --start 2025-10 --end 2026-08     # downloads to data/ (gitignored)
python -m models.btc_15m.evaluate --start 2025-10 --end 2026-08
python -m models.btc_15m.experiments --start 2025-10 --end 2026-08    # ablation, magnitude, cost, regime, cpcv
python -m models.btc_15m.ticks --start 2025-10 --end 2026-08          # optional: ~4 GB download, reduced to per-second files
python -m models.btc_15m.sequence --start 2025-10 --end 2026-08       # GRU; uses CUDA if available
python -m models.btc_15m.charts
python -m models.btc_15m.log --train-end 2026-08                 # extends the forward log
python scripts/update_readme.py
python -m pytest tests
```

## Rules this repo follows

- No number in a document is typed by hand. Tables come from `results/`, written by the evaluation scripts.
- Features are pure functions of past candles, and a test proves it.
- Every model is reported next to a baseline that uses the most obvious information available at the same moment.
- Uncertainty is computed at the day level, never per window.
- Data sources and what each was used for are listed in `docs/sources.md`.
