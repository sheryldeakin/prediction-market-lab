"""Are the conditional cells of horizons.py a last-print effect? Score the same cells under
a label built from 60-second volume-weighted prices: the VWAP of the decision minute
against the VWAP of the horizon's last minute. A pattern such as "price at its 4-hour
low" is partly "the last trade was at the bid", and the next print is then more likely
above it; averaged prices remove most of that. The deviation under each label is
compared cell by cell, pooled over the years and per year.

Needs the per-second tick tables for every month (scripts/fetch_ticks_history.py).

    python -m models.btc_15m.horizons_vwap --start 2018 --end 2026-08
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.features import Series, features_all
from models.btc_15m.horizons import HORIZONS, MIN_FIRES, candidates, labels, year_frame
from models.btc_15m.rules import vol_cutoffs
from models.btc_15m.settlement import Vwap
from models.btc_15m.stats import cluster_diff_pvalue
from models.btc_15m.ticks import load_seconds

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")


def vwap_labels(vw: Vwap, t: np.ndarray) -> dict[int, np.ndarray]:
    """label_h = VWAP of minute i+h-1 >= VWAP of minute i; NaN where either minute has no
    trades. At horizon 1 both references would be the same minute, so that horizon uses the
    minute's first and second halves (30-second VWAPs)."""
    open_ref = vw(t, t + 60)
    out = {}
    for h in HORIZONS:
        if h == 1:
            o1, c1 = vw(t, t + 30), vw(t + 30, t + 60)
            out[h] = np.where(np.isnan(o1) | np.isnan(c1), np.nan, (c1 >= o1).astype(float))
            continue
        close_ref = vw(t + 60 * (h - 1), t + 60 * h)
        lab = np.where(np.isnan(open_ref) | np.isnan(close_ref), np.nan, (close_ref >= open_ref).astype(float))
        out[h] = lab
    return out


def cells(masks: dict, L: dict, t: np.ndarray) -> pd.DataFrame:
    rows = []
    for h in HORIZONS:
        y = L[h]
        ok = ~np.isnan(y)
        yy, tt = y[ok].astype(int), t[ok]
        for name, m in masks.items():
            mm = m[ok]
            if mm.sum() < MIN_FIRES:
                continue
            b, se, p = cluster_diff_pvalue(mm, yy, tt)
            rows.append({"horizon": h, "pattern": name, "fires": int(mm.sum()), "diff": b, "z": b / se if se > 0 else 0.0})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2018)
    ap.add_argument("--end", default="2026-08")
    a = ap.parse_args()
    years = list(range(a.start, int(a.end[:4]) + 1))
    cutoffs = None
    out = []
    for year in years:
        yf = year_frame(year, a.end)
        if yf is None:
            continue
        s, D = yf
        if cutoffs is None:
            cutoffs = vol_cutoffs(D[pd.to_datetime(D.t, unit="s").dt.month <= 3])
        last = min(pd.Period(f"{year}-12", "M"), pd.Period(a.end, "M"))
        vw = Vwap(load_seconds(f"{year}-01", str(last)))
        idx, t = D.i.values, D.t.values
        C = {k: m for k, m in candidates(D, cutoffs).items() if m.sum() >= MIN_FIRES}
        P = cells(C, labels(s, idx), t).rename(columns={"diff": "diff_print", "z": "z_print", "fires": "fires_print"})
        V = cells(C, vwap_labels(vw, t), t).rename(columns={"diff": "diff_vwap", "z": "z_vwap", "fires": "fires_vwap"})
        M = P.merge(V, on=["horizon", "pattern"])
        M.insert(0, "year", year)
        out.append(M)
        print(f"{year}: {len(M)} cells; median |dev| print {M.diff_print.abs().median()*100:.2f}, vwap {M.diff_vwap.abs().median()*100:.2f}", flush=True)
        cutoffs = vol_cutoffs(D)
    A = pd.concat(out, ignore_index=True)
    A.to_csv(OUT / "horizons_vwap_cells.csv", index=False)
    g = A.groupby(["pattern", "horizon"]).apply(lambda x: pd.Series({
        "dev_print": (x.diff_print * x.fires_print).sum() / x.fires_print.sum(),
        "dev_vwap": (x.diff_vwap * x.fires_vwap).sum() / x.fires_vwap.sum(),
        "years": int(len(x)), "years_same_sign_vwap": int((np.sign(x.diff_vwap) == np.sign(x.diff_print.sum())).sum())})).reset_index()
    g["years"] = g.years.astype(int); g["years_same_sign_vwap"] = g.years_same_sign_vwap.astype(int)
    g["retained"] = g.dev_vwap / g.dev_print
    g.to_csv(OUT / "horizons_vwap_summary.csv", index=False)
    top = g.sort_values("dev_print", key=np.abs, ascending=False).head(30)
    with open(OUT / "horizons_vwap.md", "w") as f:
        f.write(f"The conditional cells under two labels, {years[0]} to {a.end}, every minute as a decision time: the last print (close of the horizon's last minute against the open of the decision minute) and 60-second VWAPs (the decision minute's VWAP against the last minute's VWAP). Deviation from the unconditional up-rate in points, firing-weighted over the years; 'retained' is the VWAP deviation as a share of the last-print one; the last column is the number of years in which the VWAP deviation had the pooled last-print sign. At horizon 1 the VWAP label compares the decision minute's first and second 30 seconds, so it is a different (shorter) question from the last-print label there. The 30 cells with the largest last-print deviation.\n\n")
        f.write("| pattern | horizon (min) | deviation, last print | deviation, VWAP | retained | years same sign under VWAP |\n|---|---|---|---|---|---|\n")
        for r in top.itertuples():
            f.write(f"| {r.pattern} | {r.horizon} | {r.dev_print*100:+.1f} | {r.dev_vwap*100:+.1f} | {r.retained*100:.0f}% | {r.years_same_sign_vwap}/{r.years} |\n")
        by_h = g.groupby("horizon").apply(lambda x: pd.Series({"median_retained": x.retained.median(), "cells": len(x), "sign_kept": (np.sign(x.dev_vwap) == np.sign(x.dev_print)).mean()}))
        f.write("\nBy horizon, over all cells: the median share of the last-print deviation retained under the VWAP label, and the share of cells whose sign is unchanged.\n\n| horizon (min) | cells | median retained | sign unchanged |\n|---|---|---|---|\n")
        for h, r in by_h.iterrows():
            f.write(f"| {h} | {int(r.cells)} | {r.median_retained*100:.0f}% | {r.sign_kept*100:.0f}% |\n")
    print("wrote horizons_vwap.md")


if __name__ == "__main__":
    main()
