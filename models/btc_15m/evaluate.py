"""Walk-forward evaluation of the BTC 15-minute direction model.

For each entry minute k, every calendar month after the first three is a test month,
and the model is trained on all earlier months only. Predictors compared:

    majority       always predicts the more common class in the training data
    lead-only      logistic regression on the current lead alone (k > 0)
    logistic-all   logistic regression on all features (standardised)
    forest         random forest on all features
    hgb-all        histogram gradient boosting (scikit-learn) on all features
    xgb-price      XGBoost on price features
    xgb-all        XGBoost on price + order-flow features

Checks, all resampling or permuting whole days (models/btc_15m/stats.py):
    ci             95% block-bootstrap interval on each accuracy
    vs baseline    interval on accuracy minus the strongest simple baseline
                   (majority at k = 0, lead-only after)
    permutation    p-value for accuracy above chance, labels permuted within days
    boundary       k = 0 scored on a label measured from one minute after the open,
                   because back-to-back windows share one boundary price
    calibration    predicted-probability deciles vs the observed rate (xgb-all, k = 0)

Writes results/btc_15m/*.md and *.csv. Every number in the README comes from here.

    python -m models.btc_15m.evaluate --start 2025-10 --end 2026-08
"""
from __future__ import annotations

import argparse
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
from xgboost import XGBClassifier

from models.btc_15m.data import load
from models.btc_15m.features import FLOW_FEATURES, PRICE_FEATURES, Series, dataset
from models.btc_15m.stats import block_bootstrap_ci, paired_difference_ci, permutation_pvalue

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
ALL = PRICE_FEATURES + FLOW_FEATURES
N_JOBS = 2                      # CPU threads for the forest, XGBoost's host-side work and OpenMP pools
threadpool_limits(N_JOBS)       # caps BLAS/OpenMP (histogram gradient boosting, numpy) in this process


def _xgb_device():
    if os.environ.get("LAB_XGB_DEVICE"):          # "cpu" to keep off a GPU another program holds
        return os.environ["LAB_XGB_DEVICE"]
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


XGB_DEVICE = _xgb_device()


def make_model(kind: str):
    if kind == "logistic":
        return make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=1000))
    if kind == "forest":
        return RandomForestClassifier(n_estimators=300, min_samples_leaf=50, max_features=0.5, n_jobs=N_JOBS, random_state=0)
    if kind == "hgb":
        return HistGradientBoostingClassifier(max_depth=3, learning_rate=0.03, max_iter=400, l2_regularization=5, random_state=0)
    return XGBClassifier(n_estimators=400, max_depth=3, learning_rate=0.03, subsample=0.8,
                         colsample_bytree=0.8, min_child_weight=50, reg_lambda=5, verbosity=0,
                         tree_method="hist", device=XGB_DEVICE, n_jobs=N_JOBS)


def runs_for(k: int):
    r = [("majority", [], "majority")]
    if k > 0:
        r.append(("lead-only", ["lead"], "logistic"))
    r += [("logistic-all", ALL, "logistic"), ("forest", ALL, "forest"), ("hgb-all", ALL, "hgb"),
          ("xgb-price", PRICE_FEATURES, "xgb"), ("xgb-all", ALL, "xgb")]
    return r


def walk_forward(D: pd.DataFrame, cols: list[str], kind: str, label: str = "y"):
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    y = D[label].values
    pred = np.full(len(D), np.nan)
    for m in sorted(month.unique())[3:]:
        tr, te = (month < m).values, (month == m).values
        if kind == "majority":
            pred[te] = y[tr].mean()
        else:
            pred[te] = make_model(kind).fit(D.loc[tr, cols], y[tr]).predict_proba(D.loc[te, cols])[:, 1]
    keep = ~np.isnan(pred)
    return pred[keep], y[keep], month[keep], D.t.values[keep]


def score(pred, y):
    return {"accuracy": float(((pred > 0.5) == y).mean()), "auc": float(roc_auc_score(y, pred)),
            "log_loss": float(log_loss(y, np.clip(pred, 1e-6, 1 - 1e-6)))}


def format_p(p: float, n_perm: int) -> str:
    """A permutation p at its floor, 1 / (n_perm + 1), means no permutation reached the
    observed accuracy; the true p is somewhere below the floor, so say that."""
    floor = 1 / (n_perm + 1)
    return f"< {floor:.4f}" if p <= floor + 1e-12 else f"{p:.4f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--minutes", default="0,1,3,5,8")
    ap.add_argument("--n-perm", type=int, default=2000)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    s = Series(load(a.start, a.end))

    rows, monthly, checks = [], [], []
    for k in [int(x) for x in a.minutes.split(",")]:
        D = dataset(s, k)
        preds = {}
        for name, cols, kind in runs_for(k):
            pred, y, month, t = walk_forward(D, cols, kind)
            preds[name] = pred
            r = {"minute": k, "model": name, "n_test": len(y), **score(pred, y)}
            rows.append(r)
            for m in sorted(month.unique()):
                mm = (month == m).values
                monthly.append({"minute": k, "model": name, "month": str(m), "n": int(mm.sum()),
                                "accuracy": float(((pred[mm] > 0.5) == y[mm]).mean())})
            print(f"k={k:2d} {name:13s} n={len(y):6d} acc={r['accuracy']*100:6.2f}% auc={r['auc']:.3f} logloss={r['log_loss']:.4f}")
        base = "majority" if k == 0 else "lead-only"
        for name in preds:
            hits = ((preds[name] > 0.5) == y).astype(float)
            m_, lo, hi = block_bootstrap_ci(hits, t)
            row = {"minute": k, "model": name, "accuracy": m_, "ci_low": lo, "ci_high": hi}
            if name != base:
                bh = ((preds[base] > 0.5) == y).astype(float)
                d, dlo, dhi = paired_difference_ci(hits, bh, t)
                row.update({"vs": base, "diff": d, "diff_low": dlo, "diff_high": dhi})
            row["perm_p"] = permutation_pvalue(preds[name], y, t, n_perm=a.n_perm)[1]     # every model, so each p sits beside its own model
            checks.append(row)
        if k == 0:
            pred, y2, _, _ = walk_forward(D, ALL, "xgb", label="y_gap1")
            rows.append({"minute": 0, "model": "xgb-all, label from 1 min in", "n_test": len(y2), **score(pred, y2)})
            print(f"k= 0 boundary check (label measured 1 min after the open): acc={rows[-1]['accuracy']*100:.2f}%")
            pred = preds["xgb-all"]
            dec = pd.qcut(pred, 10, labels=False, duplicates="drop")
            pd.DataFrame({"decile": dec, "pred": pred, "y": y}).groupby("decile").agg(
                n=("y", "size"), predicted=("pred", "mean"), observed=("y", "mean")).reset_index().to_csv(OUT / "calibration_k0.csv", index=False)
            m = make_model("xgb").fit(D[ALL], D.y)
            pd.DataFrame({"feature": ALL, "importance": m.feature_importances_}).sort_values(
                "importance", ascending=False).to_csv(OUT / "importance_k0.csv", index=False)

    pd.DataFrame(rows).to_csv(OUT / "walk_forward.csv", index=False)
    pd.DataFrame(monthly).to_csv(OUT / "walk_forward_monthly.csv", index=False)
    C = pd.DataFrame(checks)
    C.to_csv(OUT / "checks.csv", index=False)
    with open(OUT / "walk_forward.md", "w") as f:
        f.write(f"Walk-forward results, {a.start} to {a.end}, test months after the first three.\n\n")
        f.write("| minute | model | n test | accuracy | AUC | log loss |\n|---|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['minute']} | {r['model']} | {r['n_test']:,} | {r['accuracy']*100:.2f}% | {r['auc']:.3f} | {r['log_loss']:.4f} |\n")
    with open(OUT / "checks.md", "w") as f:
        f.write(f"Day-block bootstrap (95%) and within-day permutation test ({a.n_perm:,} permutations; a p shown as below a value is at the test's floor, meaning no permutation reached the observed accuracy). "
                "Each p belongs to the model on its row. \"vs\" is accuracy minus the baseline named, on the same windows.\n\n")
        f.write("| minute | model | accuracy [95% CI] | vs baseline | permutation p |\n|---|---|---|---|---|\n")
        for _, r in C.iterrows():
            vs = f"{r['diff']*100:+.2f} [{r['diff_low']*100:+.2f}, {r['diff_high']*100:+.2f}] vs {r['vs']}" if isinstance(r.get("vs"), str) else "baseline"
            p = format_p(r["perm_p"], a.n_perm) if pd.notna(r.get("perm_p")) else ""
            f.write(f"| {int(r['minute'])} | {r['model']} | {r['accuracy']*100:.2f} [{r['ci_low']*100:.2f}, {r['ci_high']*100:.2f}] | {vs} | {p} |\n")
    print(f"wrote {OUT}/walk_forward.md and checks.md")


if __name__ == "__main__":
    main()
