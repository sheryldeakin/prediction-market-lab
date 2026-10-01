"""Conditional direction tables across years: "if this pattern holds now, which way does
the price go over the next h minutes?", for every minute as a decision time.

Scope
  years      each calendar year from 2018 to the last full month; features need the
             prior HISTORY minutes, so each year is loaded with the month before it
  decision   every minute i (not only quarter-hour boundaries); the features are the
             minute-0 features of the main model, built by features_all
  horizons   1, 3, 5, 10, 15, 30 minutes: label_h = close of minute i+h-1 >= open of minute i
  patterns   the hand-named event library (rules.events) plus the threshold sweeps of the
             wide search (events2.base_events); volatility-decile cutoffs come from the
             previous year, so a year never defines its own "high volatility"
  statistic  up-rate when the pattern holds minus when it does not, day-clustered z
             (stats.cluster_diff_pvalue), per year and per horizon
  null       per year, labels rotated within each month, NULL_RUNS times; the largest
             |z| across patterns and horizons in each run gives a search-wide adjusted
             p for every cell (single-step max-T)
  stability  a cell is reported with the number of years in which its sign matched the
             pooled sign, out of the years in which it fired at least MIN_FIRES times

Also written: the reversal rule year by year (call the opposite of the previous 15
minutes), at the quarter-hour grid and at every minute, with day-block intervals.

No cell is "definite". Each is a probability with an interval, a firing rate and the
years in which it held, and the adjusted p says whether it would survive a search this
wide on labels that carry no information.

    python -m models.btc_15m.horizons --start 2018 --end 2026-08
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.data import load
from models.btc_15m.events2 import base_events
from models.btc_15m.features import WINDOW, Series, features_all
from models.btc_15m.rules import events, vol_cutoffs
from models.btc_15m.search_null import rotate_within_groups
from models.btc_15m.stats import block_bootstrap_ci, cluster_diff_pvalue

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
HORIZONS = (1, 3, 5, 10, 15, 30)
MIN_FIRES = 500
NULL_RUNS = 50


def labels(series: Series, idx: np.ndarray) -> dict[int, np.ndarray]:
    """label_h for decision minutes idx: NaN where the horizon runs past the data."""
    out = {}
    n = len(series.c)
    for h in HORIZONS:
        end = idx + h - 1
        ok = end < n
        lab = np.full(len(idx), np.nan)
        lab[ok] = (series.c[end[ok]] >= series.o[idx[ok]]).astype(float)
        out[h] = lab
    return out


def candidates(D: pd.DataFrame, cutoffs) -> dict[str, np.ndarray]:
    """Library events (minute-0 set) plus the wide search's threshold sweeps."""
    c = {k: v for k, v in events(D, 0, cutoffs).items()}
    for k, v in base_events(D).items():
        c.setdefault(f"sweep: {k}", v)
    return c


def year_frame(year: int, end: str) -> tuple[Series, pd.DataFrame] | None:
    """Features for every minute of `year` (with the month before for history)."""
    first, last = f"{year - 1}-12", f"{year}-12"
    if pd.Period(last, "M") > pd.Period(end, "M"):
        last = end
    if pd.Period(first, "M") > pd.Period(last, "M"):
        return None
    s = Series(load(first, last))
    D = features_all(s)
    D = D[pd.to_datetime(D.t, unit="s").dt.year == year].reset_index(drop=True)
    return s, D


def score_year(s: Series, D: pd.DataFrame, cutoffs, rng, null_runs: int, masks_in: dict | None = None):
    """Per-cell statistics for one year, and the null distribution of the max |z|.
    masks_in: an external candidate set aligned to D's rows (the price-action library);
    default is the event library plus the sweeps."""
    idx = D.i.values
    L = labels(s, idx)
    C = masks_in if masks_in is not None else candidates(D, cutoffs)
    t = D.t.values
    months = pd.to_datetime(D.t, unit="s").dt.to_period("M").astype(str).values
    rows = []
    masks = {k: m for k, m in C.items() if m.sum() >= MIN_FIRES}
    for h in HORIZONS:
        y = L[h]
        ok = ~np.isnan(y)
        yy, tt = y[ok].astype(int), t[ok]
        for name, m in masks.items():
            mm = m[ok]
            if mm.sum() < MIN_FIRES:
                continue
            b, se, p = cluster_diff_pvalue(mm, yy, tt)
            rows.append({"horizon": h, "pattern": name, "fires": int(mm.sum()), "share": float(mm.mean()), "up_rate": float(yy[mm].mean()),
                         "base": float(yy.mean()), "diff": b, "se": se, "z": b / se if se > 0 else 0.0, "p": p})
    R = pd.DataFrame(rows)
    max_z = []
    for _ in range(null_runs):
        best = 0.0
        for h in HORIZONS:
            y = L[h]
            ok = ~np.isnan(y)
            yr = rotate_within_groups(y[ok].astype(int), months[ok], rng)
            tt = t[ok]
            for name, m in masks.items():
                mm = m[ok]
                if mm.sum() < MIN_FIRES:
                    continue
                b, se, _ = cluster_diff_pvalue(mm, yr, tt)
                best = max(best, abs(b / se) if se > 0 else 0.0)
        max_z.append(best)
    return R, np.array(max_z)


def reversal_rows(s: Series, D: pd.DataFrame, year: int) -> list:
    """The one-bit rule (opposite of the previous 15 minutes) on the 15-minute label, at the
    quarter-hour grid and at every minute."""
    idx = D.i.values
    y = labels(s, idx)[15]
    ok = ~np.isnan(y)
    prev_up = D.win1.values >= 0
    call_up = ~prev_up
    hit = (call_up == (y == 1)).astype(float)
    out = []
    for name, sel in (("quarter-hour grid", ok & (D.t.values % 900 == 0)), ("every minute", ok)):
        m, lo, hi = block_bootstrap_ci(hit[sel], D.t.values[sel])
        out.append([year, name, int(sel.sum()), f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2018)
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--null-runs", type=int, default=NULL_RUNS)
    a = ap.parse_args()
    rng = np.random.default_rng(0)
    years = list(range(a.start, int(a.end[:4]) + 1))
    all_rows, rev_rows, null_by_year = [], [], {}
    cutoffs = None
    for year in years:
        yf = year_frame(year, a.end)
        if yf is None:
            continue
        s, D = yf
        if cutoffs is None:                                     # first year: cutoffs from its own first quarter, used for that year only
            cutoffs = vol_cutoffs(D[pd.to_datetime(D.t, unit="s").dt.month <= 3])
        R, max_z = score_year(s, D, cutoffs, rng, a.null_runs)
        R.insert(0, "year", year)
        all_rows.append(R)
        null_by_year[year] = max_z
        rev_rows += reversal_rows(s, D, year)
        print(f"{year}: {len(D):,} minutes, {R.pattern.nunique()} patterns, max |z| {R.z.abs().max():.2f}, null max |z| median {np.median(max_z):.2f}", flush=True)
        cutoffs = vol_cutoffs(D)                                # next year uses this year's deciles
    A = pd.concat(all_rows, ignore_index=True)
    null_all = np.concatenate(list(null_by_year.values()))
    A["p_adj"] = [(1 + (null_all >= abs(z)).sum()) / (len(null_all) + 1) for z in A.z]
    A.to_csv(OUT / "horizons_cells.csv", index=False)

    # pooled summary per (pattern, horizon): years held, mean deviation, weighted up-rate
    g = []
    for (pat, h), grp in A.groupby(["pattern", "horizon"]):
        sign = np.sign(grp["diff"].sum())
        held = int((np.sign(grp["diff"]) == sign).sum())
        fires = int(grp.fires.sum())
        up = float((grp.up_rate * grp.fires).sum() / fires)
        base = float((grp.base * grp.fires).sum() / fires)
        g.append({"pattern": pat, "horizon": h, "years": len(grp), "years_held": held, "fires": fires, "share": float(grp.share.mean()),
                  "up_rate": up, "deviation": up - base, "min_p_adj": float(grp.p_adj.min()), "all_years_adj_05": bool((grp.p_adj <= 0.05).all())})
    G = pd.DataFrame(g).sort_values("deviation", key=np.abs, ascending=False)
    G.to_csv(OUT / "horizons_summary.csv", index=False)

    with open(OUT / "horizons.md", "w") as f:
        f.write(f"Conditional direction by horizon, {years[0]} to {a.end}, every minute as a decision time. For each pattern and horizon: pooled up-rate of the next h minutes when the pattern holds, deviation from the unconditional rate in points, share of minutes on which it fires, years in which the sign matched the pooled sign out of years with at least {MIN_FIRES} firings, and the smallest search-wide adjusted p across years (single-step max-T over {a.null_runs} rotated-label runs per year; the smallest possible value is {1/(len(null_all)+1):.4f}). Top 40 cells by absolute deviation that held in every year; every cell is in horizons_summary.csv and every year in horizons_cells.csv.\n\n")
        f.write("| pattern | horizon (min) | up-rate | deviation (points) | fires on | years held | min adjusted p |\n|---|---|---|---|---|---|---|\n")
        top = G[G.years_held == G.years].head(40)
        for r in top.itertuples():
            f.write(f"| {r.pattern} | {r.horizon} | {r.up_rate*100:.1f}% | {r.deviation*100:+.1f} | {r.share*100:.1f}% | {r.years_held}/{r.years} | {r.min_p_adj:.4f} |\n")
        f.write("\nBy horizon: how many cells held their sign in every year, and the largest absolute deviation among them.\n\n| horizon (min) | cells tested | held every year | largest deviation among those (points) |\n|---|---|---|---|\n")
        for h in HORIZONS:
            gh = G[G.horizon == h]
            held = gh[gh.years_held == gh.years]
            f.write(f"| {h} | {len(gh)} | {len(held)} | {held.deviation.abs().max()*100:.1f} |\n")
        f.write(f"\nNull: the largest |z| across all patterns and horizons on rotated labels has median {np.median(null_all):.2f} and 95th percentile {np.quantile(null_all, 0.95):.2f}; the real search's largest |z| is {A.z.abs().max():.2f}.\n")
        f.write("\nThe reversal rule by year: call the opposite of the previous 15 minutes, scored on the next 15 minutes, at the quarter-hour grid and at every minute. Day-block 95% intervals.\n\n| year | decision times | n | accuracy [95% CI] |\n|---|---|---|---|\n")
        for r in rev_rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print("wrote horizons.md")


if __name__ == "__main__":
    main()
