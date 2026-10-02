"""Do the strongest cells survive a later entry and coarser error blocks?

Two of the review's questions about the conditional cells. First, the label starts at the
open of the decision minute, which is the same print as the close of the last candle the
features read; a cell could be partly that shared print, or a bid-ask bounce that a trader
could not capture. Second, the intervals cluster by day; a reader may ask what month blocks
say. For the strongest cells of both libraries (one per group of near-identical events):

  embargo 0   the published label: close of minute i+h-1 against the open of minute i
  embargo 1   enter one minute later: close of minute i+h against the open of minute i+1
  embargo 2   two minutes later, same horizon length
  month CI    the embargo-0 deviation with calendar months as the bootstrap blocks

Deviations are firing-minutes up-rate minus the rest, points, pooled over years with the
firing-weighted mean, day-clustered errors (and month blocks for the last column), years
held out of years with at least MIN_FIRES firings.

    python -m models.btc_15m.cells_entry --start 2018 --end 2026-08
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.cells_profile import JACCARD_DEDUP, clusters_at, event_masks, jaccard_matrix, pooled
from models.btc_15m.features import Series
from models.btc_15m.horizons import MIN_FIRES, year_frame
from models.btc_15m.rules import vol_cutoffs
from models.btc_15m.stats import cluster_diff_pvalue, month_block_bootstrap_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
EMBARGOS = (0, 1, 2)
HORIZONS = (5, 30)
CELLS_PER_HORIZON = 12


def embargo_label(s: Series, idx: np.ndarray, h: int, e: int) -> np.ndarray:
    """close of minute idx+e+h-1 against the open of minute idx+e; NaN past the data."""
    start = idx + e
    end = start + h - 1
    ok = end < len(s.c)
    y = np.full(len(idx), np.nan)
    y[ok] = (s.c[end[ok]] >= s.o[start[ok]]).astype(float)
    return y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2018)
    ap.add_argument("--end", default="2026-08")
    a = ap.parse_args()
    per_year = {}                                      # year -> (masks dict, idx, t, labels by (h, e))
    cutoffs = None
    names = None
    co = None
    for year in range(a.start, int(a.end[:4]) + 1):
        yf = year_frame(year, a.end)
        if yf is None:
            continue
        s, D = yf
        if cutoffs is None:
            cutoffs = vol_cutoffs(D[pd.to_datetime(D.t, unit="s").dt.month <= 3])
        M = event_masks(s, D, cutoffs)
        if names is None:
            names = sorted(M); co = np.zeros((len(names), len(names)))
        X = np.column_stack([M[k] for k in names]).astype(np.float32)
        for lo in range(0, len(X), 1 << 17):
            co += X[lo:lo + (1 << 17)].T @ X[lo:lo + (1 << 17)]
        L = {(h, e): embargo_label(s, D.i.values, h, e) for h in HORIZONS for e in EMBARGOS}
        per_year[year] = (M, D.t.values, L)
        cutoffs = vol_cutoffs(D)
        print(year, flush=True)
    years = sorted(per_year)

    # rank cells at embargo 0, one per near-identical group
    jlab = clusters_at(jaccard_matrix(co), JACCARD_DEDUP)
    rows = []
    for h in HORIZONS:
        stats = {}
        for name in names:
            per = []
            for y in years:
                M, t, L = per_year[y]
                yy = L[(h, 0)]; ok = ~np.isnan(yy); m = M[name][ok]
                if m.sum() < MIN_FIRES:
                    per.append((int(m.sum()), 0.0, float("inf"))); continue
                b, se, _ = cluster_diff_pvalue(m, yy[ok].astype(int), t[ok])
                per.append((int(m.sum()), b, se))
            stats[name] = pooled(per)
        held = [n for n in names if stats[n][2] == stats[n][3] == len(years)]
        order = sorted(held, key=lambda n: -abs(stats[n][0]))
        picked, seen = [], set()
        for n in order:
            c = jlab[names.index(n)]
            if c in seen:
                continue
            seen.add(c); picked.append(n)
            if len(picked) == CELLS_PER_HORIZON:
                break
        for name in picked:
            row = {"event": name, "horizon": h}
            for e in EMBARGOS:
                per = []
                for y in years:
                    M, t, L = per_year[y]
                    yy = L[(h, e)]; ok = ~np.isnan(yy); m = M[name][ok]
                    if m.sum() < MIN_FIRES:
                        per.append((int(m.sum()), 0.0, float("inf"))); continue
                    b, se, _ = cluster_diff_pvalue(m, yy[ok].astype(int), t[ok])
                    per.append((int(m.sum()), b, se))
                dev, se, hd, yr = pooled(per)
                row.update({f"dev_e{e}": dev, f"se_e{e}": se, f"held_e{e}": hd, f"years_e{e}": yr})
            # month-block interval at embargo 0: deviation values (fired minutes' labels minus the year's non-fired rate) pooled across years
            vals, ts = [], []
            for y in years:
                M, t, L = per_year[y]
                yy = L[(h, 0)]; ok = ~np.isnan(yy); m = M[name] & ok
                base = yy[ok & ~M[name]].mean()
                vals.append(yy[m] - base); ts.append(t[m])
            _, mlo, mhi = month_block_bootstrap_ci(np.concatenate(vals), np.concatenate(ts), n_boot=1000)
            row.update({"month_lo": mlo, "month_hi": mhi})
            rows.append(row)
            print(h, name, f"{row['dev_e0']*100:+.1f} -> {row['dev_e1']*100:+.1f} -> {row['dev_e2']*100:+.1f}", flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "cells_entry.csv", index=False)
    R["ratio_e1"] = R.dev_e1 / R.dev_e0; R["ratio_e2"] = R.dev_e2 / R.dev_e0

    def fmt(dev, se, hd, yr):
        return f"{dev*100:+.1f} [{(dev-1.96*se)*100:+.1f}, {(dev+1.96*se)*100:+.1f}] {hd}/{yr}"
    with open(OUT / "cells_entry.md", "w") as f:
        f.write(f"Later entry and coarser blocks for the {CELLS_PER_HORIZON} strongest cells at each of {' and '.join(str(h) for h in HORIZONS)} minutes (one per group of near-identical events), {years[0]} to {a.end}. Deviation of the up-rate when the event fires from when it does not, points, 95% interval from day-clustered errors, years held. Embargo e: the label is the close of minute i+e+h-1 against the open of minute i+e, so e=0 is the published label (its open is the same print as the last candle the features read) and e=1 skips that print and one full minute. The last column is the embargo-0 deviation's 95% interval with calendar months as the bootstrap blocks.\n\n")
        f.write("| event | horizon (min) | embargo 0 | embargo 1 | embargo 2 | embargo 0, month-block interval |\n|---|---|---|---|---|---|\n")
        for r in R.itertuples():
            f.write(f"| {r.event} | {r.horizon} | {fmt(r.dev_e0, r.se_e0, r.held_e0, r.years_e0)} | {fmt(r.dev_e1, r.se_e1, r.held_e1, r.years_e1)} | {fmt(r.dev_e2, r.se_e2, r.held_e2, r.years_e2)} | [{r.month_lo*100:+.1f}, {r.month_hi*100:+.1f}] |\n")
        for h in HORIZONS:
            g = R[R.horizon == h]
            f.write(f"\nAt {h} minutes, across the {len(g)} cells: the embargo-1 deviation is {g.ratio_e1.median()*100:.0f}% of the embargo-0 one (median; range {g.ratio_e1.min()*100:.0f}% to {g.ratio_e1.max()*100:.0f}%) and embargo-2 is {g.ratio_e2.median()*100:.0f}%; {int((g.held_e1 == g.years_e1).sum())} of {len(g)} cells still hold every year at embargo 1 and {int((g.held_e2 == g.years_e2).sum())} at embargo 2; {int(((g.month_lo > 0) | (g.month_hi < 0)).sum())} of the {len(g)} month-block intervals exclude zero.\n")
    print("wrote cells_entry.md")


if __name__ == "__main__":
    main()
