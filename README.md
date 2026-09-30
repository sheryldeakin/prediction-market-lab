# prediction-market-lab

Models, prediction logs and tracking tools for prediction markets. Each model lives in its own folder under `models/`, is evaluated walk-forward against honest baselines, and reports numbers that a script generated.

## Models

| model | question | status | report |
|---|---|---|---|
| `models/btc_15m` | Does Bitcoin close a 15-minute window above where it opened? | first version; forward log running since September 2026 | [docs/btc_15m.md](docs/btc_15m.md) |

### BTC 15-minute direction, in short

- **At the open** there is a small, repeatable signal in the backtest: about 53% against a 50.1% majority baseline, above 50% in all eight test months, confirmed by a second validation scheme, with day-clustered intervals and a permutation test behind it.
- **Once the window is under way**, the current lead explains almost all of the accuracy (66% at minute 3, 77% at minute 8). No model beats a logistic regression on the lead alone by more than half a point, and the direction of the remaining move is a coin flip.
- **What the signal is:** short-term reversal. Every stable chart event at the open points the same way: a recent rise (price at its 4-hour high, RSI above 70, a spike in the last five minutes) is followed by a down window more often than not, and the mirror holds. A break of a level is followed by a pull-back, not a continuation.
- **The forward log disagrees so far, for the fitted model.** Models frozen after August scored 50.4% at the open on September's 2,783 windows. But 27 of 29 stable chart events kept their direction in September, and a rule with no fitted parameters (act on the strongest event) scored 52.5% on the same windows, so the signal looks intact and the model's September miss looks like instability. One more month decides.
- Seventeen follow-up studies (feature ablations with an indicator bank and tick-level order flow, a GRU on the raw series, a magnitude label, regime splits, purged cross-validation, a cost score, four coins pooled with cross-asset features, honest hyperparameter search, training-window and retrain studies, triple-barrier labels with meta-labelling, ensembles and stacking, calibration, conformal abstention, adversarial validation, importance over time, an event-rule library and its September check) each moved the result by less than a point. The full tables and what each found: [docs/btc_15m.md](docs/btc_15m.md).

![accuracy by entry minute](results/btc_15m/by_minute.png)

## How the work is done

- No number in a document is typed by hand. Tables come from `results/`, written by the evaluation scripts and spliced into the docs by `scripts/update_readme.py`.
- Features are pure functions of past candles, and a test proves it by tampering with future candles.
- Every model is reported next to the strongest simple baseline available at the same moment.
- Uncertainty is computed at the day level, never per window.
- Bugs found along the way are recorded, not erased: [docs/process.md](docs/process.md).
- Data sources and what each was used for: [docs/sources.md](docs/sources.md).

## Setup

```
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
python -m models.btc_15m.data --start 2025-10 --end 2026-08     # downloads to data/ (gitignored)
python -m models.btc_15m.evaluate --start 2025-10 --end 2026-08
python -m models.btc_15m.experiments --start 2025-10 --end 2026-08    # ablation, magnitude, cost, regime, cpcv
python -m models.btc_15m.ticks --start 2025-10 --end 2026-08          # optional: ~4 GB download, reduced to per-second files
python -m models.btc_15m.sequence --start 2025-10 --end 2026-08       # GRU; uses CUDA if available
python -m models.btc_15m.multi_asset                                 # ETH, SOL, DOGE download on first run
python -m models.btc_15m.tuning --trials 30
python -m models.btc_15m.drift
python -m models.btc_15m.meta
python -m models.btc_15m.charts
python -m models.btc_15m.log --train-end 2026-08                 # extends the forward log
python scripts/update_readme.py
python -m pytest tests
python scripts/run_queue.py "python -m models.btc_15m.drift" "python -m models.btc_15m.meta"   # runs jobs when the machine is free
```

Heavy models run on the GPU when one is present (XGBoost, the GRU). Host-side threads are capped at two per process so several studies can run without saturating the machine, and features are cached under `data/feature_cache/` after the first build.

