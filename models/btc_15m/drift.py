"""How much history to train on, and how often to retrain.

Two studies, walk-forward by month, XGBoost on price + flow + indicator features:

  window     for each test month, train on the last W months only (W = 2, 3, 4, 6)
             versus every earlier month (expanding). If recent months beat all
             months, the relationship is drifting.
  decay      train once at the start of month m and keep the model for m, m+1, m+2,
             m+3 without retraining. Accuracy by months since the last retrain, pooled
             over every start month, says how fast a model goes stale.

    python -m models.btc_15m.drift --start 2025-10 --end 2026-08 --minutes 0,3
"""
from __future__ import annotations

import argparse
import warnings
from collections import defaultdict
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


def decay_study(D: pd.DataFrame, cols, kind="xgb", horizon=4):
    """Returns per-window hits keyed by months since retrain, pooled over start months."""
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    months = sorted(month.unique())
    y = D.y.values
    hits = defaultdict(list)
    for i, m in enumerate(months[MIN_TRAIN:], start=MIN_TRAIN):
        tr = (month < m).values
        model = make_model(kind).fit(D.loc[tr, cols], y[tr])
        for age in range(horizon):
            if i + age >= len(months):
                break
            te = (month == months[i + age]).values
            p = model.predict_proba(D.loc[te, cols])[:, 1]
            hits[age].append(pd.DataFrame({"t": D.t.values[te], "hit": ((p > 0.5) == y[te]).astype(float), "start": str(m)}))
    return {age: pd.concat(v, ignore_index=True) for age, v in hits.items()}


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
        for age, df in sorted(dec.items()):
            m, lo, hi = block_bootstrap_ci(df.hit.values, df.t.values)
            drows.append([k, age, df.start.nunique(), len(df), f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]"])
            print(drows[-1], flush=True)
    with open(OUT / "drift.md", "w") as f:
        f.write("Training window: for each test month, train on the last W months only or on every earlier month. XGBoost, price + flow + indicators, walk-forward. Last column: accuracy minus expanding on the same windows, day-block 95% interval.\n\n")
        f.write("| minute | training window | n | accuracy [95% CI] | log loss | vs expanding |\n|---|---|---|---|---|---|\n")
        for r in wrows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        f.write("\nRetrain frequency: a model trained at the start of a month and kept without retraining. Accuracy by months since the last retrain, pooled over all start months (later ages have fewer start months).\n\n")
        f.write("| minute | months since retrain | start months | n | accuracy [95% CI] |\n|---|---|---|---|---|\n")
        for r in drows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print("wrote drift.md")


if __name__ == "__main__":
    main()
