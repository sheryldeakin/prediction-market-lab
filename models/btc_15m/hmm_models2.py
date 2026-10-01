"""Hidden Markov models, round two: states as features, and a model per state.

Study 29 used HMM states as predictors on their own and they lost. Here the states enter
the models that already work, walk-forward by month, with the same windows and baselines:

  +minute states    the filtered probabilities of a 3-state Gaussian HMM on the minute
                    series (return, log volume ratio, taker share), fit on the training
                    months and run forward, read at the last closed minute, added as
                    three features to price + flow + indicators
  +daily regime     the previous day's filtered state from the daily HMM of the regime
                    study (results/btc_15m/regimes_daily.csv), one-hot, added likewise
  per-state forest  a forest fit separately on the training windows of each minute-scale
                    state (hard assignment), predictions mixed by the filtered
                    probabilities: a mixture of experts

Each row is compared with the same model without the extra columns on the same windows
(paired day-block interval, day sign test) and with the one-feature baseline.

    python -m models.btc_15m.hmm_models2 --start 2025-10 --end 2026-08 --minutes 0,3
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, roc_auc_score

from models.btc_15m.data import load
from models.btc_15m.evaluate import add_baseline_columns, baseline_name, baseline_walk_forward, make_model
from models.btc_15m.features import FLOW_FEATURES, PRICE_FEATURES, Series, dataset
from models.btc_15m.hmm_models import N_STATES, minute_matrix, state_probs
from models.btc_15m.indicators import INDICATOR_FEATURES
from models.btc_15m.stats import block_bootstrap_ci, day_sign_test, paired_difference_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
COLS = PRICE_FEATURES + FLOW_FEATURES + INDICATOR_FEATURES
STATE_COLS = [f"hmm_p{j}" for j in range(N_STATES)]


def daily_regime_columns(D: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """One-hot of the previous day's filtered daily HMM state, from the regime study."""
    R = pd.read_csv(OUT / "regimes_daily.csv")
    day_of_row = (R.t.values - 60) // 86400
    lab = pd.Series(R.hmm.fillna("").values, index=day_of_row)
    prev = lab.reindex(D.t.values // 86400 - 1).fillna("").values
    names = sorted(x for x in set(prev) if x)
    cols = []
    for name in names:
        col = "regime: " + name
        D[col] = (prev == name).astype(float)
        cols.append(col)
    return D, cols


def walk_forward_with_states(s: Series, D: pd.DataFrame, k: int, kind: str):
    """Walk-forward predictions for: base model, +minute states, +daily regime, per-state forest."""
    X = minute_matrix(s)
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    months = sorted(month.unique())
    ix = {int(t): i for i, t in enumerate(s.t)}
    last_closed = np.array([ix[int(t)] + k - 1 for t in D.t.values])
    y = D.y.values
    D, reg_cols = daily_regime_columns(D)
    preds = {name: np.full(len(D), np.nan) for name in ("base", "+minute states", "+daily regime", "+both", "per-state forest")}
    for mth in months[3:]:
        tr, te = (month < mth).values, (month == mth).values
        fit_minutes = np.zeros(len(s.t), bool); fit_minutes[: last_closed[tr].max() + 1] = True
        P, _ = state_probs(X, fit_minutes)
        for j in range(N_STATES):
            D[STATE_COLS[j]] = P[last_closed, j]
        preds["base"][te] = make_model(kind).fit(D.loc[tr, COLS], y[tr]).predict_proba(D.loc[te, COLS])[:, 1]
        preds["+minute states"][te] = make_model(kind).fit(D.loc[tr, COLS + STATE_COLS], y[tr]).predict_proba(D.loc[te, COLS + STATE_COLS])[:, 1]
        preds["+daily regime"][te] = make_model(kind).fit(D.loc[tr, COLS + reg_cols], y[tr]).predict_proba(D.loc[te, COLS + reg_cols])[:, 1]
        both = COLS + STATE_COLS + reg_cols
        preds["+both"][te] = make_model(kind).fit(D.loc[tr, both], y[tr]).predict_proba(D.loc[te, both])[:, 1]
        hard = P[last_closed[tr]].argmax(axis=1)
        mix = np.zeros((te.sum(), N_STATES))
        for j in range(N_STATES):
            sel = hard == j
            if sel.sum() < 500:
                mix[:, j] = preds["base"][te]
                continue
            mix[:, j] = make_model("forest").fit(D.loc[tr, COLS][sel], y[tr][sel]).predict_proba(D.loc[te, COLS])[:, 1]
        preds["per-state forest"][te] = (P[last_closed[te]] * mix).sum(axis=1)
    keep = ~np.isnan(preds["base"])
    return {n: p[keep] for n, p in preds.items()}, y[keep], D.t.values[keep]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--minutes", default="0,3")
    ap.add_argument("--kind", default="forest")
    a = ap.parse_args()
    s = Series(load(a.start, a.end))
    rows = []
    for k in [int(x) for x in a.minutes.split(",")]:
        D = add_baseline_columns(dataset(s, k), k)
        preds, y, t = walk_forward_with_states(s, D, k, a.kind)
        bp, _, _, bt = baseline_walk_forward(D, k)
        bp = pd.Series(bp, index=bt).reindex(t).values
        hits = {n: ((p > 0.5) == y).astype(float) for n, p in preds.items()}
        hb = ((bp > 0.5) == y).astype(float)
        for n, p in preds.items():
            m, lo, hi = block_bootstrap_ci(hits[n], t)
            if n == "base":
                vs = "reference"
            else:
                d, dlo, dhi = paired_difference_ci(hits[n], hits["base"], t)
                sg = day_sign_test(hits[n], hits["base"], t)
                vs = f"{d*100:+.2f} [{dlo*100:+.2f}, {dhi*100:+.2f}], days better {sg['share_days_a_better']*100:.0f}%"
            db, blo, bhi = paired_difference_ci(hits[n], hb, t)
            rows.append([k, n, len(y), f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", f"{roc_auc_score(y, p):.3f}", f"{log_loss(y, np.clip(p, 1e-6, 1-1e-6)):.4f}", vs, f"{db*100:+.2f} [{blo*100:+.2f}, {bhi*100:+.2f}] vs {baseline_name(k)}"])
            print(rows[-1], flush=True)
    with open(OUT / "hmm_models2.md", "w") as f:
        f.write(f"Hidden Markov models, round two ({a.kind} on price + flow + indicators, walk-forward by month, {a.start} to {a.end}). '+minute states': the filtered probabilities of a {N_STATES}-state HMM on the minute series added as features; '+daily regime': the previous day's filtered state from the regime study, one-hot; 'per-state forest': a forest fit per minute-scale state, mixed by the filtered probabilities. 'vs without' is accuracy minus the same model without the extra columns on the same windows, day-block 95% interval and share of days better; the last column is against the one-feature baseline.\n\n")
        f.write("| minute | model | n | accuracy [95% CI] | AUC | log loss | vs without | vs one-feature baseline |\n|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print("wrote hmm_models2.md")


if __name__ == "__main__":
    main()
