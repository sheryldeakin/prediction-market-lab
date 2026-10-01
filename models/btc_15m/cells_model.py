"""One short-horizon probability from the cells, and whether the cells keep their promises.

Two questions about the conditional cells of horizons.md and the price-action library:

  model        every minute, which events are firing (both libraries) plus the trailing-
               hour volatility tercile: a logistic regression on those 0/1 columns for the
               next-h-minute direction, fit on all earlier years, scored on each later year.
               Against two baselines on the same minutes: the previous-h-minute reversal
               rule (one bit) and "the strongest firing cell decides" (the cell with the
               largest absolute deviation on the training years, its training direction;
               abstain if none fires). Also the model's accuracy on the minutes where it is
               confident (probability beyond 0.55 either way).
  calibration  for each strong cell (held every training year, adjusted p at or below
               0.05), the up-rate the training years promised against the up-rate the test
               year delivered, pooled into bins of the promise. If a 58% cell delivers 58%,
               the cells are usable as probabilities; if it delivers 54%, they are
               directions with inflated sizes.

    python -m models.btc_15m.cells_model --start 2018 --end 2026-08 --horizon 5
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from models.btc_15m.features import Series
from models.btc_15m.horizons import MIN_FIRES, candidates, labels, year_frame
from models.btc_15m.price_action import masks_for, minute_events
from models.btc_15m.rules import vol_cutoffs
from models.btc_15m.stats import block_bootstrap_ci, day_sign_test, paired_difference_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")


def event_matrix(s: Series, D: pd.DataFrame, cutoffs) -> tuple[np.ndarray, list[str]]:
    """0/1 columns: every event of both libraries, plus the vol60 tercile (cut on the training years' cutoffs)."""
    C = candidates(D, cutoffs)
    E = masks_for(D, minute_events(s))
    cols = {**{f"lib: {k}": v for k, v in C.items()}, **{f"pa: {k}": v for k, v in E.items()}}
    names = sorted(cols)
    X = np.column_stack([cols[n].astype(np.float32) for n in names])
    return X, names


def previous_h_rule(s: Series, idx: np.ndarray, h: int) -> np.ndarray:
    """Call the opposite of the last h minutes: 1 (up) when the previous h minutes fell."""
    prev = s.c[idx - 1] / s.c[np.maximum(idx - 1 - h, 0)] - 1
    return (prev < 0).astype(float)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2018)
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--horizon", type=int, default=5)
    a = ap.parse_args()
    h = a.horizon
    years = list(range(a.start, int(a.end[:4]) + 1))
    frames = {}
    cutoffs = None
    for year in years:
        yf = year_frame(year, a.end)
        if yf is None:
            continue
        s, D = yf
        if cutoffs is None:
            cutoffs = vol_cutoffs(D[pd.to_datetime(D.t, unit="s").dt.month <= 3])
        X, names = event_matrix(s, D, cutoffs)
        y = labels(s, D.i.values)[h]
        ok = ~np.isnan(y)
        frames[year] = {"X": X[ok], "y": y[ok].astype(int), "t": D.t.values[ok], "rule": previous_h_rule(s, D.i.values[ok], h), "names": names,
                        "vol": D.vol60.values[ok]}
        cutoffs = vol_cutoffs(D)
        print(year, "features", X.shape, flush=True)

    rows, cal = [], []
    for Y in [y for y in frames if y >= 2020]:
        tr_years = [y for y in frames if y < Y]
        Xtr = np.vstack([frames[y]["X"] for y in tr_years]); ytr = np.concatenate([frames[y]["y"] for y in tr_years])
        vtr = np.concatenate([frames[y]["vol"] for y in tr_years])
        q1, q2 = np.quantile(vtr, [1 / 3, 2 / 3])
        terc = lambda v: np.column_stack([(v <= q1), (v > q1) & (v <= q2), (v > q2)]).astype(np.float32)
        Xtr_full = np.hstack([Xtr, terc(vtr)])
        model = LogisticRegression(C=0.1, max_iter=500).fit(Xtr_full, ytr)
        F = frames[Y]
        Xte_full = np.hstack([F["X"], terc(F["vol"])])
        p = model.predict_proba(Xte_full)[:, 1]
        y, t = F["y"], F["t"]
        base_tr = ytr.mean()
        # strongest-cell baseline: deviation per event on the training years, direction from it
        fires_tr = Xtr.sum(axis=0)
        dev = np.where(fires_tr >= MIN_FIRES * len(tr_years), (Xtr * ytr[:, None]).sum(axis=0) / np.maximum(fires_tr, 1) - base_tr, 0.0)
        order = np.argsort(-np.abs(dev))
        strongest = np.full(len(y), np.nan)
        for j in order:
            if dev[j] == 0:
                break
            m = (F["X"][:, j] > 0) & np.isnan(strongest)
            strongest[m] = 1.0 if dev[j] > 0 else 0.0
        hits = {"cells model": ((p > 0.5) == y).astype(float), "previous-h reversal rule": (F["rule"] == y).astype(float)}
        sc = ~np.isnan(strongest)
        hits_strongest = (strongest[sc] == y[sc]).astype(float)
        conf = np.abs(p - 0.5) > 0.05
        for name, hh in hits.items():
            m, lo, hi = block_bootstrap_ci(hh, t)
            if name == "cells model":
                d, dlo, dhi = paired_difference_ci(hh, hits["previous-h reversal rule"], t)
                sg = day_sign_test(hh, hits["previous-h reversal rule"], t)
                vs = f"{d*100:+.2f} [{dlo*100:+.2f}, {dhi*100:+.2f}], days better {sg['share_days_a_better']*100:.0f}%"
            else:
                vs = "baseline"
            rows.append([Y, name, f"{len(y):,}", "100%", f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", vs])
        m, lo, hi = block_bootstrap_ci(hits_strongest, t[sc])
        rows.append([Y, "strongest firing cell decides", f"{int(sc.sum()):,}", f"{sc.mean()*100:.0f}%", f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", "abstains when no cell fires"])
        hc = hits["cells model"][conf]
        m, lo, hi = block_bootstrap_ci(hc, t[conf])
        rows.append([Y, "cells model, confident only (p beyond 0.55)", f"{int(conf.sum()):,}", f"{conf.mean()*100:.0f}%", f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", ""])
        print(rows[-4:], flush=True)
        # calibration of the strong cells: promised (training up-rate) vs delivered (test up-rate)
        for j in np.where(np.abs(dev) >= 0.03)[0]:
            fires_te = F["X"][:, j] > 0
            if fires_te.sum() < MIN_FIRES:
                continue
            promised = dev[j] + base_tr
            delivered = y[fires_te].mean()
            cal.append({"year": Y, "event": F["names"][j], "promised": promised, "delivered": delivered, "fires": int(fires_te.sum()), "base_test": y.mean()})
    R = pd.DataFrame(rows, columns=["test year", "model", "minutes scored", "share of minutes", "accuracy [95% CI]", "vs the reversal rule"])
    R.to_csv(OUT / "cells_model.csv", index=False)
    Cal = pd.DataFrame(cal)
    Cal.to_csv(OUT / "cells_calibration.csv", index=False)
    Cal["promise_dev"] = Cal.promised - Cal.base_test
    Cal["delivered_dev"] = Cal.delivered - Cal.base_test
    bins = pd.cut(Cal.promise_dev.abs() * 100, [3, 4, 5, 6, 8, 12, 30], right=False)
    with open(OUT / "cells_model.md", "w") as f:
        f.write(f"One probability per minute from the cells, horizon {h} minutes, {years[0]} to {a.end}: a logistic regression on every event of both libraries (0/1) plus the trailing-hour volatility tercile, fit on all earlier years and scored on each later year. Baselines on the same minutes: call the opposite of the previous {h} minutes (one bit), and 'the strongest firing cell decides' (direction and ranking from the training years, abstaining when nothing fires). Day-block 95% intervals; 'vs the reversal rule' is the paired difference with the share of days the model wins.\n\n")
        f.write("| test year | model | minutes scored | share of minutes | accuracy [95% CI] | vs the reversal rule |\n|---|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        f.write(f"\nCalibration of the strong cells, forward: for every event whose training-years deviation was at least 3 points, the up-rate the training years promised against the up-rate the test year delivered (both as deviations from the respective base rates), pooled into bins of the promised size. {len(Cal):,} cell-years.\n\n")
        f.write("| promised deviation (points) | cell-years | mean promised | mean delivered | delivered as a share of promised | sign kept |\n|---|---|---|---|---|---|\n")
        for b, g in Cal.groupby(bins, observed=True):
            same = (np.sign(g.delivered_dev) == np.sign(g.promise_dev)).mean()
            ratio = (g.delivered_dev * np.sign(g.promise_dev)).mean() / g.promise_dev.abs().mean()
            f.write(f"| {b} | {len(g):,} | {g.promise_dev.abs().mean()*100:.1f} | {(g.delivered_dev * np.sign(g.promise_dev)).mean()*100:.1f} | {ratio*100:.0f}% | {same*100:.0f}% |\n")
    print("wrote cells_model.md")


if __name__ == "__main__":
    main()
