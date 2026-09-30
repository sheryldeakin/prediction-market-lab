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
    d = dataset(Series(synthetic(n=HISTORY + 900)), 3)
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
    d = dataset(Series(base), 0)
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
    d = dataset(s, 3)
    assert d.rsi14.between(0, 100).all() and d.stoch14.between(0, 1).all() and d.adx14.between(0, 100).all()
