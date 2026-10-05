"""Tick-level and derivatives events for the price-action library (docs/horizons.md, "Derivatives
and tick events"), scored with the same machinery as the rest of the library: every minute as a
decision time, horizons 1 to 30, day-clustered intervals, the rotated-label search-wide null,
the VWAP label, years held.

An event at decision minute i reads only what was known at the close of minute i-1. Every
cutoff is a percentile of the PREVIOUS calendar year (the first year reads the months before it
that the data holds: tick data begin in 2017-08), so a year never defines its own extreme.

Tick events (from the per-second trade table; "large" is the table's own flag, a trade at or
above the previous UTC day's 99th-percentile notional):

  large-trade burst        the share of the last minute's trades that were large is above the
                           previous year's 99th percentile of that share (minutes with trades);
                           also split by the sign of the last minute's net large volume
  imbalance persistence    the last minute's signed volume (aggressive buying minus aggressive
                           selling, notional) has the same sign in each of the last 3 (5) minutes
  trade-count climax       the last minute's trade count is above the previous year's 99th
                           percentile of the per-minute count; also with a new 60-minute high or
                           low in that minute, and with neither

Derivatives events, scored in every year whose previous calendar year the futures files cover in
full (funding, metrics and perp klines, every day), so the cutoffs of a year are deciles of the
futures series themselves in the year before it and never of its own. The scoring reads the files
already on disk and refuses to download:

  funding                  the last settled funding rate is strictly above (below) the top (bottom)
                           decile of the previous year; every comparison with a decile is strict
  open interest            the change over the last 15 (60) minutes is in the top (bottom)
                           decile of the previous year (spike, drop)
  liquidation signature    the 15-minute open-interest change is in the bottom decile, the
                           15-minute spot return is in its bottom (top) decile, and the perp
                           volume of the last 5 minutes against its 24-hour mean is in the top
                           decile: forced closing of longs (shorts) shows as open interest
                           falling while price moves hard on heavy volume. The public files
                           hold no liquidation orders, so this is an inference from those three.

    python -m models.btc_15m.library_events --start 2018 --end 2026-08
    python -m models.btc_15m.library_events --start 2018 --end 2026-08 --part derivatives
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m import derivatives
from models.btc_15m.horizons import HORIZONS, MIN_FIRES, NULL_RUNS, labels, score_year, year_frame
from models.btc_15m.horizons_vwap import cells as vwap_cells, vwap_labels
from models.btc_15m.settlement import Vwap
from models.btc_15m.ticks import load_seconds, tick_path

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
CACHE = Path("data/library_events")        # the working copy's own cache, never LAB_DATA_ROOT
TICK_FIRST_MONTH = "2017-08"               # the first month of the per-second table
P_EXTREME = 0.99
EXTREME_WINDOW = 60
PERSIST = (3, 5)

# (family, event) in table order
TICK_EVENTS = [
    ("large trades", "large-trade burst"),
    ("large trades", "large-trade burst with net large buying"),
    ("large trades", "large-trade burst with net large selling"),
    ("imbalance persistence", "net taker buying in each of the last 3 minutes"),
    ("imbalance persistence", "net taker selling in each of the last 3 minutes"),
    ("imbalance persistence", "net taker buying in each of the last 5 minutes"),
    ("imbalance persistence", "net taker selling in each of the last 5 minutes"),
    ("trade count", "trade-count climax"),
    ("trade count", "trade-count climax at a new 1h high"),
    ("trade count", "trade-count climax at a new 1h low"),
    ("trade count", "trade-count climax with no new 1h high or low"),
]
DERIV_EVENT_FAMILIES = [
    ("funding", "funding rate in the top decile of the previous year"),
    ("funding", "funding rate in the bottom decile of the previous year"),
    ("open interest", "open interest up over 15 minutes (top decile)"),
    ("open interest", "open interest down over 15 minutes (bottom decile)"),
    ("open interest", "open interest up over 60 minutes (top decile)"),
    ("open interest", "open interest down over 60 minutes (bottom decile)"),
    ("liquidation signature", "long liquidation signature (open interest down, price down hard, perp volume heavy)"),
    ("liquidation signature", "short liquidation signature (open interest down, price up hard, perp volume heavy)"),
]
DERIV_EVENTS = [name for _, name in DERIV_EVENT_FAMILIES]
DERIV_ARRAYS = ("funding_bp", "doi15", "doi60", "pvol_ratio5", "ret15")     # what deriv_events reads


def known_next(flag: np.ndarray) -> np.ndarray:
    """Shift a per-minute flag so the decision minute i reads minute i-1's flag (known at its close)."""
    out = np.zeros(len(flag), bool)
    out[1:] = np.asarray(flag, bool)[:-1]
    return out


# ---------------- tick events ----------------

def minute_table(r: pd.DataFrame, t0: int, n: int) -> dict[str, np.ndarray]:
    """Per-minute sums of the per-second table on the grid t0, t0+60, ... (n minutes)."""
    k = (r.sec.values - t0) // 60
    keep = (k >= 0) & (k < n)
    return {c: np.bincount(k[keep], weights=r[c].values[keep], minlength=n) for c in ("n", "big_n", "svol", "big_svol")}


def tick_quantities(m: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """The per-minute quantities the events read: trade count, large-trade share (NaN with no
    trades), signed volume and signed large volume."""
    n = m["n"]
    share = np.where(n > 0, m["big_n"] / np.where(n > 0, n, 1.0), np.nan)
    return {"n": n, "share": share, "svol": m["svol"], "big_svol": m["big_svol"]}


def tick_cutoffs(q: dict[str, np.ndarray]) -> dict[str, float]:
    """99th percentiles over the minutes that have trades."""
    has = q["n"] > 0
    return {"share": float(np.quantile(q["share"][has], P_EXTREME)), "n": float(np.quantile(q["n"][has], P_EXTREME))}


def reference_months(year: int, first: str = TICK_FIRST_MONTH) -> list[str]:
    """The months the cutoffs of `year` are taken from: the previous calendar year, or what the data hold of it."""
    months = [str(p) for p in pd.period_range(f"{year - 1}-01", f"{year - 1}-12", freq="M")]
    return [m for m in months if pd.Period(m, "M") >= pd.Period(first, "M")]


def reference_cutoffs(year: int, read_month, first: str = TICK_FIRST_MONTH) -> dict[str, float]:
    """Cutoffs for `year` from the months of the previous year only. read_month(month) returns that
    month's per-second table."""
    months = reference_months(year, first)
    if not months:
        raise ValueError(f"no data before {year} to take cutoffs from")
    parts = []
    for mo in months:
        p = pd.Period(mo, "M")
        t0 = int(p.start_time.value // 10**9)
        parts.append(tick_quantities(minute_table(read_month(mo), t0, p.days_in_month * 1440)))
    return tick_cutoffs({k: np.concatenate([x[k] for x in parts]) for k in parts[0]})


def streak(flag: np.ndarray) -> np.ndarray:
    """Number of consecutive True values ending at each position."""
    f = pd.Series(np.asarray(flag, bool))
    return f.groupby((~f).cumsum()).cumsum().values


def new_extremes(h: np.ndarray, l: np.ndarray, w: int = EXTREME_WINDOW) -> tuple[np.ndarray, np.ndarray]:
    """True where the minute's high (low) is at least (at most) every high (low) of the w minutes before it."""
    prev_hi = pd.Series(h).shift(1).rolling(w).max().values
    prev_lo = pd.Series(l).shift(1).rolling(w).min().values
    return h >= prev_hi, l <= prev_lo


def tick_events(q: dict[str, np.ndarray], cuts: dict[str, float], h: np.ndarray, l: np.ndarray) -> dict[str, np.ndarray]:
    """{event: boolean per decision minute}; the value at i depends on minutes up to i-1."""
    burst = q["share"] > cuts["share"]
    climax = q["n"] > cuts["n"]
    hi, lo = new_extremes(h, l)
    buy, sell = q["svol"] > 0, q["svol"] < 0
    flags = {
        "large-trade burst": burst,
        "large-trade burst with net large buying": burst & (q["big_svol"] > 0),
        "large-trade burst with net large selling": burst & (q["big_svol"] < 0),
        "trade-count climax": climax,
        "trade-count climax at a new 1h high": climax & hi,
        "trade-count climax at a new 1h low": climax & lo,
        "trade-count climax with no new 1h high or low": climax & ~hi & ~lo,
    }
    for k in PERSIST:
        flags[f"net taker buying in each of the last {k} minutes"] = streak(buy) >= k
        flags[f"net taker selling in each of the last {k} minutes"] = streak(sell) >= k
    return {name: known_next(flags[name]) for _, name in TICK_EVENTS}


# ---------------- derivatives events (definitions only) ----------------

def spot_return15(c: np.ndarray) -> np.ndarray:
    """15-minute spot return in basis points, known at the close of each minute."""
    out = np.full(len(c), np.nan)
    out[15:] = (c[15:] / c[:-15] - 1) * 1e4
    return out


def decile_cuts(arrs: dict[str, np.ndarray]) -> dict[str, tuple[float, float]]:
    """(10th, 90th percentile) of every series, ignoring unknown values."""
    return {k: (float(np.nanquantile(v, 0.1)), float(np.nanquantile(v, 0.9))) for k, v in arrs.items()}


def deriv_events(arrs: dict[str, np.ndarray], cuts: dict[str, tuple[float, float]]) -> dict[str, np.ndarray]:
    """arrs: funding_bp, doi15, doi60, pvol_ratio5 (derivatives.build with missing="nan") and
    ret15 (spot_return15); cuts: decile_cuts of the previous year's arrays. Unknown values never fire.
    Both comparisons are strict: a value exactly at a cut is not an extreme, because a series with a
    mass point (funding at the exchange default) can have its decile land on that point."""
    hi = lambda k: arrs[k] > cuts[k][1]
    lo = lambda k: arrs[k] < cuts[k][0]
    flags = {
        DERIV_EVENTS[0]: hi("funding_bp"),
        DERIV_EVENTS[1]: lo("funding_bp"),
        DERIV_EVENTS[2]: hi("doi15"),
        DERIV_EVENTS[3]: lo("doi15"),
        DERIV_EVENTS[4]: hi("doi60"),
        DERIV_EVENTS[5]: lo("doi60"),
        DERIV_EVENTS[6]: lo("doi15") & lo("ret15") & hi("pvol_ratio5"),
        DERIV_EVENTS[7]: lo("doi15") & hi("ret15") & hi("pvol_ratio5"),
    }
    return {k: known_next(v) for k, v in flags.items()}


# ---------------- pooling ----------------

def pool_cells(A: pd.DataFrame, V: pd.DataFrame) -> pd.DataFrame:
    """One row per (event, horizon) from the year rows A (horizons.score_year plus p_adj) and the
    VWAP-label year rows V. Deviation is the up-rate when the event fires minus the unconditional
    up-rate (as in the price-action table), firing-weighted over the years; its error combines the
    years as independent. Retained = VWAP deviation over last-print deviation, firing-weighted over
    the years in which both exist. Share is the aggregate over the scored years: total firings over
    total minutes (each year's minutes are its firings divided by its share)."""
    rows = []
    vg = {k: g for k, g in V.groupby(["pattern", "horizon"])}
    for (pat, h), g in A.groupby(["pattern", "horizon"]):
        w = g.fires / g.fires.sum()
        dev_y = (1 - g.share) * g["diff"]
        se_y = (1 - g.share) * g.se
        ok = g.share > 0
        minutes = (g.fires[ok] / g.share[ok]).sum()          # minutes scored: fires / share, summed over the scored years
        agg_share = float(g.fires[ok].sum() / minutes) if minutes > 0 else float("nan")
        dev = float((w * dev_y).sum())
        se = float(np.sqrt(((w * se_y) ** 2).sum()))
        row = {"event": pat, "horizon": h, "years": len(g), "years_held": int((np.sign(dev_y) == np.sign(dev)).sum()),
               "fires": int(g.fires.sum()), "share": agg_share, "up_rate": float((w * g.up_rate).sum()),
               "deviation": dev, "se": se, "lo": dev - 1.96 * se, "hi": dev + 1.96 * se,
               "min_p_adj": float(g.p_adj.min()), "years_adj_05": int((g.p_adj <= 0.05).sum())}
        v = vg.get((pat, h))
        if v is not None and len(v):
            dp = (v.diff_print * v.fires_print).sum() / v.fires_print.sum()
            dv = (v.diff_vwap * v.fires_vwap).sum() / v.fires_vwap.sum()
            row["retained"] = float(dv / dp) if dp != 0 else float("nan")
        else:
            row["retained"] = float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def cleared(G: pd.DataFrame, fraction: float = 1.0) -> pd.Series:
    """Cells whose search-wide adjusted p is at most 0.05 in at least `fraction` of the years they
    are scored (1.0: every year; a tiny fraction: at least one year)."""
    return G.years_adj_05 >= np.maximum(fraction * G.years, 1)


def held_all(G: pd.DataFrame) -> pd.Series:
    return G.years_held == G.years


TICK_SHARE_EVENTS = ("trade-count climax", "large-trade burst")
DERIV_SHARE_EVENTS = (DERIV_EVENTS[0], DERIV_EVENTS[6])


def sentences(G: pd.DataFrame, null_all: np.ndarray, real_max_z: float, per_year_share: pd.DataFrame, years: list[int], events: list[tuple[str, str]] = TICK_EVENTS, share_events: tuple = TICK_SHARE_EVENTS) -> list[str]:
    """The generated summary sentences the doc quotes. years: every year the part was run over;
    events: the (family, event) list that gives the order; share_events: the events whose firing
    share per year gets a sentence."""
    ev_order = [name for _, name in events]
    c_all, c_half, c_any, hd = cleared(G), cleared(G, 0.5), cleared(G, 0.0), held_all(G)
    strong = c_half & hd
    out = []
    names = lambda m: ", ".join(e for e in ev_order if e in set(G[m].event)) or "none"
    out.append(f"Of {len(G)} cells ({G.event.nunique()} events at {len(HORIZONS)} horizons), {int(hd.sum())} hold their sign in every year. A search-wide adjusted p of at most 0.05 is reached in every scored year by {int(c_all.sum())} cells, in at least half of the scored years by {int(c_half.sum())} and in at least one year by {int(c_any.sum())}; {int(strong.sum())} cells hold their sign in every year and clear the null in at least half of the years.")
    out.append(f"Events with at least one cell that holds its sign in every year and clears the null in at least half of the years: {names(strong)}.")
    out.append(f"Events with at least one cell that holds its sign in every year: {names(hd)}.")
    r = G[strong & ((G.lo > 0) | (G.hi < 0))].retained.dropna()
    if len(r):
        out.append(f"Among those {len(r)} cells (interval excludes zero), the VWAP label keeps a median of {r.median()*100:.0f}% of the last-print deviation (range {r.min()*100:.0f}% to {r.max()*100:.0f}%).")
    out.append(f"The largest absolute pooled deviation is {G.deviation.abs().max()*100:.1f} points ({G.loc[G.deviation.abs().idxmax(), 'event']}, {int(G.loc[G.deviation.abs().idxmax(), 'horizon'])} minutes); {int((G.lo > 0).sum() + (G.hi < 0).sum())} of the {len(G)} pooled 95% intervals exclude zero.")
    scored_years = G.groupby("event").years.max()
    partly = [e for e in ev_order if e in scored_years.index and scored_years[e] < len(years)]
    out += [f"'{e}' was scored in {int(scored_years[e])} of {len(years)} years (fewer than {MIN_FIRES} firings in the others)." for e in partly]
    if not partly:
        out.append("Every event was scored in every year.")
    if int(strong.sum()):
        first = min(HORIZONS)
        bad = G[strong & (G.horizon == first) & ~(G.retained >= 0.5)]
        bad = bad.assign(_o=bad.event.map({e: k for k, e in enumerate(ev_order)})).sort_values("_o")
        listed = ", ".join(f"{r.event} (retained {r.retained*100:.0f}%)" if not np.isnan(r.retained) else f"{r.event} (retained not measured)" for r in bad.itertuples()) or "none"
        out.append(f"Of the {int(strong.sum())} cells that hold their sign in every year and clear the null in at least half of the years, {len(bad)} are at the {first}-minute horizon and keep less than half of their deviation under the VWAP label: {listed}.")
    for ev in share_events:
        s = per_year_share[per_year_share.event == ev].set_index("year").share
        out.append(f"'{ev}' fires on {s.min()*100:.2f}% of minutes in its quietest year ({s.idxmin()}) and {s.max()*100:.2f}% in its busiest ({s.idxmax()}).")
    out.append(f"Null: the largest |z| across all events and horizons on rotated labels has median {np.median(null_all):.2f} and 95th percentile {np.quantile(null_all, 0.95):.2f}; the real search's largest |z| is {real_max_z:.2f}.")
    return out


# +1: the event follows a move down, so a reversal is up; -1: it follows a move up
TICK_ORIENT = {"trade-count climax at a new 1h high": -1, "trade-count climax at a new 1h low": 1,
               "net taker buying in each of the last 3 minutes": -1, "net taker selling in each of the last 3 minutes": 1,
               "net taker buying in each of the last 5 minutes": -1, "net taker selling in each of the last 5 minutes": 1,
               "large-trade burst with net large buying": -1, "large-trade burst with net large selling": 1}
TICK_EFFECTS = [("A reversal from a price extreme on heavy trading", ["trade-count climax at a new 1h high", "trade-count climax at a new 1h low"]),
                ("The same side of the flow for several minutes", [e for e in TICK_ORIENT if e.startswith("net taker")]),
                ("Large-trade bursts split by the side of the large trades", ["large-trade burst with net large buying", "large-trade burst with net large selling"]),
                ("Events with no side (deviation signed up)", ["large-trade burst", "trade-count climax", "trade-count climax with no new 1h high or low"])]
# Fixed before any derivatives result was seen. Same convention: +1 means the event follows a
# move down, so a reversal is up. Crowded longs (top funding) reverse down; liquidated longs
# (price down hard) reverse up.
DERIV_ORIENT = {DERIV_EVENTS[0]: -1, DERIV_EVENTS[1]: 1, DERIV_EVENTS[6]: 1, DERIV_EVENTS[7]: -1}
DERIV_EFFECTS = [("Funding at an extreme, read against the crowd (top decile: down is the reversal)", [DERIV_EVENTS[0], DERIV_EVENTS[1]]),
                 ("Liquidation signatures, a reversal of the forced move", [DERIV_EVENTS[6], DERIV_EVENTS[7]]),
                 ("Open interest up over 15 or 60 minutes, top decile (deviation signed up)", [DERIV_EVENTS[2], DERIV_EVENTS[4]]),
                 ("Open interest down over 15 or 60 minutes, bottom decile (deviation signed up)", [DERIV_EVENTS[3], DERIV_EVENTS[5]])]
EFFECT_HORIZONS = (5, 10, 15, 30)


def effect_sentences(G: pd.DataFrame, effects: list = TICK_EFFECTS, orient: dict = TICK_ORIENT, scale: float | None = None, A: pd.DataFrame | None = None) -> list[str]:
    """One generated sentence per group of events: the range of the pooled deviation over 5 to 30
    minutes, oriented so that a reversal is positive for events with a side. A (the per-year rows:
    year, pattern, horizon, diff), when given, adds the range of the oriented per-year deviation at
    15 minutes."""
    out = []
    for label, evs in effects:
        g = G[G.event.isin(evs) & G.horizon.isin(EFFECT_HORIZONS)]
        dev = g.deviation * g.event.map(lambda e: orient.get(e, 1))
        excl = (g.lo > 0) | (g.hi < 0)
        side = "reversal positive" if any(e in orient for e in evs) else "up positive"
        out.append(f"{label}: at {', '.join(str(h) for h in EFFECT_HORIZONS[:-1])} and {EFFECT_HORIZONS[-1]} minutes the pooled deviation runs from {dev.min()*100:+.1f} to {dev.max()*100:+.1f} points ({side}); {int(excl.sum())} of {len(g)} cells have an interval that excludes zero; cells holding their sign in every year: {int(held_all(g).sum())}.")
        if A is not None:
            a = A[A.pattern.isin(evs) & (A.horizon == 15)]
            if len(a):
                d = a["diff"] * a.pattern.map(lambda e: orient.get(e, 1))
                out[-1] += f" Per year at 15 minutes, the oriented deviation runs from {d.min()*100:+.1f} to {d.max()*100:+.1f} points over {len(d)} year-cells, {int((d > 0).sum())} of them positive."
    if scale is not None:
        out.append(f"For scale, the largest deviation among the price-action library's cells that hold their sign in every year is {scale*100:.1f} points (price_action_summary.csv).")
    return out


def tick_intro(years: list[int], end: str, null_runs: int, null_all: np.ndarray) -> str:
    return f"Tick-level events for the price-action library, {years[0]} to {end}, every minute as a decision time (definitions in models/btc_15m/library_events.py; every cutoff is a percentile of the previous year). For each event and horizon: minutes it fires on in all years, the share of minutes it fires on over the years in which it was scored (an event with fewer than {MIN_FIRES} firings in a year is not scored in it, and the years columns count the scored years), the pooled up-rate of the next h minutes, the deviation from the unconditional up-rate in points with a 95% interval (day-clustered errors, years combined as independent), the smallest search-wide adjusted p across years ({null_runs} rotated-label runs per year; the smallest possible value is {1/(len(null_all)+1):.4f}), the years in which the sign matched the pooled sign out of years with at least {MIN_FIRES} firings, the years with an adjusted p of at most 0.05, and the share of the last-print deviation kept under the 60-second VWAP label, shown only where the interval excludes zero because a ratio of two near-zero deviations means nothing (at 1 minute the VWAP label compares the two halves of the decision minute, a shorter question). Every cell is listed."


def deriv_intro(years: list[int], end: str, null_runs: int, null_all: np.ndarray) -> str:
    return f"Derivatives events for the price-action library, scored in {years[0]} to {end}, every minute as a decision time. Every cutoff is a decile of the previous calendar year of the futures series themselves, so a year never defines its own extreme. The columns are the same as in the tick table; the share is the share of minutes the event fires on over the years in which it was scored (an event with fewer than {MIN_FIRES} firings in a year is not scored in it, and the years columns count the scored years). The null covers these {len(DERIV_EVENTS)} events at the {len(HORIZONS)} horizons only ({null_runs} rotated-label runs per year; the smallest possible adjusted p is {1/(len(null_all)+1):.4f}). The comparison at each cut is strict, because the funding rate sits at the exchange default on a large share of minutes, so the previous year's upper decile can be the default itself; this was set after the one-year smoke run and is the only thing that run changed. The orientation of the funding and liquidation groups below was fixed before the run."


def render(G: pd.DataFrame, years: list[int], end: str, null_runs: int, null_all: np.ndarray, real_max_z: float, per_year_share: pd.DataFrame, scale: float | None = None, *,
           events: list[tuple[str, str]] = TICK_EVENTS, effects: list = TICK_EFFECTS, orient: dict = TICK_ORIENT, share_events: tuple = TICK_SHARE_EVENTS, intro: str | None = None, year_rows: pd.DataFrame | None = None) -> str:
    """The markdown of a scored library table: results/btc_15m/library_ticks.md by default (the tick
    events), library_derivatives.md with the derivatives arguments. One shaping function for both.
    year_rows: the per-year rows, for the per-year ranges in the effect sentences."""
    fam = {name: f for f, name in events}
    order = {name: k for k, (_, name) in enumerate(events)}
    G = G.assign(_o=G.event.map(order)).sort_values(["_o", "horizon"])
    lines = [tick_intro(years, end, null_runs, null_all) if intro is None else intro, ""]
    lines.append("| family | event | horizon (min) | fires | share (scored years) | up-rate | deviation (points) [95% interval] | min adjusted p | years held | years p<=0.05 | VWAP retained |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in G.itertuples():
        ret = f"{r.retained*100:.0f}%" if (r.lo > 0 or r.hi < 0) and not np.isnan(r.retained) else "-"
        lines.append(f"| {fam[r.event]} | {r.event} | {r.horizon} | {r.fires:,} | {r.share*100:.2f}% | {r.up_rate*100:.1f}% | {r.deviation*100:+.1f} [{r.lo*100:+.1f}, {r.hi*100:+.1f}] | {r.min_p_adj:.4f} | {r.years_held}/{r.years} | {r.years_adj_05}/{r.years} | {ret} |")
    lines += [""] + [s + "\n" for s in sentences(G, null_all, real_max_z, per_year_share, years, events, share_events) + effect_sentences(G, effects, orient, scale, year_rows)]
    return "\n".join(lines).rstrip() + "\n"


# ---------------- derivatives: what the data hold ----------------

FUTURES_SERIES = [("funding rate (monthly files)", r"-funding-(\d{4}-\d{2})\.csv$", "month"),
                  ("open interest and positioning metrics (daily files)", r"-metrics-(\d{4}-\d{2}-\d{2})\.csv$", "day"),
                  ("perpetual 1-minute klines (monthly files)", r"-perp-1m-(\d{4}-\d{2})\.csv$", "month"),
                  ("perpetual 1-minute klines (daily files)", r"-perp-1m-(\d{4}-\d{2}-\d{2})\.csv$", "day")]


def futures_days(cache: Path) -> tuple[pd.DataFrame, set]:
    """Coverage of the futures files in `cache` (first stamp, last stamp, files per series) and the
    set of days on which funding, metrics and perp klines are all present."""
    import re
    rows, days = [], {}
    names = [p.name for p in cache.glob("*.csv")] if cache.exists() else []
    for label, pat, unit in FUTURES_SERIES:
        stamps = sorted(m.group(1) for n in names if (m := re.search(pat, n)))
        rows.append({"series": label, "first": stamps[0] if stamps else "-", "last": stamps[-1] if stamps else "-", "files": len(stamps)})
        got = set()
        for s in stamps:
            if unit == "month":
                p = pd.Period(s, "M")
                got |= {str(d.date()) for d in pd.date_range(p.start_time, p.end_time.normalize())}
            else:
                got.add(s)
        days[label] = got
    f, m = days[FUTURES_SERIES[0][0]], days[FUTURES_SERIES[1][0]]
    return pd.DataFrame(rows), f & m & (days[FUTURES_SERIES[2][0]] | days[FUTURES_SERIES[3][0]])


def full_years(days: set) -> list[int]:
    """Calendar years in which every day is present."""
    ys = sorted({int(d[:4]) for d in days})
    return [y for y in ys if all(str(d.date()) in days for d in pd.date_range(f"{y}-01-01", f"{y}-12-31"))]


def scorable_years(cache: Path, start: int, end: str) -> list[int]:
    """Years that have a fully covered previous year and at least one covered day of their own,
    within start and the year of `end`."""
    return _scorable(futures_days(cache)[1], start, end)


def _scorable(days: set, start: int = 0, end: str = "9999") -> list[int]:
    ok = [y + 1 for y in full_years(days) if any(d.startswith(f"{y + 1}-") for d in days)]
    return [y for y in ok if y in range(start, int(end[:4]) + 1)]


def render_derivatives(cache: Path, G: pd.DataFrame | None = None, years: list[int] | None = None, end: str | None = None, null_runs: int | None = None,
                       null_all: np.ndarray | None = None, real_max_z: float | None = None, per_year_share: pd.DataFrame | None = None, scale: float | None = None, year_rows: pd.DataFrame | None = None) -> str:
    """The markdown of results/btc_15m/library_derivatives.md: the coverage of the futures files, and
    when G (the pooled cells) is given, the scored table and sentences from the same renderer as the
    tick table."""
    cov, days = futures_days(cache)
    full = full_years(days)
    scorable = _scorable(days)
    lines = ["Derivatives events for the price-action library: definitions and the coverage of the futures files held. Every cutoff is a percentile (decile) of the previous calendar year, so an event can be scored in year Y only if the files cover all of year Y-1. The events are defined and tested in models/btc_15m/library_events.py (`deriv_events`).", "",
             "| series | first stamp | last stamp | files |", "|---|---|---|---|"]
    lines += [f"| {r.series} | {r.first} | {r.last} | {r.files} |" for r in cov.itertuples()]
    lines.append("")
    if G is None:
        lines += ["| event |", "|---|"] + [f"| {e} |" for e in DERIV_EVENTS] + [""]
    if scorable:
        lines.append(f"Calendar years fully covered by funding, metrics and perp klines together: {', '.join(map(str, full))}; the events can be scored in {', '.join(map(str, scorable))}.")
    else:
        lines.append(f"The files cover {len(days)} days in total and no calendar year in full, so no event has a previous year to take its cutoffs from and none is scored.")
    text = "\n".join(lines).rstrip() + "\n"
    if G is None:
        return text
    intro = deriv_intro(years, end, null_runs, null_all)
    return text + "\n" + render(G, years, end, null_runs, null_all, real_max_z, per_year_share, scale, events=DERIV_EVENT_FAMILIES, effects=DERIV_EFFECTS,
                                orient=DERIV_ORIENT, share_events=DERIV_SHARE_EVENTS, intro=intro, year_rows=year_rows)


# ---------------- one year ----------------

def code_key() -> str:
    """Identifies the code that produces a year's cells (not the rendering), so a cached year is
    reused when only the tables' wording changes."""
    parts = (known_next, minute_table, tick_quantities, tick_cutoffs, reference_months, reference_cutoffs, streak, new_extremes, tick_events, run_year)
    return hashlib.sha1("".join(inspect.getsource(f) for f in parts).encode()).hexdigest()[:10] + f"-{TICK_FIRST_MONTH}-p{round(P_EXTREME * 100)}-k{''.join(map(str, PERSIST))}"


def read_month(month: str) -> pd.DataFrame:
    """One month's per-second table; refuses to download."""
    p = tick_path(month)
    if not p.exists():
        raise FileNotFoundError(f"missing raw data (nothing is downloaded here): {p}")
    return pd.read_parquet(p)


def require_files(first: str, last: str):
    from models.btc_15m import data
    missing = [str(f) for p in pd.period_range(first, last, freq="M") for f in (data.CACHE / f"BTCUSDT-1m-{p}.csv", tick_path(str(p))) if not f.exists()]
    if missing:
        raise FileNotFoundError(f"missing raw data (nothing is downloaded here): {missing[:4]}{' ...' if len(missing) > 4 else ''}")


def run_year(year: int, end: str, rng, null_runs: int) -> dict:
    """Scored cells (last print and VWAP labels), the null's max |z| runs, and the firing share of
    every event, for one year."""
    first = f"{year - 1}-12"
    last = str(min(pd.Period(f"{year}-12", "M"), pd.Period(end, "M")))
    require_files(first, last)
    cuts = reference_cutoffs(year, read_month)
    s, D = year_frame(year, end)
    r = load_seconds(first, last)
    q = tick_quantities(minute_table(r, int(s.t[0]), len(s.t)))
    E = tick_events(q, cuts, s.h, s.l)
    idx, t = D.i.values, D.t.values
    masks = {k: v[idx] for k, v in E.items()}
    R, max_z = score_year(s, D, None, rng, null_runs, masks_in=masks)
    R.insert(0, "year", year)
    vw = Vwap(r)
    scored = {k: m for k, m in masks.items() if m.sum() >= MIN_FIRES}
    P = vwap_cells(scored, labels(s, idx), t).rename(columns={"diff": "diff_print", "z": "z_print", "fires": "fires_print"})
    V = vwap_cells(scored, vwap_labels(vw, t), t).rename(columns={"diff": "diff_vwap", "z": "z_vwap", "fires": "fires_vwap"})
    V = P.merge(V, on=["horizon", "pattern"])
    V.insert(0, "year", year)
    shares = pd.DataFrame({"year": year, "event": list(masks), "share": [float(m.mean()) for m in masks.values()], "fires": [int(m.sum()) for m in masks.values()]})
    return {"R": R, "V": V, "max_z": max_z, "shares": shares, "cuts": cuts}


# ---------------- one year of derivatives events ----------------

def require_futures(months: list[str]) -> None:
    """Refuses to go on unless every futures file the months need is on disk (funding and perp klines
    monthly, metrics daily), so a build can never reach the download in derivatives._fetch."""
    cache = derivatives.CACHE
    need = []
    for m in months:
        p = pd.Period(m, "M")
        need += [cache / f"BTCUSDT-funding-{m}.csv", cache / f"BTCUSDT-perp-1m-{m}.csv"]
        need += [cache / f"BTCUSDT-metrics-{d.date()}.csv" for d in pd.date_range(p.start_time, p.end_time.normalize())]
    missing = [str(f) for f in need if not f.exists()]
    if missing:
        raise FileNotFoundError(f"missing futures files (nothing is downloaded here): {missing[:4]}{' ...' if len(missing) > 4 else ''}")


def deriv_year_arrays(year: int, end: str) -> tuple:
    """(s, D, arrs) for one year: the spot frame, the decision rows and the five per-minute arrays
    deriv_events reads, aligned to s. Unknown values are NaN."""
    frame = year_frame(year, end)
    if frame is None:
        raise ValueError(f"no data for {year} up to {end}")
    s, D = frame
    first, last = pd.Timestamp(int(s.t[0]), unit="s"), pd.Timestamp(int(s.t[-1]), unit="s")
    months = [str(p) for p in pd.period_range(first.to_period("M"), last.to_period("M"), freq="M")]
    require_futures(months)
    arrs = derivatives.build(np.asarray(s.t, dtype=np.int64), s.c, months, [], missing="nan")
    arrs["ret15"] = spot_return15(s.c)
    return s, D, {k: arrs[k] for k in DERIV_ARRAYS}


def deriv_reference_cutoffs(year: int) -> dict:
    """Deciles of the futures series in the previous calendar year only. The frame of that year
    carries the December before it for history; those minutes do not enter the cutoffs."""
    s, _, prev = deriv_year_arrays(year - 1, f"{year - 1}-12")
    in_year = pd.to_datetime(np.asarray(s.t), unit="s").year == year - 1
    return decile_cuts({k: np.asarray(v)[in_year] for k, v in prev.items()})


def run_deriv_year(year: int, end: str, rng, null_runs: int) -> dict:
    """Same result as run_year, for the derivatives events: scored cells (last print and VWAP labels),
    the null's max |z| runs and the firing share of every event, for one year."""
    first = f"{year - 1}-12"
    last = str(min(pd.Period(f"{year}-12", "M"), pd.Period(end, "M")))
    require_files(first, last)
    cuts = deriv_reference_cutoffs(year)
    s, D, arrs = deriv_year_arrays(year, end)
    E = deriv_events(arrs, cuts)
    idx, t = D.i.values, D.t.values
    masks = {k: v[idx] for k, v in E.items()}
    R, max_z = score_year(s, D, None, rng, null_runs, masks_in=masks)
    R.insert(0, "year", year)
    vw = Vwap(load_seconds(first, last))
    scored = {k: m for k, m in masks.items() if m.sum() >= MIN_FIRES}
    P = vwap_cells(scored, labels(s, idx), t).rename(columns={"diff": "diff_print", "z": "z_print", "fires": "fires_print"})
    V = vwap_cells(scored, vwap_labels(vw, t), t).rename(columns={"diff": "diff_vwap", "z": "z_vwap", "fires": "fires_vwap"})
    V = P.merge(V, on=["horizon", "pattern"])
    V.insert(0, "year", year)
    shares = pd.DataFrame({"year": year, "event": list(masks), "share": [float(m.mean()) for m in masks.values()], "fires": [int(m.sum()) for m in masks.values()]})
    return {"R": R, "V": V, "max_z": max_z, "shares": shares, "cuts": cuts}


def deriv_code_key() -> str:
    """Identifies the code that produces a derivatives year's cells, as code_key does for the ticks."""
    parts = (deriv_events, decile_cuts, spot_return15, deriv_year_arrays, deriv_reference_cutoffs, run_deriv_year, derivatives.build)
    return hashlib.sha1("".join(inspect.getsource(f) for f in parts).encode()).hexdigest()[:10]


def assemble(Rs, Vs, Ss, nulls, years, end, null_runs, out: Path, stem: str) -> tuple:
    """Concatenate the per-year results, add the search-wide adjusted p, write the three per-event csvs
    named by `stem` and return (G, A, shares, null_all, scale)."""
    A = pd.concat(Rs, ignore_index=True)
    V = pd.concat(Vs, ignore_index=True)
    shares = pd.concat(Ss, ignore_index=True)
    null_all = np.concatenate(list(nulls.values()))
    A["p_adj"] = [(1 + (null_all >= abs(z)).sum()) / (len(null_all) + 1) for z in A.z]
    A.merge(V, on=["year", "horizon", "pattern"], how="left").to_csv(out / f"{stem}_years.csv", index=False)
    shares.to_csv(out / f"{stem}_shares.csv", index=False)
    G = pool_cells(A, V)
    G.to_csv(out / f"{stem}.csv", index=False)
    pa = OUT / "price_action_summary.csv"
    scale = None
    if pa.exists():
        P = pd.read_csv(pa)
        scale = float(P[(P.years_held == P.years) & (P.years >= 5)].deviation.abs().max())
    return G, A, shares, null_all, scale


def score_years(years, end, null_runs, refresh, run, key, prefix):
    """The cache-or-run loop for one part: per year the cached result when the code and arguments
    are unchanged, else a fresh run. Prints one line per year."""
    Rs, Vs, Ss, nulls = [], [], [], {}
    for year in years:
        cached = CACHE / f"{prefix}-{year}-{end}-{null_runs}-{key}.pkl"
        if cached.exists() and not refresh:
            res = pd.read_pickle(cached)
        else:
            t0 = time.time()
            res = run(year, end, np.random.default_rng(year), null_runs)
            pd.to_pickle(res, cached)
            print(f"{year}: scored in {time.time() - t0:.0f}s", flush=True)
        Rs.append(res["R"]); Vs.append(res["V"]); Ss.append(res["shares"]); nulls[year] = res["max_z"]
        print(f"{year}: {res['R'].pattern.nunique()} events scored, max |z| {res['R'].z.abs().max():.2f}, null median {np.median(res['max_z']):.2f}; cutoffs {res['cuts']}", flush=True)
    return Rs, Vs, Ss, nulls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2018)
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--null-runs", type=int, default=NULL_RUNS)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--refresh", action="store_true", help="recompute cached years")
    ap.add_argument("--part", choices=("ticks", "derivatives", "both"), default="both")
    ap.add_argument("--years", default="", help="comma-separated years overriding the range (smoke runs)")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    t_all = time.time()
    override = [int(y) for y in a.years.split(",")] if a.years else None
    if a.part in ("ticks", "both"):
        years = override or list(range(a.start, int(a.end[:4]) + 1))
        Rs, Vs, Ss, nulls = score_years(years, a.end, a.null_runs, a.refresh, run_year, code_key(), "year")
        G, A, shares, null_all, scale = assemble(Rs, Vs, Ss, nulls, years, a.end, a.null_runs, out, "library_ticks")
        (out / "library_ticks.md").write_text(render(G, years, a.end, a.null_runs, null_all, float(A.z.abs().max()), shares, scale, year_rows=A), encoding="utf-8")
        print(f"wrote library_ticks.md in {time.time() - t_all:.0f}s", flush=True)
    if a.part in ("derivatives", "both"):
        cov = futures_days(derivatives.CACHE)[0]
        cov.to_csv(out / "library_derivatives_coverage.csv", index=False)
        years = override or scorable_years(derivatives.CACHE, a.start, a.end)
        print(f"derivatives years to score: {years}", flush=True)
        if not years:
            print("no year has a fully covered previous year in the futures files between --start and --end; writing the coverage only", flush=True)
            (out / "library_derivatives.md").write_text(render_derivatives(derivatives.CACHE), encoding="utf-8")
            return
        Rs, Vs, Ss, nulls = score_years(years, a.end, a.null_runs, a.refresh, run_deriv_year, deriv_code_key(), "deriv-year")
        G, A, shares, null_all, scale = assemble(Rs, Vs, Ss, nulls, years, a.end, a.null_runs, out, "library_derivatives")
        (out / "library_derivatives.md").write_text(render_derivatives(derivatives.CACHE, G, years, a.end, a.null_runs, null_all, float(A.z.abs().max()), shares, scale, year_rows=A), encoding="utf-8")
        print(f"wrote library_derivatives.md in {time.time() - t_all:.0f}s", flush=True)


if __name__ == "__main__":
    main()
