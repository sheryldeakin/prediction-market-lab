# prediction-market-lab

Models, prediction logs and tracking tools for prediction markets. Each model lives in its own folder under `models/`, is evaluated walk-forward against a one-feature baseline on the same windows, and reports numbers that a script generated.

## Models

| model | question | status | report |
|---|---|---|---|
| `models/btc_15m` | Does Bitcoin close a 15-minute window above where it opened? | a study of the boundary reversal; frozen models in a forward log from October 2026 | [docs/btc_15m.md](docs/btc_15m.md) |
| `models/btc_15m/horizons.py` | If a pattern holds now, which way does Bitcoin go over the next 1 to 30 minutes, and did that hold every year since 2018? | conditional tables across nine years; regimes and magnitude next | [docs/horizons.md](docs/horizons.md) |

### BTC 15-minute direction, in short

The question was whether machine learning on free Binance candles predicts the direction of a 15-minute window. The answer, after 30 studies and an outside review that forced the baselines and the statistics to be redone, is in two parts.

**There is a real effect, and it is one bit.** Consecutive 15-minute windows tend to go opposite ways. Calling the opposite of the previous window is right about 52% of the time, and that holds everywhere it was looked for: in the eleven study months, in nine earlier months no study had loaded, in September 2026 after the rules were frozen, on Coinbase and Bitstamp as well as Binance, under labels built from 60-second volume-weighted prices (so it is not noise in a shared boundary print), and at every one of the 15 ways of placing a 15-minute grid on the clock (so it is about any 15-minute boundary, not the quarter hour). A search over about 900 event rules finds the same reversal hundreds of times over against a null that finds nothing, and the rules kept their direction out of sample.

**The models add little beyond that bit, and what they add is not established.** With price and order-flow features the forest is about half a point above the one-bit rule in the backtest, with a day-level interval that includes zero; with a bank of technical indicators it is about a point above, with an interval that excludes zero on day blocks only. On the nine 2025 months the frozen forest is level with the rule. After the open, the lead over the open scaled by the volatility left in the window explains the accuracy, and no model beats it. Earlier versions of this README put the headline at 53% against a 50% majority baseline; against the right baseline the fitted models' contribution is the small, uncertain part, and the reversal is the finding.

<!-- table:headline:start -->
| where | one-bit rule | its accuracy | fitted model | its accuracy | model minus rule, points [day CI] | more |
|---|---|---|---|---|---|---|
| backtest 2025-10 to 2026-08, open | previous window reversed | 52.21% | forest (price + flow) | 52.65% | +0.44 [-0.25, +1.18] | [-0.30, +1.04], days better 54%, sign p 0.104 |
| backtest, open, richest feature set | previous window reversed | 52.21% | forest (price + flow + indicators) | 53.48% | +1.27 [+0.58, +1.95] | day-block interval only |
| backtest, minute 3 | lead z-score | 66.35% | xgb-all | 66.28% | -0.07 [-0.42, +0.27] | [-0.33, +0.21], days better 50%, sign p 0.649 |
| holdout 2025-01 to 2025-09, open (two declared runs; see the process log) | previous window reversed | 51.56% | forest (frozen forward model) | 51.64% | +0.08 [-0.58, +0.72] | days better 50%, p 0.3948 |
| holdout 2025-01 to 2025-09, open (two declared runs; see the process log) | previous window reversed | 51.56% | forest (price + flow + indicators) | 51.96% | +0.40 [-0.22, +1.02] | days better 54%, p 0.1129 |
| holdout September 2026, minute 0 (re-fitted frozen models) |  |  | forest | 50.94% |  | 2,880 windows; see the event rules row for the reversal in September |
| holdout September 2026, minute 3 (re-fitted frozen models) |  |  | xgb-all | 66.67% |  | 2,880 windows; see the event rules row for the reversal in September |
| backtest on Coinbase BTC-USD | previous window reversed | 51.95% | forest (price only) | 52.27% | +0.32 [-0.31, +0.98] | day-block interval |
| backtest on Bitstamp BTC-USD | previous window reversed | 52.06% | forest (price only) | 52.06% | -0.00 [-0.66, +0.70] | day-block interval |
| backtest, label from 60-second VWAPs inside the window (no shared prints) | previous window reversed (same label) | 52.54% | forest | 53.18% | +0.63 [-0.06, +1.37] | days better 53% |
| backtest, windows shifted 0 to 14 minutes off the quarter hour | previous window reversed | 51.31% to 52.67% | forest (price + flow) |  | -0.39 to +1.03 across the 15 offsets | an effect of any 15-minute boundary, not of the clock |
| event rules: stable survivors of the wide search | 745 real | null median 0, null maximum 147 |  |  |  | labels rotated within months, 200 runs |
| event rules: kept their direction in September 2026 | 562 of 666 | null median 330, 95th percentile 492 |  |  |  |  |
| event rules: kept their direction in 2025 | 737 of 745 |  |  |  |  | scored once |
<!-- table:headline:end -->

Every row above is read from a table a study wrote. The full tables, the 30 studies and what each one found: [docs/btc_15m.md](docs/btc_15m.md). Bugs found on the way, including fifteen from the review, and the decisions behind each study: [docs/process.md](docs/process.md).

![accuracy by entry minute](results/btc_15m/by_minute.png)

## How the work is done

- No number in a document is typed by hand. Tables come from `results/`, written by the evaluation scripts and spliced into the docs by `scripts/update_readme.py`; the README summary is built by `scripts/headline.py` from those tables.
- Features are pure functions of past candles, and a test proves it by tampering with future candles.
- Every model is reported next to a one-feature baseline on the same windows: the previous window's direction at the open, the lead z-score after it.
- Uncertainty respects time: intervals resample whole days and whole months, the model-against-baseline test uses daily differences with random sign flips, and the significance test rotates labels within months instead of shuffling them.
- The forward log is append-only with a hash chain (`python -m models.btc_15m.log --verify`) and a manifest of what the frozen models are. Windows scored under two model versions appear twice, labelled; nothing is overwritten.
- Bugs found along the way are recorded, not erased: [docs/process.md](docs/process.md). Data sources and what each was used for: [docs/sources.md](docs/sources.md).

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
python -m models.btc_15m.search_null                                 # the wide event search against a rotated-label null
python -m models.btc_15m.settlement                                  # labels from 60-second VWAPs (needs the tick files)
python -m models.btc_15m.boundary                                    # edge by minute and by phase offset
python -m models.btc_15m.venues                                      # Coinbase and Bitstamp candles download on first run
python -m models.btc_15m.holdout2025                                 # runs once; refuses a second run
python -m models.btc_15m.charts
python -m models.btc_15m.log --train-end 2026-08                 # extends the forward log
python scripts/headline.py && python scripts/update_readme.py
python -m pytest tests
python scripts/run_queue.py "python -m models.btc_15m.drift" "python -m models.btc_15m.meta"   # runs jobs when the machine is free
```

Heavy models run on the GPU when one is present (XGBoost, the sequence models). Host-side threads are capped at two per process so several studies can run without saturating the machine, and features are cached under `data/feature_cache/` after the first build.
