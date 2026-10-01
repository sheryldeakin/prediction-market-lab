"""Inside the window: the next five minutes against the close.

A pattern that fires at minute k of a 15-minute window says something about the next few
minutes; it need not say the same thing about where the window closes. For the strongest
patterns from both libraries, fired at minute k (k = 1 .. 10, so that five minutes remain
inside the window), two labels side by side:

  next 5      close of minute i+k+4 >= open of minute i+k (the short call)
  close       close of minute i+14 >= open of minute i (the window contract)

plus how often the two agree when the pattern fires, and the move in a $1 window contract
that a 5-basis-point bounce would imply at that minute under the driftless-market model of
delayed_entry.py (Phi(lead / sigma over the remaining minutes), before and after the bounce),
averaged over the firings. Years held refers to the next-5 deviation. 2018 to 2026.

    python -m models.btc_15m.within_window --start 2018 --end 2026-08
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from models.btc_15m.features import WINDOW, Series
from models.btc_15m.horizons import candidates, year_frame
from models.btc_15m.price_action import minute_events
from models.btc_15m.rules import vol_cutoffs
from models.btc_15m.stats import block_bootstrap_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
BOUNCE_BP = 5.0
BUCKETS = {"minutes 1-4": (1, 4), "minutes 5-7": (5, 7), "minutes 8-10": (8, 10)}
PATTERNS_HORIZONS = ["sweep: 5-min move < -3 sd", "sweep: 5-min move > +3 sd", "sweep: RSI14 < 25", "sweep: RSI14 > 75",
                     "sweep: range position < 0.05", "sweep: range position > 0.95"]
PATTERNS_PA = ["wick rejection at the 4h low", "wick rejection at the 4h high", "liquidity sweep of the 1h low (took it out, closed back above)",
               "liquidity sweep of the 1h high (took it out, closed back below)", "volume climax at a new 1h low (hour's largest volume)",
               "volume climax at a new 1h high (hour's largest volume)", "failed breakdown below the 4h low", "failed breakout above the 4h high",
               "reclaimed the session VWAP in the last 5 minutes after 30+ minutes below", "lost the session VWAP in the last 5 minutes after 30+ minutes above"]


def implied_move(lead_bp: np.ndarray, vol60: np.ndarray, k: np.ndarray, bounce_bp: float) -> np.ndarray:
    """Change in the implied probability of 'up' from a bounce of bounce_bp at minute k."""
    sigma = vol60 * np.sqrt(WINDOW - k)
    sigma = np.maximum(sigma, 1e-9)
    return norm.cdf((lead_bp + bounce_bp) / sigma) - norm.cdf(lead_bp / sigma)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2018)
    ap.add_argument("--end", default="2026-08")
    a = ap.parse_args()
    years = list(range(a.start, int(a.end[:4]) + 1))
    cutoffs = None
    recs = []
    for year in years:
        yf = year_frame(year, a.end)
        if yf is None:
            continue
        s, D = yf
        if cutoffs is None:
            cutoffs = vol_cutoffs(D[pd.to_datetime(D.t, unit="s").dt.month <= 3])
        idx = D.i.values
        k = ((D.t.values % 900) // 60).astype(int)                  # minute of the window
        in_range = (k >= 1) & (k <= 10) & (idx + (WINDOW - k) - 1 < len(s.c))
        wstart = idx - k                                             # the window's first minute
        n5 = np.full(len(D), np.nan); close = np.full(len(D), np.nan)
        ok = in_range & (idx + 4 < len(s.c))
        n5[ok] = (s.c[idx[ok] + 4] >= s.o[idx[ok]]).astype(float)
        close[ok] = (s.c[wstart[ok] + WINDOW - 1] >= s.o[wstart[ok]]).astype(float)
        lead = (s.c[np.maximum(idx - 1, 0)] / s.o[np.maximum(wstart, 0)] - 1) * 1e4
        move = implied_move(lead, D.vol60.values, k, BOUNCE_BP)
        C = candidates(D, cutoffs)
        E = minute_events(s)
        masks = {n: C[n] for n in PATTERNS_HORIZONS if n in C}
        masks.update({n: E[n][1][idx] for n in PATTERNS_PA if n in E})
        for name, m in masks.items():
            for bucket, (lo, hi) in BUCKETS.items():
                sel = m & ok & (k >= lo) & (k <= hi)
                base_sel = ok & (k >= lo) & (k <= hi)
                if sel.sum() < 100:
                    continue
                recs.append({"year": year, "pattern": name, "bucket": bucket, "fires": int(sel.sum()),
                             "next5": float(n5[sel].mean()), "next5_base": float(n5[base_sel].mean()),
                             "close": float(close[sel].mean()), "close_base": float(close[base_sel].mean()),
                             "agree": float((n5[sel] == close[sel]).mean()), "move": float(move[sel].mean()),
                             "t": D.t.values[sel], "n5v": n5[sel], "cv": close[sel]})
        cutoffs = vol_cutoffs(D)
        print(year, "done", flush=True)
    R = pd.DataFrame(recs)
    rows = []
    for (pat, bucket), g in R.groupby(["pattern", "bucket"], sort=False):
        w = g.fires.values
        n5_dev = g.next5.values - g.next5_base.values
        cl_dev = g.close.values - g.close_base.values
        sign = np.sign((n5_dev * w).sum())
        t = np.concatenate(g.t.values); n5v = np.concatenate(g.n5v.values); cv = np.concatenate(g.cv.values)
        _, lo5, hi5 = block_bootstrap_ci(n5v, t, n_boot=500)
        _, loc, hic = block_bootstrap_ci(cv, t, n_boot=500)
        rows.append({"pattern": pat, "bucket": bucket, "fires": int(w.sum()), "years": len(g), "years_held": int((np.sign(n5_dev) == sign).sum()),
                     "next5": float((g.next5 * w).sum() / w.sum()), "next5_dev": float((n5_dev * w).sum() / w.sum()), "next5_lo": lo5, "next5_hi": hi5,
                     "close": float((g.close * w).sum() / w.sum()), "close_dev": float((cl_dev * w).sum() / w.sum()), "close_lo": loc, "close_hi": hic,
                     "agree": float((g.agree * w).sum() / w.sum()), "move_c": float((g.move * w).sum() / w.sum()) * 100})
    S = pd.DataFrame(rows)
    S.to_csv(OUT / "within_window.csv", index=False)
    with open(OUT / "within_window.md", "w") as f:
        f.write(f"Patterns fired at minute k of a 15-minute window, {years[0]} to {a.end}: the next-5-minute direction against the window's close against its open. Up-rates with day-block 95% intervals and the deviation from the unconditional rate at those minutes (points); 'agree' is how often the two labels pointed the same way when the pattern fired; the last column is the change in the implied probability of the window contract, in cents on $1, from a {BOUNCE_BP:.0f} bp bounce at that minute under the driftless-market model (a model number, not a measured quote). Years held refers to the sign of the next-5 deviation.\n\n")
        f.write("| pattern | minute of window | fires | next 5 min up [95% CI] | deviation | window close up [95% CI] | deviation | agree | years held | implied contract move for a 5 bp bounce |\n|---|---|---|---|---|---|---|---|---|---|\n")
        for r in S.sort_values(["pattern", "bucket"]).itertuples():
            f.write(f"| {r.pattern} | {r.bucket} | {r.fires:,} | {r.next5*100:.1f}% [{r.next5_lo*100:.1f}, {r.next5_hi*100:.1f}] | {r.next5_dev*100:+.1f} | {r.close*100:.1f}% [{r.close_lo*100:.1f}, {r.close_hi*100:.1f}] | {r.close_dev*100:+.1f} | {r.agree*100:.0f}% | {r.years_held}/{r.years} | {r.move_c:.1f}c |\n")
        agg = S.groupby("bucket").apply(lambda x: pd.Series({"next5": (x.next5_dev.abs() * x.fires).sum() / x.fires.sum(), "close": (x.close_dev.abs() * x.fires).sum() / x.fires.sum(), "move": (x.move_c * x.fires).sum() / x.fires.sum()}))
        f.write("\nBy minute of the window, firing-weighted over the patterns: the mean absolute deviation of the next-5 call and of the close call, and the mean implied contract move.\n\n| minute of window | next-5 deviation (points) | close deviation (points) | implied move for 5 bp |\n|---|---|---|---|\n")
        for b, r in agg.iterrows():
            f.write(f"| {b} | {r.next5*100:.1f} | {r.close*100:.1f} | {r.move:.1f}c |\n")
    print("wrote within_window.md")


if __name__ == "__main__":
    main()
