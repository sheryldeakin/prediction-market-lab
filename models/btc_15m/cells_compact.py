"""Do the 186 named events say anything a handful of continuous quantities do not?

The cells model (cells_model.py) is a logistic regression on 186 named 0/1 events. Most of
them are costumes of "price recently rose or fell" or of "a probe of an extreme" (the cells
profile), so a small continuous model of the same quantities might carry everything the
names carry. On the same minutes, walk-forward by year:

  compact          a logistic regression with cubic splines on nine continuous quantities
                   known at the decision minute: the 5-, 15-, 60- and 240-minute returns in
                   units of the trailing-hour volatility, the position in the 4-hour range,
                   log trailing-hour volatility, and the last closed candle's upper-wick
                   share, lower-wick share and body sign
  cells            the 186 events plus the volatility tercile (the cells model as published)
  compact + cells  both sets of columns
  strongest cell   the strongest firing cell decides (ranking from the training years)

Accuracy and log loss with day-block intervals; every row paired against the compact model
on the same minutes. If adding the events to the compact model does not move accuracy or log
loss, the library is an interpretation layer, not a predictor. Training uses every third
minute of the earlier years; scoring uses every minute.

    python -m models.btc_15m.cells_compact --start 2018 --end 2026-08 --horizon 5
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler

from models.btc_15m.cells_model import event_matrix, previous_h_rule
from models.btc_15m.features import Series
from models.btc_15m.horizons import MIN_FIRES, labels, year_frame
from models.btc_15m.rules import vol_cutoffs
from models.btc_15m.stats import block_bootstrap_ci, day_sign_test, paired_difference_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
STRIDE = 3                                      # train on every third minute; score every minute
COMPACT = ["z5", "z15", "z60", "z240", "rangepos", "logvol", "upper_wick", "lower_wick", "body_sign"]


def compact_matrix(s: Series, D: pd.DataFrame) -> np.ndarray:
    """The nine continuous quantities for every decision minute in D (last closed candle is i-1)."""
    v = np.maximum(D.vol60.values, 1e-6)
    j = np.maximum(D.i.values - 1, 0)
    o, h, l, c = s.o[j], s.h[j], s.l[j], s.c[j]
    rng = np.maximum(h - l, 1e-12)
    X = np.column_stack([
        D.ret5.values / (v * np.sqrt(5)), D.ret15.values / (v * np.sqrt(15)), D.ret60.values / (v * np.sqrt(60)), D.ret240.values / (v * np.sqrt(240)),
        D.rangepos.values, np.log(v),
        (h - np.maximum(o, c)) / rng, (np.minimum(o, c) - l) / rng, np.sign(c - o),
    ]).astype(np.float32)
    return np.nan_to_num(X)


def compact_model():
    return make_pipeline(StandardScaler(), SplineTransformer(n_knots=5, degree=3), LogisticRegression(C=0.1, max_iter=1000))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2018)
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--horizon", type=int, default=5)
    a = ap.parse_args()
    h = a.horizon
    frames, cutoffs = {}, None
    for year in range(a.start, int(a.end[:4]) + 1):
        yf = year_frame(year, a.end)
        if yf is None:
            continue
        s, D = yf
        if cutoffs is None:
            cutoffs = vol_cutoffs(D[pd.to_datetime(D.t, unit="s").dt.month <= 3])
        E, names = event_matrix(s, D, cutoffs)
        Q = compact_matrix(s, D)
        y = labels(s, D.i.values)[h]
        ok = ~np.isnan(y)
        frames[year] = {"E": E[ok].astype(np.uint8), "Q": Q[ok], "y": y[ok].astype(int), "t": D.t.values[ok], "vol": D.vol60.values[ok],
                        "rule": previous_h_rule(s, D.i.values[ok], h)}
        cutoffs = vol_cutoffs(D)
        print(year, "minutes", int(ok.sum()), flush=True)

    rows = []
    for Y in [y for y in frames if y >= 2020]:
        tr = [y for y in frames if y < Y]
        Etr = np.vstack([frames[y]["E"][::STRIDE] for y in tr]); Qtr = np.vstack([frames[y]["Q"][::STRIDE] for y in tr])
        ytr = np.concatenate([frames[y]["y"][::STRIDE] for y in tr]); vtr = np.concatenate([frames[y]["vol"][::STRIDE] for y in tr])
        q1, q2 = np.quantile(vtr, [1 / 3, 2 / 3])
        terc = lambda v: np.column_stack([(v <= q1), (v > q1) & (v <= q2), (v > q2)]).astype(np.float32)
        F = frames[Y]
        preds = {}
        m = compact_model().fit(Qtr, ytr); preds["compact"] = m.predict_proba(F["Q"])[:, 1]
        Ctr = np.hstack([Etr.astype(np.float32), terc(vtr)]); Cte = np.hstack([F["E"].astype(np.float32), terc(F["vol"])])
        m = LogisticRegression(C=0.1, max_iter=500).fit(Ctr, ytr); preds["cells"] = m.predict_proba(Cte)[:, 1]
        # compact + cells: the spline expansion of the compact columns beside the event columns
        pre = make_pipeline(StandardScaler(), SplineTransformer(n_knots=5, degree=3)).fit(Qtr)
        m = LogisticRegression(C=0.1, max_iter=1000).fit(np.hstack([pre.transform(Qtr), Ctr]), ytr)
        preds["compact + cells"] = m.predict_proba(np.hstack([pre.transform(F["Q"]), Cte]))[:, 1]
        # strongest firing cell
        base_tr = ytr.mean(); fires = Etr.sum(axis=0)
        dev = np.where(fires >= MIN_FIRES * len(tr) / STRIDE, (Etr * ytr[:, None]).sum(axis=0) / np.maximum(fires, 1) - base_tr, 0.0)
        strongest = np.full(len(F["y"]), np.nan)
        for j in np.argsort(-np.abs(dev)):
            if dev[j] == 0:
                break
            sel = (F["E"][:, j] > 0) & np.isnan(strongest)
            strongest[sel] = 1.0 if dev[j] > 0 else 0.0
        preds["strongest cell"] = np.where(np.isnan(strongest), 0.5, strongest)
        preds["previous-h reversal rule"] = F["rule"]
        y, t = F["y"], F["t"]
        hits = {n: ((p > 0.5) == y).astype(float) for n, p in preds.items()}
        for n, p in preds.items():
            acc, lo, hi = block_bootstrap_ci(hits[n], t)
            ll = f"{log_loss(y, np.clip(p, 1e-6, 1 - 1e-6)):.4f}" if n in ("compact", "cells", "compact + cells") else ""
            if n == "compact":
                vs = "reference"
            else:
                d, dlo, dhi = paired_difference_ci(hits[n], hits["compact"], t)
                sg = day_sign_test(hits[n], hits["compact"], t)
                vs = f"{d*100:+.2f} [{dlo*100:+.2f}, {dhi*100:+.2f}], days better {sg['share_days_a_better']*100:.0f}%"
            rows.append([Y, n, f"{len(y):,}", f"{acc*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", ll, vs])
        print(Y, [r[3] for r in rows[-5:]], flush=True)
    R = pd.DataFrame(rows, columns=["test year", "model", "minutes", "accuracy [95% CI]", "log loss", "vs compact"])
    R.to_csv(OUT / f"cells_compact_h{h}.csv", index=False)
    with open(OUT / f"cells_compact_h{h}.md", "w") as f:
        f.write(f"The named events against a compact continuous model, horizon {h} minutes, {a.start} to {a.end}, walk-forward by year on every minute. 'compact' is a spline logistic regression on nine continuous quantities (returns over 5 to 240 minutes in volatility units, 4-hour range position, log trailing-hour volatility, the last candle's wick shares and body sign); 'cells' is the published cells model (186 events plus the volatility tercile); 'compact + cells' has both; 'strongest cell' lets the strongest firing cell decide. Day-block 95% intervals; 'vs compact' is the paired accuracy difference with the share of days the row wins.\n\n")
        f.write("| test year | model | minutes | accuracy [95% CI] | log loss | vs compact |\n|---|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print(f"wrote cells_compact_h{h}.md")


if __name__ == "__main__":
    main()
