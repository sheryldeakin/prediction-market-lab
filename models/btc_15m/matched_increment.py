"""Does the condition add anything to the move it sits on? (docs/horizons.md, "Does the condition
add anything to the move?")

The library's one robust effect is a reversal after a sharp move. Two newer events sit on top of
such a move and reverse too. This module asks whether their extra conditions add anything to the
move they contain, with one design for two contrasts:

  A  liquidation signature against the hard 15-minute move alone. Population: decision minutes
     whose 15-minute spot return (known at the close of minute i-1, as deriv_events reads it) is
     strictly below the previous year's 10th percentile (long side) or strictly above the 90th
     (short side). Treated: the population minutes that also carry the other two legs (open
     interest change over 15 minutes below its lower cut, perp volume ratio above its upper cut),
     which is exactly the library's liquidation signature. Years: the derivatives-scorable years.
  B  trade-count climax against the new 1-hour extreme alone. Population: decision minutes whose
     minute i-1 set a new 60-minute high (low). Treated: those whose minute i-1 trade count was
     above the previous year's 99th percentile, which is exactly "trade-count climax at a new 1h
     high (low)". B2 is the same population with the relative count (minute i-1's count over the
     mean count of the 1440 minutes before it) above its previous-year 99th percentile.

Orientation: reversal positive. After a fall (long side, new low) the reversal is up; after a
rise (short side, new high) it is down.

Each treated minute gets one control from the rest of the population, matched within the year and
side on the four-hour block of the day, the tercile of trailing 60-minute volatility (edges from the
previous year) and the quintile of the size of the move within the tail. The move-size bin is the
matching covariate that stops a bigger move from being read as an effect of the condition: a
treated minute is on average a deeper move than the rest of its population, and a deeper move
reverses more by itself. Controls exclude the 30 minutes after any treated minute.

    python -m models.btc_15m.matched_increment --prereg
    python -m models.btc_15m.matched_increment --start 2018 --end 2026-08 --out results/btc_15m
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import inspect
import json
import subprocess
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m import derivatives
from models.btc_15m import library_events as L
from models.btc_15m import mechanism as M
from models.btc_15m.horizons import HORIZONS, MIN_FIRES, labels, score_year, year_frame
from models.btc_15m.horizons_vwap import cells as vwap_cells, vwap_labels
from models.btc_15m.settlement import Vwap
from models.btc_15m.stats import paired_cluster_se
from models.btc_15m.ticks import load_seconds

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
CACHE = Path("data/matched_increment")        # the working copy's own cache, never LAB_DATA_ROOT
STEM = "matched_increment"

INCREMENT_POINTS = 2.0          # the increment of interest at 15 minutes, in points (half of the pooled liquidation deviation in library_derivatives.csv)
H_PRIMARY = 15
EPISODE_GAP_MIN = 30            # treated minutes with a gap of at least this many minutes start a new episode
CONTROL_BLOCK_MIN = 30          # no control within this many minutes after (and including) a treated minute
LEVEL = 0.05
Z95 = 1.96
REL_WINDOW = 1440               # minutes in the mean the relative trade count is taken against
BLOCK_HOURS = 4
N_TERC = 3
N_QUINT = 5
SMD_MAX = 0.10                  # a primary cell whose matched controls differ from the treated by more than this (standardised, move size) is 'not resolved (support)'

# (contrast, side) -> +1 when the move was a fall (reversal is up), -1 when it was a rise
SIDES = {("A", "long"): 1, ("A", "short"): -1, ("B", "low"): 1, ("B", "high"): -1, ("B2", "low"): 1, ("B2", "high"): -1}
PRIMARY = [("A", "long"), ("A", "short"), ("B", "high"), ("B", "low")]
A_EVENT = {"long": L.DERIV_EVENTS[6], "short": L.DERIV_EVENTS[7]}
B_EVENT = {"high": "trade-count climax at a new 1h high", "low": "trade-count climax at a new 1h low"}
CONTRAST_NAME = {"A": "A: liquidation signature against the hard 15-minute move",
                 "B": "B: trade-count climax against the new 1-hour extreme",
                 "B2": "B2: relative trade-count climax against the new 1-hour extreme"}
SIDE_NAME = {("A", "long"): "long (after a fall)", ("A", "short"): "short (after a rise)", ("B", "low"): "low (after a new low)", ("B", "high"): "high (after a new high)",
             ("B2", "low"): "low (after a new low)", ("B2", "high"): "high (after a new high)"}
LABELS = (("lp", "last print"), ("vw", "VWAP"))
CLUSTERS = (("day", "day"), ("ep", "episode"))
LEG_NAMES = {"ret": "15-minute return extreme", "oi": "15-minute open-interest drop", "vol": "perp volume surge"}
LEG_ORDER = ("ret", "oi", "vol")


# ---------------- populations and treated sets ----------------

def shifted(x: np.ndarray) -> np.ndarray:
    """A per-minute value shifted so decision minute i reads minute i-1's (NaN at the first minute)."""
    out = np.full(len(x), np.nan)
    out[1:] = np.asarray(x, float)[:-1]
    return out


def legs(arrs: dict, cuts: dict) -> dict[str, dict[str, np.ndarray]]:
    """The three legs of the liquidation signature per side, as per-minute flags (not yet shifted). Same
    strict comparisons as library_events.deriv_events; unknown values never fire."""
    oi = arrs["doi15"] < cuts["doi15"][0]
    vol = arrs["pvol_ratio5"] > cuts["pvol_ratio5"][1]
    return {"long": {"ret": arrs["ret15"] < cuts["ret15"][0], "oi": oi, "vol": vol},
            "short": {"ret": arrs["ret15"] > cuts["ret15"][1], "oi": oi, "vol": vol}}


def a_sets(arrs: dict, cuts: dict) -> tuple[dict, dict, np.ndarray]:
    """Contrast A at decision minutes (series-length arrays): the population (the 15-minute return
    leg alone), the treated set (the library's own signature, from deriv_events) and the size of the
    move, |15-minute return| known at the close of the previous minute."""
    E = L.deriv_events(arrs, cuts)
    lg = legs(arrs, cuts)
    pop = {side: L.known_next(lg[side]["ret"]) for side in lg}
    treated = {side: E[A_EVENT[side]] for side in lg}
    return pop, treated, np.abs(shifted(arrs["ret15"]))


def relative_count(n: np.ndarray, window: int = REL_WINDOW) -> np.ndarray:
    """Each minute's trade count over the mean count of the `window` minutes before it; NaN where
    fewer than `window` minutes precede it or the mean is zero."""
    cs = np.concatenate([[0.0], np.cumsum(np.asarray(n, float))])
    out = np.full(len(n), np.nan)
    if len(n) > window:
        mean = (cs[window:-1] - cs[:-window - 1]) / window
        out[window:] = np.where(mean > 0, n[window:] / np.where(mean > 0, mean, 1.0), np.nan)
    return out


def overshoot(h: np.ndarray, l: np.ndarray, w: int = L.EXTREME_WINDOW) -> tuple[np.ndarray, np.ndarray]:
    """How far each minute's high exceeded the highest high of the w minutes before it, and how far its
    low fell below the lowest low of those minutes, in basis points (NaN without w minutes of history)."""
    prev_hi = pd.Series(h).shift(1).rolling(w).max().values
    prev_lo = pd.Series(l).shift(1).rolling(w).min().values
    return (h / prev_hi - 1) * 1e4, (prev_lo / l - 1) * 1e4


def b_sets(q: dict, cuts: dict, rel_cut: float, h: np.ndarray, l: np.ndarray) -> tuple[dict, dict, dict, dict]:
    """Contrast B and B2 at decision minutes (series-length arrays): the population (a new 60-minute
    high or low in the previous minute), the treated sets (the library's climax at a new extreme, and
    the relative-count version) and the size of the move (overshoot of the extreme, in basis points)."""
    hi, lo = L.new_extremes(h, l)
    E = L.tick_events(q, cuts, h, l)
    rel = relative_count(q["n"])
    rel_hit = rel > rel_cut
    pop = {"high": L.known_next(hi), "low": L.known_next(lo)}
    treated = {"high": E[B_EVENT["high"]], "low": E[B_EVENT["low"]]}
    treated2 = {"high": L.known_next(rel_hit & hi), "low": L.known_next(rel_hit & lo)}
    over_hi, over_lo = overshoot(h, l)
    return pop, treated, treated2, {"high": shifted(over_hi), "low": shifted(over_lo)}


def relative_reference_cutoff(year: int, read_month, first: str = L.TICK_FIRST_MONTH) -> float:
    """The 99th percentile of the relative trade count over the minutes of the previous calendar year
    (or what the data hold of it). The month before the reference months is read for the first 1440
    minutes' history when it exists."""
    months = L.reference_months(year, first)
    if not months:
        raise ValueError(f"no data before {year} to take cutoffs from")
    prior = pd.Period(months[0], "M") - 1
    use = ([str(prior)] if prior >= pd.Period(first, "M") else []) + months
    parts = []
    for mo in use:
        p = pd.Period(mo, "M")
        parts.append(L.minute_table(read_month(mo), int(p.start_time.value // 10**9), p.days_in_month * 1440)["n"])
    rel = relative_count(np.concatenate(parts))
    skip = len(parts[0]) if len(use) > len(months) else 0
    r = rel[skip:]
    return float(np.quantile(r[np.isfinite(r)], L.P_EXTREME))


# ---------------- strata and episodes ----------------

def vol_terciles(vol: np.ndarray, edges: np.ndarray) -> np.ndarray:
    """0, 1, 2 against the two edges (the previous year's thirds of trailing 60-minute volatility)."""
    return np.searchsorted(edges, vol, side="right")


def move_quintiles(move: np.ndarray, basis: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Bin 0..4 of `move` against the quintile edges of the rows in `basis`; returns (bin per row, the four
    edges). The study passes the TREATED minutes as the basis, so each bin holds about a fifth of the treated:
    treated minutes sit far out in the population's tail, and population quintiles would put nearly all of
    them in the top bin, where the controls are smaller moves. Rows with an unknown move get -1."""
    use = move[basis & np.isfinite(move)]
    edges = np.quantile(use, [0.2, 0.4, 0.6, 0.8]) if len(use) else np.zeros(4)
    q = np.searchsorted(edges, move, side="right")
    return np.where(np.isfinite(move), q, -1), edges


def stratum_key(hour: np.ndarray, terc: np.ndarray, quint: np.ndarray) -> np.ndarray:
    """One integer per (four-hour block, volatility tercile, move-size quintile)."""
    return ((hour // BLOCK_HOURS) * N_TERC + terc) * N_QUINT + quint


def episode_ids(t: np.ndarray, gap_min: int = EPISODE_GAP_MIN) -> np.ndarray:
    """Episode number of each treated minute (t: epoch seconds, ascending). A treated minute whose gap
    from the previous treated minute is at least gap_min minutes starts a new episode; a gap of
    gap_min - 1 minutes or less continues it."""
    t = np.asarray(t, np.int64)
    if len(t) == 0:
        return np.zeros(0, np.int64)
    new = np.concatenate([[True], np.diff(t) >= gap_min * 60])
    return np.cumsum(new) - 1


# ---------------- one year ----------------

def vol_tercile_edges(year: int, D: pd.DataFrame) -> np.ndarray:
    """Thirds of trailing 60-minute volatility over the previous calendar year's decision minutes; the
    first year the data hold, which has no previous year, uses its own first quarter. Reads kline files
    that are on disk only."""
    from models.btc_15m import data
    first, last = f"{year - 2}-12", f"{year - 1}-12"
    have = all((data.CACHE / f"BTCUSDT-1m-{p}.csv").exists() for p in pd.period_range(first, last, freq="M"))
    if have:
        prev = year_frame(year - 1, f"{year - 1}-12")
        if prev is not None and len(prev[1]):
            return np.quantile(prev[1].vol60.values, [1 / 3, 2 / 3])
    q1 = D[pd.to_datetime(D.t, unit="s").dt.month <= 3]
    return np.quantile(q1.vol60.values, [1 / 3, 2 / 3])


def build_pairs(*, year: int, contrast: str, side: str, population: np.ndarray, treated: np.ndarray, move: np.ndarray, D: pd.DataFrame, n_series: int,
                vol_edges: np.ndarray, Lp: dict, Vw: dict, rng) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """The matched pairs of one (year, contrast, side), the support rows and the counts. population,
    treated and move are per row of D (treated is a subset of population)."""
    direction = SIDES[(contrast, side)]
    i_all, t = D.i.values, D.t.values
    population = population & np.isfinite(move)
    treated = treated & population
    quint, _ = move_quintiles(move, treated)
    key = stratum_key(D.hour.values, vol_terciles(D.vol60.values, vol_edges), np.maximum(quint, 0))
    fire = np.zeros(n_series, bool)
    fire[i_all[treated]] = True
    excluded = M.recent_any(fire, CONTROL_BLOCK_MIN)[i_all]
    # common support: a control whose move is smaller than the smallest treated move, or larger than the largest, has no treated
    # minute like it, and the outermost bins are open-ended, so such controls would be matched to the end bins and unbalance them
    inside = (move >= move[treated].min()) & (move <= move[treated].max()) if treated.any() else np.zeros(len(move), bool)
    eligible = np.where(population & ~excluded & inside)[0]
    event_pos = np.where(treated)[0]
    ctrl, replaced = M.match_by_stratum(key, event_pos, eligible, rng)
    ok = ctrl >= 0
    ep = episode_ids(t[event_pos])
    elig_q = np.bincount(quint[eligible], minlength=N_QUINT)
    support = pd.DataFrame({"year": year, "contrast": contrast, "side": side, "quintile": np.arange(N_QUINT),
                            "treated": np.bincount(quint[event_pos], minlength=N_QUINT), "population": np.bincount(quint[population], minlength=N_QUINT),
                            "eligible": elig_q, "unmatched": np.bincount(quint[event_pos][~ok], minlength=N_QUINT)})
    no_support = int((elig_q[quint[event_pos]] == 0).sum())
    stats = {"year": year, "contrast": contrast, "side": side, "population": int(population.sum()), "treated": int(len(event_pos)), "eligible": int(len(eligible)),
             "matched": int(ok.sum()), "unmatched": int((~ok).sum()), "unmatched_no_support": no_support, "with_replacement": int(replaced)}
    E, C = event_pos[ok], ctrl[ok]
    P = pd.DataFrame({"year": year, "contrast": contrast, "side": side, "t": t[E], "t_control": t[C], "day": t[E] // 86400, "episode": ep[ok],
                      "move_t": move[E], "move_c": move[C], "vol_t": D.vol60.values[E], "vol_c": D.vol60.values[C]})
    for h in HORIZONS:
        P[f"lp{h}_t"], P[f"lp{h}_c"] = M.orient(Lp[h][E], direction), M.orient(Lp[h][C], direction)
        P[f"vw{h}_t"], P[f"vw{h}_c"] = M.orient(Vw[h][E], direction), M.orient(Vw[h][C], direction)
    return P, support, stats


def subset_masks(arrs: dict, cuts: dict, idx: np.ndarray) -> dict[str, tuple[str, tuple[str, ...]]]:
    """Per row of D, the event 'every leg in the subset is on' for each non-empty subset of the three
    legs and each side, with its (side, legs) label."""
    from itertools import combinations
    lg = legs(arrs, cuts)
    masks, info = {}, {}
    for side in lg:
        for r in range(1, len(LEG_ORDER) + 1):
            for sub in combinations(LEG_ORDER, r):
                m = np.logical_and.reduce([lg[side][k] for k in sub])
                name = f"{side}: " + " + ".join(sub)
                masks[name] = L.known_next(m)[idx]
                info[name] = (side, sub)
    return masks, info


def run_year(year: int, end: str, do_a: bool, do_b: bool) -> dict:
    """Matched pairs, support rows, counts and (contrast A) the descriptive subset cells of one year."""
    first = f"{year - 1}-12"
    last = str(min(pd.Period(f"{year}-12", "M"), pd.Period(end, "M")))
    L.require_files(first, last)
    if do_a:
        cuts_a = L.deriv_reference_cutoffs(year)
        s, D, arrs = L.deriv_year_arrays(year, end)
    else:
        s, D = year_frame(year, end)
    idx, t = D.i.values, D.t.values
    r = load_seconds(first, last)
    Lp, Vw = labels(s, idx), vwap_labels(Vwap(r), t)
    vol_edges = vol_tercile_edges(year, D)
    out = {"year": year, "pairs": [], "support": [], "stats": [], "R": None, "V": None, "subset_info": None, "edges": [float(x) for x in vol_edges]}

    def add(contrast, side, pop, tr, mv):
        P, S, st = build_pairs(year=year, contrast=contrast, side=side, population=pop[idx], treated=tr[idx], move=mv[idx], D=D, n_series=len(s.c), vol_edges=vol_edges, Lp=Lp, Vw=Vw,
                               rng=np.random.default_rng([year, list(SIDES).index((contrast, side))]))
        out["pairs"].append(P); out["support"].append(S); out["stats"].append(st)

    if do_a:
        pop, tr, mv = a_sets(arrs, cuts_a)
        for side in ("long", "short"):
            add("A", side, pop[side], tr[side], mv)
        masks, info = subset_masks(arrs, cuts_a, idx)
        R, _ = score_year(s, D, None, np.random.default_rng(year), 0, masks_in=masks)
        R.insert(0, "year", year)
        scored = {k: m for k, m in masks.items() if m.sum() >= MIN_FIRES}
        P_ = vwap_cells(scored, Lp, t).rename(columns={"diff": "diff_print", "z": "z_print", "fires": "fires_print"})
        V_ = vwap_cells(scored, Vw, t).rename(columns={"diff": "diff_vwap", "z": "z_vwap", "fires": "fires_vwap"})
        V = P_.merge(V_, on=["horizon", "pattern"])
        V.insert(0, "year", year)
        out["R"], out["V"], out["subset_info"] = R, V, info
    if do_b:
        q = L.tick_quantities(L.minute_table(r, int(s.t[0]), len(s.t)))
        cuts = L.reference_cutoffs(year, L.read_month)
        rel_cut = relative_reference_cutoff(year, L.read_month)
        pop, tr, tr2, mv = b_sets(q, cuts, rel_cut, s.h, s.l)
        for side in ("high", "low"):
            add("B", side, pop[side], tr[side], mv[side])
            add("B2", side, pop[side], tr2[side], mv[side])
        out["cuts_b"] = {"n": cuts["n"], "rel": rel_cut}
    return out


def code_key() -> str:
    """Identifies the code that produces a year's pairs (not the rendering), so a cached year is reused
    when only the tables' wording changes."""
    parts = (shifted, legs, a_sets, relative_count, overshoot, b_sets, relative_reference_cutoff, vol_terciles, move_quintiles, stratum_key, episode_ids, vol_tercile_edges,
             build_pairs, subset_masks, run_year, M.match_by_stratum, M.recent_any, M.orient, L.deriv_events, L.known_next, L.decile_cuts, L.spot_return15, L.deriv_year_arrays,
             L.deriv_reference_cutoffs, L.tick_events, L.new_extremes, L.reference_cutoffs, L.minute_table, L.tick_quantities, labels, vwap_labels)
    consts = f"{EPISODE_GAP_MIN}-{CONTROL_BLOCK_MIN}-{REL_WINDOW}-{BLOCK_HOURS}-{N_TERC}-{N_QUINT}-{L.P_EXTREME}-{L.EXTREME_WINDOW}-{MIN_FIRES}-treatedbins"
    return hashlib.sha1((consts + "".join(inspect.getsource(f) for f in parts)).encode()).hexdigest()[:10]


# ---------------- estimates ----------------

def pair_estimate(P: pd.DataFrame, lab: str, h: int) -> dict:
    """Mean over pairs of (treated minus control), in points, with the day-clustered and the
    episode-clustered standard error, and the two oriented reversal rates."""
    tr, ct = P[f"{lab}{h}_t"].values, P[f"{lab}{h}_c"].values
    ok = ~(np.isnan(tr) | np.isnan(ct))
    n = int(ok.sum())
    if n < 2:
        return {"n": n, "est": float("nan"), "se_day": float("nan"), "se_ep": float("nan"), "treated_rate": float("nan"), "control_rate": float("nan")}
    d = (tr[ok] - ct[ok]) * 100.0
    return {"n": n, "est": float(d.mean()), "se_day": paired_cluster_se(d, P.day.values[ok]), "se_ep": paired_cluster_se(d, P.episode.values[ok]),
            "treated_rate": float(tr[ok].mean()), "control_rate": float(ct[ok].mean())}


def standardised_difference(a: np.ndarray, b: np.ndarray) -> float:
    """Difference of the means over the pooled standard deviation, sqrt((var a + var b) / 2)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    sd = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2) if len(a) > 1 and len(b) > 1 else 0.0
    return float((a.mean() - b.mean()) / sd) if sd > 0 else 0.0


def scored_years(pairs: pd.DataFrame) -> pd.DataFrame:
    """The matched pairs of the (year, contrast, side) cells that are scored: a cell-year with fewer than
    MIN_FIRES matched pairs is not scored and does not enter the pool, as the library's own tables."""
    n = pairs.groupby(["year", "contrast", "side"]).t.transform("size")
    return pairs[n >= MIN_FIRES]


def balance_table(pairs: pd.DataFrame) -> pd.DataFrame:
    """Post-match balance per (year, contrast, side) and, as year 'all', pooled over the scored years: the
    mean move size of treated minutes and of their matched controls, the standardised difference, and the
    same for the trailing volatility. The move size is in the unit of the contrast (basis points)."""
    rows = []
    sc = scored_years(pairs)
    for year, src in [(y, g) for y, g in pairs.groupby("year")] + [("all", sc)]:
        for (contrast, side), P in src.groupby(["contrast", "side"], sort=False):
            rows.append({"year": year, "contrast": contrast, "side": side, "pairs": len(P),
                         "move_treated": float(P.move_t.mean()), "move_control": float(P.move_c.mean()), "move_smd": standardised_difference(P.move_t.values, P.move_c.values),
                         "vol_treated": float(P.vol_t.mean()), "vol_control": float(P.vol_c.mean()), "vol_smd": standardised_difference(P.vol_t.values, P.vol_c.values)})
    return pd.DataFrame(rows)


def year_cells(pairs: pd.DataFrame) -> pd.DataFrame:
    """One row per (year, contrast, side, horizon, label), for the scored cell-years only."""
    rows = []
    for (year, contrast, side), P in scored_years(pairs).groupby(["year", "contrast", "side"]):
        for h in HORIZONS:
            for lab, _ in LABELS:
                rows.append({"year": year, "contrast": contrast, "side": side, "horizon": h, "label": lab, **pair_estimate(P, lab, h)})
    return pd.DataFrame(rows)


def pool(g: pd.DataFrame) -> dict:
    """Pool the year rows of one (contrast, side, horizon, label) by pairs, as library_events.pool_cells
    pools by firings: the estimate is the pair-weighted mean of the year estimates and its error
    combines the years as independent. Years with an unknown or infinite error are left out."""
    g = g[np.isfinite(g.est) & np.isfinite(g.se_day) & np.isfinite(g.se_ep) & (g.n > 0)]
    if not len(g):
        return {"years": 0, "n": 0}
    w = g.n / g.n.sum()
    est = float((w * g.est).sum())
    out = {"years": len(g), "n": int(g.n.sum()), "est": est, "held": int((np.sign(g.est) == np.sign(est)).sum()),
           "treated_rate": float((w * g.treated_rate).sum()), "control_rate": float((w * g.control_rate).sum()),
           "yr_min": float(g.est.min()), "yr_max": float(g.est.max())}
    for key, _ in CLUSTERS:
        se = float(np.sqrt(((w * g[f"se_{key}"]) ** 2).sum()))
        out[f"se_{key}"], out[f"lo_{key}"], out[f"hi_{key}"] = se, est - Z95 * se, est + Z95 * se
    return out


def main_table(Y: pd.DataFrame, stats: pd.DataFrame) -> pd.DataFrame:
    """One row per (contrast, side, horizon): the pooled estimates under both labels and both error
    estimates, the pairs and the share drawn without replacement."""
    rows = []
    for (contrast, side), s in stats.groupby(["contrast", "side"]):
        matched = int(s.matched.sum())
        nonrepl = 1 - s.with_replacement.sum() / matched if matched else float("nan")
        for h in HORIZONS:
            row = {"contrast": contrast, "side": side, "horizon": h, "matched_without_replacement": nonrepl, "years_total": int(len(s))}
            for lab, _ in LABELS:
                p = pool(Y[(Y.contrast == contrast) & (Y.side == side) & (Y.horizon == h) & (Y.label == lab)])
                row.update({f"{lab}_{k}": v for k, v in p.items()})
            rows.append(row)
    return pd.DataFrame(rows)


# ---------------- the pre-registered rule ----------------

def cell_interval(row, lab: str) -> dict:
    return {key: (row[f"{lab}_lo_{key}"], row[f"{lab}_hi_{key}"]) for key, _ in CLUSTERS}


def decide(c: dict, increment: float = INCREMENT_POINTS, smd: float | None = None) -> tuple[str, str]:
    """The decision rule of the pre-registration. c: {"lp": {"day": (lo, hi), "ep": (lo, hi)}, "vw": {...},
    "held_lp", "held_vw", "years"} in points. 'adds something' when all four intervals (two labels, two
    error estimates) lie above zero and the sign is held in a majority of years under both labels;
    'adds nothing measurable' when all four lie below the increment of interest; otherwise 'not resolved',
    with the reason in words. Before either, a cell whose post-match standardised difference of the move
    size (smd) exceeds SMD_MAX in absolute value is 'not resolved (support)' regardless of the intervals."""
    if smd is not None and abs(smd) > SMD_MAX:
        return "not resolved (support)", "the matched controls do not balance the size of the move, so the intervals are not read"
    iv = {lab: [c[lab][k] for k, _ in CLUSTERS] for lab, _ in LABELS}
    above = {lab: all(lo > 0 for lo, _ in v) for lab, v in iv.items()}
    majority = c["held_lp"] * 2 > c["years"] and c["held_vw"] * 2 > c["years"]
    if all(above.values()) and majority:
        return "adds something", "all four intervals are above zero and the sign is held in a majority of years under both labels"
    if all(hi < increment for v in iv.values() for _, hi in v):
        return "adds nothing measurable", "all four intervals lie below the increment of interest"
    if all(above.values()):
        return "not resolved", "the intervals are above zero but the sign is held in half of the years or fewer under at least one label"
    if above["lp"] != above["vw"]:
        return "not resolved", "one label clears zero under both error estimates and the other does not"
    return "not resolved", "an interval straddles zero or the increment of interest"


def holm(p: list[float]) -> list[float]:
    """Holm step-down adjusted p-values."""
    order = np.argsort(p)
    adj = np.empty(len(p))
    run = 0.0
    for rank, k in enumerate(order):
        run = max(run, min(1.0, (len(p) - rank) * p[k]))
        adj[k] = run
    return adj.tolist()


def cell_p(row) -> float:
    """The p-value of the 'adds something' claim for one pooled cell: the largest two-sided p over the four
    (label, error) estimates, taken as 1 if any estimate is not above zero (the claim is an intersection)."""
    from scipy.stats import norm
    ps = []
    for lab, _ in LABELS:
        for key, _ in CLUSTERS:
            est, se = row[f"{lab}_est"], row[f"{lab}_se_{key}"]
            ps.append(1.0 if not (np.isfinite(est) and se > 0 and est > 0) else float(2 * (1 - norm.cdf(est / se))))
    return max(ps)


def verdicts(G: pd.DataFrame, bal: pd.DataFrame | None = None) -> list[dict]:
    """The verdict of each primary cell by the rule, with the Holm adjustment. bal: balance_table, whose
    pooled ('all') row gives each cell's standardised difference of the move size."""
    out = []
    for contrast, side in PRIMARY:
        r = G[(G.contrast == contrast) & (G.side == side) & (G.horizon == H_PRIMARY)]
        if not len(r) or not r.iloc[0].get("lp_years", 0):
            out.append({"contrast": contrast, "side": side, "verdict": "not scored", "reason": "no year had pairs", "p": 1.0})
            continue
        r = r.iloc[0]
        c = {"lp": cell_interval(r, "lp"), "vw": cell_interval(r, "vw"), "held_lp": int(r.lp_held), "held_vw": int(r.vw_held), "years": int(min(r.lp_years, r.vw_years))}
        smd = None
        if bal is not None:
            b = bal[(bal.year.astype(str) == "all") & (bal.contrast == contrast) & (bal.side == side)]
            smd = float(b.move_smd.iloc[0]) if len(b) else None
        v, why = decide(c, smd=smd)
        out.append({"contrast": contrast, "side": side, "verdict": v, "reason": why, "p": cell_p(r), "move_smd": smd})
    adj = holm([x["p"] for x in out])
    for x, a in zip(out, adj):
        x["p_holm"] = a
    return out


# ---------------- pre-registration ----------------

def pooled_se(years: pd.DataFrame, event: str, h: int = H_PRIMARY) -> tuple[float, int]:
    """The pooled standard error of the paired difference from the treated cell's per-year errors: sqrt(2)
    times the cell's error in each year, combined by firings as library_events.pool_cells does. Returns
    (standard error in the table's units, years used)."""
    g = years[(years.pattern == event) & (years.horizon == h)]
    if not len(g):
        return float("nan"), 0
    w = g.fires / g.fires.sum()
    return float(np.sqrt(((w * np.sqrt(2) * g.se) ** 2).sum())), len(g)


def prereg_block(years_a: pd.DataFrame, years_b: pd.DataFrame, lib_a: pd.DataFrame, commit: str, stamp: str) -> tuple[str, dict]:
    """The pre-registration text (markdown) and its numbers (json), from existing data only: the
    per-year errors of the library's treated cells and the pooled liquidation deviation."""
    dev = {side: float(lib_a[(lib_a.event == A_EVENT[side]) & (lib_a.horizon == H_PRIMARY)].deviation.iloc[0]) * 100 * SIDES[("A", side)] for side in ("long", "short")}
    mdi = {}
    for contrast, side in PRIMARY:
        years, event = (years_a, A_EVENT[side]) if contrast == "A" else (years_b, B_EVENT[side])
        se, n = pooled_se(years, event)
        mdi[f"{contrast}-{side}"] = {"se_points": se * 100, "detectable_points": Z95 * se * 100, "years": n}
    lines = [f"Pre-registration of the matched-increment study, written {stamp} at commit {commit[:10]} from existing data only, before any matched result was computed. It is generated by `python -m models.btc_15m.matched_increment --prereg` and is not edited afterwards.", "",
             f"**Increment of interest.** {INCREMENT_POINTS:.1f} points at the {H_PRIMARY}-minute horizon, in the oriented difference (treated reversal rate minus control reversal rate, in points). The rule that sets it: half of the pooled liquidation deviation at {H_PRIMARY} minutes in library_derivatives.csv, which is {dev['long']:+.1f} points for the long signature and {dev['short']:+.1f} points for the short signature (reversal positive), so half of them is {dev['long'] / 2:.2f} and {dev['short'] / 2:.2f} points; the constant is set to {INCREMENT_POINTS:.1f}.", "",
             f"**Minimum detectable increment.** For each primary cell the paired difference's standard error is taken as the square root of two times the treated cell's per-year standard error at {H_PRIMARY} minutes (library_derivatives_years.csv for contrast A, library_ticks_years.csv for contrast B), combined over the years by firings as the library's pooled cells are; the detectable increment is {Z95} times that error.", ""]
    for contrast, side in PRIMARY:
        m = mdi[f"{contrast}-{side}"]
        rel = "above" if INCREMENT_POINTS > m["detectable_points"] else "below"
        lines.append(f"- {CONTRAST_NAME[contrast]}, {SIDE_NAME[(contrast, side)]}: the detectable increment is {m['detectable_points']:.2f} points over {m['years']} years, so the increment of interest ({INCREMENT_POINTS:.2f} points) is {rel} it.")
    lines += ["", f"**Decision rule.** The condition 'adds something' at a horizon only if the pooled treated-minus-control difference has a day-clustered AND an episode-clustered {100 - 100 * LEVEL:.0f}% interval above zero under BOTH labels (last print and VWAP) and the sign holds in a majority of years under both labels. It 'adds nothing measurable' only if both intervals under both labels lie below the increment of interest ({INCREMENT_POINTS:.1f} points). Otherwise the result is 'not resolved', and is stated as such. Before any of this, a primary cell whose matched controls do not balance the size of the move, a standardised difference (difference of the treated and control means over the pooled standard deviation, pooled over the scored years) above {SMD_MAX:.2f} in absolute value, is 'not resolved (support)' regardless of the intervals.", "",
              f"**Primary cells.** The {H_PRIMARY}-minute horizon for the four cells {', '.join(f'{c}-{s}' for c, s in PRIMARY)}, with Holm's step-down adjustment across the four at level {LEVEL} (each cell's p is the largest two-sided p of its four estimates, so it rejects only when the rule's intervals are all above zero). Every other horizon and the relative-count contrast (B2) are descriptive. The subsets of the three legs of contrast A are a descriptive table only.", "",
              f"**Design in one sentence.** Each treated minute is matched within its year and side to one control from the rest of its population, in the same four-hour block, the same tercile of trailing 60-minute volatility (edges from the previous year) and the same bin of the move's size, where the five bins are the quintiles of the TREATED minutes' move size in that year and side (so each holds about a fifth of the treated, because the treated sit far out in the population's tail); a control whose move is smaller than the smallest treated move or larger than the largest is not eligible (the outermost bins are open-ended, and controls beyond the treated range would unbalance them); a treated minute in a bin with no eligible control is left unmatched and counted; controls exclude the {CONTROL_BLOCK_MIN} minutes after any treated minute; episodes merge treated minutes less than {EPISODE_GAP_MIN} minutes apart.", "",
              f"**Scored years.** As in the library's tables, a year with fewer than {MIN_FIRES} matched pairs in a cell is not scored for that cell and does not enter its pool; the results state in how many of the years each cell was scored."]
    data = {"written": stamp, "commit": commit, "increment_points": INCREMENT_POINTS, "horizon": H_PRIMARY, "level": LEVEL, "liquidation_deviation_points": dev,
            "minimum_detectable": mdi, "primary": [f"{c}-{s}" for c, s in PRIMARY], "episode_gap_minutes": EPISODE_GAP_MIN, "control_block_minutes": CONTROL_BLOCK_MIN,
            "min_pairs_per_cell_year": MIN_FIRES, "smd_max": SMD_MAX}
    return "\n".join(lines) + "\n", data


def git(*args) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip()


def write_prereg(out: Path, lib: Path = OUT) -> None:
    md, data = prereg_block(pd.read_csv(lib / "library_derivatives_years.csv"), pd.read_csv(lib / "library_ticks_years.csv"), pd.read_csv(lib / "library_derivatives.csv"),
                            git("rev-parse", "HEAD"), dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
    (out / f"{STEM}_prereg.md").write_text(md, encoding="utf-8")
    (out / f"{STEM}_prereg.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------- rendering ----------------

def _iv(lo: float, hi: float) -> str:
    return f"[{lo:+.1f}, {hi:+.1f}]"


def _diff(r, lab: str) -> str:
    if not r.get(f"{lab}_years", 0):
        return "n/a"
    return f"{r[f'{lab}_est']:+.1f} day {_iv(r[f'{lab}_lo_day'], r[f'{lab}_hi_day'])}, episode {_iv(r[f'{lab}_lo_ep'], r[f'{lab}_hi_ep'])}"


def render_main(G: pd.DataFrame, stats: pd.DataFrame, V: list[dict], years: dict, end: str) -> str:
    ya = years.get("A", [])
    intro = (f"Does the condition add anything to the move it sits on? Matched treated minutes (the condition holds) against controls (the move alone), reversal positive, every minute as a decision time. "
             f"Contrast A, {', '.join(map(str, ya)) or 'no year'}: the liquidation signature against the hard 15-minute move (return strictly beyond the previous year's 10th or 90th percentile). "
             f"Contrast B, {years['B'][0]} to {years['B'][-1]}: a trade count above the previous year's 99th percentile at a new 1-hour extreme, against new 1-hour extremes without it; B2 uses the count relative to the previous {REL_WINDOW} minutes. "
             f"Each treated minute has one control in the same year and side, the same four-hour block, the same tercile of trailing 60-minute volatility (previous-year edges) and the same bin of the move's size (the five bins are the quintiles of the treated minutes' move size in that year and side, and controls outside the range of the treated minutes' move size are not eligible); a year with fewer than {MIN_FIRES} matched pairs in a cell is not scored for it; controls exclude the {CONTROL_BLOCK_MIN} minutes after any treated minute. "
             f"The difference is the mean over pairs of (treated outcome minus control outcome) in points, under the last-print label and the 60-second VWAP label, with {100 - 100 * LEVEL:.0f}% intervals from errors clustered by UTC day and by episode (treated minutes less than {EPISODE_GAP_MIN} minutes apart form one), years pooled by pairs as the library tables pool by firings. "
             f"Reversal rate is the share of oriented outcomes that point back against the move. Years held: years whose difference has the pooled sign, under the last print and under the VWAP label. The per-year range is shown at {H_PRIMARY} minutes, last print and VWAP.")
    lines = [intro, "", "| contrast | side | horizon (min) | pairs | drawn without replacement | treated reversal rate | control reversal rate | difference, last print (points) | difference, VWAP (points) | years held (last print, VWAP) | per-year range at 15 min (last print; VWAP) |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    order = {k: n for n, k in enumerate(SIDES)}
    for r in sorted(G.itertuples(index=False), key=lambda r: (order[(r.contrast, r.side)], r.horizon)):
        d = r._asdict()
        if not d.get("lp_years", 0):
            continue
        rng = f"{d['lp_yr_min']:+.1f} to {d['lp_yr_max']:+.1f}; {d['vw_yr_min']:+.1f} to {d['vw_yr_max']:+.1f}" if r.horizon == H_PRIMARY and d.get("vw_years", 0) else "-"
        lines.append(f"| {r.contrast} | {SIDE_NAME[(r.contrast, r.side)]} | {r.horizon} | {int(d['lp_n']):,} | {d['matched_without_replacement']*100:.1f}% | {d['lp_treated_rate']*100:.1f}% | {d['lp_control_rate']*100:.1f}% | "
                     f"{_diff(d, 'lp')} | {_diff(d, 'vw')} | {int(d['lp_held'])}/{int(d['lp_years'])}, {int(d.get('vw_held', 0))}/{int(d.get('vw_years', 0))} | {rng} |")
    lines.append("")
    for v in V:
        g = G[(G.contrast == v["contrast"]) & (G.side == v["side"]) & (G.horizon == H_PRIMARY)]
        extra = f" Standardised difference of the move size after matching {v['move_smd']:+.3f}." if v.get("move_smd") is not None else ""
        if len(g) and g.iloc[0].get("lp_years", 0):
            r = g.iloc[0]
            extra += f" Last print {_diff(r, 'lp')}; VWAP {_diff(r, 'vw')}; years held {int(r.lp_held)}/{int(r.lp_years)} and {int(r.vw_held)}/{int(r.vw_years)}."
        lines.append(f"{CONTRAST_NAME[v['contrast']]}, {SIDE_NAME[(v['contrast'], v['side'])]}, {H_PRIMARY} minutes, by the pre-registered rule: {v['verdict']} ({v['reason']}).{extra}\n")
    rej = sum(x["p_holm"] <= LEVEL for x in V)
    adj = ", ".join("{}-{} {:.3f}".format(x["contrast"], x["side"], x["p_holm"]) for x in V)
    lines.append(f"Holm across the four primary cells at level {LEVEL}: {rej} of {len(V)} rejected (adjusted p {adj}).\n")
    for (contrast, side), s in stats.groupby(["contrast", "side"], sort=False):
        g = G[(G.contrast == contrast) & (G.side == side) & (G.horizon == H_PRIMARY)]
        n_scored = int(g.iloc[0].lp_years) if len(g) and np.isfinite(g.iloc[0].get("lp_years", np.nan)) else 0
        if n_scored < len(s):
            lines.append(f"'{CONTRAST_NAME[contrast]}, {SIDE_NAME[(contrast, side)]}' was scored in {n_scored} of {len(s)} years (fewer than {MIN_FIRES} pairs in the others).\n")
    for (contrast, side), s in stats.groupby(["contrast", "side"], sort=False):
        m, tr = int(s.matched.sum()), int(s.treated.sum())
        lines.append(f"{CONTRAST_NAME[contrast]}, {SIDE_NAME[(contrast, side)]}: {m:,} of {tr:,} treated minutes matched, {(1 - s.with_replacement.sum() / m) * 100 if m else float('nan'):.1f}% of the pairs drawn without replacement; {int(s.unmatched.sum()):,} treated minutes unmatched, of which {int(s.unmatched_no_support.sum()):,} fall in a move-size bin with no eligible control.\n")
    for v in V:
        g = G[(G.contrast == v["contrast"]) & (G.side == v["side"]) & (G.horizon == H_PRIMARY)]
        if len(g) and g.iloc[0].get("lp_years", 0):
            r = g.iloc[0]
            lines.append(f"{CONTRAST_NAME[v['contrast']]}, {SIDE_NAME[(v['contrast'], v['side'])]}: per year at {H_PRIMARY} minutes the difference runs from {r.lp_yr_min:+.1f} to {r.lp_yr_max:+.1f} points under the last print and from {r.vw_yr_min:+.1f} to {r.vw_yr_max:+.1f} under the VWAP label, over {int(r.lp_years)} year{'s' if int(r.lp_years) != 1 else ''}.\n")
    return "\n".join(lines).rstrip() + "\n"


def render_support(S: pd.DataFrame, stats: pd.DataFrame, bal: pd.DataFrame | None = None) -> str:
    intro = ("Common support of the matching: for each year, contrast and side, the share of treated minutes and the share of the population in each bin of the move's size (bin 1 is the smallest move; the bin edges are the quintiles of the treated minutes' move size in that year and side, so the treated shares are near one fifth and the population shares show where the rest of the population lies), and the number of eligible controls and of unmatched treated minutes in the bin. "
             "A treated minute in a bin with no eligible control is unmatched.")
    lines = [intro, "", "| year | contrast | side | move-size bin | treated minutes | share of treated | population minutes | share of population | eligible controls | unmatched treated |", "|---|---|---|---|---|---|---|---|---|---|"]
    for (year, contrast, side), g in S.groupby(["year", "contrast", "side"], sort=False):
        for r in g.itertuples():
            lines.append(f"| {year} | {contrast} | {side} | {r.quintile + 1} | {r.treated:,} | {r.treated / max(g.treated.sum(), 1) * 100:.1f}% | {r.population:,} | {r.population / max(g.population.sum(), 1) * 100:.1f}% | {r.eligible:,} | {r.unmatched:,} |")
    lines.append("")
    n_ns, n_tr = int(stats.unmatched_no_support.sum()), int(stats.treated.sum())
    lines.append(f"Across all years, contrasts and sides, {n_ns:,} of {n_tr:,} treated minutes fall in a bin with no eligible control and are left unmatched.\n")
    if bal is not None and len(bal):
        lines += ["Balance after matching, per year and pooled over the scored years ('all'): the mean move size (basis points) and the mean trailing 60-minute volatility of the treated minutes and of their matched controls, and the standardised difference of each (difference of the means over the pooled standard deviation). A primary cell with an absolute standardised difference of the move size above " + f"{SMD_MAX:.2f}" + " is 'not resolved (support)'.", "",
                  "| year | contrast | side | pairs | move, treated | move, controls | move, standardised difference | volatility, treated | volatility, controls | volatility, standardised difference |", "|---|---|---|---|---|---|---|---|---|---|"]
        for r in bal.itertuples():
            lines.append(f"| {r.year} | {r.contrast} | {r.side} | {r.pairs:,} | {r.move_treated:.2f} | {r.move_control:.2f} | {r.move_smd:+.3f} | {r.vol_treated:.3f} | {r.vol_control:.3f} | {r.vol_smd:+.3f} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_subsets(G: pd.DataFrame, info: dict) -> str:
    intro = (f"Descriptive and unmatched: the legs of the liquidation signature added one at a time. For each side and each non-empty subset of the three legs (the 15-minute return beyond its previous-year cut, the 15-minute open-interest change below its lower cut, the perp volume ratio above its upper cut), the event is 'every leg in the subset is on', scored against all other minutes as in the derivatives table: pooled up-rate of the next h minutes, the oriented deviation from the unconditional rate in points (reversal positive) with a {100 - 100 * LEVEL:.0f}% interval (day-clustered errors, years combined as independent), and the share of the last-print deviation kept under the VWAP label. "
             f"A subset-year with fewer than {MIN_FIRES} firings is not scored. No matching and no null are applied, so a larger deviation in a bigger subset can come from a bigger move.")
    lines = [intro, "", "| side | legs on | horizon (min) | fires | share | reversal rate | deviation (points) [95% interval] | years held | VWAP retained |", "|---|---|---|---|---|---|---|---|---|"]
    names = {k: n for n, k in enumerate(info)}
    for r in G.assign(_o=G.event.map(names)).sort_values(["_o", "horizon"]).itertuples():
        side, sub = info[r.event]
        o = SIDES[("A", side)]
        dev, lo, hi = r.deviation * o * 100, sorted([r.lo * o * 100, r.hi * o * 100])[0], sorted([r.lo * o * 100, r.hi * o * 100])[1]
        rate = (r.up_rate if o > 0 else 1 - r.up_rate) * 100
        ret = f"{r.retained * 100:.0f}%" if (r.lo > 0 or r.hi < 0) and not np.isnan(r.retained) else "-"
        lines.append(f"| {side} | {' + '.join(LEG_NAMES[k] for k in sub)} | {r.horizon} | {r.fires:,} | {r.share * 100:.2f}% | {rate:.1f}% | {dev:+.1f} [{lo:+.1f}, {hi:+.1f}] | {r.years_held}/{r.years} | {ret} |")
    return "\n".join(lines).rstrip() + "\n"


# ---------------- run ----------------

def main():
    from threadpoolctl import threadpool_limits
    threadpool_limits(2)
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2018)
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--refresh", action="store_true", help="recompute cached years")
    ap.add_argument("--years", default="", help="comma-separated years overriding the range (smoke runs)")
    ap.add_argument("--prereg", action="store_true", help="write the pre-registration block from existing data and stop")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.prereg:
        write_prereg(out)
        print(f"wrote {STEM}_prereg.md and .json to {out}")
        return
    CACHE.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    years_b = [int(y) for y in a.years.split(",")] if a.years else list(range(a.start, int(a.end[:4]) + 1))
    scorable = L.scorable_years(derivatives.CACHE, min(years_b), a.end)
    years_a = [y for y in years_b if y in scorable]
    print(f"contrast A years: {years_a}; contrast B years: {years_b}", flush=True)
    key = code_key()
    res = []
    for year in years_b:
        cached = CACHE / f"year-{year}-{a.end}-{int(year in years_a)}-{key}.pkl"
        if cached.exists() and not a.refresh:
            r = pd.read_pickle(cached)
        else:
            t1 = time.time()
            r = run_year(year, a.end, year in years_a, True)
            pd.to_pickle(r, cached)
            print(f"{year}: built in {time.time() - t1:.0f}s", flush=True)
        res.append(r)
        print(f"{year}: " + "; ".join(f"{s['contrast']}-{s['side']} {s['matched']}/{s['treated']} matched" for s in r["stats"]), flush=True)
    pairs = pd.concat([P for r in res for P in r["pairs"]], ignore_index=True)
    S = pd.concat([x for r in res for x in r["support"]], ignore_index=True)
    stats = pd.DataFrame([x for r in res for x in r["stats"]])
    Y = year_cells(pairs)
    G = main_table(Y, stats)
    bal = balance_table(pairs)
    V = verdicts(G, bal)
    bal.to_csv(out / f"{STEM}_balance.csv", index=False)
    Y.to_csv(out / f"{STEM}_years.csv", index=False)
    G.to_csv(out / f"{STEM}.csv", index=False)
    S.to_csv(out / f"{STEM}_support.csv", index=False)
    (out / f"{STEM}.md").write_text(render_main(G, stats, V, {"A": years_a, "B": years_b}, a.end), encoding="utf-8")
    (out / f"{STEM}_support.md").write_text(render_support(S, stats, bal), encoding="utf-8")
    Rs = [r["R"] for r in res if r["R"] is not None]
    if Rs:
        info = next(r["subset_info"] for r in res if r["subset_info"])
        A_ = pd.concat(Rs, ignore_index=True).assign(p_adj=1.0)
        V_ = pd.concat([r["V"] for r in res if r["V"] is not None], ignore_index=True)
        GS = L.pool_cells(A_, V_)
        GS.to_csv(out / f"{STEM}_subsets.csv", index=False)
        (out / f"{STEM}_subsets.md").write_text(render_subsets(GS, info), encoding="utf-8")
    dirty = bool(git("status", "--porcelain", "--untracked-files=no"))
    (out / f"{STEM}.json").write_text(json.dumps({"ran_at": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "commit": git("rev-parse", "HEAD"), "dirty": dirty, "years_a": years_a, "years_b": years_b,
                                                  "end": a.end, "wall_seconds": round(time.time() - t0), "verdicts": V, "counts": stats.to_dict("records")}, indent=2), encoding="utf-8")
    for v in V:
        print(f"{v['contrast']}-{v['side']}: {v['verdict']} ({v['reason']})")
    print(f"wrote matched-increment tables to {out} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
