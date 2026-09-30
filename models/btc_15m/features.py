"""Features for predicting whether a 15-minute BTC window closes above its open.

Windows are aligned to the quarter hour. A window opening at candle index i covers
candles i .. i+14. Features for entry minute k use only candles up to i+k-1, all of
which have closed by minute k. The lookahead test in tests/test_features.py enforces
this: changing any candle at index >= i+k must leave the features unchanged.

Everything is a pure function of numpy arrays so it can be tested and reused live.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.indicators import INDICATOR_FEATURES, compute as compute_indicators

HISTORY = 1500          # minutes of history a window needs (24h volume baseline + margin)
WINDOW = 15

PRICE_FEATURES = ["lead", "ret5", "ret15", "ret60", "ret240", "win1", "win2", "win3", "win4",
                  "vol15", "vol60", "vol240", "rangepos", "hour", "wday"]
FLOW_FEATURES = ["flow1", "flow3", "flow5", "flow15", "flow60", "vratio5", "vratio15", "nratio5", "size5"]


class Series:
    """Precomputed arrays for one continuous minute series."""

    def __init__(self, frame: pd.DataFrame):
        self.t = frame.t.values.astype(np.int64)
        self.ok = frame.ok.values
        self.o, self.h, self.l, self.c = (frame[x].values.astype(float) for x in ["open", "high", "low", "close"])
        self.v = frame.volume.values.astype(float)
        self.n = frame.trades.values.astype(float)
        signed = 2 * frame.taker_buy.values.astype(float) - self.v      # taker buys minus taker sells
        self.r1 = np.diff(np.log(self.c), prepend=np.log(self.c[0])) * 1e4
        cs = lambda x: np.concatenate([[0.0], np.cumsum(x)])
        self.cv, self.csv, self.cn = cs(self.v), cs(signed), cs(self.n)
        self.ind = compute_indicators(self.o, self.h, self.l, self.c, self.v)
        self.ticks = None                      # optional TickFlow, set by the caller

    def fingerprint(self) -> str:
        """Identifies the series content, not only its time span: two coins over the same
        months must never share a cache file (they did once; see tests/test_features.py)."""
        h = hashlib.sha1()
        h.update(np.ascontiguousarray(self.t[::997]).tobytes())
        h.update(np.ascontiguousarray(self.c[::997]).tobytes())
        h.update(np.ascontiguousarray(self.v[::997]).tobytes())
        return f"{int(self.t[0])}-{int(self.t[-1])}-{len(self.t)}-{h.hexdigest()[:12]}"

    def window_starts(self):
        first = ((self.t[0] // 900) + 1) * 900
        i0 = int((first - self.t[0]) // 60)
        return range(i0 + HISTORY, len(self.t) - WINDOW, WINDOW)

    def label(self, i: int) -> int:
        return int(self.c[i + WINDOW - 1] >= self.o[i])

    def move_bp(self, i: int) -> float:
        return (self.c[i + WINDOW - 1] / self.o[i] - 1) * 1e4

    def features(self, i: int, k: int) -> dict | None:
        """Features known at minute k of the window opening at candle i (k = 0..14)."""
        j = i + k                                   # first candle NOT yet closed
        if i < HISTORY or not self.ok[i - HISTORY:i + WINDOW].all():
            return None
        c, o, h, l, r1 = self.c, self.o, self.h, self.l, self.r1
        p = c[j - 1]
        f = {}
        f["lead"] = (p / o[i] - 1) * 1e4 if k else 0.0
        for w in (5, 15, 60, 240):
            f[f"ret{w}"] = (p / c[j - 1 - w] - 1) * 1e4
        for w in range(1, 5):
            s = i - WINDOW * w
            f[f"win{w}"] = (c[s + WINDOW - 1] / o[s] - 1) * 1e4
        for w in (15, 60, 240):
            f[f"vol{w}"] = r1[j - w:j].std()
        hi, lo = h[j - 240:j].max(), l[j - 240:j].min()
        f["rangepos"] = (p - lo) / (hi - lo) if hi > lo else 0.5
        f["hour"] = int((self.t[i] // 3600) % 24)
        f["wday"] = int((self.t[i] // 86400 + 4) % 7)
        cv, csv, cn = self.cv, self.csv, self.cn
        for w in (1, 3, 5, 15, 60):
            vol = cv[j] - cv[j - w]
            f[f"flow{w}"] = (csv[j] - csv[j - w]) / vol if vol > 0 else 0.0
        base_v = (cv[j] - cv[j - 1440]) / 1440 + 1e-9
        base_n = (cn[j] - cn[j - 1440]) / 1440 + 1e-9
        f["vratio5"] = (cv[j] - cv[j - 5]) / 5 / base_v
        f["vratio15"] = (cv[j] - cv[j - 15]) / 15 / base_v
        f["nratio5"] = (cn[j] - cn[j - 5]) / 5 / base_n
        f["size5"] = ((cv[j] - cv[j - 5]) / max(cn[j] - cn[j - 5], 1.0)) / (base_v / base_n)
        for name in INDICATOR_FEATURES:
            f[name] = float(self.ind[name][j - 1])
        if self.ticks is not None:
            f.update(self.ticks.features(int(self.t[i]), k))
        return f


CACHE_DIR = Path("data/feature_cache")
FEATURE_VERSION = 2          # bump when a feature definition changes; invalidates the cache


def dataset(series: Series, k: int, cache: bool = True) -> pd.DataFrame:
    """All windows with features at minute k, the label, and the open time.

    Cached to data/feature_cache keyed on the series span, minute, feature version and
    whether tick features are attached, so repeated runs skip the pure-Python build."""
    key = None
    if cache:
        tag = f"{series.fingerprint()}-k{k}-v{FEATURE_VERSION}-{'ticks' if series.ticks is not None else 'noticks'}"
        key = CACHE_DIR / f"{tag}.parquet"
        if key.exists():
            return pd.read_parquet(key)
    rows = []
    for i in series.window_starts():
        f = series.features(i, k)
        if f is not None:
            f["t"] = int(series.t[i])
            f["y"] = series.label(i)
            f["y_gap1"] = int(series.c[i + WINDOW - 1] >= series.c[i])   # measured from 1 minute in
            f["move_bp"] = series.move_bp(i)
            rows.append(f)
    D = pd.DataFrame(rows)
    if key is not None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        D.to_parquet(key, index=False)
    return D
