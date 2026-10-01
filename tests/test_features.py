import numpy as np
import pandas as pd
import pytest

from models.btc_15m.features import FLOW_FEATURES, HISTORY, PRICE_FEATURES, Series, dataset
from models.btc_15m.indicators import INDICATOR_FEATURES


def synthetic(n=HISTORY + 200, seed=0):
    rng = np.random.default_rng(seed)
    t0 = 1_700_000_000 - 1_700_000_000 % 900
    close = 50_000 * np.exp(np.cumsum(rng.normal(0, 5e-4, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    vol = rng.gamma(2, 1, n)
    return pd.DataFrame({
        "t": t0 + 60 * np.arange(n), "open": open_, "high": np.maximum(open_, close) * 1.0002,
        "low": np.minimum(open_, close) * 0.9998, "close": close, "volume": vol,
        "trades": rng.integers(50, 500, n).astype(float), "taker_buy": vol * rng.uniform(0.3, 0.7, n), "ok": True,
    })


@pytest.mark.parametrize("k", [0, 1, 3, 8, 14])
def test_no_lookahead(k):
    """Changing any candle from minute k onward must not change the features."""
    base = synthetic()
    s = Series(base)
    i = next(iter(s.window_starts()))
    before = s.features(i, k)
    tampered = base.copy()
    cols = ["open", "high", "low", "close", "volume", "trades", "taker_buy"]
    tampered.loc[i + k:, cols] = tampered.loc[i + k:, cols].values * 3.0 + 1.0
    after = Series(tampered).features(i, k)
    assert before == after


@pytest.mark.parametrize("k", [1, 3, 8])
def test_uses_latest_closed_candle(k):
    """The candle that closed at minute k must be able to move the features."""
    base = synthetic()
    s = Series(base)
    i = next(iter(s.window_starts()))
    before = s.features(i, k)
    tampered = base.copy()
    tampered.loc[i + k - 1, "close"] *= 1.01
    after = Series(tampered).features(i, k)
    assert before["lead"] != after["lead"]


def test_feature_names_complete():
    s = Series(synthetic())
    f = s.features(next(iter(s.window_starts())), 3)
    assert set(f) == set(PRICE_FEATURES + FLOW_FEATURES + INDICATOR_FEATURES)


def test_lead_is_zero_at_open():
    s = Series(synthetic())
    assert s.features(next(iter(s.window_starts())), 0)["lead"] == 0.0


def test_flow_share_bounds():
    d = dataset(Series(synthetic(n=HISTORY + 900)), 3, cache=False)
    for w in (1, 3, 5, 15, 60):
        assert d[f"flow{w}"].between(-1, 1).all()


def test_label_definition():
    base = synthetic()
    s = Series(base)
    i = next(iter(s.window_starts()))
    assert s.label(i) == int(base.close[i + 14] >= base.open[i])


def test_windows_skip_gaps():
    base = synthetic(n=HISTORY + 900)
    base.loc[HISTORY + 100, "ok"] = False
    d = dataset(Series(base), 0, cache=False)
    gap_t = base.t[HISTORY + 100]
    assert not ((d.t <= gap_t) & (d.t + 900 > gap_t)).any()


def test_indicators_are_causal():
    """Indicator values at index i must not change when later candles change."""
    from models.btc_15m.indicators import compute
    base = synthetic()
    a = compute(base.open.values, base.high.values, base.low.values, base.close.values, base.volume.values)
    t = base.copy()
    t.loc[HISTORY + 50:, ["open", "high", "low", "close", "volume"]] *= 2.0
    b = compute(t.open.values, t.high.values, t.low.values, t.close.values, t.volume.values)
    for k in a:
        assert np.allclose(a[k][:HISTORY + 50], b[k][:HISTORY + 50]), k


def test_indicator_ranges():
    s = Series(synthetic(n=HISTORY + 900))
    d = dataset(s, 3, cache=False)
    assert d.rsi14.between(0, 100).all() and d.stoch14.between(0, 1).all() and d.adx14.between(0, 100).all()


def test_cache_key_differs_for_different_prices_on_the_same_timestamps(tmp_path, monkeypatch):
    """Two coins over the same months once shared one cache file and ETH, SOL and DOGE
    silently reported BTC's numbers. The key must depend on the prices, not only the span."""
    import models.btc_15m.features as F
    monkeypatch.setattr(F, "CACHE_DIR", tmp_path)
    a = synthetic(n=HISTORY + 900, seed=0)
    b = synthetic(n=HISTORY + 900, seed=1)
    assert (a.t == b.t).all()
    sa, sb = Series(a), Series(b)
    assert sa.fingerprint() != sb.fingerprint()
    da = dataset(sa, 0)
    db = dataset(sb, 0)
    assert len(list(tmp_path.glob("*.parquet"))) == 2
    assert not np.allclose(da.ret60.values, db.ret60.values)
    assert dataset(sa, 0).equals(da)          # second read comes from the cache and matches


def test_weekday_is_monday_zero():
    """The old mapping made Sunday 0, so 'weekend' (wday >= 5) meant Friday and Saturday."""
    base = synthetic()
    sat = 1_727_481_600                       # 2024-09-28 00:00 UTC, a Saturday
    base["t"] = sat - 60 * HISTORY - 60 * 15 + 60 * np.arange(len(base))
    s = Series(base)
    i = int(np.searchsorted(s.t, sat))
    assert s.features(i, 0)["wday"] == 5
    assert s.features(i + 4 * 15, 0)["wday"] == 5          # still Saturday an hour later


def test_window_starts_include_the_last_complete_window():
    base = synthetic(n=HISTORY + 15 * 10 + 15)
    s = Series(base)
    starts = list(s.window_starts())
    assert starts[-1] + 15 == len(base)                       # the final window ends on the last candle
    first = ((s.t[0] // 900) + 1) * 900
    i0 = int((first - s.t[0]) // 60) + HISTORY
    assert len(starts) == (len(base) - i0) // 15


def test_features_do_not_depend_on_the_window_being_complete():
    """A missing candle later in the window removes the label, not the features at minute k."""
    base = synthetic()
    i = next(iter(Series(base).window_starts()))
    base.loc[i + 10, "ok"] = False
    s = Series(base)
    assert s.features(i, 3) is not None
    assert not s.label_ok(i)
    assert s.features(i, 11) is None                          # minute 11 needs candle i+10


def test_cache_key_covers_every_column_and_extra_contents():
    a = synthetic()
    b = a.copy(); b["high"] = b["high"] * 1.0001
    assert Series(a).fingerprint() != Series(b).fingerprint()
    c = a.copy(); c["taker_buy"] = c["taker_buy"] * 0.9
    assert Series(a).fingerprint() != Series(c).fingerprint()
    s1, s2 = Series(a), Series(a)
    s1.extra = {"basis_bp": np.zeros(len(a))}
    s2.extra = {"basis_bp": np.ones(len(a))}
    assert s1.fingerprint() != s2.fingerprint()
    assert Series(a).fingerprint() == Series(a.copy()).fingerprint()
