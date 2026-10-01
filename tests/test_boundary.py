import numpy as np
import pandas as pd

from models.btc_15m.boundary import boundary_gap, minute_returns, signed_by_call
from models.btc_15m.features import HISTORY, Series


def flat_series(n=HISTORY + 60):
    t0 = 1_700_000_000 - 1_700_000_000 % 900
    c = np.full(n, 100.0)
    return Series(pd.DataFrame({"t": t0 + 60 * np.arange(n), "open": c, "high": c, "low": c, "close": c,
                                "volume": 1.0, "trades": 1.0, "taker_buy": 0.5, "ok": True}))


def test_minute_returns_cover_the_window_and_sum_to_the_window_move():
    s = flat_series()
    i = next(iter(s.window_starts()))
    s.o[i] = 100.0
    s.c[i:i + 15] = 100.0 * np.cumprod(np.full(15, 1.0001))
    R = minute_returns(s, np.array([s.t[i]]))
    assert R.shape == (1, 15)
    total = (np.prod(1 + R[0] / 1e4) - 1) * 1e4
    assert np.isclose(total, (s.c[i + 14] / s.o[i] - 1) * 1e4)


def test_signed_returns_follow_the_call():
    R = np.array([[2.0, -1.0], [2.0, -1.0]])
    S = signed_by_call(np.array([0.7, 0.3]), R)
    assert S.tolist() == [[2.0, -1.0], [-2.0, 1.0]]


def test_boundary_gap_is_open_against_the_previous_close():
    s = flat_series()
    i = next(iter(s.window_starts()))
    s.c[i - 1] = 100.0; s.o[i] = 100.01
    assert np.isclose(boundary_gap(s, np.array([s.t[i]]))[0], 1.0)
