"""Hidden Markov models as predictors, in the 15-minute window framework.

Two rows for the model comparison, both walk-forward by month against the one-feature
baseline on the same windows (evaluate.baseline_name):

  hmm-state     a Gaussian HMM with N_STATES states on the minute series (return in bp,
                log volume ratio to the trailing day, taker-buy share), fit on the training
                months. For each window the filtered state probabilities at the last closed
                minute (forward pass only) are combined with each state's up-rate in the
                training windows: P(up) = sum_s p_s * q_s. Also scored on the magnitude
                label (the window moves at least 10 bp), where volatility states should
                help.
  ms-baseline   a Markov-switching version of the one-feature baseline: a logistic
                regression of the label on the baseline feature fit separately in each
                state (training windows assigned to their most likely state), predictions
                mixed by the filtered state probabilities. The per-state coefficients say
                whether the reversal is stronger in some states.

    python -m models.btc_15m.hmm_models --start 2025-10 --end 2026-08 --minutes 0,3
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score

from models.btc_15m.data import load
from models.btc_15m.evaluate import add_baseline_columns, baseline_name, walk_forward
from models.btc_15m.features import Series, dataset
from models.btc_15m.regimes import forward_filter
from models.btc_15m.stats import block_bootstrap_ci, day_sign_test, paired_difference_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
N_STATES = 3
MAG_BP = 10.0


def minute_matrix(s: Series) -> np.ndarray:
    """Per-minute observations: return (bp), log volume ratio to the trailing 1440 minutes, taker share."""
    v = s.v
    cs = np.concatenate([[0.0], np.cumsum(v)])
    trail = np.full(len(v), np.nan)
    trail[1440:] = (cs[1440:-1] - cs[:-1441]) / 1440
    vr = np.log((v + 1e-9) / (trail + 1e-9))
    share = np.where(v > 0, s._raw[1] / np.maximum(v, 1e-9), 0.5)
    X = np.column_stack([s.r1, vr, 2 * share - 1])
    X[:1440] = 0.0
    return X


def state_probs(X: np.ndarray, fit_mask: np.ndarray, n_states=N_STATES, seed=0) -> tuple[np.ndarray, GaussianHMM]:
    """Fit on the rows in fit_mask (standardised there), filter forward over all rows."""
    mu, sd = X[fit_mask].mean(0), X[fit_mask].std(0) + 1e-9
    Z = (X - mu) / sd
    m = GaussianHMM(n_components=n_states, covariance_type="diag", n_iter=100, random_state=seed).fit(Z[fit_mask])
    return forward_filter(m, Z), m


def hmm_rows(s: Series, D: pd.DataFrame, k: int, label: str = "y"):
    """Walk-forward predictions of hmm-state and ms-baseline for the windows of D at minute k."""
    X = minute_matrix(s)
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    months = sorted(month.unique())
    ix = {int(t): i for i, t in enumerate(s.t)}
    last_closed = np.array([ix[int(t)] + k - 1 for t in D.t.values])            # minute k reads up to i+k-1
    y = D[label].values
    bcol = "prev_up" if k == 0 else "lead_z"
    p_hmm = np.full(len(D), np.nan)
    p_ms = np.full(len(D), np.nan)
    coefs = []
    for mth in months[3:]:
        tr, te = (month < mth).values, (month == mth).values
        fit_minutes = np.zeros(len(s.t), bool)
        fit_minutes[: last_closed[tr].max() + 1] = True
        P, model = state_probs(X, fit_minutes)
        Ptr, Pte = P[last_closed[tr]], P[last_closed[te]]
        q = np.array([(y[tr] * Ptr[:, j]).sum() / max(Ptr[:, j].sum(), 1e-9) for j in range(N_STATES)])   # soft state up-rates
        p_hmm[te] = Pte @ q
        hard = Ptr.argmax(axis=1)
        preds = np.zeros((te.sum(), N_STATES))
        row = {"month": str(mth), "minute": k}
        for j in range(N_STATES):
            sel = hard == j
            if sel.sum() < 50 or len(np.unique(y[tr][sel])) < 2:
                preds[:, j] = y[tr].mean()
                row[f"state {j} coef"] = np.nan
                continue
            lr = LogisticRegression(C=1.0, max_iter=500).fit(D.loc[tr, [bcol]].values[sel], y[tr][sel])
            preds[:, j] = lr.predict_proba(D.loc[te, [bcol]].values)[:, 1]
            row[f"state {j} coef"] = float(lr.coef_[0][0])
            row[f"state {j} share"] = float(sel.mean())
            row[f"state {j} vol"] = float(np.sqrt(model.covars_[j][0]) if model.covars_.ndim == 2 else np.sqrt(model.covars_[j][0, 0]))
        p_ms[te] = (Pte * preds).sum(axis=1)
        coefs.append(row)
    keep = ~np.isnan(p_hmm)
    return p_hmm[keep], p_ms[keep], y[keep], D.t.values[keep], pd.DataFrame(coefs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--minutes", default="0,3")
    a = ap.parse_args()
    s = Series(load(a.start, a.end))
    rows, coef_tables = [], []
    for k in [int(x) for x in a.minutes.split(",")]:
        D = add_baseline_columns(dataset(s, k), k)
        base = baseline_name(k)
        for label, lname in (("y", "direction"), ("mag", f"magnitude (>= {MAG_BP:.0f} bp)")):
            if label == "mag":
                D["mag"] = (D.move_bp.abs() >= MAG_BP).astype(int)
            p_hmm, p_ms, y, t, C = hmm_rows(s, D, k, label)
            if label == "y":
                bp, by, _, bt = walk_forward(D, [("prev_up" if k == 0 else "lead_z")], "bitrate" if k == 0 else "logistic", label)
                bname = base
            else:
                bp, by, _, bt = walk_forward(D, ["vol60"], "logistic", label)
                bname = "vol60 logistic"
            assert np.array_equal(t, bt)
            hb = ((bp > 0.5) == y).astype(float)
            for name, p in ((bname, bp), ("hmm-state", p_hmm), ("ms-baseline", p_ms)):
                h = ((p > 0.5) == y).astype(float)
                m, lo, hi = block_bootstrap_ci(h, t)
                if name == bname:
                    vs = "baseline"
                else:
                    d, dlo, dhi = paired_difference_ci(h, hb, t)
                    sg = day_sign_test(h, hb, t)
                    vs = f"{d*100:+.2f} [{dlo*100:+.2f}, {dhi*100:+.2f}], days better {sg['share_days_a_better']*100:.0f}%"
                rows.append([k, lname, name, len(y), f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", f"{roc_auc_score(y, p):.3f}", f"{log_loss(y, np.clip(p, 1e-6, 1-1e-6)):.4f}", vs])
                print(rows[-1], flush=True)
            if label == "y":
                C.insert(0, "label", lname)
                coef_tables.append(C)
    with open(OUT / "hmm_models.md", "w") as f:
        f.write(f"Hidden Markov models as predictors, walk-forward by month, {a.start} to {a.end}. hmm-state: a {N_STATES}-state Gaussian HMM on the minute series (return, log volume ratio, taker share) fit on the training months, filtered forward, each state's training up-rate mixed by the filtered probabilities at the last closed minute. ms-baseline: the one-feature baseline refit per state and mixed the same way. Direction label and the magnitude label (window moves at least {MAG_BP:.0f} bp). Last column: accuracy minus the baseline on the same windows, day-block 95% interval, share of days better.\n\n")
        f.write("| minute | label | model | n | accuracy [95% CI] | AUC | log loss | vs baseline |\n|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        C = pd.concat(coef_tables, ignore_index=True)
        f.write("\nMarkov-switching baseline: the baseline feature's logistic coefficient in each state per test month (states ordered by the HMM's internal index, which can change between months; 'vol' is the state's return standard deviation in standardised units and 'share' its share of training windows).\n\n")
        cols = [c for c in C.columns]
        f.write("| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n")
        for r in C.itertuples(index=False):
            f.write("| " + " | ".join("" if (isinstance(x, float) and np.isnan(x)) else (f"{x:.3f}" if isinstance(x, float) else str(x)) for x in r) + " |\n")
    print("wrote hmm_models.md")


if __name__ == "__main__":
    main()
