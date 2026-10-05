"""Tick-level order flow from Binance aggregated trades, reduced to one-second bins.

Source: https://data.binance.vision monthly aggTrades files (about 350 MB each).
Columns: agg_trade_id, price, qty, first_trade_id, last_trade_id, timestamp,
is_buyer_maker, is_best_match. is_buyer_maker = True means the buyer was the resting
order, so the aggressor sold. Timestamps are microseconds from 2025, milliseconds before.

Each month is reduced to a per-second table (notional volume, base quantity, signed
volume, trade count, count of large trades, signed large volume; notional over quantity
is the second's VWAP) and cached as
data/binance_ticks/BTCUSDT-1s-v2-YYYY-MM.parquet. The raw file is deleted after reduction.

A trade is large when its notional is at or above the 99th percentile of the PREVIOUS
UTC day's trades, so the cutoff is known before the day starts. (Version 1 used the
whole month's 99th percentile, which let early windows see later trade sizes.) Each
month writes its per-day cutoffs beside the table, BTCUSDT-1s-v2-YYYY-MM-cutoffs.csv,
so the next month's first day can use this month's last day. With no previous day
available the day has no large trades.

    python -m models.btc_15m.ticks --start 2025-10 --end 2026-08
"""
from __future__ import annotations

import argparse
import io
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.paths import DATA_ROOT

CACHE = DATA_ROOT / "binance_ticks"
URL = "https://data.binance.vision/data/spot/monthly/aggTrades/{sym}/{sym}-aggTrades-{month}.zip"
COLS = ["id", "price", "qty", "first", "last", "ts", "buyer_maker", "best"]


VERSION = "v2"


def tick_path(month: str, symbol: str = "BTCUSDT") -> Path:
    return CACHE / f"{symbol}-1s-{VERSION}-{month}.parquet"


def cutoff_path(month: str, symbol: str = "BTCUSDT") -> Path:
    return CACHE / f"{symbol}-1s-{VERSION}-{month}-cutoffs.csv"


def large_trade_mask(sec: np.ndarray, notional: np.ndarray, prev_cutoff: float = np.inf) -> tuple[np.ndarray, pd.Series]:
    """Large-trade flag per trade, using the previous UTC day's 99th-percentile notional.
    prev_cutoff is the cutoff for the first day present (from the day before it).
    Returns the mask and this data's own per-day 99th percentiles (indexed by day number)."""
    day = sec // 86400
    q = pd.Series(notional).groupby(day).quantile(0.99)
    days = q.index.values
    cut_for = pd.Series(np.concatenate([[prev_cutoff], q.values[:-1]]), index=days)
    # a gap of more than one day means "the previous day" is not in the data
    gap = np.concatenate([[False], np.diff(days) > 1])
    cut_for[gap] = np.inf
    return notional >= cut_for.reindex(day).values, q


def reduce_month(month: str, symbol: str = "BTCUSDT") -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    out = tick_path(month, symbol)
    if out.exists():
        return out
    prev_file = cutoff_path(str(pd.Period(month) - 1), symbol)
    prev_cutoff = np.inf
    if prev_file.exists():
        pc = pd.read_csv(prev_file)
        first_day = pd.Period(month).start_time.value // 10**9 // 86400
        if len(pc) and int(pc.day.iloc[-1]) == first_day - 1:
            prev_cutoff = float(pc.cutoff.iloc[-1])
    raw = urllib.request.urlopen(URL.format(sym=symbol, month=month), timeout=600).read()
    z = zipfile.ZipFile(io.BytesIO(raw))
    d = pd.read_csv(z.open(z.namelist()[0]), header=None, names=COLS, usecols=["price", "qty", "ts", "buyer_maker"])
    del raw, z
    ts = d.ts.values
    sec = np.where(ts > 1e14, ts // 1_000_000, ts // 1000).astype(np.int64)
    qty = d.qty.values.astype(float)
    notional = qty * d.price.values
    sign = np.where(d.buyer_maker.values, -1.0, 1.0)          # aggressor bought -> +
    big, q = large_trade_mask(sec, notional, prev_cutoff)
    pd.DataFrame({"day": q.index.values, "cutoff": q.values}).to_csv(cutoff_path(month, symbol), index=False)
    g = pd.DataFrame({"sec": sec, "vol": notional, "qty": qty, "svol": sign * notional, "n": 1.0,
                      "big_n": big.astype(float), "big_svol": np.where(big, sign * notional, 0.0)})
    r = g.groupby("sec").sum().reset_index()
    r.to_parquet(out, index=False)
    return out


def load_seconds(start: str, end: str, symbol: str = "BTCUSDT") -> pd.DataFrame:
    """Per-second flow for the month range, with cumulative sums for fast range queries."""
    parts = [pd.read_parquet(reduce_month(str(p), symbol)) for p in pd.period_range(start, end, freq="M")]
    r = pd.concat(parts).groupby("sec").sum().reset_index().sort_values("sec")
    return r


class TickFlow:
    """Range sums over seconds via cumulative sums. flow(a, b) covers seconds [a, b)."""

    def __init__(self, r: pd.DataFrame):
        self.sec = r.sec.values
        self.c = {k: np.concatenate([[0.0], np.cumsum(r[k].values)]) for k in ["vol", "svol", "n", "big_n", "big_svol"]}

    def sums(self, a: int, b: int) -> dict:
        i, j = np.searchsorted(self.sec, a), np.searchsorted(self.sec, b)
        return {k: float(v[j] - v[i]) for k, v in self.c.items()}

    def features(self, t_open: int, k: int) -> dict:
        """Flow features known at minute k of the window opening at t_open."""
        now = t_open + 60 * k
        f = {}
        for w in (5, 15, 30, 60, 300):
            s = self.sums(now - w, now)
            f[f"tick_imb{w}"] = s["svol"] / s["vol"] if s["vol"] > 0 else 0.0
            f[f"tick_n{w}"] = s["n"]
        s = self.sums(now - 60, now)
        f["tick_big_imb60"] = s["big_svol"] / s["vol"] if s["vol"] > 0 else 0.0
        f["tick_big_share60"] = s["big_n"] / s["n"] if s["n"] > 0 else 0.0
        base = self.sums(now - 86400, now)
        f["tick_n60_ratio"] = (self.sums(now - 60, now)["n"] / 60) / (base["n"] / 86400 + 1e-9)
        return f


TICK_FEATURES = [f"tick_imb{w}" for w in (5, 15, 30, 60, 300)] + [f"tick_n{w}" for w in (5, 15, 30, 60, 300)] + \
                ["tick_big_imb60", "tick_big_share60", "tick_n60_ratio"]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    a = ap.parse_args()
    for p in pd.period_range(a.start, a.end, freq="M"):
        print(str(p), reduce_month(str(p)), flush=True)
