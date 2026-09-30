"""Walk-forward evaluation of the BTC 15-minute direction model.

For each entry minute k, every calendar month after the first three is a test month,
and the model is trained on all earlier months only. Four predictors are compared:

    majority      always predicts the more common class in the training data
    lead-only     logistic regression on the current lead alone (k > 0)
    xgb-price     gradient boosting on price features
    xgb-all       gradient boosting on price + order-flow features

Two extra checks:
    boundary      k = 0 scored on a label measured from one minute after the open,
                  because back-to-back windows share one boundary price and noise in
                  it can fake predictability
    calibration   predicted-probability deciles vs the observed rate (xgb-all, k = 0)

Writes results/btc_15m/*.md and *.csv. Every number in the README comes from here.

    python -m models.btc_15m.evaluate --start 2025-10 --end 2026-08
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from xgboost import XGBClassifier

from models.btc_15m.data import load
from models.btc_15m.features import FLOW_FEATURES, PRICE_FEATURES, Series, dataset

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")


def xgb():
    return XGBClassifier(n_estimators=400, max_depth=3, learning_rate=0.03, subsample=0.8,
                         colsample_bytree=0.8, min_child_weight=50, reg_lambda=5, verbosity=0)


def walk_forward(D: pd.DataFrame, cols: list[str], kind: str, label: str = "y"):
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    y = D[label].values
    pred = np.full(len(D), np.nan)
    for m in sorted(month.unique())[3:]:
        tr, te = (month < m).values, (month == m).values
        if kind == "majority":
            pred[te] = y[tr].mean()
        elif kind == "logistic":
            pred[te] = LogisticRegression(max_iter=500).fit(D.loc[tr, cols], y[tr]).predict_proba(D.loc[te, cols])[:, 1]
        else:
            pred[te] = xgb().fit(D.loc[tr, cols], y[tr]).predict_proba(D.loc[te, cols])[:, 1]
    keep = ~np.isnan(pred)
    return pred[keep], y[keep], month[keep]


def score(pred, y):
    return {"accuracy": float(((pred > 0.5) == y).mean()), "auc": float(roc_auc_score(y, pred)),
            "log_loss": float(log_loss(y, np.clip(pred, 1e-6, 1 - 1e-6)))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--minutes", default="0,1,3,5,8")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    s = Series(load(a.start, a.end))

    rows, monthly = [], []
    for k in [int(x) for x in a.minutes.split(",")]:
        D = dataset(s, k)
        runs = [("majority", [], "majority"), ("xgb-price", PRICE_FEATURES, "xgb"), ("xgb-all", PRICE_FEATURES + FLOW_FEATURES, "xgb")]
        if k > 0:
            runs.insert(1, ("lead-only", ["lead"], "logistic"))
        for name, cols, kind in runs:
            pred, y, month = walk_forward(D, cols, kind)
            r = {"minute": k, "model": name, "n_test": len(y), **score(pred, y)}
            rows.append(r)
            for m in sorted(month.unique()):
                mm = (month == m).values
                monthly.append({"minute": k, "model": name, "month": str(m), "n": int(mm.sum()),
                                "accuracy": float(((pred[mm] > 0.5) == y[mm]).mean())})
            print(f"k={k:2d} {name:10s} n={len(y):6d} acc={r['accuracy']*100:6.2f}% auc={r['auc']:.3f} logloss={r['log_loss']:.4f}")
        if k == 0:
            pred, y, _ = walk_forward(D, PRICE_FEATURES + FLOW_FEATURES, "xgb", label="y_gap1")
            rows.append({"minute": 0, "model": "xgb-all, label from 1 min in", "n_test": len(y), **score(pred, y)})
            print(f"k= 0 boundary check (label measured 1 min after the open): acc={rows[-1]['accuracy']*100:.2f}%")
            pred, y, _ = walk_forward(D, PRICE_FEATURES + FLOW_FEATURES, "xgb")
            dec = pd.qcut(pred, 10, labels=False, duplicates="drop")
            cal = pd.DataFrame({"decile": dec, "pred": pred, "y": y}).groupby("decile").agg(
                n=("y", "size"), predicted=("pred", "mean"), observed=("y", "mean")).reset_index()
            cal.to_csv(OUT / "calibration_k0.csv", index=False)
            m = xgb().fit(D[PRICE_FEATURES + FLOW_FEATURES], D.y)
            imp = pd.DataFrame({"feature": PRICE_FEATURES + FLOW_FEATURES, "importance": m.feature_importances_}
                               ).sort_values("importance", ascending=False)
            imp.to_csv(OUT / "importance_k0.csv", index=False)

    res = pd.DataFrame(rows)
    res.to_csv(OUT / "walk_forward.csv", index=False)
    pd.DataFrame(monthly).to_csv(OUT / "walk_forward_monthly.csv", index=False)
    with open(OUT / "walk_forward.md", "w") as f:
        f.write(f"Walk-forward results, {a.start} to {a.end}, test months after the first three.\n\n")
        f.write("| minute | model | n test | accuracy | AUC | log loss |\n|---|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['minute']} | {r['model']} | {r['n_test']:,} | {r['accuracy']*100:.2f}% | {r['auc']:.3f} | {r['log_loss']:.4f} |\n")
    print(f"wrote {OUT}/walk_forward.md")


if __name__ == "__main__":
    main()
