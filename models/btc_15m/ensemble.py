"""Ensembles and stacking.

Base models (logistic-all, forest, hgb-all, xgb-all) produce out-of-fold probabilities
month by month, as in evaluate.py. Then:

  average     the mean of the four probabilities
  stacking    logistic regression on the four out-of-fold probabilities, trained only on
              months whose base predictions were themselves out of fold and earlier than
              the month being scored, so the stacker never sees a base prediction that
              was fit on the same month

Both are compared with the best single base model on the same windows, with day-block
intervals. Read-only; writes results/btc_15m/ensemble.md.

    python -m models.btc_15m.ensemble --start 2025-10 --end 2026-08 --minutes 0,3
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score

from models.btc_15m.data import load
from models.btc_15m.evaluate import baseline_name, baseline_walk_forward, make_model
from models.btc_15m.features import FLOW_FEATURES, PRICE_FEATURES, Series, dataset
from models.btc_15m.indicators import INDICATOR_FEATURES
from models.btc_15m.stats import block_bootstrap_ci, paired_difference_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
COLS = PRICE_FEATURES + FLOW_FEATURES + INDICATOR_FEATURES
BASES = [("logistic-all", "logistic"), ("forest", "forest"), ("hgb-all", "hgb"), ("xgb-all", "xgb")]


def oof(D: pd.DataFrame, cols, kind: str) -> np.ndarray:
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    y = D.y.values
    p = np.full(len(D), np.nan)
    for m in sorted(month.unique())[3:]:
        tr, te = (month < m).values, (month == m).values
        p[te] = make_model(kind).fit(D.loc[tr, cols], y[tr]).predict_proba(D.loc[te, cols])[:, 1]
    return p


def stack(P: np.ndarray, y: np.ndarray, t: np.ndarray) -> np.ndarray:
    """P: (n, k) out-of-fold base probabilities (nan before the fourth month).
    For each month, fit a logistic stacker on all earlier rows that have base predictions."""
    month = pd.to_datetime(t, unit="s").to_period("M")
    have = ~np.isnan(P).any(axis=1)
    out = np.full(len(y), np.nan)
    X = np.log(np.clip(P, 1e-6, 1 - 1e-6) / np.clip(1 - P, 1e-6, 1))     # logits
    for m in sorted(set(month[have])):
        tr = have & np.asarray(month < m)
        te = have & np.asarray(month == m)
        if tr.sum() < 500:
            continue
        out[te] = LogisticRegression(C=1.0, max_iter=500).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--minutes", default="0,3")
    a = ap.parse_args()
    s = Series(load(a.start, a.end))
    rows = []
    for k in [int(x) for x in a.minutes.split(",")]:
        D = dataset(s, k)
        y, t = D.y.values, D.t.values
        P = np.column_stack([oof(D, COLS, kind) for _, kind in BASES])
        preds = {name: P[:, i] for i, (name, _) in enumerate(BASES)}
        preds["average"] = P.mean(axis=1)
        preds["stacking"] = stack(P, y, t)
        bname = baseline_name(k)
        bp, _, _, bt = baseline_walk_forward(D, k)
        preds[bname] = pd.Series(bp, index=bt).reindex(t).values
        keep = ~np.isnan(preds["stacking"])                      # common scoring set: months where every variant exists
        hits = {n: ((p[keep] > 0.5) == y[keep]).astype(float) for n, p in preds.items()}
        best = max((n for n, _ in BASES), key=lambda n: hits[n].mean())
        for n, p in preds.items():
            m, lo, hi = block_bootstrap_ci(hits[n], t[keep])
            if n == best:
                vs = "best single"
            else:
                d, dlo, dhi = paired_difference_ci(hits[n], hits[best], t[keep])
                vs = f"{d*100:+.2f} [{dlo*100:+.2f}, {dhi*100:+.2f}] vs {best}"
            if n == bname:
                vb = "baseline"
            else:
                d, dlo, dhi = paired_difference_ci(hits[n], hits[bname], t[keep])
                vb = f"{d*100:+.2f} [{dlo*100:+.2f}, {dhi*100:+.2f}]"
            rows.append([k, n, int(keep.sum()), f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", f"{roc_auc_score(y[keep], p[keep]):.3f}",
                         f"{log_loss(y[keep], np.clip(p[keep], 1e-6, 1-1e-6)):.4f}", vs, vb])
            print(rows[-1], flush=True)
    with open(OUT / "ensemble.md", "w") as f:
        f.write("Ensembles: the mean of four base models' out-of-fold probabilities, and a logistic stacker fit on earlier months' out-of-fold probabilities only. Scored on the months where every variant exists (the stacker needs one month of base predictions to start). The last two columns are accuracy minus the best single base model and minus the one-feature baseline (the previous window at the open, the lead z-score after), on the same windows, day-block 95% intervals.\n\n")
        f.write("| minute | model | n | accuracy [95% CI] | AUC | log loss | vs best single | vs one-feature baseline |\n|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print("wrote ensemble.md")


if __name__ == "__main__":
    main()
