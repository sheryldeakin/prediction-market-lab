"""Direction with magnitude from any minute: given a pattern, how likely is the price to
touch +X basis points before -X within h minutes?

For every decision minute i, barrier X (bp) and horizon h: the outcome is +1 if a minute's
high reaches open(i) * (1 + X) before any minute's low reaches open(i) * (1 - X) within
minutes i .. i+h-1, -1 if the lower barrier comes first, 0 if neither is touched. A minute
whose high and low both cross is decided by its close (as in meta.py). Per pattern and
year: the share of firings with a touch, the share of touches that were up, against the
same shares when the pattern does not hold, with day-clustered z; a rotated-outcome null
per year gives the search-wide reference.

    python -m models.btc_15m.horizons_barrier --start 2018 --end 2026-08
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.features import Series
from models.btc_15m.horizons import MIN_FIRES, candidates, year_frame
from models.btc_15m.rules import vol_cutoffs
from models.btc_15m.search_null import rotate_within_groups
from models.btc_15m.stats import cluster_diff_pvalue

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
BARRIERS_BP = (5, 10, 20)
HORIZONS = (5, 15, 30)
NULL_RUNS = 20


def barrier_outcomes(s: Series, idx: np.ndarray, x_bp: float, h: int) -> np.ndarray:
    """+1 up barrier first, -1 down first, 0 neither, NaN when the horizon runs past the data."""
    n = len(s.c)
    o = s.o[idx]
    up_lvl, dn_lvl = o * (1 + x_bp / 1e4), o * (1 - x_bp / 1e4)
    out = np.zeros(len(idx))
    decided = np.zeros(len(idx), bool)
    valid = idx + h - 1 < n
    for k in range(h):
        j = np.minimum(idx + k, n - 1)
        up = s.h[j] >= up_lvl
        dn = s.l[j] <= dn_lvl
        both = up & dn
        res = np.where(both, np.where(s.c[j] >= o, 1.0, -1.0), np.where(up, 1.0, np.where(dn, -1.0, 0.0)))
        new = (~decided) & (res != 0)
        out[new] = res[new]
        decided |= new
    out[~valid] = np.nan
    return out


def score_year(s: Series, D: pd.DataFrame, cutoffs, rng, null_runs: int):
    idx, t = D.i.values, D.t.values
    months = pd.to_datetime(D.t, unit="s").dt.to_period("M").astype(str).values
    masks = {k: m for k, m in candidates(D, cutoffs).items() if m.sum() >= MIN_FIRES}
    rows, max_z = [], []
    for x in BARRIERS_BP:
        for h in HORIZONS:
            out = barrier_outcomes(s, idx, x, h)
            ok = ~np.isnan(out)
            touched = (out != 0) & ok
            up_first = (out > 0).astype(int)
            for name, m in masks.items():
                mt = m & touched
                if mt.sum() < MIN_FIRES:
                    continue
                b, se, p = cluster_diff_pvalue(m[touched], up_first[touched], t[touched])
                rows.append({"barrier_bp": x, "horizon": h, "pattern": name, "fires": int((m & ok).sum()), "touch_share": float(touched[m & ok].mean()),
                             "touch_share_all": float(touched[ok].mean()), "p_up_first": float(up_first[mt].mean()), "p_up_first_all": float(up_first[touched].mean()),
                             "diff": b, "z": b / se if se > 0 else 0.0, "p": p})
            for _ in range(null_runs // (len(BARRIERS_BP) * len(HORIZONS)) or 1):
                yr = rotate_within_groups(up_first[touched], months[touched], rng)
                best = 0.0
                for name, m in masks.items():
                    if (m & touched).sum() < MIN_FIRES:
                        continue
                    b, se, _ = cluster_diff_pvalue(m[touched], yr, t[touched])
                    best = max(best, abs(b / se) if se > 0 else 0.0)
                max_z.append(best)
    return pd.DataFrame(rows), np.array(max_z)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2018)
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--null-runs", type=int, default=NULL_RUNS)
    a = ap.parse_args()
    rng = np.random.default_rng(0)
    years = list(range(a.start, int(a.end[:4]) + 1))
    cutoffs = None
    frames, nulls = [], []
    for year in years:
        yf = year_frame(year, a.end)
        if yf is None:
            continue
        s, D = yf
        if cutoffs is None:
            cutoffs = vol_cutoffs(D[pd.to_datetime(D.t, unit="s").dt.month <= 3])
        R, mz = score_year(s, D, cutoffs, rng, a.null_runs)
        R.insert(0, "year", year)
        frames.append(R); nulls.append(mz)
        print(f"{year}: {len(R)} cells, max |z| {R.z.abs().max():.2f}, null max |z| median {np.median(mz):.2f}", flush=True)
        cutoffs = vol_cutoffs(D)
    A = pd.concat(frames, ignore_index=True)
    null_all = np.concatenate(nulls)
    A["p_adj"] = [(1 + (null_all >= abs(z)).sum()) / (len(null_all) + 1) for z in A.z]
    A.to_csv(OUT / "horizons_barrier_cells.csv", index=False)
    g = []
    for (pat, x, h), grp in A.groupby(["pattern", "barrier_bp", "horizon"]):
        w = grp.fires.values
        sign = np.sign(grp["diff"].sum())
        g.append({"pattern": pat, "barrier_bp": x, "horizon": h, "years": len(grp), "years_held": int((np.sign(grp["diff"]) == sign).sum()),
                  "fires": int(w.sum()), "touch_share": float((grp.touch_share * w).sum() / w.sum()), "touch_share_all": float((grp.touch_share_all * w).sum() / w.sum()),
                  "p_up_first": float((grp.p_up_first * w).sum() / w.sum()), "p_up_first_all": float((grp.p_up_first_all * w).sum() / w.sum()),
                  "min_p_adj": float(grp.p_adj.min())})
    G = pd.DataFrame(g)
    G["deviation"] = G.p_up_first - G.p_up_first_all
    G.to_csv(OUT / "horizons_barrier_summary.csv", index=False)
    held = G[G.years_held == G.years].sort_values("deviation", key=np.abs, ascending=False)
    with open(OUT / "horizons_barrier.md", "w") as f:
        f.write(f"Direction with magnitude from any minute, {years[0]} to {a.end}: given a pattern, the probability that the price touches +X basis points before -X within h minutes. 'Touched' is the share of firings in which either barrier was reached in time (against the share for all minutes); 'up first' is the share of those touches that hit the upper barrier first, against the same share for all touched minutes; deviation is the difference in points. Years held: years in which the sign of the deviation matched the pooled sign. Adjusted p is search-wide (single-step max-T over rotated outcomes). Top 40 cells by absolute deviation that held in every year.\n\n")
        f.write("| pattern | barrier (bp) | horizon (min) | fires on | touched (pattern) | touched (all) | up first (pattern) | up first (all) | deviation (points) | years held | min adjusted p |\n|---|---|---|---|---|---|---|---|---|---|---|\n")
        for r in held.head(40).itertuples():
            f.write(f"| {r.pattern} | {r.barrier_bp} | {r.horizon} | {r.fires:,} | {r.touch_share*100:.0f}% | {r.touch_share_all*100:.0f}% | {r.p_up_first*100:.1f}% | {r.p_up_first_all*100:.1f}% | {r.deviation*100:+.1f} | {r.years_held}/{r.years} | {r.min_p_adj:.4f} |\n")
        f.write("\nBy barrier and horizon: the unconditional share of minutes with a touch and of touches that were up, the number of cells that held every year, and the largest deviation among them.\n\n| barrier (bp) | horizon (min) | touched (all) | up first (all) | cells held every year | largest deviation (points) |\n|---|---|---|---|---|---|\n")
        for (x, h), grp in G.groupby(["barrier_bp", "horizon"]):
            hh = grp[grp.years_held == grp.years]
            f.write(f"| {x} | {h} | {grp.touch_share_all.mean()*100:.0f}% | {grp.p_up_first_all.mean()*100:.1f}% | {len(hh)} | {hh.deviation.abs().max()*100:.1f} |\n")
        f.write(f"\nNull: the largest |z| across cells on rotated outcomes has median {np.median(null_all):.2f} and 95th percentile {np.quantile(null_all, 0.95):.2f}; the real search's largest |z| is {A.z.abs().max():.2f}.\n")
    print("wrote horizons_barrier.md")


if __name__ == "__main__":
    main()
