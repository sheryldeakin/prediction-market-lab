import numpy as np
import pandas as pd

from models.btc_15m.derivatives import carry_forward
from models.btc_15m.features import HISTORY, Series


def test_carry_forward_uses_only_stamps_at_or_before_the_time():
    stamps = np.array([100, 400, 700])
    vals = np.array([1.0, 2.0, 3.0])
    at = np.array([50, 100, 399, 400, 1000])
    out = carry_forward(stamps, vals, at)
    assert np.isnan(out[0])                      # before the first stamp
    assert list(out[1:]) == [1.0, 1.0, 2.0, 3.0]


def test_carry_forward_lag_looks_back():
    stamps = np.array([0, 300, 600, 900])
    vals = np.array([10.0, 11.0, 12.0, 13.0])
    at = np.array([950])
    assert carry_forward(stamps, vals, at)[0] == 13.0
    assert carry_forward(stamps, vals, at, lag=900)[0] == 10.0      # value 15 minutes earlier


def synthetic(n=HISTORY + 200, seed=0):
    rng = np.random.default_rng(seed)
    t0 = 1_700_000_000 - 1_700_000_000 % 900
    close = 50_000 * np.exp(np.cumsum(rng.normal(0, 5e-4, n)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    vol = rng.gamma(2, 1, n)
    return pd.DataFrame({"t": t0 + 60 * np.arange(n), "open": open_, "high": np.maximum(open_, close) * 1.0002, "low": np.minimum(open_, close) * 0.9998,
                         "close": close, "volume": vol, "trades": 100.0, "taker_buy": vol * 0.5, "ok": True})


def test_extra_arrays_enter_features_at_the_last_closed_minute():
    base = synthetic()
    s = Series(base)
    arr = np.arange(len(base), dtype=float)                        # value == minute index
    s.extra = {"basis_bp": arr}
    i = next(iter(s.window_starts()))
    for k in (0, 3, 8):
        f = s.features(i, k)
        assert f["basis_bp"] == float(i + k - 1)                  # minute k reads index i+k-1, never i+k
    # tampering with the array from minute k on must not change the feature
    s2 = Series(base)
    arr2 = arr.copy(); arr2[i + 3:] = -999
    s2.extra = {"basis_bp": arr2}
    assert s2.features(i, 3)["basis_bp"] == s.features(i, 3)["basis_bp"]


def test_metrics_rows_are_not_visible_until_five_minutes_after_their_stamp(monkeypatch):
    """Binance's 5-minute metrics describe the period starting at the stamp. A row stamped T
    must not enter any feature before T + 300; using it at T leaked the first five minutes
    of the window (a false 65% at the open, 2026-09-30)."""
    import models.btc_15m.derivatives as D
    n = 2000
    spot_t = 1_700_000_000 + 60 * np.arange(n)
    spot_close = np.full(n, 100.0)
    P = pd.DataFrame({"t": spot_t, "close": 100.0, "volume": 1.0, "taker_buy": 0.5})
    Fd = pd.DataFrame({"t": [spot_t[0]], "rate_bp": [1.0]})
    stamps = spot_t[0] + 300 * np.arange(n // 5)
    M = pd.DataFrame({"t": stamps, "oi": 1000.0 + np.arange(len(stamps)), "ls_top": 1.0, "ls_all": 1.0, "taker_ls": np.arange(len(stamps), dtype=float)})
    monkeypatch.setattr(D, "perp_klines", lambda months, days, symbol="BTCUSDT": P)
    monkeypatch.setattr(D, "funding", lambda months, symbol="BTCUSDT": Fd)
    monkeypatch.setattr(D, "metrics", lambda days, symbol="BTCUSDT": M)
    arrs = D.build(spot_t, spot_close, ["2023-11"], [])
    # minute index 10 closes at spot_t[0] + 660: stamp 600 (index 2) is not yet known, stamp 300 (index 1) is
    assert arrs["taker_ls"][10] == 1.0
    assert arrs["taker_ls"][14] == 2.0          # minute 14 closes at 900 = 600 + 300: now known


def test_carry_forward_goes_unknown_when_the_source_has_a_gap():
    stamps = np.array([0, 28_800])
    vals = np.array([1.0, 2.0])
    out = carry_forward(stamps, vals, np.array([28_800 + 3600, 28_800 + 10 * 3600]), max_age=9 * 3600)
    assert out[0] == 2.0 and np.isnan(out[1])


def test_funding_for_daily_file_days_loads_that_months_file_and_never_freezes(monkeypatch):
    """The forward run loaded only August's funding, so funding sat at August's last value
    through September (council review, 2026-09-30)."""
    import models.btc_15m.derivatives as D
    seen = []
    t0 = int(pd.Timestamp("2026-09-01").timestamp())
    n = 3 * 1440
    spot_t = t0 + 60 * np.arange(n)
    P = pd.DataFrame({"t": spot_t, "close": 100.0, "volume": 1.0, "taker_buy": 0.5})
    def fake_funding(months, symbol="BTCUSDT"):
        seen.extend(months)
        return pd.DataFrame({"t": [t0 - 3600], "rate_bp": [1.0]})          # only August's last settlement exists
    monkeypatch.setattr(D, "perp_klines", lambda months, days, symbol="BTCUSDT": P)
    monkeypatch.setattr(D, "funding", fake_funding)
    monkeypatch.setattr(D, "metrics", lambda days, symbol="BTCUSDT": pd.DataFrame({"t": spot_t[::5], "oi": 1.0, "ls_top": 1.0, "ls_all": 1.0, "taker_ls": 1.0}))
    arrs = D.build(spot_t, np.full(n, 100.0), ["2026-08"], ["2026-09-01", "2026-09-02", "2026-09-03"], missing="nan")
    assert "2026-09" in seen
    assert arrs["funding_bp"][0] == 1.0                                       # within one settlement period
    assert np.isnan(arrs["funding_bp"][-1])                                   # two days later: unknown, not frozen


def test_epoch_seconds_do_not_depend_on_datetime_resolution():
    from models.btc_15m.derivatives import to_epoch_seconds
    s = pd.Series(["2026-08-01 00:05:00", "2026-08-01 00:10:00"])
    want = [int(pd.Timestamp(x, tz="UTC").timestamp()) for x in s]
    assert list(to_epoch_seconds(s)) == want
    assert list(to_epoch_seconds(pd.to_datetime(s).astype("datetime64[s]"))) == want
