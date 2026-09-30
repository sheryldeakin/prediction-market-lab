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
| forest | random forest, 300 trees, leaves of 50+ windows | all 24 |
| hgb-all | histogram gradient boosting (scikit-learn) | all 24 |
| xgb-price | XGBoost, depth 3 | 15 price features |
| xgb-all | XGBoost, depth 3 | 15 price + 9 order-flow features |

Price features: lead over the open, returns over the prior 5/15/60/240 minutes, the last four windows' returns, realised volatility at three horizons, position in the 4-hour range, hour and weekday. Order-flow features: taker-buy share of volume over 1/3/5/15/60 minutes, volume and trade-count ratios to the 24-hour average, mean trade size ratio.

#### Results

<!-- results:start -->
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
<!-- results:end -->

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

#### What to test next

In rough order of how much they could add, with the reason each is worth the time:

1. **Tick-level order flow.** The candle-level taker-buy share adds little. Trade-by-trade data (Binance aggTrades, about 358 MB per month) allows order-flow imbalance over the seconds before the open, and published work on Binance futures reports that imbalance at quarter-hour openings carries predictive information (see sources). This is the one input the current features cannot express.
2. **Sequence models on the raw minute series.** A small temporal convolutional network or GRU over the last 60 to 240 one-minute returns and flows, compared against the same baselines. The published comparisons that favour recurrent networks mostly use longer horizons and technical indicators; the honest question here is whether a sequence model beats hand-built features on a 15-minute label, and that has to be shown, not assumed.
3. **Volatility-scaled labels.** Instead of up or down, predict whether the move exceeds a threshold that matters (for example, larger than the typical bid-ask cost). This reframes the problem from direction to "is this window worth acting on".
4. **Regime features.** Realised volatility and volume already appear as inputs; a next step is to evaluate accuracy by regime (quiet vs active hours, trending vs ranging days) to see where the small signal lives.
5. **Combinatorial purged cross-validation** as a second estimate next to walk-forward, with an embargo of 4 hours (the longest feature lookback). The two should agree; if they do not, that is a finding.
6. **A cost-aware score.** Expected value per window at a stated fee and spread, so that a 53% model can be read as "worth it" or "not" without a separate calculation.

Reported accuracies of 80% or more for Bitcoin direction in the literature are almost always at daily or longer horizons, use overlapping labels, or leak information at decision time; a diagnostic study that toggles one evaluation convention at a time finds that centred features and same-day execution alone produce large, stable inflation. Nothing here should be compared with those numbers.

## Setup

```
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
python -m models.btc_15m.data --start 2025-10 --end 2026-08     # downloads to data/ (gitignored)
python -m models.btc_15m.evaluate --start 2025-10 --end 2026-08
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
