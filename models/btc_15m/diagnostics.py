"""Diagnostics on the walk-forward predictions: calibration, abstention, drift and
feature importance. Pure functions at the top (tested); the runner at the bottom.

  calibration   Platt and isotonic recalibration fit on earlier months' out-of-fold
                probabilities only; Brier score split into reliability (calibration
                error) and resolution; expected calibration error by month
  conformal     split conformal prediction sets: the previous month calibrates a
                threshold, the current month gets a set {up}, {down} or {up, down};
                abstain when the set holds both. Reported: coverage (does the set
                contain the truth as often as promised) and accuracy on the windows
                where one class was issued
  adversarial   a classifier trained to tell a month's windows from all earlier
                months; its AUC measures distribution shift and its top features say
                what moved
  importance    permutation importance on each held-out month (accuracy drop when a
                feature is shuffled) and mean absolute SHAP from the booster, both
                tracked month by month

    python -m models.btc_15m.diagnostics --start 2025-10 --end 2026-08 --minutes 0,3
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

from models.btc_15m.data import load
from models.btc_15m.evaluate import XGB_DEVICE, N_JOBS, make_model
from models.btc_15m.features import FLOW_FEATURES, PRICE_FEATURES, Series, dataset
from models.btc_15m.indicators import INDICATOR_FEATURES

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
COLS = PRICE_FEATURES + FLOW_FEATURES + INDICATOR_FEATURES


# ---------------- pure functions ----------------

def brier_decomposition(p: np.ndarray, y: np.ndarray, bins: int = 10) -> dict:
    """Brier = reliability - resolution + uncertainty, binned on predicted probability."""
    p = np.clip(p, 0, 1)
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    base = y.mean()
    rel = res = 0.0
    for b in range(bins):
        m = idx == b
        if m.any():
            rel += m.mean() * (p[m].mean() - y[m].mean()) ** 2
            res += m.mean() * (y[m].mean() - base) ** 2
    unc = base * (1 - base)
    return {"brier": float(np.mean((p - y) ** 2)), "reliability": float(rel), "resolution": float(res), "uncertainty": float(unc)}


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    return float(sum((idx == b).mean() * abs(p[idx == b].mean() - y[idx == b].mean()) for b in range(bins) if (idx == b).any()))


def recalibrate(p_train, y_train, p_apply, method: str) -> np.ndarray:
    if method == "platt":
        z = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / np.clip(1 - p, 1e-6, 1)).reshape(-1, 1)
        return LogisticRegression(C=1e6).fit(z(p_train), y_train).predict_proba(z(p_apply))[:, 1]
    iso = IsotonicRegression(out_of_bounds="clip").fit(p_train, y_train)
    return iso.predict(p_apply)


def conformal_sets(p_cal, y_cal, p_new, alpha: float):
    """Split conformal for binary labels. Score = 1 - p(true class). Threshold = the
    (1-alpha) quantile of calibration scores (finite-sample corrected). A class is in the
    set when 1 - p(class) <= threshold. Returns (in_set_up, in_set_down) booleans."""
    n = len(y_cal)
    s = np.where(y_cal == 1, 1 - p_cal, p_cal)
    q = float(np.quantile(s, min(1.0, np.ceil((n + 1) * (1 - alpha)) / n), method="higher"))
    return (1 - p_new) <= q, p_new <= q


def permutation_importance(model, X: pd.DataFrame, y: np.ndarray, cols, seed=0) -> dict:
    rng = np.random.default_rng(seed)
    base = ((model.predict_proba(X[cols])[:, 1] > 0.5) == y).mean()
    out = {}
    for c in cols:
        Xp = X[cols].copy()
        Xp[c] = rng.permutation(Xp[c].values)
        out[c] = float(base - ((model.predict_proba(Xp)[:, 1] > 0.5) == y).mean())
    return out


# ---------------- runner ----------------

def month_index(D):
    return pd.to_datetime(D.t, unit="s").dt.to_period("M")


def oof_with_models(D, cols, kind="xgb"):
    month = month_index(D)
    months = sorted(month.unique())
    y = D.y.values
    p = np.full(len(D), np.nan)
    fitted = {}
    for m in months[3:]:
        tr, te = (month < m).values, (month == m).values
        model = make_model(kind).fit(D.loc[tr, cols], y[tr])
        fitted[m] = model
        p[te] = model.predict_proba(D.loc[te, cols])[:, 1]
    return p, fitted


def md(path, header, cols, rows):
    with open(path, "w") as f:
        f.write(header + "\n\n| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--minutes", default="0,3")
    a = ap.parse_args()
    s = Series(load(a.start, a.end))
    cal_rows, cal_month_rows, conf_rows, adv_rows, imp_rows = [], [], [], [], []
    for k in [int(x) for x in a.minutes.split(",")]:
        D = dataset(s, k)
        y, t = D.y.values, D.t.values
        month = month_index(D)
        months = sorted(month.unique())
        p, fitted = oof_with_models(D, COLS)
        have = ~np.isnan(p)

        # ---- calibration ----
        variants = {"raw": p.copy(), "platt": np.full(len(p), np.nan), "isotonic": np.full(len(p), np.nan)}
        for m in months[4:]:
            tr = have & (month < m).values
            te = (month == m).values
            for meth in ("platt", "isotonic"):
                variants[meth][te] = recalibrate(p[tr], y[tr], p[te], meth)
        common = ~np.isnan(variants["isotonic"])
        for name, v in variants.items():
            d = brier_decomposition(v[common], y[common])
            cal_rows.append([k, name, int(common.sum()), f"{d['brier']:.4f}", f"{d['reliability']:.5f}", f"{d['resolution']:.5f}", f"{ece(v[common], y[common])*100:.2f}%"])
            print(cal_rows[-1], flush=True)
        for m in months[3:]:
            te = (month == m).values
            cal_month_rows.append([k, str(m), int(te.sum()), f"{ece(p[te], y[te])*100:.2f}%", f"{p[te].mean()*100:.1f}%", f"{y[te].mean()*100:.1f}%"])

        # ---- conformal ----
        for alpha in (0.10, 0.20, 0.30, 0.40):
            cov, issued, right = [], 0, 0
            n_total = 0
            for i in range(4, len(months)):
                cal, te = (month == months[i - 1]).values, (month == months[i]).values
                up, down = conformal_sets(p[cal], y[cal], p[te], alpha)
                truth_in = np.where(y[te] == 1, up, down)
                cov.append(truth_in.mean())
                single = up ^ down
                issued += int(single.sum())
                right += int(((up & (y[te] == 1)) | (down & (y[te] == 0)))[single].sum())
                n_total += int(te.sum())
            conf_rows.append([k, f"{1-alpha:.0%}", n_total, f"{np.mean(cov)*100:.1f}%", f"{100*issued/n_total:.1f}%", f"{100*right/issued:.2f}%" if issued else "no single-class sets"])
            print(conf_rows[-1], flush=True)

        # ---- adversarial validation ----
        for m in months[3:]:
            te = (month == m).values
            earlier = (month < m).values
            X = pd.concat([D.loc[earlier, COLS], D.loc[te, COLS]])
            z = np.r_[np.zeros(earlier.sum()), np.ones(te.sum())]
            rng = np.random.default_rng(0)
            idx = rng.permutation(len(z))
            half = len(z) // 2
            clf = XGBClassifier(n_estimators=200, max_depth=3, learning_rate=0.05, verbosity=0, tree_method="hist", device=XGB_DEVICE, n_jobs=N_JOBS)
            clf.fit(X.iloc[idx[:half]], z[idx[:half]])
            auc = roc_auc_score(z[idx[half:]], clf.predict_proba(X.iloc[idx[half:]])[:, 1])
            top = sorted(zip(clf.feature_importances_, COLS), reverse=True)[:3]
            adv_rows.append([k, str(m), f"{auc:.3f}", ", ".join(n for _, n in top)])
            print(adv_rows[-1], flush=True)

        # ---- importance over time ----
        for m in months[3:]:
            te = (month == m).values
            pi = permutation_importance(fitted[m], D[te], y[te], COLS)
            top_pi = sorted(pi.items(), key=lambda x: -x[1])[:5]
            booster = fitted[m].get_booster()
            import xgboost as xgb
            contrib = booster.predict(xgb.DMatrix(D.loc[te, COLS]), pred_contribs=True)[:, :-1]
            shap = dict(zip(COLS, np.abs(contrib).mean(axis=0)))
            top_shap = sorted(shap.items(), key=lambda x: -x[1])[:5]
            imp_rows.append([k, str(m), ", ".join(f"{n} {v*100:+.2f}" for n, v in top_pi), ", ".join(f"{n} {v:.3f}" for n, v in top_shap)])
            print(imp_rows[-1], flush=True)

    md(OUT / "calibration.md", "Calibration of the XGBoost probabilities (price + flow + indicators), walk-forward. Platt and isotonic recalibration are fit on earlier months' out-of-fold probabilities only. Brier = reliability - resolution + uncertainty; lower reliability is better calibration, higher resolution is more information. ECE is the expected calibration error over ten bins.",
       ["minute", "probabilities", "n", "Brier", "reliability", "resolution", "ECE"], cal_rows)
    with open(OUT / "calibration.md", "a") as f:
        f.write("\nReliability by month (raw probabilities): ECE, mean predicted, observed rate of up.\n\n| minute | month | n | ECE | mean predicted | observed |\n|---|---|---|---|---|---|\n")
        for r in cal_month_rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    md(OUT / "conformal.md", "Split conformal prediction sets: the previous month calibrates the threshold, the current month is scored. Coverage is how often the set contains the truth (should be at least the target). A single-class set is a call; a two-class set is an abstention.",
       ["minute", "target coverage", "n", "coverage", "share with a single-class set", "accuracy when a call is made"], conf_rows)
    md(OUT / "adversarial.md", "Adversarial validation: a classifier trained to tell a test month's windows from all earlier months, scored on a held-out half. AUC 0.5 means the month is indistinguishable; higher means the feature distribution moved, and the top features say where.",
       ["minute", "month", "AUC", "top features"], adv_rows)
    md(OUT / "importance.md", "Feature importance on each held-out month. Permutation importance is the accuracy drop (points) when the feature is shuffled; SHAP is the mean absolute contribution from the booster. Top five of each.",
       ["minute", "month", "permutation importance (points)", "mean |SHAP|"], imp_rows)
    print("wrote calibration.md, conformal.md, adversarial.md, importance.md")


if __name__ == "__main__":
    main()
