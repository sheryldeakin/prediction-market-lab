"""A wider event search: threshold sweeps, pairs of events, and session-conditioned
versions, with the correction that a wide search requires, and the September check.

Candidates (built from the feature frame at the entry minute):
  sweeps    RSI14 below 20/25/30/35 and above 65/70/75/80, hour-RSI below 35/40/45 and
            above 55/60/65, range position below 0.05/0.10/0.15 and above 0.85/0.90/0.95,
            5- and 15-minute spikes at 1.5/2/2.5/3 sd, 4-hour return beyond 25/50/100 bp,
            taker share beyond 0.1/0.2/0.3, VWAP deviation beyond 15/30/50 bp
  pairs     every pair of the base events (both must hold)
  sessions  every base event restricted to Asia, Europe or US hours

Every candidate is scored on the search period (2025-10 to 2026-08) with a day-clustered
p-value, corrected across all candidates (Benjamini-Hochberg, 10%), checked for
month-by-month stability, and then scored on September 2026, which the search never
saw. Reported: the stable survivors ranked by deviation, with their September result.

    python -m models.btc_15m.events2 --start 2025-10 --end 2026-08 --forward-through 2026-09-29
"""
from __future__ import annotations

import argparse
import datetime as dt
import itertools
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.data import load, load_days
from models.btc_15m.features import Series, dataset
from models.btc_15m.rules import REF_MONTHS, bh, day_pvalue, is_stable, month_agreement, reference_rows, reference_sign
from models.btc_15m.stats import block_bootstrap_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")


def base_events(D: pd.DataFrame) -> dict[str, np.ndarray]:
    v = D.vol60.values + 1e-9
    e = {}
    for th in (20, 25, 30, 35):
        e[f"RSI14 < {th}"] = D.rsi14.values < th
    for th in (65, 70, 75, 80):
        e[f"RSI14 > {th}"] = D.rsi14.values > th
    for th in (35, 40, 45):
        e[f"RSI60 < {th}"] = D.rsi60.values < th
    for th in (55, 60, 65):
        e[f"RSI60 > {th}"] = D.rsi60.values > th
    for th in (0.05, 0.10, 0.15):
        e[f"range position < {th}"] = D.rangepos.values < th
        e[f"range position > {1-th:.2f}"] = D.rangepos.values > 1 - th
    for sd in (1.5, 2, 2.5, 3):
        e[f"5-min move > +{sd} sd"] = D.ret5.values > sd * v * np.sqrt(5)
        e[f"5-min move < -{sd} sd"] = D.ret5.values < -sd * v * np.sqrt(5)
        e[f"15-min move > +{sd} sd"] = D.ret15.values > sd * v * np.sqrt(15)
        e[f"15-min move < -{sd} sd"] = D.ret15.values < -sd * v * np.sqrt(15)
    for bp in (25, 50, 100):
        e[f"4h return > +{bp} bp"] = D.ret240.values > bp
        e[f"4h return < -{bp} bp"] = D.ret240.values < -bp
    for th in (0.1, 0.2, 0.3):
        e[f"taker buy share > {th} (15 min)"] = D.flow15.values > th
        e[f"taker sell share > {th} (15 min)"] = D.flow15.values < -th
    for bp in (15, 30, 50):
        e[f"price > VWAP60 + {bp} bp"] = D.vwap_dev60.values > bp
        e[f"price < VWAP60 - {bp} bp"] = D.vwap_dev60.values < -bp
    e["previous window up"] = D.win1.values > 0
    e["previous window down"] = D.win1.values <= 0
    e["two windows up"] = (D.win1.values > 0) & (D.win2.values > 0)
    e["two windows down"] = (D.win1.values <= 0) & (D.win2.values <= 0)
    e["MACD hist > 0"] = D.macd_hist.values > 0
    e["MACD hist < 0"] = D.macd_hist.values < 0
    e["OBV rising"] = D.obv_slope60.values > 0.3
    e["OBV falling"] = D.obv_slope60.values < -0.3
    e["EMA9 > EMA21 + 10 bp"] = D.ema_cross.values > 10
    e["EMA9 < EMA21 - 10 bp"] = D.ema_cross.values < -10
    e["larger trades than usual (size5 > 1.2)"] = D.size5.values > 1.2
    e["more trades than usual (nratio5 > 1.5)"] = D.nratio5.values > 1.5
    return e


SESSIONS = {"Asia (0-7 UTC)": (0, 7), "Europe (8-13 UTC)": (8, 13), "US (14-21 UTC)": (14, 21)}


def all_candidates(D: pd.DataFrame, pair_names: list[str] | None = None) -> dict[str, np.ndarray]:
    base = base_events(D)
    out = dict(base)
    names = pair_names if pair_names is not None else list(base)
    for a, b in itertools.combinations(names, 2):
        if a.split(" ")[0] == b.split(" ")[0] and a.split(" ")[0] in ("RSI14", "RSI60", "5-min", "15-min", "4h", "range", "taker", "price"):
            continue                                            # same family at two thresholds is not a pair
        out[f"{a} AND {b}"] = base[a] & base[b]
    h = D.hour.values
    for name, m in base.items():
        for sname, (lo, hi) in SESSIONS.items():
            out[f"{name}, {sname}"] = m & (h >= lo) & (h <= hi)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--forward-through", default=str(dt.datetime.utcnow().date() - dt.timedelta(days=1)))
    ap.add_argument("--k", type=int, default=0)
    ap.add_argument("--min-fires", type=int, default=300)
    a = ap.parse_args()
    s = Series(load(a.start, a.end))
    D = dataset(s, a.k)
    y, t = D.y.values, D.t.values
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    months = sorted(month.unique())
    base_rate = y.mean()
    first = (pd.Period(a.end, freq="M") + 1).to_timestamp().date()
    last = dt.date.fromisoformat(a.forward_through)
    days = [str(first + dt.timedelta(days=i)) for i in range((last - first).days + 1)]
    F = dataset(Series(load_days([a.end], days)), a.k, cache=False)
    F = F[F.t >= int(pd.Timestamp(first).timestamp())].reset_index(drop=True)

    # pairs are only formed from base events that fire often enough on their own
    base = base_events(D)
    frequent = [n for n, m in base.items() if m.sum() >= 2 * a.min_fires]
    C = all_candidates(D, frequent)
    CF = all_candidates(F, frequent)
    print(f"{len(C)} candidates ({len(base)} base, {sum(' AND ' in n for n in C)} pairs, {sum(', ' in n and ' UTC)' in n for n in C)} session-conditioned)", flush=True)

    names, masks, devs, pvals = [], [], [], []
    for name, m in C.items():
        if m.sum() < a.min_fires:
            continue
        names.append(name); masks.append(m)
        devs.append(y[m].mean() - base_rate)
        pvals.append(day_pvalue(y[m].astype(float), t[m], base_rate))
    keep = bh(np.array(pvals))
    print(f"{len(names)} tested, {keep.sum()} survive FDR", flush=True)
    rows = []
    ref = reference_rows(D)
    for name, m, dev, p, kp in zip(names, masks, devs, pvals, keep):
        if not kp:
            continue
        sign = reference_sign(m, y, ref)
        agree, tot, _ = month_agreement(m, y, month, months[REF_MONTHS:], sign)
        if not (is_stable(agree, tot, sign) and np.sign(dev) == sign):
            continue
        mu, lo, hi = block_bootstrap_ci(y[m].astype(float), t[m])
        mf = CF[name]
        if mf.sum() >= 30:
            fdev = F.y.values[mf].mean() - F.y.mean()
            fwd = f"{fdev*100:+.1f} on {int(mf.sum())}"
            held = "same" if np.sign(fdev) == np.sign(dev) else "flipped"
        else:
            fwd, held = f"fires {int(mf.sum())}", "too few"
        kind = "pair" if " AND " in name else "session" if " UTC)" in name else "single"
        rows.append([name, kind, int(m.sum()), f"{100*m.mean():.1f}%", f"{mu*100:.1f}% [{lo*100:.1f}, {hi*100:.1f}]", f"{dev*100:+.1f}", f"{agree}/{tot}", fwd, held])
    rows.sort(key=lambda r: -abs(float(r[5])))
    held_n = sum(r[8] == "same" for r in rows); flipped_n = sum(r[8] == "flipped" for r in rows)
    with open(OUT / "events2.md", "w") as f:
        f.write(f"Wider event search at minute {a.k}: {len(C)} candidates (threshold sweeps, pairs of frequent events, session-conditioned events), {len(names)} with at least {a.min_fires} firings, {int(keep.sum())} surviving Benjamini-Hochberg at 10%, {len(rows)} also stable month by month. Search period {a.start} to {a.end}; forward column is {first} to {last}, never seen by the search. Of the stable survivors with enough September firings, {held_n} kept their direction and {flipped_n} flipped. Top 40 by deviation.\n\n")
        f.write("| if | kind | fires | share | up-rate [95% CI] | vs base | months agreeing | September deviation | held? |\n|---|---|---|---|---|---|---|---|---|\n")
        for r in rows[:40]:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    pd.DataFrame(rows, columns=["event", "kind", "fires", "share", "up_rate_ci", "deviation", "months_agreeing", "forward", "held"]).to_csv(OUT / "events2_all.csv", index=False)
    print(f"wrote events2.md: {len(rows)} stable survivors, {held_n} held in September, {flipped_n} flipped")


if __name__ == "__main__":
    main()
