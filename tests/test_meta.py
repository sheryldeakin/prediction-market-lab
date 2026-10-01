import numpy as np
import pandas as pd

from models.btc_15m.meta import barrier_labels, meta_label, triple_barrier, walk_forward_oof
from models.btc_15m.features import HISTORY, Series


def path(*bps, open_price=100.0):
    return np.array([open_price * (1 + b / 1e4) for b in bps])


def test_upper_barrier_first():
    lab, touch = triple_barrier(path(2, 5, 12, -20, -30), 100.0, 10, 10)
    assert (lab, touch) == (1, "upper")


def test_lower_barrier_first_even_if_it_ends_up():
    lab, touch = triple_barrier(path(-3, -11, 5, 30), 100.0, 10, 10)
    assert (lab, touch) == (-1, "lower")


def test_time_limit_uses_final_sign():
    assert triple_barrier(path(2, -3, 4, -1), 100.0, 10, 10) == (-1, "time")
    assert triple_barrier(path(2, -3, 4, 1), 100.0, 10, 10) == (1, "time")
    assert triple_barrier(path(0, 0, 0), 100.0, 10, 10) == (1, "time")     # zero move counts as up, like the plain label


def test_asymmetric_barriers():
    assert triple_barrier(path(6, 7), 100.0, 5, 20) == (1, "upper")
    assert triple_barrier(path(-6, -7), 100.0, 5, 20) == (-1, "time")


def synthetic(n_per_month=1500, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for m in pd.period_range("2026-01", "2026-07", freq="M"):
        t = int(m.to_timestamp().timestamp()) + 900 * np.arange(n_per_month)
        a = rng.normal(size=n_per_month)
        b = rng.normal(size=n_per_month)
        # direction depends on a; whether the call is reliable depends on |b| (large |b| -> noisy)
        noise = rng.normal(size=n_per_month) * (np.abs(b) > 1.0) * 6
        rows.append(pd.DataFrame({"t": t, "a": a, "b": b, "y": ((a + noise) > 0).astype(int)}))
    return pd.concat(rows, ignore_index=True)


def test_oof_predictions_only_after_three_months():
    D = synthetic()
    p = walk_forward_oof(D, ["a", "b"], D.y.values, kind="logistic")
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    assert np.isnan(p[(month < pd.Period("2026-04", "M")).values]).all()
    assert not np.isnan(p[(month >= pd.Period("2026-04", "M")).values]).any()


def test_meta_model_ranks_reliable_calls_higher():
    D = synthetic()
    y = D.y.values
    primary = walk_forward_oof(D, ["a", "b"], y, kind="logistic")
    meta = meta_label(D, ["a", "b"], y, primary, kind="xgb")
    have = ~np.isnan(meta)
    # meta is only defined from the second month that has OOF primary predictions
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    assert np.isnan(meta[(month <= pd.Period("2026-04", "M")).values]).all()
    right = ((primary[have] > 0.5) == y[have])
    assert meta[have][right].mean() > meta[have][~right].mean()
    quiet = np.abs(D.b.values[have]) <= 1.0
    assert meta[have][quiet].mean() > meta[have][~quiet].mean()     # it learned where the primary is trustworthy


def test_barrier_labels_ignore_minutes_already_seen():
    """A touch before the entry minute must not decide the label at that entry minute."""
    import pandas as pd
    n = HISTORY + 60
    t0 = 1_700_000_000 - 1_700_000_000 % 900
    close = np.full(n, 100.0)
    s = Series(pd.DataFrame({"t": t0 + 60 * np.arange(n), "open": close, "high": close * 1.0001, "low": close * 0.9999,
                             "close": close, "volume": 1.0, "trades": 1.0, "taker_buy": 0.5, "ok": True}))
    i = next(iter(s.window_starts()))
    # spike up 30 bp at minute 1, back to flat, then drift down 2 bp by the end
    s.c[i + 0] = 100.0 * (1 + 30 / 1e4)
    s.c[i + 1:i + 15] = 100.0
    s.c[i + 14] = 100.0 * (1 - 2 / 1e4)
    s.h[i:i + 15] = np.maximum(s.c[i:i + 15], 100.0)        # bars consistent with the closes
    s.l[i:i + 15] = np.minimum(s.c[i:i + 15], 100.0)
    D =pd.DataFrame({"t": [int(s.t[i])], "vol60": [1.0]})
    lab0, touch0 = barrier_labels(s, D, 0, None, 10.0)
    lab3, touch3 = barrier_labels(s, D, 3, None, 10.0)
    assert (lab0[0], touch0[0]) == (1, "upper")          # at the open the spike is in the future
    assert (lab3[0], touch3[0]) == (-1, "time")          # at minute 3 the spike is in the past


def test_barrier_touch_uses_the_minute_high_and_low():
    """Closes alone missed a barrier crossed inside a minute (council review, 2026-09-30)."""
    closes = np.array([100.05, 100.02, 99.99])
    highs = np.array([100.12, 100.05, 100.02])         # first minute's high crosses +10 bp; its close does not
    lows = np.array([100.00, 99.98, 99.95])
    assert triple_barrier(closes, 100.0, 10, 10) == (-1, "time")
    assert triple_barrier(closes, 100.0, 10, 10, highs, lows) == (1, "upper")


def test_a_minute_crossing_both_barriers_is_ambiguous_and_follows_its_close():
    closes = np.array([99.97]); highs = np.array([100.2]); lows = np.array([99.8])
    assert triple_barrier(closes, 100.0, 10, 10, highs, lows) == (-1, "both")
    assert triple_barrier(np.array([100.03]), 100.0, 10, 10, highs, lows) == (1, "both")
