"""Is the minute-0 call still worth anything a few seconds after the open?

Nothing can be bought at the exact boundary print. This study enters N seconds after the
open (N = 1, 5, 30) at a price implied by where Bitcoin is then: with the lead L (bp from
the open to the last second's VWAP) and the volatility expected over the remaining
900 - N seconds, a driftless market would price "up" at

    q_up = Phi(L / (sigma_per_second * sqrt(900 - N))),  sigma_per_second = vol60 / sqrt(60)

(vol60 is the trailing standard deviation of one-minute returns, in bp). Buying the side
the call favours at that price returns hit - q on each window. A positive mean says the
call knows something the first N seconds of price movement have not already priced; at
N = 0 the price is 0.5 and the return is accuracy - 0.5. No fees or spread: this measures
the information, not a trade.

    python -m models.btc_15m.delayed_entry --start 2025-10 --end 2026-08
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from models.btc_15m.data import load
from models.btc_15m.evaluate import ALL, add_baseline_columns, walk_forward
from models.btc_15m.features import Series, dataset
from models.btc_15m.settlement import Vwap
from models.btc_15m.stats import block_bootstrap_ci, month_block_bootstrap_ci
from models.btc_15m.ticks import load_seconds

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")


def implied_up(lead_bp: np.ndarray, vol60: np.ndarray, n_sec: int) -> np.ndarray:
    sigma = vol60 / np.sqrt(60) * np.sqrt(900 - n_sec)
    return norm.cdf(lead_bp / np.maximum(sigma, 1e-9))


def call_return(pred: np.ndarray, y: np.ndarray, q_up: np.ndarray) -> np.ndarray:
    """Return of buying the favoured side at the implied price: 1 - q if right, -q if wrong."""
    up = pred > 0.5
    price = np.where(up, q_up, 1 - q_up)
    return (up == (y == 1)).astype(float) - price


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--seconds", default="0,1,5,30")
    a = ap.parse_args()
    s = Series(load(a.start, a.end))
    vw = Vwap(load_seconds(a.start, a.end))
    D = add_baseline_columns(dataset(s, 0), 0)
    pf, y, _, t = walk_forward(D, ALL, "forest")
    pb, _, _, _ = walk_forward(D, ["prev_up"], "bitrate")
    E = D.set_index("t").loc[t]
    ix = {int(x): i for i, x in enumerate(s.t)}
    open_px = s.o[np.array([ix[int(x)] for x in t])]
    rows = []
    for n in [int(x) for x in a.seconds.split(",")]:
        if n == 0:
            q = np.full(len(t), 0.5)
        else:
            px = vw(t + n - 1, t + n)
            fallback = vw(t + n - 5, t + n)
            px = np.where(np.isnan(px), fallback, px)
            px = np.where(np.isnan(px), open_px, px)
            q = implied_up((px / open_px - 1) * 1e4, E.vol60.values, n)
        for name, p in (("prev-window", pb), ("forest", pf)):
            r = call_return(p, y, q)
            m, lo, hi = block_bootstrap_ci(r, t)
            _, mlo, mhi = month_block_bootstrap_ci(r, t)
            rows.append([n, name, len(t), f"{np.mean(np.abs(q - 0.5))*100:.2f}", f"{m*100:+.2f} [{lo*100:+.2f}, {hi*100:+.2f}] [{mlo*100:+.2f}, {mhi*100:+.2f}]"])
            print(rows[-1], flush=True)
    with open(OUT / "delayed_entry.md", "w") as f:
        f.write(f"Entering N seconds after the open at the price a driftless market would set from the lead so far and the trailing volatility, {a.start} to {a.end}, walk-forward calls made at the open. Return per window in cents per $1 contract, buying the side the call favours, no fees or spread; intervals from day blocks then month blocks. The fourth column is how far the implied price has already moved from 0.5, on average, in cents.\n\n")
        f.write("| seconds after open | call | windows | implied price distance from 0.5 (c) | return per window, c [day CI] [month CI] |\n|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print("wrote delayed_entry.md")


if __name__ == "__main__":
    main()
