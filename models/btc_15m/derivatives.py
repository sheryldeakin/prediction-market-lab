"""Inputs from the perpetual-futures market: basis, funding, perp order flow, open
interest and positioning. All from Binance's public futures files (free, no key).

Files (data.binance.vision, futures/um):
  monthly klines 1m      perp OHLCV with taker-buy volume, same layout as spot
  monthly fundingRate    calc_time, funding_interval_hours, last_funding_rate (every 8 h)
  daily metrics          create_time (5-min), sum_open_interest, sum_open_interest_value,
                         count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio,
                         count_long_short_ratio, sum_taker_long_short_vol_ratio

Per-minute arrays aligned to the spot series (value at index i is known by the close
of minute i; 5-minute and 8-hour series are carried forward from their last stamp at or
before that close, never interpolated across the future):

  basis_bp        perp close / spot close - 1, in basis points
  dbasis5/15      change in basis over the last 5 / 15 minutes
  pflow5/15       perp taker-buy share (signed, -1..1) over the last 5 / 15 minutes
  pvol_ratio5     perp volume in the last 5 minutes relative to its 24-hour mean
  funding_bp      last settled funding rate, in basis points per 8 hours
  doi15/doi60     change in open interest over the last 15 / 60 minutes, in percent
  ls_top          top-trader long/short position ratio (last 5-min stamp)
  ls_all          all-account long/short ratio
  taker_ls        taker buy/sell volume ratio, last 5-min stamp

    python -m models.btc_15m.derivatives --start 2025-10 --end 2026-08   # downloads and caches
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path("data/binance_futures")
BASE = "https://data.binance.vision/data/futures/um"
METRICS_DELAY = 300          # seconds after a metrics stamp before that row is known
FUNDING_MAX_AGE = 9 * 3600   # funding settles every 8 hours; older than this means the file is missing
METRICS_MAX_AGE = 3600       # metrics stamp every 5 minutes; older than this means the day file is missing
DERIV_FEATURES = ["basis_bp", "dbasis5", "dbasis15", "pflow5", "pflow15", "pvol_ratio5", "funding_bp", "doi15", "doi60", "ls_top", "ls_all", "taker_ls"]


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


def _to_seconds(x):
    x = np.asarray(x, dtype=np.int64)
    return np.where(x > 1e14, x // 1_000_000, x // 1000)


def perp_klines(months: list[str], days: list[str], symbol="BTCUSDT") -> pd.DataFrame:
    CACHE.mkdir(parents=True, exist_ok=True)
    cols = ["t", "open", "high", "low", "close", "volume", "ct", "qv", "n", "taker_buy", "tbq", "x"]
    frames = []
    for m in months:
        p = _fetch(f"{BASE}/monthly/klines/{symbol}/1m/{symbol}-1m-{m}.zip", CACHE / f"{symbol}-perp-1m-{m}.csv")
        if p:
            frames.append(pd.read_csv(p, header=None, names=cols, skiprows=lambda i: i == 0 and False))
    for d in days:
        p = _fetch(f"{BASE}/daily/klines/{symbol}/1m/{symbol}-1m-{d}.zip", CACHE / f"{symbol}-perp-1m-{d}.csv")
        if p:
            frames.append(pd.read_csv(p, header=None, names=cols))
    df = pd.concat(frames)
    df = df[pd.to_numeric(df.t, errors="coerce").notna()].copy()     # futures files may carry a header row
    df["t"] = _to_seconds(df.t.astype(np.int64))
    for c in ("close", "volume", "taker_buy"):
        df[c] = df[c].astype(float)
    return df[["t", "close", "volume", "taker_buy"]].drop_duplicates("t").sort_values("t").reset_index(drop=True)


def funding(months: list[str], symbol="BTCUSDT") -> pd.DataFrame:
    frames = []
    for m in months:
        p = _fetch(f"{BASE}/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{m}.zip", CACHE / f"{symbol}-funding-{m}.csv")
        if p:
            frames.append(pd.read_csv(p))
    df = pd.concat(frames)
    df["t"] = _to_seconds(df.calc_time.astype(np.int64))
    df["rate_bp"] = df.last_funding_rate.astype(float) * 1e4
    return df[["t", "rate_bp"]].sort_values("t").reset_index(drop=True)


def metrics(days: list[str], symbol="BTCUSDT") -> pd.DataFrame:
    frames = []
    for d in days:
        p = _fetch(f"{BASE}/daily/metrics/{symbol}/{symbol}-metrics-{d}.zip", CACHE / f"{symbol}-metrics-{d}.csv")
        if p:
            frames.append(pd.read_csv(p))
    df = pd.concat(frames)
    df["t"] = to_epoch_seconds(df.create_time)
    return df.rename(columns={"sum_open_interest": "oi", "sum_toptrader_long_short_ratio": "ls_top", "count_long_short_ratio": "ls_all",
                              "sum_taker_long_short_vol_ratio": "taker_ls"})[["t", "oi", "ls_top", "ls_all", "taker_ls"]].sort_values("t").reset_index(drop=True)


def to_epoch_seconds(stamps) -> np.ndarray:
    """Epoch seconds from date-time strings, independent of the datetime resolution pandas
    picks (casting a datetime64[s] column to int64 and dividing by 1e9 gives nonsense)."""
    return pd.to_datetime(stamps).values.astype("datetime64[s]").astype(np.int64)


def carry_forward(stamp_t: np.ndarray, values: np.ndarray, at_t: np.ndarray, lag: int = 0, max_age: float | None = None) -> np.ndarray:
    """Value of the last stamp at or before each at_t - lag (a stamp is known once its
    time has passed). NaN before the first stamp, and NaN when the last stamp is older
    than max_age (the source has a gap, so carrying the old value forward would freeze it)."""
    q = at_t - lag
    idx = np.searchsorted(stamp_t, q, side="right") - 1
    ii = np.clip(idx, 0, len(values) - 1)
    out = np.where(idx >= 0, values[ii], np.nan)
    if max_age is not None:
        out = np.where((idx >= 0) & (q - stamp_t[ii] > max_age), np.nan, out)
    return out


def build(spot_t: np.ndarray, spot_close: np.ndarray, months: list[str], days: list[str], symbol="BTCUSDT", missing: str = "zero") -> dict[str, np.ndarray]:
    """Per-minute derivative arrays aligned to the spot minute index.

    Funding comes only in monthly files, so for daily-file days the month's funding file is
    loaded when Binance has published it; until then funding is unknown (NaN) beyond the
    last settlement rather than frozen at it. missing="zero" fills unknown values with 0
    (the training default), missing="nan" keeps them so callers can measure coverage."""
    P = perp_klines(months, days, symbol)
    fmonths = sorted(set(months) | {d[:7] for d in days})
    Fd = funding(fmonths, symbol)
    M = metrics([str(d) for d in pd.date_range(pd.Period(months[0]).to_timestamp(), pd.Timestamp(days[-1]) if days else (pd.Period(months[-1]) + 1).to_timestamp() - pd.Timedelta(days=1)).date], symbol)
    # perp close and flow onto the spot grid (perp minute t is known at t + 60, same as spot)
    pi = pd.Series(P.close.values, index=P.t.values).reindex(spot_t).ffill().values
    pv = pd.Series(P.volume.values, index=P.t.values).reindex(spot_t).fillna(0).values
    ptb = pd.Series(P.taker_buy.values, index=P.t.values).reindex(spot_t).fillna(0).values
    basis = (pi / spot_close - 1) * 1e4
    cs = lambda x: np.concatenate([[0.0], np.cumsum(x)])
    cv, cs_signed = cs(pv), cs(2 * ptb - pv)
    n = len(spot_t)
    i = np.arange(n)

    def flow(w):
        a = np.clip(i + 1 - w, 0, n)
        vol = cv[i + 1] - cv[a]
        return np.where(vol > 0, (cs_signed[i + 1] - cs_signed[a]) / np.maximum(vol, 1e-9), 0.0)

    def lagged(x, w):
        return x - np.concatenate([np.full(w, np.nan), x[:-w]])

    vol24 = pd.Series(pv).rolling(1440).mean().values
    out = {"basis_bp": basis, "dbasis5": lagged(basis, 5), "dbasis15": lagged(basis, 15), "pflow5": flow(5), "pflow15": flow(15),
           "pvol_ratio5": (cv[i + 1] - cv[np.clip(i - 4, 0, n)]) / 5 / (vol24 + 1e-9)}
    close_t = spot_t + 60                                             # the minute's values are known at its close
    out["funding_bp"] = carry_forward(Fd.t.values, Fd.rate_bp.values, close_t, max_age=FUNDING_MAX_AGE)
    # A metrics row stamped T describes the five minutes STARTING at T (checked: the taker
    # ratio stamped T correlates with the spot return over [T, T+5) far more than over
    # [T-5, T)), so it is known only at T + 300. Treating it as known at T leaked the first
    # five minutes of every window and produced a false 65% at the open.
    mt = M.t.values + METRICS_DELAY
    oi = carry_forward(mt, M.oi.values, close_t, max_age=METRICS_MAX_AGE)
    oi15 = carry_forward(mt, M.oi.values, close_t, lag=900, max_age=METRICS_MAX_AGE)
    oi60 = carry_forward(mt, M.oi.values, close_t, lag=3600, max_age=METRICS_MAX_AGE)
    out["doi15"] = (oi / oi15 - 1) * 100
    out["doi60"] = (oi / oi60 - 1) * 100
    for c in ("ls_top", "ls_all", "taker_ls"):
        out[c] = carry_forward(mt, M[c].values, close_t, max_age=METRICS_MAX_AGE)
    out = {k: np.asarray(v, dtype=float) for k, v in out.items()}
    if missing == "nan":
        return out
    return {k: np.nan_to_num(v, nan=0.0) for k, v in out.items()}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    a = ap.parse_args()
    from models.btc_15m.data import load
    spot = load(a.start, a.end)
    months = [str(p) for p in pd.period_range(a.start, a.end, freq="M")]
    arrs = build(spot.t.values.astype(np.int64), spot.close.values, months, [])
    for k, v in arrs.items():
        print(f"{k:12s} mean {np.nanmean(v):+.3f} sd {np.nanstd(v):.3f} zeros {np.mean(v == 0)*100:.1f}%")
