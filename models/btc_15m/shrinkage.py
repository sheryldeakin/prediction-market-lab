"""How much of the headline increment is the luck of picking the best of several models?

The report leads with the model that did best against the baseline. Choosing the best of
M noisy estimates inflates the winner. The bootstrap estimates that inflation directly:
resample days with replacement, pick the best model in each resample the same way, and
compare the winner's increment there with the same model's increment in the original
data. The average gap is the selection bias; subtracting it gives a corrected increment
(Efron and Tibshirani's bootstrap bias correction, applied to the selection step).

Reads the per-window walk-forward predictions written by evaluate.py.

    python -m models.btc_15m.shrinkage --minutes 0,3
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.evaluate import baseline_name

OUT = Path("results/btc_15m")
NOT_CANDIDATES = {"majority", "prev-window", "win1-logistic", "lead-only", "lead-z"}


def selection_corrected(inc: np.ndarray, t: np.ndarray, names: list[str], n_boot: int = 2000, seed: int = 0) -> dict:
    """inc: (windows, models) per-window hit minus baseline hit. Returns the observed best
    model and increment, the bootstrap estimate of the selection bias, and the corrected
    increment with a day-block interval for the corrected value."""
    days = t // 86400
    uniq, inv = np.unique(days, return_inverse=True)
    sums = np.stack([np.bincount(inv, weights=inc[:, j]) for j in range(inc.shape[1])], axis=1)
    counts = np.bincount(inv)
    obs = sums.sum(axis=0) / counts.sum()
    best = int(np.argmax(obs))
    rng = np.random.default_rng(seed)
    bias, corrected = [], []
    for _ in range(n_boot):
        pick = rng.integers(0, len(uniq), len(uniq))
        b = sums[pick].sum(axis=0) / counts[pick].sum()
        w = int(np.argmax(b))
        bias.append(b[w] - obs[w])                 # how far the resample's winner sits above its own original value
        corrected.append(b[best])
    bias = float(np.mean(bias))
    c = np.array(corrected) - bias
    return {"best": names[best], "observed": float(obs[best]), "bias": bias, "corrected": float(obs[best] - bias),
            "low": float(np.quantile(c, 0.025)), "high": float(np.quantile(c, 0.975))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", default="0,3")
    a = ap.parse_args()
    rows = []
    for k in [int(x) for x in a.minutes.split(",")]:
        O = pd.read_parquet(OUT / f"oof_k{k}.parquet")
        base = baseline_name(k)
        names = [c for c in O.columns if c not in ("t", "y") and c not in NOT_CANDIDATES]
        bh = ((O[base].values > 0.5) == O.y.values).astype(float)
        inc = np.column_stack([((O[n].values > 0.5) == O.y.values).astype(float) - bh for n in names])
        r = selection_corrected(inc, O.t.values, names)
        rows.append([k, base, len(names), r["best"], f"{r['observed']*100:+.2f}", f"{r['bias']*100:.2f}", f"{r['corrected']*100:+.2f} [{r['low']*100:+.2f}, {r['high']*100:+.2f}]"])
        print(rows[-1], flush=True)
    with open(OUT / "shrinkage.md", "w") as f:
        f.write("The best model's accuracy increment over the one-feature baseline, corrected for having picked the best of several models. Selection bias is estimated by resampling days, re-picking the best model in each resample, and measuring how far that winner sits above its own original increment. Points of accuracy; the interval is day-block bootstrap on the corrected value.\n\n")
        f.write("| minute | baseline | models compared | best model | observed increment | selection bias | corrected increment [95% CI] |\n|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print("wrote shrinkage.md")


if __name__ == "__main__":
    main()
