"""What drives the short-horizon reversal? Two hypotheses the per-second trade table can see,
specified before any table was generated (docs/horizons.md, "The mechanism").

  A  bid-ask bounce or last-trade noise: after a sharp move the last print sits on one side
     of the spread, and the next prints return across it. The deviation then lives in the
     last print, vanishes when the label starts a minute or two later, and is complete
     within seconds.
  B  transient price impact: aggressive flow pushes the price past where it settles, and it
     comes back over minutes. The deviation then survives a later entry, the event minute
     carries extreme flow against ordinary minutes, and the recovery is larger when the
     flow was larger.

Not testable here: the table holds last prints only (no bid, ask or book depth), so
inventory, replenishment and spread are out of reach.

This module holds the pure pieces, each tested in tests/test_mechanism.py:

  events     the six events (3-sd 5-minute drop and rise, 4-hour low and high, RSI14 below
             25 and above 75) with the library's own definitions, and the first firing in
             any 30 minutes of each, plus the same rule on any of the six ("union")
  controls   one matched minute per event: same year, same hour of day, same previous-year
             volatility decile, no firing of the six in the 30 minutes up to and including it
  labels     the library's last-print label, and VWAP labels with an embargo: entry at the
             VWAP of minute i+g, exit at the VWAP of minute i+g+h-1 (g = 0, 1, 2)
  paths      the per-second VWAP path after the event minute, relative to its close
  flows      the event minute's flow, and flow in the same bins as the path
  terciles   within-year thirds of the event minute's flow

Orientation: every label, path and flow is signed so that "reversal" is positive. A down-move
event (direction +1) expects the price up; an up-move event (direction -1) expects it down.
A control carries the orientation of the event it is matched to.

The event frames are built year by year by build_year; models/btc_15m/mechanism_tables.py
aggregates them and writes the result tables.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from models.btc_15m.horizons import HORIZONS, candidates, labels

warnings.filterwarnings("ignore")

SIX = ["drop5", "rise5", "low4h", "high4h", "rsi_lo", "rsi_hi"]
SLICES = ["union"] + SIX
NAMES = {"union": "any of the six", "drop5": "3-sd 5-minute drop", "rise5": "3-sd 5-minute rise", "low4h": "price at 4-hour low",
         "high4h": "price at 4-hour high", "rsi_lo": "RSI14 below 25", "rsi_hi": "RSI14 above 75"}
LIBRARY_KEY = {"drop5": "sweep: 5-min move < -3 sd", "rise5": "sweep: 5-min move > +3 sd",
               "low4h": "price at 4h low (rangepos <= 0.02)", "high4h": "price at 4h high (rangepos >= 0.98)",
               "rsi_lo": "sweep: RSI14 < 25", "rsi_hi": "sweep: RSI14 > 75"}
DIRECTION = {"drop5": 1, "low4h": 1, "rsi_lo": 1, "rise5": -1, "high4h": -1, "rsi_hi": -1}     # +1: a down-move, the reversal is up

BLOCK_MIN = 30               # no two events of a set within this many minutes
MIN_EVENTS_YEAR = 100        # a slice-year with fewer events is not scored
EVAL_H = (5, 15, 30)         # label horizons, minutes
GAPS = (0, 1, 2)             # embargo, minutes
MAX_WINDOW = 60              # path windows are the trailing min(lag, 60) seconds
LAGS = [(1, "1 s"), (5, "5 s"), (10, "10 s"), (30, "30 s"), (60, "60 s"), (120, "2 min"), (300, "5 min"), (900, "15 min"),
        (1800, "30 min"), (3600, "60 min")]
EDGES = [0] + [s for s, _ in LAGS]          # flow bins are the gaps between consecutive lags
assert set(EVAL_H) <= set(HORIZONS)


# ---------------- events ----------------

def six_masks(D: pd.DataFrame, cutoffs: tuple[float, float]) -> dict[str, np.ndarray]:
    """The six events with the library's own definitions (horizons.candidates), aligned to D's rows."""
    c = candidates(D, cutoffs)
    return {k: np.asarray(c[LIBRARY_KEY[k]], bool) for k in SIX}


def first_in_window(i: np.ndarray, gap: int) -> np.ndarray:
    """Keep flags for sorted minute indices: an event is kept when it is at least `gap` minutes
    after the last kept one, so the first firing in any `gap` minutes is the event."""
    keep = np.zeros(len(i), bool)
    last = None
    for k, v in enumerate(i):
        if last is None or v - last >= gap:
            keep[k] = True
            last = v
    return keep


def event_sets(masks: dict[str, np.ndarray], i: np.ndarray, gap: int = BLOCK_MIN) -> tuple[dict[str, np.ndarray], np.ndarray, int]:
    """Row positions of the events in each of the six slices and in the union, the direction of
    every row (+1 down-move, -1 up-move, 0 neither or both), and the number of ambiguous rows.
    A row where a down-side and an up-side event both fire is ambiguous: it is nobody's event
    (and is still a firing for the purpose of excluding controls)."""
    down = np.zeros(len(i), bool)
    up = np.zeros(len(i), bool)
    for k in SIX:
        if DIRECTION[k] > 0:
            down |= masks[k]
        else:
            up |= masks[k]
    ambiguous = down & up
    direction = np.where(down & ~up, 1, np.where(up & ~down, -1, 0))
    sets = {}
    for k in SIX + ["union"]:
        m = (down | up) if k == "union" else masks[k]
        pos = np.where(m & ~ambiguous)[0]
        sets[k] = pos[first_in_window(i[pos], gap)]
    return sets, direction, int(ambiguous.sum())


def recent_any(fire: np.ndarray, window: int) -> np.ndarray:
    """True where `fire` is true at this minute or any of the previous window-1 minutes."""
    cs = np.concatenate([[0], np.cumsum(fire.astype(np.int64))])
    n = len(fire)
    lo = np.maximum(np.arange(n) - window + 1, 0)
    return (cs[np.arange(n) + 1] - cs[lo]) > 0


def vol_decile(vol: np.ndarray, edges: np.ndarray) -> np.ndarray:
    """Decile 0..9 of vol against nine edges (the previous year's 10th ... 90th percentiles)."""
    return np.searchsorted(edges, vol, side="right")


def match_controls(hour: np.ndarray, decile: np.ndarray, event_pos: np.ndarray, eligible_pos: np.ndarray, rng) -> tuple[np.ndarray, int]:
    """One control row per event row, drawn from the eligible rows with the same hour and
    decile. Without replacement while the stratum has enough rows, with replacement when it
    does not; -1 where the stratum is empty. Returns the control positions and the number drawn
    with replacement."""
    key = hour.astype(np.int64) * 10 + decile.astype(np.int64)
    out = np.full(len(event_pos), -1, dtype=np.int64)
    replaced = 0
    pool_by_key = {}
    for k in np.unique(key[eligible_pos]):
        pool_by_key[k] = eligible_pos[key[eligible_pos] == k]
    for k in np.unique(key[event_pos]):
        sel = np.where(key[event_pos] == k)[0]
        pool = pool_by_key.get(k)
        if pool is None or len(pool) == 0:
            continue
        if len(pool) >= len(sel):
            out[sel] = rng.choice(pool, size=len(sel), replace=False)
        else:
            out[sel] = rng.choice(pool, size=len(sel), replace=True)
            replaced += len(sel)
    return out, replaced


# ---------------- per-second table ----------------

class SecCum:
    """Range sums over the per-second trade table by cumulative sums: sums(a, b) covers the
    seconds [a, b) for arrays a and b. vwap = notional over quantity."""
    COLS = ("vol", "qty", "svol", "n", "big_n", "big_svol")

    def __init__(self, r: pd.DataFrame):
        self.sec = r.sec.values
        self.c = {k: np.concatenate([[0.0], np.cumsum(r[k].values, dtype=float)]) for k in self.COLS}

    def sums(self, a, b) -> dict[str, np.ndarray]:
        i, j = np.searchsorted(self.sec, a), np.searchsorted(self.sec, b)
        return {k: v[j] - v[i] for k, v in self.c.items()}

    def vwap(self, a, b) -> np.ndarray:
        s = self.sums(a, b)
        return np.where(s["qty"] > 0, s["vol"] / np.where(s["qty"] > 0, s["qty"], 1.0), np.nan)


# ---------------- labels, paths, flows ----------------

def orient(x: np.ndarray, direction: np.ndarray) -> np.ndarray:
    """Binary label 1 = up becomes 1 = reversal: unchanged after a down-move, complemented after an up-move."""
    return np.where(direction > 0, x, 1.0 - x)


def embargo_up(vw, T: np.ndarray, g: int, h: int) -> np.ndarray:
    """1 if the VWAP of minute g+h-1 after T is at least the VWAP of minute g after T, else 0;
    NaN when either minute has no trades. T is the start of the decision minute. g = 0 is the
    VWAP label of horizons_vwap; g = 1, 2 enter one or two minutes later."""
    entry = vw(T + 60 * g, T + 60 * (g + 1))
    exit_ = vw(T + 60 * (g + h - 1), T + 60 * (g + h))
    return np.where(np.isnan(entry) | np.isnan(exit_), np.nan, (exit_ >= entry).astype(float))


def path_prices(vw, T: np.ndarray, lags=LAGS) -> np.ndarray:
    """VWAP of the trailing window [T+lag-w, T+lag), w = min(lag, 60) seconds, one column per
    lag; NaN where the window has no trades."""
    return np.column_stack([vw(T + s - min(s, MAX_WINDOW), T + s) for s, _ in lags])


def path_bp(P: np.ndarray, p0: np.ndarray, direction: np.ndarray) -> np.ndarray:
    """Basis points moved from p0, positive in the reversal direction."""
    return direction[:, None] * (P / p0[:, None] - 1.0) * 1e4


def flow_bins(cum: SecCum, T: np.ndarray, edges=EDGES) -> np.ndarray:
    """Signed aggressor volume over volume (svol/vol) in [T+a, T+b) for consecutive edges,
    one column per bin; NaN where the bin has no trades."""
    cols = []
    for a, b in zip(edges[:-1], edges[1:]):
        s = cum.sums(T + a, T + b)
        cols.append(np.where(s["vol"] > 0, s["svol"] / np.where(s["vol"] > 0, s["vol"], 1.0), np.nan))
    return np.column_stack(cols)


def minute_flow(cum: SecCum, T: np.ndarray) -> dict[str, np.ndarray]:
    """The minute before T: signed imbalance (svol/vol, positive = aggressive buying), trade
    count over the previous 24 hours' per-minute mean, and the share of trades that were large."""
    s = cum.sums(T - 60, T)
    base = cum.sums(T - 60 - 86400, T - 60)
    base_n = base["n"] / 1440.0
    return {"imb": np.where(s["vol"] > 0, s["svol"] / np.where(s["vol"] > 0, s["vol"], 1.0), np.nan),
            "nratio": np.where(base_n > 0, s["n"] / np.where(base_n > 0, base_n, 1.0), np.nan),
            "big": np.where(s["n"] > 0, s["big_n"] / np.where(s["n"] > 0, s["n"], 1.0), np.nan)}


def tercile(values: np.ndarray, ref: np.ndarray) -> np.ndarray:
    """0, 1, 2 by the thirds of `ref` (ties go down); -1 where the value is NaN."""
    c1, c2 = np.nanquantile(ref, [1 / 3, 2 / 3])
    out = (values > c1).astype(int) + (values > c2).astype(int)
    return np.where(np.isnan(values), -1, out)


# ---------------- one year ----------------

def measures(series, cum: SecCum, i: np.ndarray, direction: np.ndarray, ret5_abs: np.ndarray) -> dict[str, np.ndarray]:
    """Every outcome and covariate for decision minutes i (series indices), oriented by direction."""
    T = series.t[i]
    out = {"i": i, "t": T, "dir": direction, "hour": ((T // 3600) % 24).astype(int), "ret5_abs": ret5_abs}
    L = labels(series, i)
    vw = cum.vwap
    for h in EVAL_H:
        out[f"lp_{h}"] = orient(L[h], direction)
        for g in GAPS:
            out[f"vw{g}_{h}"] = orient(embargo_up(vw, T, g, h), direction)
    p0 = series.c[i - 1]
    close_vwap = vw(T - 60, T)
    out["gap_bp"] = np.abs(p0 / close_vwap - 1.0) * 1e4
    P = path_bp(path_prices(vw, T), p0, direction)
    F = -direction[:, None] * flow_bins(cum, T)           # positive = aggressive flow in the direction of the move
    for k, (_, name) in enumerate(LAGS):
        out[f"path_{k}"] = P[:, k]
        out[f"flow_{k}"] = F[:, k]
    mf = minute_flow(cum, T)
    out["ev_imb"] = -direction * mf["imb"]
    out["ev_absimb"] = np.abs(mf["imb"])
    out["ev_nratio"] = mf["nratio"]
    out["ev_big"] = mf["big"]
    return out


def build_year(series, D: pd.DataFrame, cum: SecCum, edges: np.ndarray, rng, year: int) -> tuple[pd.DataFrame, dict]:
    """The event frame of one year: every event row and its matched control row, with kind,
    pair, slice memberships, oriented labels, paths and flows. D holds the year's decision
    minutes (features_all rows), edges the previous year's volatility decile edges."""
    masks = six_masks(D, (float(edges[0]), float(edges[-1])))
    i_all = D.i.values
    sets, direction, ambiguous = event_sets(masks, i_all)
    event_pos = np.unique(np.concatenate([sets[k] for k in SIX + ["union"]]))
    fire = np.zeros(len(series.c), bool)
    fire[i_all[np.any([masks[k] for k in SIX], axis=0)]] = True
    eligible = np.where(~recent_any(fire, BLOCK_MIN)[i_all])[0]
    ctrl, replaced = match_controls(D.hour.values, vol_decile(D.vol60.values, edges), event_pos, eligible, rng)
    ok = ctrl >= 0
    E, C = event_pos[ok], ctrl[ok]
    stats = {"year": year, "rows": int(len(D)), "ambiguous": ambiguous, "events": {k: int(len(sets[k])) for k in SLICES},
             "unique_events": int(len(event_pos)), "unmatched": int((~ok).sum()), "controls_with_replacement": int(replaced if ok.any() else 0)}
    if not ok.any():
        return pd.DataFrame(), stats
    ret5_abs = np.abs(D.ret5.values)
    ev = measures(series, cum, i_all[E], direction[E], ret5_abs[E])
    ct = measures(series, cum, i_all[C], direction[E], ret5_abs[C])
    n = len(E)
    f = pd.concat([pd.DataFrame(ev), pd.DataFrame(ct)], ignore_index=True)
    f.insert(0, "year", year)
    f.insert(1, "is_event", np.repeat([True, False], n))
    f.insert(2, "pair", np.tile(np.arange(n), 2))
    for k in SLICES:
        f[f"m_{k}"] = np.tile(np.isin(E, sets[k]), 2)
    # covariates of the event, shared by its control
    med = np.nanmedian(ev["gap_bp"])
    f["far"] = np.tile(ev["gap_bp"] > med, 2)
    union_rows = np.isin(E, sets["union"])
    f["terc_imb"] = np.tile(tercile(ev["ev_absimb"], ev["ev_absimb"][union_rows]), 2)
    f["terc_big"] = np.tile(tercile(ev["ev_big"], ev["ev_big"][union_rows]), 2)
    return f, stats
