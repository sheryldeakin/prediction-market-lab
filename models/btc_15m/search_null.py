"""How many "stable survivors" would the wide event search find if nothing were there?

The wide search (events2.py) tests about 1,500 overlapping candidates. Benjamini-Hochberg
assumes the tests are independent or positively dependent, and hundreds of overlapping
pairs describe one effect many times, so the survivor count alone says little. This
module re-runs the whole search on labels with the link to the features broken, many
times, and compares the real counts with that distribution.

  null labels   within each calendar month the label sequence is rotated by a random
                offset. Each month keeps its base rate and its runs of up and down
                windows; only the alignment with the features is broken.
  survivors     candidates surviving the false-discovery correction, and those also
                stable month by month, real against the null distribution
  max statistic the largest |z| across all candidates in each null run; a candidate's
                adjusted p is the share of null runs whose largest |z| reaches its own
                (single-step max-T, as in Romano and Wolf), which holds under any
                dependence between candidates
  September     for the stable survivors with enough September firings, how many kept
                their direction, against (a) September labels rotated within the month,
                which gives the count expected if the effects were gone, and (b) the
                count expected if every effect had kept its backtest size

    python -m models.btc_15m.search_null --start 2025-10 --end 2026-08 --runs 200
"""
from __future__ import annotations

import argparse
import datetime as dt
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from models.btc_15m.data import load, load_days
from models.btc_15m.events2 import all_candidates, base_events
from models.btc_15m.features import Series, dataset
from models.btc_15m.rules import REF_MONTHS, bh, is_stable, month_agreement, reference_rows, reference_sign
from models.btc_15m.stats import cluster_diff_pvalue

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")


def rotate_within_groups(y: np.ndarray, groups: np.ndarray, rng) -> np.ndarray:
    """y with each group's values (in their order) rotated by a random nonzero offset."""
    out = y.copy()
    for g in np.unique(groups):
        idx = np.where(groups == g)[0]
        if len(idx) > 1:
            out[idx] = np.roll(y[idx], int(rng.integers(1, len(idx))))
    return out


def search(masks: list[np.ndarray], y: np.ndarray, t: np.ndarray, month: pd.Series, months: list) -> pd.DataFrame:
    """The events2 pipeline on given labels: clustered z and p per candidate, the
    false-discovery correction, and stability against the reference months' direction."""
    z, p, dev = [], [], []
    for m in masks:
        b, se, pv = cluster_diff_pvalue(m, y, t)
        z.append(b / se if se > 0 else 0.0); p.append(pv); dev.append(b)
    out = pd.DataFrame({"z": z, "p": p, "dev": dev})
    out["fdr"] = bh(out.p.values)
    ref = reference_rows(pd.DataFrame({"t": t}))
    stable = np.zeros(len(masks), bool)
    for i in np.where(out.fdr.values)[0]:
        sign = reference_sign(masks[i], y, ref)
        agree, tot, _ = month_agreement(masks[i], y, month, months[REF_MONTHS:], sign)
        stable[i] = is_stable(agree, tot, sign) and np.sign(out.dev.iloc[i]) == sign
    out["stable"] = stable
    return out


def held_count(masks, y_f: np.ndarray, signs: np.ndarray, min_fires: int = 30) -> tuple[int, int]:
    """(held, scored): of the masks firing at least min_fires times, how many have a
    deviation from the period's base rate with the given sign."""
    held = scored = 0
    base = y_f.mean()
    for m, sg in zip(masks, signs):
        if m.sum() >= min_fires:
            scored += 1
            held += int(np.sign(y_f[m].mean() - base) == sg)
    return held, scored


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--forward-through", default=str(dt.datetime.utcnow().date() - dt.timedelta(days=1)))
    ap.add_argument("--k", type=int, default=0)
    ap.add_argument("--min-fires", type=int, default=300)
    ap.add_argument("--runs", type=int, default=200)
    ap.add_argument("--sept-draws", type=int, default=1000)
    a = ap.parse_args()
    rng = np.random.default_rng(0)
    D = dataset(Series(load(a.start, a.end)), a.k)
    y, t = D.y.values, D.t.values
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    months = sorted(month.unique())
    codes = month.astype(str).values
    base = base_events(D)
    frequent = [n for n, m in base.items() if m.sum() >= 2 * a.min_fires]
    C = all_candidates(D, frequent)
    names = [n for n, m in C.items() if m.sum() >= a.min_fires]
    masks = [C[n] for n in names]
    print(f"{len(names)} candidates with at least {a.min_fires} firings", flush=True)

    real = search(masks, y, t, month, months)
    n_fdr, n_stable, max_z = int(real.fdr.sum()), int(real.stable.sum()), float(real.z.abs().max())
    print(f"real: {n_fdr} survive FDR, {n_stable} stable, max |z| {max_z:.2f}", flush=True)
    null = []
    for r in range(a.runs):
        res = search(masks, rotate_within_groups(y, codes, rng), t, month, months)
        null.append((int(res.fdr.sum()), int(res.stable.sum()), float(res.z.abs().max())))
        if (r + 1) % 20 == 0:
            print(f"null run {r + 1}/{a.runs}: last {null[-1]}", flush=True)
    N = pd.DataFrame(null, columns=["fdr", "stable", "max_z"])
    N.to_csv(OUT / "search_null_runs.csv", index=False)
    real["p_maxT"] = [(1 + (N.max_z.values >= abs(zz)).sum()) / (len(N) + 1) for zz in real.z.values]
    real.insert(0, "event", names)
    real.to_csv(OUT / "search_null_candidates.csv", index=False)

    # ---- September: held against two references ----
    first = (pd.Period(a.end, freq="M") + 1).to_timestamp().date()
    last = dt.date.fromisoformat(a.forward_through)
    days = [str(first + dt.timedelta(days=i)) for i in range((last - first).days + 1)]
    F = dataset(Series(load_days([a.end], days)), a.k, cache=False)
    F = F[F.t >= int(pd.Timestamp(first).timestamp())].reset_index(drop=True)
    CF = all_candidates(F, frequent)
    st = real[real.stable]
    fmasks = [CF[n] for n in st.event]
    signs = np.sign(st.dev.values)
    yf = F.y.values
    held, scored = held_count(fmasks, yf, signs)
    gone = [held_count(fmasks, np.roll(yf, int(rng.integers(1, len(yf)))), signs)[0] for _ in range(a.sept_draws)]
    p_f = yf.mean() * (1 - yf.mean())
    persisted = sum(norm.cdf(abs(d) / np.sqrt(p_f / m.sum() + p_f / (~m).sum())) for d, m in zip(st.dev.values, fmasks) if m.sum() >= 30)

    q = lambda v, x: float(np.quantile(v, x))
    with open(OUT / "search_null.md", "w") as f:
        f.write(f"The wide event search at minute {a.k} ({len(names)} candidates with at least {a.min_fires} firings, {a.start} to {a.end}) re-run {a.runs} times on labels rotated within each month, which keeps each month's base rate and runs but breaks the link to the features. The rows compare the real search with that null distribution.\n\n")
        f.write("| quantity | real | null median | null 95th percentile | null maximum | share of null runs at or above real |\n|---|---|---|---|---|---|\n")
        for label, val, col in (("survive the false-discovery correction", n_fdr, "fdr"), ("also stable month by month", n_stable, "stable"), ("largest abs(z) across candidates", max_z, "max_z")):
            fmt = (lambda v: f"{v:.2f}") if col == "max_z" else (lambda v: f"{v:.0f}")
            f.write(f"| {label} | {fmt(val)} | {fmt(q(N[col], 0.5))} | {fmt(q(N[col], 0.95))} | {fmt(N[col].max())} | {(N[col].values >= val).mean()*100:.1f}% |\n")
        f.write(f"\nAdjusted for the whole search (single-step max-T over {a.runs} null runs, valid under any dependence between candidates): {int((real.p_maxT <= 0.05).sum())} candidates have an adjusted p at or below 0.05 and {int((real.p_maxT <= 0.10).sum())} at or below 0.10. The smallest adjusted p possible with {a.runs} runs is {1/(a.runs+1):.4f}. Every candidate's z and adjusted p are in search_null_candidates.csv.\n\n")
        f.write(f"September ({first} to {last}): of the {len(st)} stable survivors, {scored} fired at least 30 times and {held} kept their direction. With September's labels rotated within the month (effects gone, overlap between candidates kept) the held count has median {q(gone, 0.5):.0f} and 95th percentile {q(gone, 0.95):.0f} over {a.sept_draws} draws; {np.mean(np.array(gone) >= held)*100:.1f}% of draws reach {held}. If every effect had kept its backtest size, about {persisted:.0f} would hold (this expectation treats windows as independent, so it is approximate).\n")
    print(f"wrote search_null.md: real {n_fdr}/{n_stable}, null median {N.fdr.median():.0f}/{N.stable.median():.0f}; September held {held} of {scored}")


if __name__ == "__main__":
    main()
