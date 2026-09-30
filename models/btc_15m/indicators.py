"""Classic technical indicators on the 1-minute series, computed causally over the whole
series once (value at index i uses candles <= i) and read at the last closed candle.

They are deterministic transforms of the same prices and volumes the other features
see, so the honest expectation is little gain; they are here as an ablation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

INDICATOR_FEATURES = ["rsi14", "rsi60", "macd_hist", "bb_pctb", "atr14", "ema_cross", "stoch14", "obv_slope60", "vwap_dev60", "adx14"]


def compute(o: np.ndarray, h: np.ndarray, l: np.ndarray, c: np.ndarray, v: np.ndarray) -> dict[str, np.ndarray]:
    C = pd.Series(c)
    H, L, V = pd.Series(h), pd.Series(l), pd.Series(v)
    out = {}
    d = C.diff()
    for n in (14, 60):
        up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
        dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
        out[f"rsi{n}"] = (100 - 100 / (1 + up / dn.replace(0, np.nan))).fillna(50).values
    macd = C.ewm(span=12, adjust=False).mean() - C.ewm(span=26, adjust=False).mean()
    out["macd_hist"] = ((macd - macd.ewm(span=9, adjust=False).mean()) / C * 1e4).values
    m20, s20 = C.rolling(20).mean(), C.rolling(20).std()
    out["bb_pctb"] = ((C - (m20 - 2 * s20)) / (4 * s20)).fillna(0.5).values
    tr = pd.concat([H - L, (H - C.shift()).abs(), (L - C.shift()).abs()], axis=1).max(axis=1)
    out["atr14"] = (tr.ewm(alpha=1 / 14, adjust=False).mean() / C * 1e4).values
    out["ema_cross"] = ((C.ewm(span=9, adjust=False).mean() / C.ewm(span=21, adjust=False).mean() - 1) * 1e4).values
    lo14, hi14 = L.rolling(14).min(), H.rolling(14).max()
    out["stoch14"] = ((C - lo14) / (hi14 - lo14)).fillna(0.5).values
    obv = (np.sign(d.fillna(0)) * V).cumsum()
    out["obv_slope60"] = ((obv - obv.shift(60)) / (V.rolling(60).sum() + 1e-9)).fillna(0).values
    vwap = (C * V).rolling(60).sum() / (V.rolling(60).sum() + 1e-9)
    out["vwap_dev60"] = ((C / vwap - 1) * 1e4).fillna(0).values
    up_m, dn_m = H.diff(), -L.diff()
    plus = pd.Series(np.where((up_m > dn_m) & (up_m > 0), up_m, 0.0))
    minus = pd.Series(np.where((dn_m > up_m) & (dn_m > 0), dn_m, 0.0))
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
    pdi = 100 * plus.ewm(alpha=1 / 14, adjust=False).mean() / atr
    mdi = 100 * minus.ewm(alpha=1 / 14, adjust=False).mean() / atr
    dx = (100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)).fillna(0)
    out["adx14"] = dx.ewm(alpha=1 / 14, adjust=False).mean().values
    return {k: np.nan_to_num(np.asarray(val, dtype=float)) for k, val in out.items()}
