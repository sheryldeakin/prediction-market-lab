"""How much history to train on, and how often to retrain.

Two studies, walk-forward by month, XGBoost on price + flow + indicator features:

  window     for each test month, train on the last W months only (W = 2, 3, 4, 6)
             versus every earlier month (expanding). If recent months beat all
             months, the relationship is drifting.
  decay      for each target month, score the model retrained just before it and the
             models last retrained 1, 2 and 3 months earlier, all on the target month's
             windows. Paired differences against the fresh model say how fast a model
             goes stale. (An earlier version pooled each age over different target
             months, so an age effect was confounded with which months it was scored on.)

    python -m models.btc_15m.drift --start 2025-10 --end 2026-08 --minutes 0,3
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss

from models.btc_15m.data import load
from models.btc_15m.evaluate import make_model
from models.btc_15m.features import FLOW_FEATURES, PRICE_FEATURES, Series, dataset
from models.btc_15m.indicators import INDICATOR_FEATURES
from models.btc_15m.stats import block_bootstrap_ci, paired_difference_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
COLS = PRICE_FEATURES + FLOW_FEATURES + INDICATOR_FEATURES
MIN_TRAIN = 3


def training_months(months: list, test_month, window: int | None) -> list:
    """Months to train on for a given test month: the last `window` before it, or all."""
    earlier = [m for m in months if m < test_month]
    return earlier if window is None else earlier[-window:]


def window_study(D: pd.DataFrame, cols, kind="xgb", windows=(2, 3, 4, 6, None)):
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    months = sorted(month.unique())
    y = D.y.values
    out = {}
    for w in windows:
        pred = np.full(len(D), np.nan)
        for m in months[MIN_TRAIN:]:
            tr = month.isin(training_months(months, m, w)).values
            te = (month == m).values
            pred[te] = make_model(kind).fit(D.loc[tr, cols], y[tr]).predict_proba(D.loc[te, cols])[:, 1]
        keep = ~np.isnan(pred)
        out["expanding" if w is None else f"last {w} months"] = (pred[keep], y[keep], D.t.values[keep])
    return out


def decay_study(D: pd.DataFrame, cols, kind="xgb", horizon=4) -> pd.DataFrame:
    """One row per window of every target month that all ages can score: columns t,
    target, and hit_0 .. hit_{horizon-1}, where hit_a comes from a model trained on the
    months before target - a (so a = 0 is the fresh model). Every age is scored on the
    same rows. Each model needs MIN_TRAIN months of training data."""
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    months = sorted(month.unique())
    y = D.y.values
    models = {}
    for j in range(MIN_TRAIN, len(months)):
        tr = (month < months[j]).values
        models[j] = make_model(kind).fit(D.loc[tr, cols], y[tr])
    frames = []
    for i in range(MIN_TRAIN + horizon - 1, len(months)):
        te = (month == months[i]).values
        out = pd.DataFrame({"t": D.t.values[te], "target": str(months[i])})
        for age in range(horizon):
            p = models[i - age].predict_proba(D.loc[te, cols])[:, 1]
            out[f"hit_{age}"] = ((p > 0.5) == y[te]).astype(float)
        frames.append(out)
    return pd.concat(frames, ignore_index=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--minutes", default="0,3")
    a = ap.parse_args()
    s = Series(load(a.start, a.end))
    wrows, drows = [], []
    for k in [int(x) for x in a.minutes.split(",")]:
        D = dataset(s, k)
        res = window_study(D, COLS)
        base = ((res["expanding"][0] > 0.5) == res["expanding"][1]).astype(float)
        for name, (pred, y, t) in res.items():
            hits = ((pred > 0.5) == y).astype(float)
            m, lo, hi = block_bootstrap_ci(hits, t)
            if name == "expanding":
                vs = "baseline"
            else:
                d, dlo, dhi = paired_difference_ci(hits, base, t)
                vs = f"{d*100:+.2f} [{dlo*100:+.2f}, {dhi*100:+.2f}]"
            wrows.append([k, name, len(y), f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", f"{log_loss(y, np.clip(pred, 1e-6, 1-1e-6)):.4f}", vs])
            print(wrows[-1], flush=True)
        dec = decay_study(D, COLS)
        for age in range(4):
            h = dec[f"hit_{age}"].values
            m, lo, hi = block_bootstrap_ci(h, dec.t.values)
            if age == 0:
                vs = "reference"
            else:
                d, dlo, dhi = paired_difference_ci(h, dec.hit_0.values, dec.t.values)
                vs = f"{d*100:+.2f} [{dlo*100:+.2f}, {dhi*100:+.2f}]"
            drows.append([k, age, dec.target.nunique(), len(dec), f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", vs])
            print(drows[-1], flush=True)
    with open(OUT / "drift.md", "w") as f:
        f.write("Training window: for each test month, train on the last W months only or on every earlier month. XGBoost, price + flow + indicators, walk-forward. Last column: accuracy minus expanding on the same windows, day-block 95% interval.\n\n")
        f.write("| minute | training window | n | accuracy [95% CI] | log loss | vs expanding |\n|---|---|---|---|---|---|\n")
        for r in wrows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        f.write(f"\nRetrain frequency: on each target month ({dec.target.iloc[0]} to {dec.target.iloc[-1]}), the model retrained just before it and the models last retrained one, two and three months earlier, all scored on the same windows. Last column: accuracy minus the fresh model, day-block 95% interval.\n\n")
        f.write("| minute | months since retrain | target months | n | accuracy [95% CI] | vs fresh model |\n|---|---|---|---|---|---|\n")
        for r in drows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print("wrote drift.md")


if __name__ == "__main__":
    main()
