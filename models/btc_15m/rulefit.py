"""One model from the good bits, built without peeking.

For each test month m (walk-forward, from the fourth month on):
  1. mine rules: a random forest is fit on the months before m; every leaf with enough
     support and lift becomes a candidate rule (models.btc_15m.patterns.leaf_rules)
  2. add the hand-named events (models.btc_15m.rules.events)
  3. turn every rule and event into a 0/1 column, together with the raw features
  4. fit an L1-regularised logistic regression on the months before m, so it keeps
     the rules that earn their place and drops the rest
  5. score month m

Nothing about month m is used before it is scored: the rules are mined, the events
are fixed in advance, and the weights are fit, all on earlier months. Compared with the
forest and the lead-only/majority baseline on the same windows, with day-block
intervals. Also reports how many rules the regularisation kept per month.

    python -m models.btc_15m.rulefit --start 2025-10 --end 2026-08 --minutes 0,3
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler

from models.btc_15m.data import load
from models.btc_15m.evaluate import make_model
from models.btc_15m.features import FLOW_FEATURES, PRICE_FEATURES, Series, dataset
from models.btc_15m.indicators import INDICATOR_FEATURES
from models.btc_15m.patterns import leaf_rules, rule_mask, simplify
from models.btc_15m.rules import events
from models.btc_15m.stats import block_bootstrap_ci, paired_difference_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
COLS = PRICE_FEATURES + FLOW_FEATURES + INDICATOR_FEATURES


def rule_columns(Dtr: pd.DataFrame, Dte: pd.DataFrame, k: int, seed=0):
    """Mine rules on Dtr, return (Xtr, Xte, names) of 0/1 rule and event columns."""
    forest = RandomForestClassifier(n_estimators=40, max_depth=4, min_samples_leaf=300, max_features=0.5, n_jobs=2, random_state=seed)
    forest.fit(Dtr[COLS].values, Dtr.y.values)
    cands = leaf_rules(forest, COLS, Dtr[COLS].values, Dtr.y.values, min_support=300, min_lift=0.03)
    seen = {}
    for conds, dev, n in cands:
        m = rule_mask(conds, Dtr)
        key = m.tobytes()
        if key not in seen or len(conds) < len(seen[key][0]):
            seen[key] = (conds, dev)
    names, tr_cols, te_cols = [], [], []
    for conds, dev in seen.values():
        names.append("rule: " + simplify(conds))
        tr_cols.append(rule_mask(conds, Dtr).astype(float))
        te_cols.append(rule_mask(conds, Dte).astype(float))
    Etr, Ete = events(Dtr, k), events(Dte, k)
    for name in Etr:
        if Etr[name].sum() >= 100:
            names.append("event: " + name)
            tr_cols.append(Etr[name].astype(float))
            te_cols.append(Ete[name].astype(float))
    return np.column_stack(tr_cols), np.column_stack(te_cols), names


def fit_rulefit(Xtr_rules, Xtr_raw, y, C=0.05):
    sc = StandardScaler().fit(Xtr_raw)
    X = np.hstack([Xtr_rules, sc.transform(Xtr_raw)])
    model = LogisticRegression(penalty="l1", C=C, solver="liblinear", max_iter=2000).fit(X, y)
    return model, sc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--minutes", default="0,3")
    ap.add_argument("--C", type=float, default=0.05)
    a = ap.parse_args()
    s = Series(load(a.start, a.end))
    rows, kept_rows = [], []
    for k in [int(x) for x in a.minutes.split(",")]:
        D = dataset(s, k)
        y, t = D.y.values, D.t.values
        month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
        months = sorted(month.unique())
        preds = {"rulefit": np.full(len(D), np.nan), "forest": np.full(len(D), np.nan), "baseline": np.full(len(D), np.nan)}
        for m in months[3:]:
            tr, te = (month < m).values, (month == m).values
            Dtr, Dte = D[tr].reset_index(drop=True), D[te].reset_index(drop=True)
            Rtr, Rte, names = rule_columns(Dtr, Dte, k)
            model, sc = fit_rulefit(Rtr, Dtr[COLS].values, Dtr.y.values, a.C)
            preds["rulefit"][te] = model.predict_proba(np.hstack([Rte, sc.transform(Dte[COLS].values)]))[:, 1]
            preds["forest"][te] = make_model("forest").fit(Dtr[COLS], Dtr.y).predict_proba(Dte[COLS])[:, 1]
            if k > 0:
                preds["baseline"][te] = LogisticRegression(max_iter=500).fit(Dtr[["lead"]], Dtr.y).predict_proba(Dte[["lead"]])[:, 1]
            else:
                preds["baseline"][te] = Dtr.y.mean()
            coef = model.coef_[0][:len(names)]
            kept = [(names[i], coef[i]) for i in np.argsort(-np.abs(coef))[:5] if coef[i] != 0]
            kept_rows.append([k, str(m), len(names), int((coef != 0).sum()), "; ".join(f"{n} ({c:+.2f})" for n, c in kept)])
            print(f"k={k} {m}: {len(names)} candidate columns, {int((coef != 0).sum())} kept, acc rulefit {((preds['rulefit'][te] > .5) == y[te]).mean()*100:.2f}% forest {((preds['forest'][te] > .5) == y[te]).mean()*100:.2f}%", flush=True)
        keep = ~np.isnan(preds["rulefit"])
        hits = {n: ((p[keep] > 0.5) == y[keep]).astype(float) for n, p in preds.items()}
        bname = "lead-only" if k > 0 else "majority"
        for n in ("baseline", "forest", "rulefit"):
            mu, lo, hi = block_bootstrap_ci(hits[n], t[keep])
            if n == "forest":
                vs = "reference"
            else:
                d, dlo, dhi = paired_difference_ci(hits[n], hits["forest"], t[keep])
                vs = f"{d*100:+.2f} [{dlo*100:+.2f}, {dhi*100:+.2f}] vs forest"
            rows.append([k, bname if n == "baseline" else n, int(keep.sum()), f"{mu*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", f"{roc_auc_score(y[keep], preds[n][keep]):.3f}",
                         f"{log_loss(y[keep], np.clip(preds[n][keep], 1e-6, 1-1e-6)):.4f}", vs])
            print(rows[-1], flush=True)
    with open(OUT / "rulefit.md", "w") as f:
        f.write("One model from the rules and events, nested walk-forward: for each test month the rules are mined by a forest on earlier months, the hand-named events are added, and an L1-regularised logistic regression on those 0/1 columns plus the raw features is fit on earlier months, then scored on the test month. Compared with the forest and the simple baseline on the same windows.\n\n")
        f.write("| minute | model | n | accuracy [95% CI] | AUC | log loss | vs forest |\n|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        f.write("\nWhat the regularisation kept, per test month: candidate rule and event columns, how many received a non-zero weight, and the five largest weights.\n\n| minute | month | candidates | kept | largest weights |\n|---|---|---|---|---|\n")
        for r in kept_rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print("wrote rulefit.md")


if __name__ == "__main__":
    main()
