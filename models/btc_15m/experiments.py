"""Follow-up experiments on the BTC 15-minute model. Each writes its own table under
results/btc_15m/ and the README splices them in.

    ablation     feature sets: price, +flow, +indicators, +tick flow (if the per-second
                 tick files exist), walk-forward by month, forest and xgb
    magnitude    a second label: does the window move more than a threshold (10 bp)?
                 baseline is logistic on recent volatility alone
    cost         expected value per window at a stated spread and fee, trading only
                 when the model's probability is far enough from 0.5
    regime       accuracy at the open by session, volatility tercile and trend tercile
    cpcv         combinatorial purged cross-validation with a 4-hour embargo, as a
                 second estimate next to walk-forward

    python -m models.btc_15m.experiments --start 2025-10 --end 2026-08 [--which ablation,cost,...]
"""
from __future__ import annotations

import argparse
import itertools
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from models.btc_15m.data import load
from models.btc_15m.evaluate import make_model, walk_forward
from models.btc_15m.features import FLOW_FEATURES, PRICE_FEATURES, Series, dataset
from models.btc_15m.indicators import INDICATOR_FEATURES
from models.btc_15m.stats import block_bootstrap_ci, paired_difference_ci
from models.btc_15m.ticks import TICK_FEATURES, TickFlow, load_seconds, tick_path

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
SPREAD, FEE = 0.01, 0.0175          # dollars per contract on a $1 binary, stated in the README


def md_table(path: Path, header: str, cols: list[str], rows: list[list]):
    with open(path, "w") as f:
        f.write(header + "\n\n| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")


def ablation(s: Series, minutes, has_ticks: bool):
    sets = {"price": PRICE_FEATURES, "price + flow": PRICE_FEATURES + FLOW_FEATURES,
            "price + flow + indicators": PRICE_FEATURES + FLOW_FEATURES + INDICATOR_FEATURES}
    if has_ticks:
        sets["price + flow + tick flow"] = PRICE_FEATURES + FLOW_FEATURES + TICK_FEATURES
        sets["everything"] = PRICE_FEATURES + FLOW_FEATURES + INDICATOR_FEATURES + TICK_FEATURES
    rows = []
    for k in minutes:
        D = dataset(s, k)
        base_hits = None
        for name, cols in sets.items():
            for kind in ("forest", "xgb"):
                pred, y, _, t = walk_forward(D, cols, kind)
                hits = ((pred > 0.5) == y).astype(float)
                if name == "price" and kind == "forest":
                    base_hits = hits
                d, lo, hi = paired_difference_ci(hits, base_hits, t) if base_hits is not None else (0, 0, 0)
                rows.append([k, name, kind, len(y), f"{hits.mean()*100:.2f}%", f"{roc_auc_score(y, pred):.3f}",
                             f"{log_loss(y, np.clip(pred, 1e-6, 1-1e-6)):.4f}", f"{d*100:+.2f} [{lo*100:+.2f}, {hi*100:+.2f}]"])
                print("ablation", rows[-1], flush=True)
    md_table(OUT / "ablation.md", "Feature-set ablation, walk-forward by month. Last column: accuracy minus the price-only forest on the same windows, day-block 95% interval.",
             ["minute", "features", "model", "n", "accuracy", "AUC", "log loss", "vs price-only forest"], rows)


def magnitude(s: Series, minutes, tau_bp: float = 10.0):
    rows = []
    for k in minutes:
        D = dataset(s, k)
        D["y"] = (D.move_bp.abs() >= tau_bp).astype(int)          # reuse the label column for walk_forward
        base_rate = D.y.mean()
        for name, cols, kind in (("vol60 only", ["vol60"], "logistic"), ("all features", PRICE_FEATURES + FLOW_FEATURES + INDICATOR_FEATURES, "xgb")):
            pred, y, _, t = walk_forward(D, cols, kind)
            m, lo, hi = block_bootstrap_ci(((pred > 0.5) == y).astype(float), t)
            rows.append([k, name, len(y), f"{base_rate*100:.1f}%", f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]",
                         f"{roc_auc_score(y, pred):.3f}", f"{log_loss(y, np.clip(pred, 1e-6, 1-1e-6)):.4f}"])
            print("magnitude", rows[-1], flush=True)
    md_table(OUT / "magnitude.md", f"Magnitude label: the window moves at least {tau_bp:.0f} basis points from its open, in either direction.",
             ["minute", "model", "n", "share of windows that move", "accuracy [95% CI]", "AUC", "log loss"], rows)


def cost(s: Series, minutes):
    """Buy the side the model favours at 0.5 + spread/2 (at the open the market is a coin
    flip) and pay the fee; payoff 1 if right. EV in cents per traded window."""
    rows = []
    for k in minutes:
        D = dataset(s, k)
        pred, y, _, t = walk_forward(D, PRICE_FEATURES + FLOW_FEATURES, "forest")
        conf = np.abs(pred - 0.5)
        for th in (0.0, 0.03, 0.05, 0.08):
            m = conf >= th
            if m.sum() < 100:
                rows.append([k, f">= {0.5+th:.2f} or <= {0.5-th:.2f}", int(m.sum()), "", "", ""])
                continue
            hit = ((pred[m] > 0.5) == y[m]).astype(float)
            ev = hit - (0.5 + SPREAD / 2) - FEE
            e, lo, hi = block_bootstrap_ci(ev, t[m])
            rows.append([k, f">= {0.5+th:.2f} or <= {0.5-th:.2f}", int(m.sum()), f"{100*m.mean():.0f}%", f"{hit.mean()*100:.2f}%",
                         f"{e*100:+.2f} [{lo*100:+.2f}, {hi*100:+.2f}]"])
            print("cost", rows[-1], flush=True)
    md_table(OUT / "cost.md", f"Expected value per traded window, cents per $1 contract, buying the favoured side at 0.5 + half a {SPREAD*100:.0f}c spread and paying a {FEE*100:.2f}c fee. Forest, price + flow features, walk-forward. Note: after the open a real market would not be priced at 0.5, so only the minute-0 rows describe a real trade.",
             ["minute", "trade when probability", "windows", "share traded", "accuracy", "EV cents [95% CI]"], rows)


def regime(s: Series):
    D = dataset(s, 0)
    pred, y, _, t = walk_forward(D, PRICE_FEATURES + FLOW_FEATURES, "forest")
    keep = D.t.isin(t).values
    E = D[keep].copy()
    E["hit"] = ((pred > 0.5) == y).astype(float)
    E["session"] = pd.cut(E.hour, [-1, 7, 13, 21, 24], labels=["Asia 00-07", "Europe 08-13", "US 14-21", "late 22-23"])
    E["volatility"] = pd.qcut(E.vol60, 3, labels=["low", "mid", "high"])
    E["trend"] = pd.qcut(E.ret240.abs(), 3, labels=["flat", "mid", "strong"])
    rows = []
    for col in ("session", "volatility", "trend"):
        for g, grp in E.groupby(col, observed=True):
            m, lo, hi = block_bootstrap_ci(grp.hit.values, grp.t.values)
            rows.append([col, g, len(grp), f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]"])
    md_table(OUT / "regime.md", "Accuracy at the open (forest, price + flow) by regime, walk-forward predictions. Volatility is the trailing 60-minute realised volatility; trend is the absolute 4-hour return.",
             ["split", "group", "windows", "accuracy [95% CI]"], rows)
    for r in rows:
        print("regime", r, flush=True)


def cpcv(s: Series, k: int = 0, n_groups: int = 6, n_test: int = 2, embargo_s: int = 4 * 3600):
    """Combinatorial purged CV: every choice of n_test groups out of n_groups contiguous
    time blocks is a test set; training rows within `embargo_s` of any test row are
    dropped. Reports the spread of accuracies across the C(6,2) = 15 paths."""
    D = dataset(s, k)
    cols = PRICE_FEATURES + FLOW_FEATURES
    t = D.t.values
    groups = pd.qcut(t, n_groups, labels=False)
    rows, accs = [], []
    for test_groups in itertools.combinations(range(n_groups), n_test):
        te = np.isin(groups, test_groups)
        tr = ~te
        for g in test_groups:                                   # purge + embargo around each test block
            a, b = t[groups == g].min() - embargo_s, t[groups == g].max() + 900 + embargo_s
            tr &= ~((t >= a) & (t <= b))
        pred = make_model("forest").fit(D.loc[tr, cols], D.y[tr]).predict_proba(D.loc[te, cols])[:, 1]
        acc = ((pred > 0.5) == D.y[te]).mean()
        accs.append(acc)
        rows.append([str(test_groups), int(tr.sum()), int(te.sum()), f"{acc*100:.2f}%"])
        print("cpcv", rows[-1], flush=True)
    accs = np.array(accs)
    rows.append(["all 15 paths", "", "", f"mean {accs.mean()*100:.2f}%, min {accs.min()*100:.2f}%, max {accs.max()*100:.2f}%"])
    md_table(OUT / "cpcv.md", f"Combinatorial purged cross-validation at minute {k}: {n_groups} contiguous blocks, every pair as the test set, training rows within 4 hours of a test block dropped. Forest, price + flow. Unlike walk-forward, some paths train on data from after the test block.",
             ["test blocks", "train rows", "test rows", "accuracy"], rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--which", default="ablation,magnitude,cost,regime,cpcv")
    ap.add_argument("--minutes", default="0,3")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    minutes = [int(x) for x in a.minutes.split(",")]
    s = Series(load(a.start, a.end))
    months = [str(p) for p in pd.period_range(a.start, a.end, freq="M")]
    has_ticks = all(tick_path(m).exists() for m in months)
    if has_ticks:
        s.ticks = TickFlow(load_seconds(a.start, a.end))
        print("tick flow features available", flush=True)
    which = a.which.split(",")
    if "ablation" in which:
        ablation(s, minutes, has_ticks)
    if "magnitude" in which:
        magnitude(s, minutes)
    if "cost" in which:
        cost(s, minutes)
    if "regime" in which:
        regime(s)
    if "cpcv" in which:
        cpcv(s)


if __name__ == "__main__":
    main()
