"""Triple-barrier labels and meta-labelling.

At entry minute k > 0 the barriers are measured from the entry price over the remaining
minutes only. Measuring them from the open would let a barrier touched in the minutes
the model has already seen decide the label (a 74% "result" at minute 3 came from
exactly that before it was caught by a test).

Triple barrier (Lopez de Prado, Advances in Financial Machine Learning, ch. 3): a window
is labelled by whichever comes first inside its 15 minutes: the price touching an upper
barrier (+b), the lower barrier (-b), or the time limit, in which case the sign of the
final move decides. Barriers are set in basis points, either fixed or as a multiple of
the trailing 60-minute volatility scaled to 15 minutes. The label is +1 or -1; the
"first touch" also records how the window resolved.

Meta-labelling: a primary model calls the direction; a secondary model, given the same
features plus the primary's probability, predicts whether that call will be right. The
secondary model is trained only on primary predictions that were themselves made out of
sample (walk-forward), so it never sees a primary prediction that was fit on the same
month. Its use is sizing: act only when the secondary model says the call is likely
right, and compare accuracy and expected value on that subset against acting always.

    python -m models.btc_15m.meta --start 2025-10 --end 2026-08 --minutes 0,3
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from models.btc_15m.data import load
from models.btc_15m.evaluate import make_model
from models.btc_15m.features import FLOW_FEATURES, PRICE_FEATURES, WINDOW, Series, dataset
from models.btc_15m.indicators import INDICATOR_FEATURES
from models.btc_15m.stats import block_bootstrap_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
COLS = PRICE_FEATURES + FLOW_FEATURES + INDICATOR_FEATURES
SPREAD, FEE = 0.01, 0.0175


def triple_barrier(closes: np.ndarray, open_price: float, upper_bp: float, lower_bp: float) -> tuple[int, str]:
    """closes: the window's minute closes in order. Returns (label in {+1,-1}, touch)."""
    for c in closes:
        r = (c / open_price - 1) * 1e4
        if r >= upper_bp:
            return 1, "upper"
        if r <= -lower_bp:
            return -1, "lower"
    final = (closes[-1] / open_price - 1) * 1e4
    return (1 if final >= 0 else -1), "time"


def barrier_labels(s: Series, D: pd.DataFrame, k: int, mult: float | None, fixed_bp: float | None):
    """Label every row of D for entry at minute k. Barriers are measured from the entry
    price (the open at k = 0, else the last close before minute k) over the minutes that
    remain, so nothing the model has already seen can decide the label. Width = mult *
    vol60 * sqrt(remaining minutes) bp, or fixed_bp."""
    ix = {int(t): i for i, t in enumerate(s.t)}
    labels, touches = [], []
    remaining = WINDOW - k
    for t, v60 in zip(D.t.values, D.vol60.values):
        i = ix[int(t)]
        entry = s.o[i] if k == 0 else s.c[i + k - 1]
        b = fixed_bp if fixed_bp is not None else max(mult * v60 * np.sqrt(remaining), 1.0)
        lab, touch = triple_barrier(s.c[i + k:i + WINDOW], entry, b, b)
        labels.append(lab)
        touches.append(touch)
    return np.array(labels), np.array(touches)


def walk_forward_oof(D: pd.DataFrame, cols, y, kind="xgb"):
    """Out-of-fold probabilities for months 4+, each from a model trained on earlier months."""
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    pred = np.full(len(D), np.nan)
    for m in sorted(month.unique())[3:]:
        tr, te = (month < m).values, (month == m).values
        pred[te] = make_model(kind).fit(D.loc[tr, cols], y[tr]).predict_proba(D.loc[te, cols])[:, 1]
    return pred


def meta_label(D: pd.DataFrame, cols, y_up: np.ndarray, primary: np.ndarray, kind="xgb"):
    """Secondary model: P(primary call is right). Trained only on rows with an out-of-fold
    primary prediction from earlier months. Returns meta probabilities (nan where unavailable)."""
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    call = (primary > 0.5).astype(int)
    correct = (call == y_up).astype(int)
    X = D[cols].copy()
    X["primary_prob"] = primary
    X["primary_conf"] = np.abs(primary - 0.5)
    meta = np.full(len(D), np.nan)
    have = ~np.isnan(primary)
    for m in sorted(month[have].unique())[1:]:                # need at least one earlier month of OOF rows
        tr = have & (month < m).values
        te = (month == m).values & have
        if tr.sum() < 500:
            continue
        meta[te] = make_model(kind).fit(X[tr], correct[tr]).predict_proba(X[te])[:, 1]
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--minutes", default="0,3")
    a = ap.parse_args()
    s = Series(load(a.start, a.end))
    brows, mrows = [], []
    for k in [int(x) for x in a.minutes.split(",")]:
        D = dataset(s, k)
        # --- triple-barrier labels vs the plain close-over-open label ---
        for name, mult, fixed in (("close >= open (plain)", None, None), ("fixed 10 bp barriers", None, 10.0), ("1.0 x volatility barriers", 1.0, None), ("2.0 x volatility barriers", 2.0, None)):
            if mult is None and fixed is None:
                y = D.y.values
                touch_share = ""
            else:
                lab, touch = barrier_labels(s, D, k, mult, fixed)
                y = (lab > 0).astype(int)
                touch_share = f"upper {np.mean(touch=='upper')*100:.0f}%, lower {np.mean(touch=='lower')*100:.0f}%, time {np.mean(touch=='time')*100:.0f}%"
            pred = walk_forward_oof(D, COLS, y)
            keep = ~np.isnan(pred)
            hits = ((pred[keep] > 0.5) == y[keep]).astype(float)
            m, lo, hi = block_bootstrap_ci(hits, D.t.values[keep])
            brows.append([k, name, touch_share, f"{y.mean()*100:.1f}%", f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", f"{roc_auc_score(y[keep], pred[keep]):.3f}"])
            print(brows[-1], flush=True)
        # --- meta-labelling on the plain label ---
        y = D.y.values
        primary = walk_forward_oof(D, COLS, y)
        meta = meta_label(D, COLS, y, primary)
        have = ~np.isnan(meta)
        call_right = ((primary[have] > 0.5) == y[have]).astype(float)
        t = D.t.values[have]
        auc = roc_auc_score(call_right, meta[have])
        for name, mask in (("act always", np.ones(have.sum(), bool)), ("act when meta >= 0.5", meta[have] >= 0.5),
                           ("act when meta >= 0.55", meta[have] >= 0.55), ("act when meta >= 0.6", meta[have] >= 0.6)):
            if mask.sum() < 100:
                mrows.append([k, name, int(mask.sum()), "", "", "", ""])
                continue
            m_, lo, hi = block_bootstrap_ci(call_right[mask], t[mask])
            ev = call_right[mask] - (0.5 + SPREAD / 2) - FEE
            e, elo, ehi = block_bootstrap_ci(ev, t[mask])
            mrows.append([k, name, int(mask.sum()), f"{mask.mean()*100:.0f}%", f"{m_*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]",
                          f"{e*100:+.2f} [{elo*100:+.2f}, {ehi*100:+.2f}]", f"{auc:.3f}" if name == "act always" else ""])
            print(mrows[-1], flush=True)
    with open(OUT / "meta.md", "w") as f:
        f.write("Triple-barrier labels: which comes first in the 15 minutes, the upper barrier, the lower barrier, or the time limit (then the sign of the final move). XGBoost, price + flow + indicators, walk-forward.\n\n")
        f.write("| minute | label | how windows resolved | share up | accuracy [95% CI] | AUC |\n|---|---|---|---|---|---|\n")
        for r in brows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        f.write(f"\nMeta-labelling: a second model predicts whether the primary direction call is right, trained only on out-of-sample primary predictions from earlier months. EV in cents per $1 contract at a {SPREAD*100:.0f}c spread and {FEE*100:.2f}c fee, priced at 0.5 (only meaningful at minute 0). The AUC is the secondary model's ability to rank right calls above wrong ones.\n\n")
        f.write("| minute | rule | windows | share acted on | accuracy of primary [95% CI] | EV cents [95% CI] | meta AUC |\n|---|---|---|---|---|---|---|\n")
        for r in mrows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print("wrote meta.md")


if __name__ == "__main__":
    main()
