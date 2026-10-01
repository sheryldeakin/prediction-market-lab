"""Acting only when a strong event fires.

Takes the event library from rules.py, keeps the events whose direction was stable
month by month over the backtest, and builds three rules:

  any stable event      act on every window where at least one stable event fires, in
                        the direction of the strongest (largest absolute deviation)
  strong events only    the same, restricted to events with a deviation of 5 points
                        or more
  votes                 act only when the stable events that fire all agree

Each is scored on the backtest months (the same windows the events were found on,
so this part is in-sample) and then on the forward period (September 2026 onward,
loaded from Binance daily files, never seen by the event search), which is the honest
test. Reported: share of windows acted on, accuracy, and expected value at a 1c
spread and 1.75c fee on a $1 contract priced at 0.5.

    python -m models.btc_15m.event_portfolio --start 2025-10 --end 2026-08 --forward-through 2026-09-29
"""
from __future__ import annotations

import argparse
import datetime as dt
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.data import load, load_days
from models.btc_15m.features import Series, dataset
from models.btc_15m.rules import REF_MONTHS, bh, event_pvalue, events, is_stable, month_agreement, reference_rows, reference_sign, vol_cutoffs
from models.btc_15m.stats import block_bootstrap_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
SPREAD, FEE = 0.01, 0.0175


def stable_events(D: pd.DataFrame, k: int, min_fires=300, agree=0.75):
    """Events surviving FDR whose direction in the reference months holds in >= agree of
    the later months (and matches the pooled direction).
    Returns {name: signed deviation} where sign > 0 means 'up when it fires'."""
    y, t = D.y.values, D.t.values
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    months = sorted(month.unique())
    base = y.mean()
    E = events(D, k)
    names, pvals, devs, masks = [], [], [], []
    for name, mask in E.items():
        if mask.sum() < min_fires:
            continue
        names.append(name); masks.append(mask)
        devs.append(y[mask].mean() - base)
        pvals.append(event_pvalue(mask, y, t))
    keep = bh(np.array(pvals)) if names else np.array([], bool)
    out = {}
    ref = reference_rows(D)
    for name, mask, dev, kp in zip(names, masks, devs, keep):
        if not kp:
            continue
        sign = reference_sign(mask, y, ref)
        ok, tot, _ = month_agreement(mask, y, month, months[REF_MONTHS:], sign)
        if is_stable(ok, tot, sign, agree) and np.sign(dev) == sign:
            out[name] = dev
    return out


def decide(D: pd.DataFrame, k: int, stable: dict, min_dev=0.0, mode="strongest", cutoffs=None):
    """Returns (act mask, predicted up mask). cutoffs: vol60 deciles from training rows."""
    E = events(D, k, cutoffs)
    n = len(D)
    score = np.zeros(n)
    best = np.zeros(n)
    n_up = np.zeros(n); n_down = np.zeros(n)
    for name, dev in stable.items():
        if abs(dev) < min_dev:
            continue
        m = E[name]
        if mode == "strongest":
            stronger = m & (np.abs(dev) > np.abs(best))
            best[stronger] = dev
        else:
            n_up[m & (dev > 0)] += 1
            n_down[m & (dev < 0)] += 1
    if mode == "strongest":
        act = best != 0
        up = best > 0
    else:
        act = ((n_up > 0) ^ (n_down > 0))
        up = n_up > 0
    return act, up


def score(act, up, y, t):
    if act.sum() < 30:
        return [int(act.sum()), f"{100*act.mean():.1f}%", "", ""]
    hits = (up[act] == (y[act] == 1)).astype(float)
    m, lo, hi = block_bootstrap_ci(hits, t[act])
    ev = hits - (0.5 + SPREAD / 2) - FEE
    e, elo, ehi = block_bootstrap_ci(ev, t[act])
    return [int(act.sum()), f"{100*act.mean():.1f}%", f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", f"{e*100:+.2f} [{elo*100:+.2f}, {ehi*100:+.2f}]"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--forward-through", default=str(dt.datetime.utcnow().date() - dt.timedelta(days=1)))
    ap.add_argument("--minutes", default="0")
    a = ap.parse_args()
    s = Series(load(a.start, a.end))
    first = (pd.Period(a.end, freq="M") + 1).to_timestamp().date()
    last = dt.date.fromisoformat(a.forward_through)
    days = [str(first + dt.timedelta(days=i)) for i in range((last - first).days + 1)]
    fs = Series(load_days([a.end], days))
    start_t = int(pd.Timestamp(first).timestamp())
    rows, ev_rows = [], []
    for k in [int(x) for x in a.minutes.split(",")]:
        D = dataset(s, k)
        F = dataset(fs, k, cache=False)
        F = F[F.t >= start_t].reset_index(drop=True)
        stable = stable_events(D, k)
        print(f"minute {k}: {len(stable)} stable events", flush=True)
        # each stable event on its own, backtest vs forward
        cut = vol_cutoffs(D[reference_rows(D)])          # deciles from training months, used for the forward rows too
        Eb, Ef = events(D, k, cut), events(F, k, cut)
        base_f = F.y.mean()
        for name, dev in sorted(stable.items(), key=lambda x: -abs(x[1])):
            mb, mf = Eb[name], Ef[name]
            fdev = (F.y.values[mf].mean() - base_f) if mf.sum() >= 30 else np.nan
            ev_rows.append([k, name, "up" if dev > 0 else "down", f"{dev*100:+.1f}", int(mf.sum()), f"{fdev*100:+.1f}" if not np.isnan(fdev) else "too few", "" if np.isnan(fdev) else ("same" if np.sign(fdev) == np.sign(dev) else "flipped")])
        for label, min_dev, mode in (("any stable event, strongest wins", 0.0, "strongest"), ("events with 5+ point deviation, strongest wins", 0.05, "strongest"), ("all firing stable events agree", 0.0, "votes")):
            for period, X in (("backtest (in-sample)", D), ("forward", F)):
                act, up = decide(X, k, stable, min_dev, mode, cut)
                rows.append([k, label, period] + score(act, up, X.y.values, X.t.values))
                print(rows[-1], flush=True)
    with open(OUT / "event_portfolio.md", "w") as f:
        f.write(f"Acting only when a stable event fires. Stable events are found on {a.start} to {a.end} (so the backtest rows are in-sample); the forward rows are {first} to {last}, never seen by the event search. EV in cents per $1 contract at a 1c spread and 1.75c fee, priced at 0.5.\n\n")
        f.write("| minute | rule | period | windows acted on | share | accuracy [95% CI] | EV cents [95% CI] |\n|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        f.write(f"\nEach stable event on its own: the deviation of the up-rate from the base rate in the backtest, and the same in the forward period.\n\n| minute | event | direction | backtest deviation (points) | forward fires | forward deviation (points) | held? |\n|---|---|---|---|---|---|---|\n")
        for r in ev_rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print("wrote event_portfolio.md")


if __name__ == "__main__":
    main()
