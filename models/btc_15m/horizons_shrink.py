"""Each conditional cell as a small meta-analysis across years.

A cell's nine yearly deviations are nine noisy estimates of effects that may differ by
year. The DerSimonian-Laird random-effects model gives a pooled mean that weights years by
their precision, a between-year standard deviation tau (how much the true effect moves
from year to year), and a shrunken estimate for each year that pulls noisy years toward
the pool. The 2026 shrunken estimate is the honest "what to expect now" number: this
year's data, pulled toward the pool by an amount set by how consistent the cell has been.

Reads horizons_cells.csv; writes horizons_shrink.md and horizons_shrink.csv.

    python -m models.btc_15m.horizons_shrink
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("results/btc_15m")


def random_effects(d: np.ndarray, se: np.ndarray) -> dict:
    """DerSimonian-Laird. Returns pooled mean, its standard error, tau, and per-year shrunken means."""
    w = 1 / se**2
    fixed = (w * d).sum() / w.sum()
    Q = (w * (d - fixed) ** 2).sum()
    k = len(d)
    c = w.sum() - (w**2).sum() / w.sum()
    tau2 = max(0.0, (Q - (k - 1)) / c) if c > 0 else 0.0
    w_re = 1 / (se**2 + tau2)
    mu = (w_re * d).sum() / w_re.sum()
    se_mu = np.sqrt(1 / w_re.sum())
    shrink = tau2 / (tau2 + se**2)                    # weight on the year's own estimate
    shrunk = shrink * d + (1 - shrink) * mu
    return {"mu": mu, "se_mu": se_mu, "tau": np.sqrt(tau2), "shrunk": shrunk, "shrink_weight": shrink, "I2": max(0.0, (Q - (k - 1)) / Q) if Q > 0 else 0.0}


def main():
    A = pd.read_csv(OUT / "horizons_cells.csv")
    rows = []
    for (pat, h), g in A.groupby(["pattern", "horizon"]):
        g = g.sort_values("year")
        if len(g) < 3 or (g.se <= 0).any():
            continue
        r = random_effects(g["diff"].values, g.se.values)
        last = g.year.iloc[-1]
        rows.append({"pattern": pat, "horizon": h, "years": len(g), "pooled": r["mu"], "pooled_se": r["se_mu"], "tau": r["tau"], "I2": r["I2"],
                     "last_year": int(last), "last_raw": float(g["diff"].iloc[-1]), "last_shrunk": float(r["shrunk"][-1]), "last_weight_on_own": float(r["shrink_weight"][-1]),
                     "fires": int(g.fires.sum())})
    S = pd.DataFrame(rows)
    S.to_csv(OUT / "horizons_shrink.csv", index=False)
    top = S.sort_values("pooled", key=np.abs, ascending=False).head(30)
    with open(OUT / "horizons_shrink.md", "w") as f:
        f.write("Each cell pooled across years with a random-effects model (DerSimonian-Laird): the pooled deviation in points with its standard error, tau (the between-year standard deviation of the true effect, points), I-squared (the share of the yearly variation that is real change rather than noise), and for the latest year the raw deviation, the shrunken deviation, and the weight the shrunken value puts on that year's own data. The 30 cells with the largest pooled deviation.\n\n")
        f.write("| pattern | horizon (min) | pooled (se) | tau | I-squared | latest year | raw | shrunk | weight on own year |\n|---|---|---|---|---|---|---|---|---|\n")
        for r in top.itertuples():
            f.write(f"| {r.pattern} | {r.horizon} | {r.pooled*100:+.1f} ({r.pooled_se*100:.1f}) | {r.tau*100:.1f} | {r.I2*100:.0f}% | {r.last_year} | {r.last_raw*100:+.1f} | {r.last_shrunk*100:+.1f} | {r.last_weight_on_own:.2f} |\n")
        f.write(f"\nOver all {len(S)} cells: median tau {S.tau.median()*100:.1f} points, median I-squared {S.I2.median()*100:.0f}%, median weight on the latest year's own data {S.last_weight_on_own.median():.2f}. A high I-squared with a stable sign (the usual case here) means the size of a cell changes from year to year while its direction does not, so the pooled value is a long-run average and the shrunken latest-year value is the better guide to the present.\n")
    print("wrote horizons_shrink.md")


if __name__ == "__main__":
    main()
