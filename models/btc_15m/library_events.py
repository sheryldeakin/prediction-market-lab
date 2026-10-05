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

Derivatives events (pure definitions, tested; not scored: the futures files held here cover
2025-10 to 2026-09 only, so there is no previous year to cut from, see docs/horizons.md):

  funding                  the last settled funding rate is in the top (bottom) decile of the
                           previous year
  open interest            the change over the last 15 (60) minutes is in the top (bottom)
                           decile of the previous year (spike, drop)
  liquidation signature    the 15-minute open-interest change is in the bottom decile, the
                           15-minute spot return is in its bottom (top) decile, and the perp
                           volume of the last 5 minutes against its 24-hour mean is in the top
                           decile: forced closing of longs (shorts) shows as open interest
                           falling while price moves hard on heavy volume. The public files
                           hold no liquidation orders, so this is an inference from those three.

    python -m models.btc_15m.library_events --start 2018 --end 2026-08
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
DERIV_EVENTS = [
    "funding rate in the top decile of the previous year",
    "funding rate in the bottom decile of the previous year",
    "open interest up over 15 minutes (top decile)",
    "open interest down over 15 minutes (bottom decile)",
    "open interest up over 60 minutes (top decile)",
    "open interest down over 60 minutes (bottom decile)",
    "long liquidation signature (open interest down, price down hard, perp volume heavy)",
    "short liquidation signature (open interest down, price up hard, perp volume heavy)",
]


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
    ret15 (spot_return15); cuts: decile_cuts of the previous year's arrays. Unknown values never fire."""
    hi = lambda k: arrs[k] >= cuts[k][1]
    lo = lambda k: arrs[k] <= cuts[k][0]
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
    the years in which both exist."""
    rows = []
    vg = {k: g for k, g in V.groupby(["pattern", "horizon"])}
    for (pat, h), g in A.groupby(["pattern", "horizon"]):
        w = g.fires / g.fires.sum()
        dev_y = (1 - g.share) * g["diff"]
        se_y = (1 - g.share) * g.se
        dev = float((w * dev_y).sum())
        se = float(np.sqrt(((w * se_y) ** 2).sum()))
        row = {"event": pat, "horizon": h, "years": len(g), "years_held": int((np.sign(dev_y) == np.sign(dev)).sum()),
               "fires": int(g.fires.sum()), "share": float(g.share.mean()), "up_rate": float((w * g.up_rate).sum()),
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


def sentences(G: pd.DataFrame, null_all: np.ndarray, real_max_z: float, per_year_share: pd.DataFrame) -> list[str]:
    """The generated summary sentences the doc quotes."""
    ev_order = [name for _, name in TICK_EVENTS]
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
    for ev in ("trade-count climax", "large-trade burst"):
        s = per_year_share[per_year_share.event == ev].set_index("year").share
        out.append(f"'{ev}' fires on {s.min()*100:.2f}% of minutes in its quietest year ({s.idxmin()}) and {s.max()*100:.2f}% in its busiest ({s.idxmax()}).")
    out.append(f"Null: the largest |z| across all events and horizons on rotated labels has median {np.median(null_all):.2f} and 95th percentile {np.quantile(null_all, 0.95):.2f}; the real search's largest |z| is {real_max_z:.2f}.")
    return out


# +1: the event follows a move down, so a reversal is up; -1: it follows a move up
ORIENT = {"trade-count climax at a new 1h high": -1, "trade-count climax at a new 1h low": 1,
          "net taker buying in each of the last 3 minutes": -1, "net taker selling in each of the last 3 minutes": 1,
          "net taker buying in each of the last 5 minutes": -1, "net taker selling in each of the last 5 minutes": 1,
          "large-trade burst with net large buying": -1, "large-trade burst with net large selling": 1}
EFFECTS = [("A reversal from a price extreme on heavy trading", ["trade-count climax at a new 1h high", "trade-count climax at a new 1h low"]),
           ("The same side of the flow for several minutes", [e for e in ORIENT if e.startswith("net taker")]),
           ("Large-trade bursts split by the side of the large trades", ["large-trade burst with net large buying", "large-trade burst with net large selling"]),
           ("Events with no side (deviation signed up)", ["large-trade burst", "trade-count climax", "trade-count climax with no new 1h high or low"])]
EFFECT_HORIZONS = (5, 10, 15, 30)


def effect_sentences(G: pd.DataFrame, scale: float | None = None) -> list[str]:
    """One generated sentence per group of events: the range of the pooled deviation over 5 to 30
    minutes, oriented so that a reversal is positive for events with a side."""
    out = []
    for label, evs in EFFECTS:
        g = G[G.event.isin(evs) & G.horizon.isin(EFFECT_HORIZONS)]
        dev = g.deviation * g.event.map(lambda e: ORIENT.get(e, 1))
        excl = (g.lo > 0) | (g.hi < 0)
        side = "reversal positive" if any(e in ORIENT for e in evs) else "up positive"
        out.append(f"{label}: at {', '.join(str(h) for h in EFFECT_HORIZONS[:-1])} and {EFFECT_HORIZONS[-1]} minutes the pooled deviation runs from {dev.min()*100:+.1f} to {dev.max()*100:+.1f} points ({side}); {int(excl.sum())} of {len(g)} cells have an interval that excludes zero; cells holding their sign in every year: {int(held_all(g).sum())}.")
    if scale is not None:
        out.append(f"For scale, the largest deviation among the price-action library's cells that hold their sign in every year is {scale*100:.1f} points (price_action_summary.csv).")
    return out


def render(G: pd.DataFrame, years: list[int], end: str, null_runs: int, null_all: np.ndarray, real_max_z: float, per_year_share: pd.DataFrame, scale: float | None = None) -> str:
    """The markdown of results/btc_15m/library_ticks.md."""
    fam = {name: f for f, name in TICK_EVENTS}
    order = {name: k for k, (_, name) in enumerate(TICK_EVENTS)}
    G = G.assign(_o=G.event.map(order)).sort_values(["_o", "horizon"])
    lines = [f"Tick-level events for the price-action library, {years[0]} to {end}, every minute as a decision time (definitions in models/btc_15m/library_events.py; every cutoff is a percentile of the previous year). For each event and horizon: minutes it fires on in all years, the share of minutes it fires on, the pooled up-rate of the next h minutes, the deviation from the unconditional up-rate in points with a 95% interval (day-clustered errors, years combined as independent), the smallest search-wide adjusted p across years ({null_runs} rotated-label runs per year; the smallest possible value is {1/(len(null_all)+1):.4f}), the years in which the sign matched the pooled sign out of years with at least {MIN_FIRES} firings, the years with an adjusted p of at most 0.05, and the share of the last-print deviation kept under the 60-second VWAP label, shown only where the interval excludes zero because a ratio of two near-zero deviations means nothing (at 1 minute the VWAP label compares the two halves of the decision minute, a shorter question). Every cell is listed.", ""]
    lines.append("| family | event | horizon (min) | fires | share | up-rate | deviation (points) [95% interval] | min adjusted p | years held | years p<=0.05 | VWAP retained |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in G.itertuples():
        ret = f"{r.retained*100:.0f}%" if (r.lo > 0 or r.hi < 0) and not np.isnan(r.retained) else "-"
        lines.append(f"| {fam[r.event]} | {r.event} | {r.horizon} | {r.fires:,} | {r.share*100:.2f}% | {r.up_rate*100:.1f}% | {r.deviation*100:+.1f} [{r.lo*100:+.1f}, {r.hi*100:+.1f}] | {r.min_p_adj:.4f} | {r.years_held}/{r.years} | {r.years_adj_05}/{r.years} | {ret} |")
    lines += [""] + [s + "\n" for s in sentences(G, null_all, real_max_z, per_year_share) + effect_sentences(G, scale)]
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


def render_derivatives(cache: Path) -> str:
    """The markdown of results/btc_15m/library_derivatives.md: the events, and whether the files held
    allow them to be scored."""
    cov, days = futures_days(cache)
    full = full_years(days)
    scorable = [y + 1 for y in full if any(d.startswith(f"{y + 1}-") for d in days)]
    lines = ["Derivatives events for the price-action library: definitions and the coverage of the futures files held. Every cutoff is a percentile (decile) of the previous calendar year, so an event can be scored in year Y only if the files cover all of year Y-1. The events are defined and tested in models/btc_15m/library_events.py (`deriv_events`).", "",
             "| series | first stamp | last stamp | files |", "|---|---|---|---|"]
    lines += [f"| {r.series} | {r.first} | {r.last} | {r.files} |" for r in cov.itertuples()]
    lines += ["", "| event |", "|---|"] + [f"| {e} |" for e in DERIV_EVENTS] + [""]
    if scorable:
        lines.append(f"Calendar years fully covered by funding, metrics and perp klines together: {', '.join(map(str, full))}; the events can be scored in {', '.join(map(str, scorable))}.")
    else:
        lines.append(f"The files cover {len(days)} days in total and no calendar year in full, so no event has a previous year to take its cutoffs from and none is scored.")
    return "\n".join(lines).rstrip() + "\n"


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2018)
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--null-runs", type=int, default=NULL_RUNS)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--refresh", action="store_true", help="recompute cached years")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    t_all = time.time()
    years = list(range(a.start, int(a.end[:4]) + 1))
    Rs, Vs, Ss, nulls = [], [], [], {}
    for year in years:
        cached = CACHE / f"year-{year}-{a.end}-{a.null_runs}-{code_key()}.pkl"
        if cached.exists() and not a.refresh:
            res = pd.read_pickle(cached)
        else:
            t0 = time.time()
            res = run_year(year, a.end, np.random.default_rng(year), a.null_runs)
            pd.to_pickle(res, cached)
            print(f"{year}: scored in {time.time() - t0:.0f}s", flush=True)
        Rs.append(res["R"]); Vs.append(res["V"]); Ss.append(res["shares"]); nulls[year] = res["max_z"]
        print(f"{year}: {res['R'].pattern.nunique()} events scored, max |z| {res['R'].z.abs().max():.2f}, null median {np.median(res['max_z']):.2f}; cutoffs {res['cuts']}", flush=True)
    A = pd.concat(Rs, ignore_index=True)
    V = pd.concat(Vs, ignore_index=True)
    shares = pd.concat(Ss, ignore_index=True)
    null_all = np.concatenate(list(nulls.values()))
    A["p_adj"] = [(1 + (null_all >= abs(z)).sum()) / (len(null_all) + 1) for z in A.z]
    A.merge(V, on=["year", "horizon", "pattern"], how="left").to_csv(out / "library_ticks_years.csv", index=False)
    shares.to_csv(out / "library_ticks_shares.csv", index=False)
    G = pool_cells(A, V)
    G.to_csv(out / "library_ticks.csv", index=False)
    pa = OUT / "price_action_summary.csv"
    scale = None
    if pa.exists():
        P = pd.read_csv(pa)
        scale = float(P[(P.years_held == P.years) & (P.years >= 5)].deviation.abs().max())
    (out / "library_ticks.md").write_text(render(G, years, a.end, a.null_runs, null_all, float(A.z.abs().max()), shares, scale), encoding="utf-8")
    (out / "library_derivatives.md").write_text(render_derivatives(derivatives.CACHE), encoding="utf-8")
    futures_days(derivatives.CACHE)[0].to_csv(out / "library_derivatives.csv", index=False)
    print(f"wrote library_ticks.md in {time.time() - t_all:.0f}s")


if __name__ == "__main__":
    main()
