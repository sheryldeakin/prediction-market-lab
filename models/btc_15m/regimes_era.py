"""Is the regime doubling a volatility effect or an era effect?

The regime study found the strongest conditional cells about twice as large in the daily
HMM's high-volatility state as in its low-volatility state. The high-volatility days are
concentrated in 2020 to 2022, when every cell was larger (the eras table), and the
trailing-hour volatility tercile does not scale the cells at all (the cells profile). So
the doubling could be the era wearing a volatility label. This study scores the same cells
by HMM state inside each era, so that the comparison between states is made among days of
the same period:

  per cell      deviation of the up-rate from the state's own base rate within the era,
                day-block 95% interval, firings; for the low, mid and high volatility states
                (the 'high vol, down' days join 'high vol') in each era with HMM states
                (2019 is the first year the walk-forward HMM scores)
  ratios        high over low, pooled over all years (the regime study's number) and pooled
                within eras (each era's high and low deviations weighted by the smaller
                firing count, so no era is compared with another)

If the within-era ratio is near 1 while the all-years ratio is near 2, the doubling is the
era. The HMM states are the regime study's, read from results/btc_15m/regimes_daily.csv:
the previous day's filtered state, known at the time.

    python -m models.btc_15m.regimes_era --start 2017-08 --end 2026-08
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.data import load
from models.btc_15m.features import Series, features_all
from models.btc_15m.horizons import candidates, labels
from models.btc_15m.regimes import TOP_CELLS
from models.btc_15m.rules import vol_cutoffs
from models.btc_15m.stats import block_bootstrap_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
ERAS = {"2019": (2019, 2019), "2020-21": (2020, 2021), "2022-23": (2022, 2023), "2024-26": (2024, 2026)}
STATES = ("low", "mid", "high")
MIN_N = 300


def vol_group(label: str) -> str:
    """'low vol, flat' -> 'low'; 'high vol, down' -> 'high'; '' -> ''."""
    return label.split(" ")[0] if label else ""


def minute_states(R: pd.DataFrame, t: np.ndarray) -> np.ndarray:
    """The previous day's HMM volatility group for each minute (R.t is the day's last close time)."""
    day_index = pd.Series(R.hmm.fillna("").map(vol_group).values, index=(R.t.values - 60) // 86400)
    return day_index.reindex(t // 86400 - 1).fillna("").values


def cell_table(y: np.ndarray, m: np.ndarray, state: np.ndarray, year: np.ndarray, t: np.ndarray) -> dict:
    """Deviation (dev, lo, hi, n) of a cell in each (era, state) and over all years per state."""
    out = {}
    ok = ~np.isnan(y)
    for era, (a, b) in list(ERAS.items()) + [("all", (ERAS["2019"][0], ERAS["2024-26"][1]))]:
        in_era = ok & (year >= a) & (year <= b)
        for st in STATES:
            sel = in_era & (state == st)
            fired = sel & m
            if fired.sum() < MIN_N:
                out[(era, st)] = (np.nan, np.nan, np.nan, int(fired.sum()))
                continue
            base = y[sel].mean()
            dev, lo, hi = block_bootstrap_ci(y[fired] - base, t[fired], n_boot=500)
            out[(era, st)] = (dev, lo, hi, int(fired.sum()))
    return out


def ratios(table: dict) -> tuple[float, float, int]:
    """(all-years high/low ratio, within-era pooled high/low ratio, eras used). Pooling weights each era by the smaller of its two firing counts."""
    all_hi, all_lo = table[("all", "high")], table[("all", "low")]
    r_all = all_hi[0] / all_lo[0] if np.isfinite(all_hi[0]) and np.isfinite(all_lo[0]) and all_lo[0] != 0 else np.nan
    num = den = 0.0
    used = 0
    for era in ERAS:
        hi, lo = table[(era, "high")], table[(era, "low")]
        if np.isfinite(hi[0]) and np.isfinite(lo[0]):
            w = min(hi[3], lo[3])
            num += w * hi[0]; den += w * lo[0]; used += 1
    r_within = num / den if used and den != 0 else np.nan
    return r_all, r_within, used


def fmt(c) -> str:
    dev, lo, hi, n = c
    return f"{dev*100:+.1f} [{lo*100:+.1f}, {hi*100:+.1f}] n={n:,}" if np.isfinite(dev) else (f"n={n}" if n else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2017-08")
    ap.add_argument("--end", default="2026-08")
    a = ap.parse_args()
    s = Series(load(a.start, a.end))
    F = features_all(s)
    F = F[F.t >= int(pd.Timestamp("2018-01-01").timestamp())].reset_index(drop=True)
    cut = vol_cutoffs(F[pd.to_datetime(F.t, unit="s").dt.year == 2018])
    C = candidates(F, cut)
    L = labels(s, F.i.values)
    R = pd.read_csv(OUT / "regimes_daily.csv")
    state = minute_states(R, F.t.values)
    year = pd.to_datetime(F.t, unit="s").dt.year.values
    top = pd.read_csv(OUT / "horizons_summary.csv")
    top = top[top.years_held == top.years].sort_values("deviation", key=np.abs, ascending=False).head(TOP_CELLS)
    rows, ratio_rows = [], []
    for r in top.itertuples():
        tab = cell_table(L[int(r.horizon)], C[r.pattern], state, year, F.t.values)
        r_all, r_within, used = ratios(tab)
        ratio_rows.append({"pattern": r.pattern, "horizon": int(r.horizon), "ratio_all_years": r_all, "ratio_within_eras": r_within, "eras_used": used})
        for (era, st), c in tab.items():
            rows.append({"pattern": r.pattern, "horizon": int(r.horizon), "era": era, "state": st, "deviation": c[0], "lo": c[1], "hi": c[2], "n": c[3]})
        print(r.pattern, int(r.horizon), f"all {r_all:.2f} within {r_within:.2f}", flush=True)
    T = pd.DataFrame(rows); T.to_csv(OUT / "regimes_era.csv", index=False)
    Q = pd.DataFrame(ratio_rows); Q.to_csv(OUT / "regimes_era_ratios.csv", index=False)

    with open(OUT / "regimes_era.md", "w") as f:
        f.write(f"The {TOP_CELLS} strongest conditional cells by the daily HMM's volatility state inside each era, 2019 to {a.end} (2019 is the first year the walk-forward HMM scores; 'high vol, down' days are counted as high). Deviation of the up-rate from that state's own rate within the era, points, day-block 95% interval, firings; blank where a state fired fewer than {MIN_N} times in the era. The ratio columns divide the high-volatility deviation by the low-volatility one: over all years (the regime study's comparison, which mixes eras) and pooled within eras (each era's two deviations weighted by the smaller firing count).\n\n")
        heads = [f"{era} {st}" for era in ERAS for st in STATES]
        f.write("| pattern | horizon (min) | " + " | ".join(heads) + " | high/low, all years | high/low, within eras |\n|---|---|" + "---|" * len(heads) + "---|---|\n")
        for r in top.itertuples():
            sub = T[(T.pattern == r.pattern) & (T.horizon == int(r.horizon))].set_index(["era", "state"])
            q = Q[(Q.pattern == r.pattern) & (Q.horizon == int(r.horizon))].iloc[0]
            cells = [fmt(tuple(sub.loc[(era, st), ["deviation", "lo", "hi", "n"]])) for era in ERAS for st in STATES]
            f.write(f"| {r.pattern} | {int(r.horizon)} | " + " | ".join(cells) + f" | {q.ratio_all_years:.2f} | {q.ratio_within_eras:.2f} |\n")
        ok = Q.dropna()
        f.write(f"\nAcross the {len(ok)} cells with both ratios: high over low is {ok.ratio_all_years.median():.2f} over all years (range {ok.ratio_all_years.min():.2f} to {ok.ratio_all_years.max():.2f}) and {ok.ratio_within_eras.median():.2f} within eras (range {ok.ratio_within_eras.min():.2f} to {ok.ratio_within_eras.max():.2f}).\n")
        f.write("\nDays per volatility state in each era, from the regime study's daily table.\n\n| era | low | mid | high |\n|---|---|---|---|\n")
        Ry = pd.to_datetime(R.t, unit="s").dt.year
        for era, (a_, b_) in ERAS.items():
            g = R[(Ry >= a_) & (Ry <= b_)].hmm.fillna("").map(vol_group)
            f.write(f"| {era} | {(g == 'low').sum()} | {(g == 'mid').sum()} | {(g == 'high').sum()} |\n")
    print("wrote regimes_era.md")


if __name__ == "__main__":
    main()
