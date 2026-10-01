"""Finding patterns a person would not name: rules mined from a forest, and shapes of
the recent path.

Part 1, rule extraction. A random forest is fit on the first half of the months; every
leaf of every tree is a conjunction of feature thresholds ("rsi14 <= 34.9 and flow15
<= -0.12 and win1 <= 0"). Leaves with at least 300 training windows and a lift of 3
points or more over the base rate are kept as candidate rules, then scored on the
second half of the months, which the forest never saw: up-rate when the rule fires,
day-clustered p-value against that period's base rate, false-discovery correction
across all candidates, and month-by-month stability. Duplicate rules (the same
firing set) are merged.

Part 2, shape mining. The last 60 one-minute returns before each window's open are
normalised by their own volatility and clustered (k-means, 24 shapes) on the first
half of the months; each shape is then scored on the second half in the same way.
A shape is a pattern of the recent path, not an indicator threshold.

Both parts report the same columns as the event library so they read side by side.

    python -m models.btc_15m.patterns --start 2025-10 --end 2026-08
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier

from models.btc_15m.data import load
from models.btc_15m.features import FLOW_FEATURES, HISTORY, PRICE_FEATURES, Series, dataset
from models.btc_15m.indicators import INDICATOR_FEATURES
from models.btc_15m.rules import bh, day_pvalue, is_stable, month_agreement
from models.btc_15m.stats import block_bootstrap_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
COLS = PRICE_FEATURES + FLOW_FEATURES + INDICATOR_FEATURES


# ---------------- rule extraction ----------------

def leaf_rules(forest: RandomForestClassifier, cols, X_train: np.ndarray, y_train: np.ndarray, min_support=300, min_lift=0.03):
    """Every leaf as a list of (feature, op, threshold); keep leaves with enough training
    support and a lift over the base rate. Returns [(conditions, train_dev, n_train)]."""
    base = y_train.mean()
    out = []
    for est in forest.estimators_:
        tree = est.tree_
        leaf_of = est.apply(X_train)
        # walk every root-to-leaf path
        stack = [(0, [])]
        while stack:
            node, conds = stack.pop()
            left, right = tree.children_left[node], tree.children_right[node]
            if left == -1:
                m = leaf_of == node
                n = int(m.sum())
                if n >= min_support:
                    dev = y_train[m].mean() - base
                    if abs(dev) >= min_lift:
                        out.append((conds, float(dev), n))
                continue
            f, thr = cols[tree.feature[node]], float(tree.threshold[node])
            stack.append((left, conds + [(f, "<=", thr)]))
            stack.append((right, conds + [(f, ">", thr)]))
    return out


def rule_mask(conds, D: pd.DataFrame) -> np.ndarray:
    m = np.ones(len(D), bool)
    for f, op, thr in conds:
        v = D[f].values
        m &= (v <= thr) if op == "<=" else (v > thr)
    return m


def simplify(conds):
    """Tighten repeated thresholds on the same feature into one bound each."""
    lo, hi = {}, {}
    for f, op, thr in conds:
        if op == "<=":
            hi[f] = min(hi.get(f, np.inf), thr)
        else:
            lo[f] = max(lo.get(f, -np.inf), thr)
    parts = []
    for f in sorted(set(lo) | set(hi)):
        if f in lo and f in hi:
            parts.append(f"{lo[f]:.3g} < {f} <= {hi[f]:.3g}")
        elif f in lo:
            parts.append(f"{f} > {lo[f]:.3g}")
        else:
            parts.append(f"{f} <= {hi[f]:.3g}")
    return " and ".join(parts)


# ---------------- shape mining ----------------

def path_matrix(s: Series, D: pd.DataFrame, L: int = 60) -> np.ndarray:
    """Last L one-minute returns before each window's open, scaled by their own sd."""
    ix = {int(t): i for i, t in enumerate(s.t)}
    M = np.stack([s.r1[ix[int(t)] - L:ix[int(t)]] for t in D.t.values])
    sd = M.std(axis=1, keepdims=True) + 1e-9
    return M / sd


def describe_shape(center: np.ndarray) -> str:
    """A few words for a cluster centre: cumulative path over the hour in sd units."""
    cum = np.cumsum(center)
    q = [cum[14], cum[29], cum[44], cum[59]]
    words = []
    for a, b, name in ((0, q[0], "first quarter"), (q[0], q[1], "second"), (q[1], q[2], "third"), (q[2], q[3], "last quarter")):
        d = b - a
        words.append(f"{name} {'up' if d > 0.4 else 'down' if d < -0.4 else 'flat'}")
    return f"net {q[3]:+.1f} sd; " + ", ".join(words)


# ---------------- scoring shared with the event library ----------------

def score_masks(named_masks, D: pd.DataFrame, mined_signs, min_fires=100):
    """Score each (name, mask) on the scoring frame D. Stability compares each scoring
    month with the direction the rule or shape had on the mining half (mined_signs, one
    +1/-1 per mask), not with its pooled direction on D, which those months helped set."""
    y, t = D.y.values, D.t.values
    named_masks = [(name, m, sg) for (name, m), sg in zip(named_masks, mined_signs)]
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    months = sorted(month.unique())
    base = y.mean()
    names, masks, devs, pvals, cis, signs = [], [], [], [], [], []
    for name, m, sg in named_masks:
        if m.sum() < min_fires:
            continue
        names.append(name); masks.append(m); signs.append(int(np.sign(sg)))
        mu, lo, hi = block_bootstrap_ci(y[m].astype(float), t[m])
        devs.append(mu - base); cis.append((mu, lo, hi))
        pvals.append(day_pvalue(y[m].astype(float), t[m], base))
    keep = bh(np.array(pvals)) if names else np.array([], bool)
    rows = []
    for name, m, dev, p, (mu, lo, hi), kp, sg in zip(names, masks, devs, pvals, cis, keep, signs):
        agree, tot, per = month_agreement(m, y, month, months, sg)
        rows.append([name, int(m.sum()), f"{100*m.mean():.1f}%", f"{mu*100:.1f}% [{lo*100:.1f}, {hi*100:.1f}]", f"{dev*100:+.1f}", f"{p:.3f}",
                     "yes" if kp else "", f"{agree}/{tot}", " ".join(per), "stable" if kp and is_stable(agree, tot, sg) else ""])
    rows.sort(key=lambda r: float(r[5]))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--k", type=int, default=0)
    ap.add_argument("--shapes", type=int, default=24)
    a = ap.parse_args()
    s = Series(load(a.start, a.end))
    D = dataset(s, a.k)
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    months = sorted(month.unique())
    split = months[len(months) // 2]
    tr, te = (month < split).values, (month >= split).values
    Dtr, Dte = D[tr].reset_index(drop=True), D[te].reset_index(drop=True)
    print(f"search months: {months[0]}..{months[len(months)//2 - 1]} ({tr.sum()} windows); scoring months: {split}..{months[-1]} ({te.sum()} windows)", flush=True)

    # ---- part 1 ----
    forest = RandomForestClassifier(n_estimators=60, max_depth=4, min_samples_leaf=300, max_features=0.5, n_jobs=2, random_state=0)
    forest.fit(Dtr[COLS].values, Dtr.y.values)
    cands = leaf_rules(forest, COLS, Dtr[COLS].values, Dtr.y.values)
    # merge duplicates by their firing set on the scoring months
    seen = {}
    for conds, dev, n in cands:
        m = rule_mask(conds, Dte)
        key = m.tobytes()
        if key not in seen or len(conds) < len(seen[key][0]):
            seen[key] = (conds, dev, n, m)
    print(f"{len(cands)} leaf rules, {len(seen)} distinct firing sets", flush=True)
    named = [(simplify(c), m) for c, dev, n, m in seen.values()]
    rule_rows = score_masks(named, Dte, [dev for c, dev, n, m in seen.values()])
    for r in rule_rows[:10]:
        print("rule", r[:7], flush=True)

    # ---- part 2 ----
    Ptr, Pte = path_matrix(s, Dtr), path_matrix(s, Dte)
    km = KMeans(n_clusters=a.shapes, n_init=4, random_state=0).fit(Ptr)
    lab = km.predict(Pte)
    named = [(f"shape {c}: {describe_shape(km.cluster_centers_[c])}", lab == c) for c in range(a.shapes)]
    ytr = Dtr.y.values
    shape_signs = [np.sign(ytr[km.labels_ == c].mean() - ytr.mean()) if (km.labels_ == c).any() else 0 for c in range(a.shapes)]
    shape_rows = score_masks(named, Dte, shape_signs)
    for r in shape_rows[:8]:
        print("shape", r[:7], flush=True)

    with open(OUT / "patterns.md", "w") as f:
        f.write(f"Rules mined from a random forest fit on {months[0]} to {months[len(months)//2 - 1]}, scored on {split} to {months[-1]} (never seen by the forest). Up-rate when the rule fires, day-block 95% interval, day-clustered p against the scoring period's base rate, false-discovery correction across all {len(rule_rows)} candidate rules, and month-by-month stability (at least three quarters of months agreeing). Only rules that survive the correction are listed.\n\n")
        stable = [r for r in rule_rows if r[9] == "stable"]
        top = sorted(stable, key=lambda r: -abs(float(r[4])))[:25]
        f.write(f"Of {len(rule_rows)} candidates, {sum(1 for r in rule_rows if r[6] == 'yes')} survive the correction and {len(stable)} are also stable month by month. The 25 stable rules with the largest deviation are listed; every candidate is in patterns_rules.csv.\n\n")
        f.write("| rule | fires | share | up-rate [95% CI] | vs base (points) | p | survives FDR | months agreeing | by month | verdict |\n|---|---|---|---|---|---|---|---|---|---|\n")
        for r in top:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        pd.DataFrame(rule_rows, columns=["rule", "fires", "share", "up_rate_ci", "deviation_points", "p", "survives_fdr", "months_agreeing", "by_month", "verdict"]).to_csv(OUT / "patterns_rules.csv", index=False)
        f.write(f"\nShapes of the last 60 minutes before the open ({a.shapes} clusters found on the search months, scored on the later months). Each shape is described by its cumulative path in standard-deviation units.\n\n")
        f.write("| shape | fires | share | up-rate [95% CI] | vs base (points) | p | survives FDR | months agreeing | by month | verdict |\n|---|---|---|---|---|---|---|---|---|---|\n")
        for r in shape_rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print(f"wrote patterns.md ({sum(1 for r in rule_rows if r[6]=='yes')} rules survive, {sum(1 for r in shape_rows if r[6]=='yes')} shapes survive)")


if __name__ == "__main__":
    main()
