"""Binance public 1-minute klines for BTCUSDT.

Source: https://data.binance.vision (free, no key). Monthly zip files, one CSV each.
Columns (Binance order): open_time, open, high, low, close, volume, close_time,
quote_volume, trade_count, taker_buy_base, taker_buy_quote, ignore. Timestamps are
milliseconds before 2025 and microseconds from 2025 on; both are normalised to seconds.

    python -m models.btc_15m.data --start 2025-10 --end 2026-08
"""
from __future__ import annotations

import argparse
import io
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path("data/binance_klines")
COLS = ["t", "open", "high", "low", "close", "volume", "close_time",
        "quote_volume", "trades", "taker_buy", "taker_buy_quote", "ignore"]
URL = "https://data.binance.vision/data/spot/monthly/klines/{sym}/1m/{sym}-1m-{month}.zip"


def fetch_month(month: str, symbol: str = "BTCUSDT") -> Path:
    """Download one month if not cached; return the CSV path."""
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"{symbol}-1m-{month}.csv"
    if not out.exists():
        raw = urllib.request.urlopen(URL.format(sym=symbol, month=month), timeout=120).read()
        z = zipfile.ZipFile(io.BytesIO(raw))
        out.write_bytes(z.read(z.namelist()[0]))
    return out


def load(start: str, end: str, symbol: str = "BTCUSDT") -> pd.DataFrame:
    """Continuous 1-minute frame from start to end month (inclusive), one row per minute.

    Missing minutes are filled forward for prices and with zero for volumes, and
    flagged in the `ok` column so callers can skip windows that touch a gap.
    """
    frames = []
    for p in pd.period_range(start, end, freq="M"):
        d = pd.read_csv(fetch_month(str(p), symbol), header=None, names=COLS)
        d["t"] = np.where(d.t > 1e14, d.t // 1_000_000, d.t // 1000)
        frames.append(d[["t", "open", "high", "low", "close", "volume", "trades", "taker_buy"]])
    df = pd.concat(frames).drop_duplicates("t").sort_values("t").reset_index(drop=True)
    full = pd.DataFrame({"t": np.arange(df.t.min(), df.t.max() + 60, 60)}).merge(df, on="t", how="left")
    full["ok"] = full.close.notna()
    full[["open", "high", "low", "close"]] = full[["open", "high", "low", "close"]].ffill()
    full[["volume", "trades", "taker_buy"]] = full[["volume", "trades", "taker_buy"]].fillna(0.0)
    return full


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    a = ap.parse_args()
    f = load(a.start, a.end)
    print(f"{len(f):,} minutes, {int((~f.ok).sum())} missing, "
          f"{pd.to_datetime(f.t.iloc[0], unit='s').date()} to {pd.to_datetime(f.t.iloc[-1], unit='s').date()}")
