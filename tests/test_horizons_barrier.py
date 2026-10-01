import numpy as np
import pandas as pd

from models.btc_15m.features import HISTORY, Series
from models.btc_15m.horizons_barrier import barrier_outcomes


def series_with(path):
    n = HISTORY + 100
    t0 = 1_700_000_000 - 1_700_000_000 % 900
    c = np.full(n, 100.0); h = c.copy(); l = c.copy(); o = c.copy()
    s = Series(pd.DataFrame({"t": t0 + 60 * np.arange(n), "open": o, "high": h, "low": l, "close": c, "volume": 1.0, "trades": 1.0, "taker_buy": 0.5, "ok": True}))
    i = HISTORY
    for k, (hi, lo, cl) in enumerate(path):
        s.h[i + k], s.l[i + k], s.c[i + k] = hi, lo, cl
    return s, i


def test_upper_barrier_first_by_a_high_then_nothing():
    s, i = series_with([(100.05, 99.98, 100.0), (100.15, 99.97, 100.1), (100.0, 99.8, 99.9)])     # +10 bp touched in minute 2 by the high
    assert barrier_outcomes(s, np.array([i]), 10, 5)[0] == 1.0
    assert barrier_outcomes(s, np.array([i]), 20, 5)[0] == -1.0       # at 20 bp only the low in minute 3 reaches -20 bp
    assert barrier_outcomes(s, np.array([i]), 20, 2)[0] == 0.0        # within 2 minutes nothing at 20 bp


def test_both_in_one_minute_is_decided_by_the_close_and_horizon_end_is_nan():
    s, i = series_with([(100.3, 99.7, 99.9)])
    assert barrier_outcomes(s, np.array([i]), 20, 1)[0] == -1.0
    s.c[i] = 100.1
    assert barrier_outcomes(s, np.array([i]), 20, 1)[0] == 1.0
    assert np.isnan(barrier_outcomes(s, np.array([len(s.c) - 1]), 5, 5)[0])
