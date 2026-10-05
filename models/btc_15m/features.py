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

from models.btc_15m import indicators as _indicators
from models.btc_15m.indicators import INDICATOR_FEATURES, compute as compute_indicators

_INDICATOR_SOURCE = hashlib.sha1(Path(_indicators.__file__).read_bytes()).hexdigest()[:12]
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
        self.extra = {}                        # optional per-minute arrays (e.g. derivatives), value at i known at minute i's close
        self.phase = 0                         # window starts at quarter hour + phase minutes (0..14); 0 is the clock-aligned grid
        self._raw = (frame.trades.values.astype(float), frame.taker_buy.values.astype(float))

    def fingerprint(self) -> str:
        """Identifies everything a cached dataset depends on: the content of all seven
        columns, the ok mask, the extra arrays' contents, the tick table, the window
        constants, the feature version and the indicator code. Two coins over the same
        months once shared a cache file; a key on close and volume alone would still let
        two series differing only in high, or in an extra array, collide."""
        h = hashlib.sha1()
        step = 97
        for a in (self.t, self.o, self.h, self.l, self.c, self.v, *self._raw, self.ok.astype(np.int8)):
            h.update(np.ascontiguousarray(a[::step]).tobytes())
        for name in sorted(self.extra):
            arr = np.asarray(self.extra[name], dtype=float)
            h.update(name.encode()); h.update(np.ascontiguousarray(arr[::step]).tobytes())
        if self.ticks is not None:
            for k in sorted(self.ticks.c):
                h.update(np.ascontiguousarray(self.ticks.c[k][::997]).tobytes())
        h.update((f"{HISTORY}-{WINDOW}-{FEATURE_VERSION}-{_INDICATOR_SOURCE}" + (f"-phase{self.phase}" if self.phase else "")).encode())
        return f"{int(self.t[0])}-{int(self.t[-1])}-{len(self.t)}-{h.hexdigest()[:16]}"

    def window_starts(self):
        """Every quarter-hour start with HISTORY minutes behind it and all fifteen of its
        own candles inside the series (the last complete window included)."""
        first = ((self.t[0] // 900) + 1) * 900 + 60 * self.phase
        i0 = int((first - self.t[0]) // 60)
        return range(i0 + HISTORY, len(self.t) - WINDOW + 1, WINDOW)

    def label_ok(self, i: int) -> bool:
        """Whether the window's own candles are all present, so its label exists. This is
        label availability, not a feature: nothing about minutes after k enters features()."""
        return bool(self.ok[i:i + WINDOW].all())

    def label(self, i: int) -> int:
        return int(self.c[i + WINDOW - 1] >= self.o[i])

    def move_bp(self, i: int) -> float:
        return (self.c[i + WINDOW - 1] / self.o[i] - 1) * 1e4

    def features(self, i: int, k: int) -> dict | None:
        """Features known at minute k of the window opening at candle i (k = 0..14)."""
        j = i + k                                   # first candle NOT yet closed
        if i < HISTORY or not self.ok[i - HISTORY:j].all():
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
        f["wday"] = int((self.t[i] // 86400 + 3) % 7)        # Monday 0 ... Sunday 6 (1970-01-01 was a Thursday)
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
        for name, arr in self.extra.items():
            f[name] = float(arr[j - 1])
        return f


CACHE_DIR = Path("data/feature_cache")       # a write location: deliberately not under LAB_DATA_ROOT (see paths.py)
FEATURE_VERSION = 3          # bump when a feature definition changes; invalidates the cache (3: weekday Monday 0)


def dataset(series: Series, k: int, cache: bool = True) -> pd.DataFrame:
    """All windows with features at minute k, the label, and the open time.

    Cached to data/feature_cache keyed on the series fingerprint (content, extras, ticks,
    constants, code version) and the minute, so repeated runs skip the pure-Python build."""
    key = None
    if cache:
        tag = f"{series.fingerprint()}-k{k}-v{FEATURE_VERSION}-{'ticks' if series.ticks is not None else 'noticks'}-{'+'.join(sorted(series.extra)) or 'noextra'}"
        key = CACHE_DIR / f"{tag}.parquet"
        if key.exists():
            return pd.read_parquet(key)
    rows = []
    for i in series.window_starts():
        if not series.label_ok(i):
            continue
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


def _rolling_sum(x: np.ndarray, w: int) -> np.ndarray:
    """out[i] = sum(x[i-w:i]) (the w values before i), NaN where i < w."""
    cs = np.concatenate([[0.0], np.cumsum(x, dtype=float)])
    out = np.full(len(x), np.nan)
    out[w:] = cs[w:-1] - cs[:-w - 1]
    return out


def _rolling_std_before(x: np.ndarray, w: int) -> np.ndarray:
    """out[i] = std(x[i-w:i]) with ddof 0, matching numpy's .std() in features()."""
    s1, s2 = _rolling_sum(x, w), _rolling_sum(x * x, w)
    var = s2 / w - (s1 / w) ** 2
    return np.sqrt(np.maximum(var, 0.0))


def _rolling_extreme_before(x: np.ndarray, w: int, fn) -> np.ndarray:
    """out[i] = fn(x[i-w:i]); fn is np.max or np.min. Uses pandas rolling for speed."""
    r = pd.Series(x).rolling(w)
    v = (r.max() if fn is np.max else r.min()).values
    out = np.full(len(x), np.nan)
    out[1:] = v[:-1]
    return out


def features_all(series: Series) -> pd.DataFrame:
    """The minute-0 features of features() for EVERY minute i treated as a decision time,
    vectorised. Row i reads only candles up to i-1 (the same as features(i, 0)); rows
    without HISTORY clean candles behind them are dropped. Used by the any-minute studies,
    where 4.7 million rows make the per-window Python builder impractical. Equality with
    features(i, 0) is tested row for row in tests/test_features.py."""
    assert series.ticks is None, "tick features are not vectorised; attach them per study"
    c, o, h, l, r1, v, n = series.c, series.o, series.h, series.l, series.r1, series.v, series.n
    N = len(c)
    i = np.arange(N)
    p = np.concatenate([[np.nan], c[:-1]])                     # c[i-1]
    f = {"lead": np.zeros(N)}
    for w in (5, 15, 60, 240):
        prev = np.full(N, np.nan); prev[w + 1:] = c[:-w - 1]   # c[i-1-w]
        f[f"ret{w}"] = (p / prev - 1) * 1e4
    for w in range(1, 5):
        s = i - WINDOW * w
        ok_s = s >= 0
        num = np.full(N, np.nan); den = np.full(N, np.nan)
        num[ok_s] = c[s[ok_s] + WINDOW - 1]; den[ok_s] = o[s[ok_s]]
        f[f"win{w}"] = (num / den - 1) * 1e4
    for w in (15, 60, 240):
        f[f"vol{w}"] = _rolling_std_before(r1, w)
    hi, lo = _rolling_extreme_before(h, 240, np.max), _rolling_extreme_before(l, 240, np.min)
    f["rangepos"] = np.where(hi > lo, (p - lo) / (hi - lo), 0.5)
    f["hour"] = ((series.t // 3600) % 24).astype(int)
    f["wday"] = ((series.t // 86400 + 3) % 7).astype(int)
    signed = 2 * series._raw[1] - v
    for w in (1, 3, 5, 15, 60):
        vol = _rolling_sum(v, w)
        f[f"flow{w}"] = np.where(vol > 0, _rolling_sum(signed, w) / np.where(vol > 0, vol, 1.0), 0.0)
    base_v = _rolling_sum(v, 1440) / 1440 + 1e-9
    base_n = _rolling_sum(n, 1440) / 1440 + 1e-9
    v5, n5 = _rolling_sum(v, 5), _rolling_sum(n, 5)
    f["vratio5"] = v5 / 5 / base_v
    f["vratio15"] = _rolling_sum(v, 15) / 15 / base_v
    f["nratio5"] = n5 / 5 / base_n
    f["size5"] = (v5 / np.maximum(n5, 1.0)) / (base_v / base_n)
    for name in INDICATOR_FEATURES:
        arr = np.asarray(series.ind[name], dtype=float)
        f[name] = np.concatenate([[np.nan], arr[:-1]])
    for name, arr in series.extra.items():
        arr = np.asarray(arr, dtype=float)
        f[name] = np.concatenate([[np.nan], arr[:-1]])
    D = pd.DataFrame(f)
    D["t"] = series.t
    D["i"] = i
    bad = (~series.ok).astype(float)
    clean = _rolling_sum(bad, HISTORY) == 0                     # all of ok[i-HISTORY:i]
    D = D[(i >= HISTORY) & clean].reset_index(drop=True)
    return D
