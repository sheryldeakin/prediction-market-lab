"""Walk-forward evaluation of the BTC 15-minute direction model.

For each entry minute k, every calendar month after the first three is a test month,
and the model is trained on all earlier months only. Predictors compared:

    majority       always predicts the more common class in the training data
    prev-window    the previous window's direction as one bit (k = 0): the up-rate in the
                   training months after an up window and after a down window. With a
                   reversal effect it calls the opposite of the previous window.
    win1-logistic  logistic regression on the previous window's move in bp (k = 0)
    lead-only      logistic regression on the current lead alone (k > 0)
    lead-z         logistic regression on the lead divided by the volatility expected over
                   the remaining minutes, vol60 * sqrt(15 - k) (k > 0)
    logistic-all   logistic regression on all features (standardised)
    forest         random forest on all features
    hgb-all        histogram gradient boosting (scikit-learn) on all features
    xgb-price      XGBoost on price features
    xgb-all        XGBoost on price + order-flow features

Checks (models/btc_15m/stats.py), all keeping the serial dependence between windows:
    ci             95% intervals on each accuracy, resampling whole days and, separately,
                   whole months (with about eight test months the month interval is wide)
    vs baseline    accuracy minus the one-feature baseline for that minute (prev-window at
                   k = 0, lead-z after; see baseline_name), with day and month intervals
    day sign test  per-day accuracy minus the baseline's; share of days the model wins and
                   a sign-flip p for the mean daily difference
    circular shift p for accuracy above what the labels' own structure gives: the label
                   sequence is rotated within each month by a random offset
    (The within-day label permutation used before 2026-10-01 ignored dependence between
    neighbouring windows and was retired.)
    boundary       k = 0 scored on a label measured from one minute after the open,
                   because back-to-back windows share one boundary price
    calibration    predicted-probability deciles vs the observed rate (xgb-all, k = 0)

Writes results/btc_15m/*.md and *.csv. Every number in the README comes from here. Every entry
minute 0 to 14 is evaluated; walk_forward.md (the table the report splices) keeps the minutes in
walk_forward_by_minute.PUBLISHED_MINUTES, walk_forward_all.md has them all, and
walk_forward_by_minute.csv / .md put the minute's one-feature rule beside each fitted family.

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
from models.btc_15m.features import FLOW_FEATURES, PRICE_FEATURES, WINDOW, Series, dataset
from models.btc_15m.stats import block_bootstrap_ci, circular_shift_pvalue, day_sign_test, month_block_bootstrap_ci, paired_difference_ci
from models.btc_15m.walk_forward_by_minute import PUBLISHED_MINUTES, render_walk_forward, write_tables as write_by_minute_tables

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


def add_baseline_columns(D: pd.DataFrame, k: int) -> pd.DataFrame:
    """prev_up: the previous window closed at or above its open (the label's own rule).
    lead_z: the lead in units of the volatility expected over the remaining minutes."""
    D = D.copy()
    D["prev_up"] = (D.win1.values >= 0).astype(int)
    D["lead_z"] = D.lead.values / (D.vol60.values * np.sqrt(WINDOW - k) + 1e-9)
    return D


def baseline_name(k: int) -> str:
    return "prev-window" if k == 0 else "lead-z"


def baseline_walk_forward(D: pd.DataFrame, k: int, label: str = "y"):
    """Walk-forward predictions of the minute's one-feature baseline on D's windows."""
    name, cols, kind = next(r for r in runs_for(k) if r[0] == baseline_name(k))
    return walk_forward(add_baseline_columns(D, k), cols, kind, label)


def runs_for(k: int):
    r = [("majority", [], "majority")]
    if k == 0:
        r += [("prev-window", ["prev_up"], "bitrate"), ("win1-logistic", ["win1"], "logistic")]
    else:
        r += [("lead-only", ["lead"], "logistic"), ("lead-z", ["lead_z"], "logistic")]
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
        elif kind == "bitrate":                      # training up-rate for each value of one binary column
            x = D[cols[0]].values
            rates = {v: y[tr & (x == v)].mean() for v in (0, 1)}
            pred[te] = np.where(x[te] == 1, rates[1], rates[0])
        else:
            pred[te] = make_model(kind).fit(D.loc[tr, cols], y[tr]).predict_proba(D.loc[te, cols])[:, 1]
    keep = ~np.isnan(pred)
    return pred[keep], y[keep], month[keep], D.t.values[keep]


def score(pred, y):
    return {"accuracy": float(((pred > 0.5) == y).mean()), "auc": float(roc_auc_score(y, pred)),
            "log_loss": float(log_loss(y, np.clip(pred, 1e-6, 1 - 1e-6)))}


def format_p(p: float, n_perm: int) -> str:
    """A resampling p at its floor, 1 / (n_perm + 1), means no draw reached the observed
    statistic; the true p is somewhere below the floor, so say that."""
    floor = 1 / (n_perm + 1)
    return f"< {floor:.4f}" if p <= floor + 1e-12 else f"{p:.4f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--minutes", default=",".join(str(k) for k in range(WINDOW)), help="entry minutes to evaluate; the walk_forward.md the report splices keeps only PUBLISHED_MINUTES of them")
    ap.add_argument("--n-perm", type=int, default=2000, help="draws for the sign-flip and circular-shift tests")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    s = Series(load(a.start, a.end))

    rows, monthly, checks = [], [], []
    for k in [int(x) for x in a.minutes.split(",")]:
        D = add_baseline_columns(dataset(s, k), k)
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
        base = baseline_name(k)
        oof = pd.DataFrame({"t": t, "y": y, **{name: preds[name] for name in preds}})
        oof.to_parquet(OUT / f"oof_k{k}.parquet", index=False)                 # per-window predictions, for later analyses
        for name in preds:
            hits = ((preds[name] > 0.5) == y).astype(float)
            m_, lo, hi = block_bootstrap_ci(hits, t)
            _, mlo, mhi = month_block_bootstrap_ci(hits, t)
            row = {"minute": k, "model": name, "accuracy": m_, "ci_low": lo, "ci_high": hi, "ci_month_low": mlo, "ci_month_high": mhi}
            if name != base:
                bh = ((preds[base] > 0.5) == y).astype(float)
                d, dlo, dhi = paired_difference_ci(hits, bh, t)
                _, dmlo, dmhi = month_block_bootstrap_ci(hits - bh, t)
                sg = day_sign_test(hits, bh, t, n_draws=a.n_perm)
                row.update({"vs": base, "diff": d, "diff_low": dlo, "diff_high": dhi, "diff_month_low": dmlo, "diff_month_high": dmhi,
                            "days_better": sg["share_days_a_better"], "sign_p": sg["p"]})
            row["shift_p"] = circular_shift_pvalue(preds[name], y, t, n_draws=a.n_perm)[1]       # every model, so each p sits beside its own model
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
    R = pd.DataFrame(rows)
    (OUT / "walk_forward.md").write_text(render_walk_forward(R, a.start, a.end, PUBLISHED_MINUTES), encoding="utf-8")     # the table the report splices
    (OUT / "walk_forward_all.md").write_text(render_walk_forward(R, a.start, a.end), encoding="utf-8")
    write_by_minute_tables(OUT, a.start, a.end)
    with open(OUT / "checks.md", "w") as f:
        f.write("Accuracy with 95% intervals from resampling whole days and whole months; \"vs baseline\" is accuracy minus the one-feature baseline on the same windows (the previous window's direction at the open, the lead z-score after), with the same two intervals. "
                f"Day sign test: share of days on which the model beats the baseline, and a one-sided p for the mean daily difference under random sign flips. Circular shift: one-sided p for accuracy above what the labels' own structure gives, rotating the labels within each month. {a.n_perm:,} draws each; a p shown as below a value is at the test's floor. Each p belongs to the model on its row.\n\n")
        f.write("| minute | model | accuracy [day CI] [month CI] | vs baseline [day CI] [month CI] | days beating baseline | sign-test p | circular-shift p |\n|---|---|---|---|---|---|---|\n")
        for _, r in C.iterrows():
            acc = f"{r['accuracy']*100:.2f} [{r['ci_low']*100:.2f}, {r['ci_high']*100:.2f}] [{r['ci_month_low']*100:.2f}, {r['ci_month_high']*100:.2f}]"
            if isinstance(r.get("vs"), str):
                vs = f"{r['diff']*100:+.2f} [{r['diff_low']*100:+.2f}, {r['diff_high']*100:+.2f}] [{r['diff_month_low']*100:+.2f}, {r['diff_month_high']*100:+.2f}] vs {r['vs']}"
                days, sp = f"{r['days_better']*100:.0f}%", format_p(r["sign_p"], a.n_perm)
            else:
                vs, days, sp = "baseline", "", ""
            f.write(f"| {int(r['minute'])} | {r['model']} | {acc} | {vs} | {days} | {sp} | {format_p(r['shift_p'], a.n_perm)} |\n")
    print(f"wrote {OUT}/walk_forward.md and checks.md")


if __name__ == "__main__":
    main()
