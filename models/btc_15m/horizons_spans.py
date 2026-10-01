"""Do the conditional cells of horizons.py change over time, and how much history should
a live rule look back on? Reads results/btc_15m/horizons_cells.csv (one row per pattern,
horizon and year) and writes horizons_spans.md.

  eras       each cell's deviation in 2018-19, 2020-21, 2022-23 and 2024-26 (firing-
             weighted), with the slope of its deviation against the year and whether
             its sign ever flipped
  spans      for each test year Y from 2020: select the cells that were strong (adjusted
             p at or below 0.05) and same-signed in every year of a selection span
             (Y-1 only; Y-2 to Y-1; Y-3 to Y-1; all years before Y), then score the
             selection on Y alone: how many cells, how many kept their sign, and the
             firing-weighted accuracy of calling the selected direction. The spans are
             separate tests; nothing is pooled across them.

    python -m models.btc_15m.horizons_spans
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("results/btc_15m")
ERAS = {"2018-19": (2018, 2019), "2020-21": (2020, 2021), "2022-23": (2022, 2023), "2024-26": (2024, 2026)}
SPANS = {"previous year": 1, "previous 2 years": 2, "previous 3 years": 3, "all earlier years": 99}


def weighted_dev(g: pd.DataFrame) -> float:
    return float(((g.up_rate - g.base) * g.fires).sum() / g.fires.sum()) if g.fires.sum() else np.nan


def era_table(A: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (pat, h), g in A.groupby(["pattern", "horizon"]):
        r = {"pattern": pat, "horizon": h}
        for era, (a, b) in ERAS.items():
            r[era] = weighted_dev(g[(g.year >= a) & (g.year <= b)])
        dev = (g.up_rate - g.base).values
        if len(g) >= 3:
            r["slope_per_year"] = float(np.polyfit(g.year.values, dev, 1)[0])
        else:
            r["slope_per_year"] = np.nan
        r["sign_flips"] = int((np.sign(dev) != np.sign(dev.sum())).sum())
        r["pooled"] = weighted_dev(g)
        rows.append(r)
    return pd.DataFrame(rows)


def span_test(A: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """Select on a span of earlier years, score on the test year. Returns one row per
    (test year, span)."""
    years = sorted(A.year.unique())
    rows = []
    for Y in [y for y in years if y >= 2020]:
        test = A[A.year == Y].set_index(["pattern", "horizon"])
        for span, k in SPANS.items():
            sel_years = [y for y in years if y < Y and y >= Y - k]
            S = A[A.year.isin(sel_years)]
            chosen = []
            for (pat, h), g in S.groupby(["pattern", "horizon"]):
                if len(g) < len(sel_years):
                    continue
                signs = np.sign(g["diff"].values)
                if (g.p_adj <= alpha).all() and (signs == signs[0]).all() and signs[0] != 0:
                    chosen.append((pat, h, int(signs[0])))
            held = fires = right = 0
            for pat, h, sg in chosen:
                if (pat, h) not in test.index:
                    continue
                r = test.loc[(pat, h)]
                held += int(np.sign(r["diff"]) == sg)
                acc = r.up_rate if sg > 0 else 1 - r.up_rate
                fires += r.fires
                right += acc * r.fires
            rows.append({"test_year": Y, "selected_on": span, "years_in_span": len(sel_years), "cells_selected": len(chosen),
                         "kept_sign": held, "accuracy_calling_selected_direction": right / fires if fires else np.nan, "firings": int(fires)})
    return pd.DataFrame(rows)


def main():
    A = pd.read_csv(OUT / "horizons_cells.csv")
    E = era_table(A)
    E.to_csv(OUT / "horizons_eras.csv", index=False)
    held = E[E.sign_flips == 0]
    S = span_test(A)
    S.to_csv(OUT / "horizons_spans.csv", index=False)
    with open(OUT / "horizons_spans.md", "w") as f:
        f.write("Eras: each cell's deviation of the conditional up-rate from the unconditional rate, in points, firing-weighted within each era, for the 25 cells with the largest pooled deviation that never flipped sign. Slope is the change in deviation per year from a straight-line fit across the nine years.\n\n")
        f.write("| pattern | horizon (min) | 2018-19 | 2020-21 | 2022-23 | 2024-26 | pooled | slope per year |\n|---|---|---|---|---|---|---|---|\n")
        for r in held.sort_values("pooled", key=np.abs, ascending=False).head(25).itertuples():
            f.write(f"| {r.pattern} | {r.horizon} | {getattr(r, '_3')*100:+.1f} | {getattr(r, '_4')*100:+.1f} | {getattr(r, '_5')*100:+.1f} | {getattr(r, '_6')*100:+.1f} | {r.pooled*100:+.1f} | {r.slope_per_year*100:+.2f} |\n")
        shrinking = (np.sign(held.slope_per_year) != np.sign(held.pooled)).mean()
        f.write(f"\nAcross the {len(held)} cells that never flipped sign, the deviation moved toward zero over the years in {shrinking*100:.0f}% of them; the median absolute deviation was {held[['2018-19']].abs().median().item()*100:.1f} points in 2018-19 and {held[['2024-26']].abs().median().item()*100:.1f} in 2024-26.\n")
        f.write("\nSpans: cells selected on earlier years only (adjusted p at or below 0.05 and the same sign in every year of the span), then scored on the test year alone. Accuracy is the firing-weighted rate at which the selected direction was right in the test year; 50% is chance.\n\n")
        f.write("| test year | selected on | cells selected | kept their sign | accuracy of the selected direction | firings in test year |\n|---|---|---|---|---|---|\n")
        for r in S.itertuples():
            acc = f"{r.accuracy_calling_selected_direction*100:.1f}%" if not np.isnan(r.accuracy_calling_selected_direction) else ""
            f.write(f"| {r.test_year} | {r.selected_on} | {r.cells_selected} | {r.kept_sign} | {acc} | {r.firings:,} |\n")
        f.write("\nBy span, averaged over test years:\n\n| selected on | mean cells selected | share that kept their sign | mean accuracy of the selected direction |\n|---|---|---|---|\n")
        for span, g in S.groupby("selected_on", sort=False):
            kept = g.kept_sign.sum() / max(g.cells_selected.sum(), 1)
            f.write(f"| {span} | {g.cells_selected.mean():.0f} | {kept*100:.0f}% | {g.accuracy_calling_selected_direction.mean()*100:.1f}% |\n")
    print("wrote horizons_spans.md")


if __name__ == "__main__":
    main()
