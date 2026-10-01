"""Multi-asset training and cross-asset features.

Three questions, all walk-forward by month with day-clustered intervals:

  own       each coin predicted by a model trained on its own history
  pooled    one model trained on all four coins' earlier months (features are
            scale-free: basis points, ratios, shares), tested on each coin
  cross     BTC predicted from its own features plus the same-moment features of
            ETH and SOL (their lead, recent returns and taker-buy share), to test
            whether one coin's last minutes say anything about another's next window

Rows from different coins are joined on the window open time, so a cross feature at
minute k comes from the other coin's candles closed by minute k and nothing later.

    python -m models.btc_15m.multi_asset --start 2025-10 --end 2026-08 --minutes 0,3
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, roc_auc_score

from models.btc_15m.data import load
from models.btc_15m.evaluate import baseline_name, baseline_walk_forward, make_model
from models.btc_15m.features import FLOW_FEATURES, PRICE_FEATURES, Series, dataset
from models.btc_15m.stats import block_bootstrap_ci, paired_difference_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT"]
BASE = PRICE_FEATURES + FLOW_FEATURES
CROSS_COLS = ["lead", "ret5", "ret15", "ret60", "flow5", "flow15"]


def cross_features(target: pd.DataFrame, others: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Join other coins' same-window features onto the target frame by open time.
    Windows missing in any other coin are dropped so every row has every column."""
    out = target.copy()
    for name, D in others.items():
        add = D[["t"] + CROSS_COLS].rename(columns={c: f"{name}_{c}" for c in CROSS_COLS})
        out = out.merge(add, on="t", how="inner")
    return out.reset_index(drop=True)


def month_of(t):
    return pd.to_datetime(t, unit="s").to_period("M")


def walk_forward_pooled(frames: dict[str, pd.DataFrame], cols, kind, target: str):
    """Train on every coin's earlier months, test on the target coin's month."""
    T = frames[target]
    tm = month_of(T.t.values)
    pooled = pd.concat([f.assign(_sym=s) for s, f in frames.items()], ignore_index=True)
    pm = month_of(pooled.t.values)
    pred = np.full(len(T), np.nan)
    for m in sorted(tm.unique())[3:]:
        tr = np.asarray(pm < m)
        te = np.asarray(tm == m)
        model = make_model(kind).fit(pooled.loc[tr, cols], pooled.y.values[tr])
        pred[te] = model.predict_proba(T.loc[te, cols])[:, 1]
    keep = ~np.isnan(pred)
    return pred[keep], T.y.values[keep], T.t.values[keep]


def walk_forward_single(D: pd.DataFrame, cols, kind):
    return walk_forward_pooled({"x": D}, cols, kind, "x")


def report(name, pred, y, t, base_hits=None):
    hits = ((pred > 0.5) == y).astype(float)
    m, lo, hi = block_bootstrap_ci(hits, t)
    row = [name, len(y), f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", f"{roc_auc_score(y, pred):.3f}",
           f"{log_loss(y, np.clip(pred, 1e-6, 1-1e-6)):.4f}"]
    if base_hits is not None:
        d, dlo, dhi = paired_difference_ci(hits, base_hits, t)
        row.append(f"{d*100:+.2f} [{dlo*100:+.2f}, {dhi*100:+.2f}]")
    else:
        row.append("baseline")
    return row, hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--minutes", default="0,3")
    ap.add_argument("--kind", default="xgb")
    a = ap.parse_args()
    series = {s: Series(load(a.start, a.end, s)) for s in SYMBOLS}
    rows = []
    for k in [int(x) for x in a.minutes.split(",")]:
        frames = {s: dataset(series[s], k) for s in SYMBOLS}
        own_hits = {}
        for s in SYMBOLS:
            pred, y, t = walk_forward_single(frames[s], BASE, a.kind)
            row, own_hits[s] = report(f"{s[:-4]} own", pred, y, t)
            rows.append([k] + row)
            print(k, row, flush=True)
        for s in SYMBOLS:
            pred, _, _, t = baseline_walk_forward(frames[s], k)
            y = frames[s].set_index("t").y.reindex(t).values
            base = own_hits[s]
            row, _ = report(f"{s[:-4]} one-feature baseline ({baseline_name(k)})", pred, y, t, base if len(base) == len(y) else None)
            rows.append([k] + row)
            print(k, row, flush=True)
        for s in SYMBOLS:
            pred, y, t = walk_forward_pooled(frames, BASE, a.kind, s)
            base = own_hits[s]
            row, _ = report(f"{s[:-4]} pooled (4 coins)", pred, y, t, base if len(base) == len(y) else None)
            rows.append([k] + row)
            print(k, row, flush=True)
        # cross-asset features for BTC
        X = cross_features(frames["BTCUSDT"], {"eth": frames["ETHUSDT"], "sol": frames["SOLUSDT"]})
        cols_cross = BASE + [f"{n}_{c}" for n in ("eth", "sol") for c in CROSS_COLS]
        p0, y0, t0 = walk_forward_single(X, BASE, a.kind)
        row0, h0 = report("BTC own (cross-joined rows)", p0, y0, t0)
        rows.append([k] + row0)
        p1, y1, t1 = walk_forward_single(X, cols_cross, a.kind)
        row1, _ = report("BTC + ETH and SOL features", p1, y1, t1, h0)
        rows.append([k] + row1)
        print(k, row0, row1, flush=True)
    with open(OUT / "multi_asset.md", "w") as f:
        f.write(f"Multi-asset results ({a.kind}, price + flow features), walk-forward by month, {a.start} to {a.end}. "
                "Last column: accuracy minus the coin's own-history model on the same windows, day-block 95% interval.\n\n")
        f.write("| minute | setup | n | accuracy [95% CI] | AUC | log loss | vs own |\n|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print("wrote multi_asset.md")


if __name__ == "__main__":
    main()
