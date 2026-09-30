"""Binance public 1-minute klines for BTCUSDT.

Source: https://data.binance.vision (free, no key). Monthly zip files for completed
months and daily zip files for recent days, one CSV each. Columns (Binance order):
open_time, open, high, low, close, volume, close_time, quote_volume, trade_count,
taker_buy_base, taker_buy_quote, ignore. Timestamps are milliseconds before 2025 and
microseconds from 2025 on; both are normalised to seconds.

    python -m models.btc_15m.data --start 2025-10 --end 2026-08
"""
from __future__ import annotations

import argparse
import io
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path("data/binance_klines")
COLS = ["t", "open", "high", "low", "close", "volume", "close_time",
        "quote_volume", "trades", "taker_buy", "taker_buy_quote", "ignore"]
MONTH_URL = "https://data.binance.vision/data/spot/monthly/klines/{sym}/1m/{sym}-1m-{month}.zip"
DAY_URL = "https://data.binance.vision/data/spot/daily/klines/{sym}/1m/{sym}-1m-{day}.zip"


def _fetch(url: str, out: Path) -> Path | None:
    if not out.exists():
        try:
            raw = urllib.request.urlopen(url, timeout=120).read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise
        z = zipfile.ZipFile(io.BytesIO(raw))
        out.write_bytes(z.read(z.namelist()[0]))
    return out


def fetch_month(month: str, symbol: str = "BTCUSDT") -> Path:
    """Download one month (YYYY-MM) if not cached; return the CSV path."""
    CACHE.mkdir(parents=True, exist_ok=True)
    p = _fetch(MONTH_URL.format(sym=symbol, month=month), CACHE / f"{symbol}-1m-{month}.csv")
    if p is None:
        raise FileNotFoundError(f"no monthly file for {month}")
    return p


def fetch_day(day: str, symbol: str = "BTCUSDT") -> Path | None:
    """Download one day (YYYY-MM-DD) if not cached; None if Binance has not published it yet."""
    CACHE.mkdir(parents=True, exist_ok=True)
    return _fetch(DAY_URL.format(sym=symbol, day=day), CACHE / f"{symbol}-1m-{day}.csv")


def _read(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path, header=None, names=COLS)
    d["t"] = np.where(d.t > 1e14, d.t // 1_000_000, d.t // 1000)
    return d[["t", "open", "high", "low", "close", "volume", "trades", "taker_buy"]]


def _continuous(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """One row per minute. Missing minutes are filled forward for prices and with zero
    for volumes, and flagged in `ok` so callers can skip windows that touch a gap."""
    df = pd.concat(frames).drop_duplicates("t").sort_values("t").reset_index(drop=True)
    full = pd.DataFrame({"t": np.arange(df.t.min(), df.t.max() + 60, 60)}).merge(df, on="t", how="left")
    full["ok"] = full.close.notna()
    full[["open", "high", "low", "close"]] = full[["open", "high", "low", "close"]].ffill()
    full[["volume", "trades", "taker_buy"]] = full[["volume", "trades", "taker_buy"]].fillna(0.0)
    return full


def load(start: str, end: str, symbol: str = "BTCUSDT") -> pd.DataFrame:
    """Continuous frame from start to end month (inclusive)."""
    return _continuous([_read(fetch_month(str(p), symbol)) for p in pd.period_range(start, end, freq="M")])


def load_days(months: list[str], days: list[str], symbol: str = "BTCUSDT") -> pd.DataFrame:
    """Continuous frame from whole months plus individual days, skipping unpublished days."""
    frames = [_read(fetch_month(m, symbol)) for m in months]
    for d in days:
        p = fetch_day(d, symbol)
        if p is not None:
            frames.append(_read(p))
    return _continuous(frames)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    a = ap.parse_args()
    f = load(a.start, a.end)
    print(f"{len(f):,} minutes, {int((~f.ok).sum())} missing, "
          f"{pd.to_datetime(f.t.iloc[0], unit='s').date()} to {pd.to_datetime(f.t.iloc[-1], unit='s').date()}")
