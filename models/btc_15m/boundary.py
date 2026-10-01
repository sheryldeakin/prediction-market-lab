"""Where the minute-0 edge lives: by minute of the window, by boundary type, and by where
the 15-minute grid is placed.

  by minute      for each window the call at the open (forest, and the prev-window
                 baseline) is +1 for up and -1 for down; each minute's return is signed
                 by the call. The mean signed return per minute, in basis points, says
                 which minutes carry the edge. Minute 1 runs from the window's open price
                 to the close of its first candle.
  boundary type  the gap between the previous window's last close and this window's
                 open: flat (under half a basis point) or a gap. If the edge is print
                 noise at a shared boundary it should sit in the gapped windows.
  phase          the same comparison with windows starting 0..14 minutes after the
                 quarter hour. An effect tied to the clock boundary (where 15-minute
                 markets settle) shows at phase 0 only; an effect of any 15-minute
                 boundary shows at every phase.

    python -m models.btc_15m.boundary --start 2025-10 --end 2026-08
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.data import load
from models.btc_15m.evaluate import ALL, add_baseline_columns, walk_forward
from models.btc_15m.features import WINDOW, Series, dataset
from models.btc_15m.stats import block_bootstrap_ci, day_sign_test, paired_difference_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
FLAT_BP = 0.5


def minute_returns(s: Series, t: np.ndarray) -> np.ndarray:
    """(windows, 15) returns in bp: column 0 is open -> first close, column j is close j-1 -> close j."""
    ix = {int(x): i for i, x in enumerate(s.t)}
    i = np.array([ix[int(x)] for x in t])
    closes = np.stack([s.c[i + j] for j in range(WINDOW)], axis=1)
    prev = np.column_stack([s.o[i], closes[:, :-1]])
    return (closes / prev - 1) * 1e4


def boundary_gap(s: Series, t: np.ndarray) -> np.ndarray:
    """This window's open against the previous candle's close, in bp."""
    ix = {int(x): i for i, x in enumerate(s.t)}
    i = np.array([ix[int(x)] for x in t])
    return (s.o[i] / s.c[i - 1] - 1) * 1e4


def signed_by_call(pred: np.ndarray, R: np.ndarray) -> np.ndarray:
    return np.where(pred > 0.5, 1.0, -1.0)[:, None] * R


def compare(D: pd.DataFrame):
    """Walk-forward forest and prev-window at k = 0 on D. Returns preds, y, t."""
    pf, y, _, t = walk_forward(D, ALL, "forest")
    pb, yb, _, tb = walk_forward(D, ["prev_up"], "bitrate")
    assert np.array_equal(t, tb)
    return {"forest": pf, "prev-window": pb}, y, t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--phases", default=",".join(str(p) for p in range(15)))
    a = ap.parse_args()
    s = Series(load(a.start, a.end))

    # ---- phase 0: by minute and by boundary type ----
    D = add_baseline_columns(dataset(s, 0), 0)
    preds, y, t = compare(D)
    R = minute_returns(s, t)
    minute_rows = []
    for name, p in preds.items():
        S = signed_by_call(p, R)
        for j in range(WINDOW):
            m, lo, hi = block_bootstrap_ci(S[:, j], t)
            minute_rows.append([name, j + 1, f"{m:+.3f} [{lo:+.3f}, {hi:+.3f}]", f"{(S[:, j] > 0).mean()*100:.1f}%"])
    gap = boundary_gap(s, t)
    flat = np.abs(gap) < FLAT_BP
    hits = {n: ((p > 0.5) == y).astype(float) for n, p in preds.items()}
    gap_rows = []
    for label, m in (("flat (under 0.5 bp)", flat), ("gap (0.5 bp or more)", ~flat)):
        row = [label, int(m.sum()), f"{m.mean()*100:.1f}%"]
        for n in ("prev-window", "forest"):
            mu, lo, hi = block_bootstrap_ci(hits[n][m], t[m])
            row.append(f"{mu*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]")
        d, dlo, dhi = paired_difference_ci(hits["forest"][m], hits["prev-window"][m], t[m])
        row.append(f"{d*100:+.2f} [{dlo*100:+.2f}, {dhi*100:+.2f}]")
        gap_rows.append(row)
        print("boundary", row, flush=True)

    # ---- phases ----
    phase_rows = []
    for ph in [int(x) for x in a.phases.split(",")]:
        s.phase = ph
        Dp = add_baseline_columns(dataset(s, 0), 0)
        pp, yp, tp = compare(Dp)
        hp = {n: ((p > 0.5) == yp).astype(float) for n, p in pp.items()}
        row = [ph, len(yp)]
        for n in ("prev-window", "forest"):
            mu, lo, hi = block_bootstrap_ci(hp[n], tp)
            row.append(f"{mu*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]")
        d, dlo, dhi = paired_difference_ci(hp["forest"], hp["prev-window"], tp)
        row.append(f"{d*100:+.2f} [{dlo*100:+.2f}, {dhi*100:+.2f}]")
        row.append(f"{day_sign_test(hp['forest'], hp['prev-window'], tp)['share_days_a_better']*100:.0f}%")
        phase_rows.append(row)
        print("phase", row, flush=True)
    s.phase = 0

    with open(OUT / "boundary.md", "w") as f:
        f.write(f"Where the minute-0 edge lives, {a.start} to {a.end}, walk-forward by month. Each window's call at the open (forest on price + flow, and the prev-window baseline) signs every minute's return: positive means the minute moved the way the call said. Minute 1 runs from the open price to the first close. Mean signed return in basis points with a day-block 95% interval, and the share of windows in which that minute moved with the call.\n\n")
        f.write("| model | minute | signed return, bp [95% CI] | moved with the call |\n|---|---|---|---|\n")
        for r in minute_rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        f.write(f"\nBy boundary type: the gap between the previous candle's close and this window's open. Accuracy at the open with day-block 95% intervals; the last column is forest minus prev-window on the same windows.\n\n")
        f.write("| boundary | windows | share | prev-window | forest | forest minus prev-window |\n|---|---|---|---|---|---|\n")
        for r in gap_rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        f.write("\nBy phase: windows starting this many minutes after the quarter hour (0 is the clock grid). Accuracy at the open, day-block 95% intervals, forest minus prev-window on the same windows, and the share of days the forest beats prev-window.\n\n")
        f.write("| phase (minutes) | windows | prev-window | forest | forest minus prev-window | days forest better |\n|---|---|---|---|---|---|\n")
        for r in phase_rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print("wrote boundary.md")


if __name__ == "__main__":
    main()
