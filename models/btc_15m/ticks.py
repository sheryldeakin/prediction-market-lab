"""Tick-level order flow from Binance aggregated trades, reduced to one-second bins.

Source: https://data.binance.vision monthly aggTrades files (about 350 MB each).
Columns: agg_trade_id, price, qty, first_trade_id, last_trade_id, timestamp,
is_buyer_maker, is_best_match. is_buyer_maker = True means the buyer was the resting
order, so the aggressor sold. Timestamps are microseconds from 2025, milliseconds before.

Each month is reduced to a per-second table (volume, signed volume, trade count, count
of trades above the month's 99th-percentile size, signed large volume) and cached as
data/binance_ticks/BTCUSDT-1s-YYYY-MM.parquet. The raw file is deleted after reduction.

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

CACHE = Path("data/binance_ticks")
URL = "https://data.binance.vision/data/spot/monthly/aggTrades/{sym}/{sym}-aggTrades-{month}.zip"
COLS = ["id", "price", "qty", "first", "last", "ts", "buyer_maker", "best"]


def reduce_month(month: str, symbol: str = "BTCUSDT") -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"{symbol}-1s-{month}.parquet"
    if out.exists():
        return out
    raw = urllib.request.urlopen(URL.format(sym=symbol, month=month), timeout=600).read()
    z = zipfile.ZipFile(io.BytesIO(raw))
    d = pd.read_csv(z.open(z.namelist()[0]), header=None, names=COLS, usecols=["price", "qty", "ts", "buyer_maker"])
    del raw, z
    ts = d.ts.values
    sec = np.where(ts > 1e14, ts // 1_000_000, ts // 1000).astype(np.int64)
    qty = d.qty.values.astype(float)
    notional = qty * d.price.values
    sign = np.where(d.buyer_maker.values, -1.0, 1.0)          # aggressor bought -> +
    big = notional >= np.quantile(notional, 0.99)
    g = pd.DataFrame({"sec": sec, "vol": notional, "svol": sign * notional, "n": 1.0,
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
