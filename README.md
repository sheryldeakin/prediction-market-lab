# prediction-market-lab

Models, prediction logs and tracking tools for prediction markets. Each model lives in its own folder under `models/`, is evaluated walk-forward against honest baselines, and reports numbers that a script generated.

## Models

### BTC 15-minute direction (`models/btc_15m`)

Predicts whether Bitcoin closes a 15-minute window (aligned to the quarter hour) at or above where it opened. Data is free public 1-minute candles from Binance, including the taker-buy volume that gives a per-minute measure of order flow.

The question is asked at several points inside the window: at the open (minute 0, nothing of the window seen yet) and 1, 3, 5 and 8 minutes in. Later entries are easier because the current lead over the open is known, so every model is compared with a logistic regression that sees only that lead. A model that cannot beat the lead-only baseline has found nothing the current price does not already say.

Evaluation is walk-forward by calendar month: each test month is predicted by a model trained only on earlier months. The first three months are training only.

<!-- results:start -->
Walk-forward results, 2025-10 to 2026-08, test months after the first three.

| minute | model | n test | accuracy | AUC | log loss |
|---|---|---|---|---|---|
| 0 | majority | 23,327 | 50.14% | 0.494 | 0.6932 |
| 0 | xgb-price | 23,327 | 52.28% | 0.534 | 0.6924 |
| 0 | xgb-all | 23,327 | 52.54% | 0.536 | 0.6920 |
| 0 | xgb-all, label from 1 min in | 23,327 | 51.89% | 0.525 | 0.6936 |
| 1 | majority | 23,327 | 50.14% | 0.494 | 0.6932 |
| 1 | lead-only | 23,327 | 58.87% | 0.623 | 0.6727 |
| 1 | xgb-price | 23,327 | 59.15% | 0.629 | 0.6671 |
| 1 | xgb-all | 23,327 | 59.09% | 0.628 | 0.6674 |
| 3 | majority | 23,327 | 50.14% | 0.494 | 0.6932 |
| 3 | lead-only | 23,327 | 66.32% | 0.713 | 0.6304 |
| 3 | xgb-price | 23,327 | 66.22% | 0.718 | 0.6170 |
| 3 | xgb-all | 23,327 | 66.17% | 0.718 | 0.6172 |
| 5 | majority | 23,327 | 50.14% | 0.494 | 0.6932 |
| 5 | lead-only | 23,327 | 70.01% | 0.762 | 0.5916 |
| 5 | xgb-price | 23,327 | 69.90% | 0.773 | 0.5702 |
| 5 | xgb-all | 23,327 | 69.96% | 0.772 | 0.5707 |
| 8 | majority | 23,327 | 50.14% | 0.494 | 0.6932 |
| 8 | lead-only | 23,327 | 77.44% | 0.846 | 0.5008 |
| 8 | xgb-price | 23,327 | 77.32% | 0.856 | 0.4722 |
| 8 | xgb-all | 23,327 | 77.36% | 0.855 | 0.4733 |
<!-- results:end -->

What the table says:

- At the open there is a small, repeatable signal: about 52.5% against a 50.1% majority baseline, and above 50% in every one of the eight test months (`results/btc_15m/walk_forward_monthly.csv`).
- Part of that comes from the shared boundary price between back-to-back windows. Measuring the label from one minute after the open, which removes the shared price, leaves 51.9%.
- Once the window is under way, the current lead explains almost all of the accuracy. Gradient boosting improves the probabilities (lower log loss, from accounting for volatility) but not the direction calls.
- Minute-level order flow adds about a quarter of a point at the open and nothing later.

Full outputs: `results/btc_15m/` (walk-forward table, per-month accuracy, calibration deciles, feature importance).

## Setup

```
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
python -m models.btc_15m.data --start 2025-10 --end 2026-08     # downloads to data/ (gitignored)
python -m models.btc_15m.evaluate --start 2025-10 --end 2026-08
python -m pytest tests
```

## Rules this repo follows

- No number in a document is typed by hand. Tables come from `results/`, written by the evaluation scripts.
- Features are pure functions of past candles. `tests/test_features.py` tampers with future candles and asserts the features do not change.
- Every model is reported next to a baseline that uses the most obvious information available at the same moment.
- Data sources and what each was used for are listed in `docs/sources.md`.
