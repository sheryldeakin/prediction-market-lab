"""Does the boundary effect survive a price someone could settle on?

The main label compares two single prints: the open of the window's first minute and
the close of its last. Back-to-back windows share a boundary print, so noise in that one
print pushes the previous window and this one in opposite directions, which looks like
reversal. Averaged reference prices remove most of that noise. This study relabels every
window with 60-second volume-weighted prices from the tick data and re-runs the minute-0
comparison.

  last print     the main label: close of minute 15 >= open of minute 1
  VWAP ending at each boundary
                 open reference = VWAP of [T - 60 s, T), close reference = VWAP of
                 [T + 840 s, T + 900 s). The previous window's close reference is this
                 window's open reference, as with a settlement average taken before a
                 boundary. Known at the open, so the open reference is not a forecast.
  VWAP inside the window
                 open reference = VWAP of [T, T + 60 s), close reference = VWAP of the
                 last 60 s. Neighbouring windows share no trades at all.

Each label gets its own one-bit baseline (the previous window's label under the same
definition) as well as the candle-based prev-window baseline, and the forest on price +
flow features, walk-forward by month.

    python -m models.btc_15m.settlement --start 2025-10 --end 2026-08
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.data import load
from models.btc_15m.evaluate import ALL, add_baseline_columns, walk_forward
from models.btc_15m.features import Series, dataset
from models.btc_15m.stats import block_bootstrap_ci, day_sign_test, month_block_bootstrap_ci, paired_difference_ci
from models.btc_15m.ticks import load_seconds

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")


class Vwap:
    """60-second (or any) VWAP over [a, b) from the per-second table, by cumulative sums."""

    def __init__(self, r: pd.DataFrame):
        self.sec = r.sec.values
        self.cv = np.concatenate([[0.0], np.cumsum(r.vol.values)])
        self.cq = np.concatenate([[0.0], np.cumsum(r.qty.values)])

    def __call__(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        i, j = np.searchsorted(self.sec, a), np.searchsorted(self.sec, b)
        q = self.cq[j] - self.cq[i]
        return np.where(q > 0, (self.cv[j] - self.cv[i]) / np.where(q > 0, q, 1.0), np.nan)


def vwap_labels(T: np.ndarray, vw: Vwap, width: int = 60) -> dict[str, np.ndarray]:
    """Labels (1 up, 0 down, NaN when a reference has no trades) for windows opening at T."""
    end_open, end_close = vw(T - width, T), vw(T + 900 - width, T + 900)
    in_open, in_close = vw(T, T + width), vw(T + 900 - width, T + 900)
    lab = lambda o, c: np.where(np.isnan(o) | np.isnan(c), np.nan, (c >= o).astype(float))
    return {"vwap_end": lab(end_open, end_close), "vwap_in": lab(in_open, in_close)}


def previous_label(t: np.ndarray, y: np.ndarray) -> np.ndarray:
    """The label of the window that closed at each window's open (NaN if not in the data)."""
    s = pd.Series(y, index=t)
    return s.reindex(t - 900).values


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    a = ap.parse_args()
    s = Series(load(a.start, a.end))
    vw = Vwap(load_seconds(a.start, a.end))
    D = add_baseline_columns(dataset(s, 0), 0)
    labels = {"last print": D.y.values.astype(float), **vwap_labels(D.t.values, vw)}
    for name, y in labels.items():
        D[f"lab_{name}"] = y
        D[f"prev_{name}"] = previous_label(D.t.values, y)
    ok = np.all([~np.isnan(D[f"lab_{n}"].values) & ~np.isnan(D[f"prev_{n}"].values) for n in labels], axis=0)
    D = D[ok].reset_index(drop=True)
    agree = {n: float((D[f"lab_{n}"] == D["lab_last print"]).mean()) for n in labels}

    rows = []
    for name in labels:
        col = f"lab_{name}"
        D[col] = D[col].astype(int)
        D["prev_same"] = D[f"prev_{name}"].astype(int)
        preds = {}
        for model, cols, kind in (("own previous label", ["prev_same"], "bitrate"), ("prev-window (candles)", ["prev_up"], "bitrate"), ("forest", ALL, "forest")):
            pred, y, _, t = walk_forward(D, cols, kind, label=col)
            preds[model] = pred
        hits = {m: ((p > 0.5) == y).astype(float) for m, p in preds.items()}
        for m in preds:
            mu, lo, hi = block_bootstrap_ci(hits[m], t)
            _, mlo, mhi = month_block_bootstrap_ci(hits[m], t)
            if m == "forest":
                d, dlo, dhi = paired_difference_ci(hits["forest"], hits["own previous label"], t)
                sg = day_sign_test(hits["forest"], hits["own previous label"], t)
                vs = f"{d*100:+.2f} [{dlo*100:+.2f}, {dhi*100:+.2f}], days better {sg['share_days_a_better']*100:.0f}%"
            else:
                vs = ""
            rows.append([name, f"{agree[name]*100:.1f}%", f"{y.mean()*100:.1f}%", m, len(y), f"{mu*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}] [{mlo*100:.2f}, {mhi*100:.2f}]", vs])
            print(rows[-1], flush=True)
    with open(OUT / "settlement.md", "w") as f:
        f.write(f"Minute-0 accuracy under three labels, {a.start} to {a.end}, walk-forward by month. 'Last print' is the main label; the VWAP labels use 60-second volume-weighted prices from the tick data, either ending at each boundary or inside the window's first and last minute. 'Own previous label' calls the opposite of (or the same as, whichever the training months favour) the previous window's label under the same definition. Intervals: day blocks, then month blocks. The last column is the forest minus the own-previous-label baseline, day-block interval, and the share of days the forest wins.\n\n")
        f.write("| label | agrees with last print | share up | model | n | accuracy [day CI] [month CI] | forest vs own previous label |\n|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print("wrote settlement.md")


if __name__ == "__main__":
    main()
