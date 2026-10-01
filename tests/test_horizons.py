import numpy as np
import pandas as pd

from models.btc_15m.features import HISTORY, Series, features_all
from models.btc_15m.horizons import HORIZONS, labels


def flat(n=HISTORY + 300):
    t0 = 1_700_000_000 - 1_700_000_000 % 900
    c = 100.0 + np.cumsum(np.random.default_rng(0).normal(0, 0.01, n))
    o = np.concatenate([[c[0]], c[:-1]])
    return Series(pd.DataFrame({"t": t0 + 60 * np.arange(n), "open": o, "high": np.maximum(o, c), "low": np.minimum(o, c), "close": c,
                                "volume": 1.0, "trades": 1.0, "taker_buy": 0.5, "ok": True}))


def test_horizon_labels_compare_the_close_h_minutes_on_with_this_minutes_open():
    s = flat()
    idx = np.array([HISTORY, HISTORY + 10, len(s.c) - 2])
    L = labels(s, idx)
    assert set(L) == set(HORIZONS)
    for h in HORIZONS:
        for k, i in enumerate(idx):
            if i + h - 1 < len(s.c):
                assert L[h][k] == float(s.c[i + h - 1] >= s.o[i])
            else:
                assert np.isnan(L[h][k])                       # the last decision minute cannot be labelled at long horizons
    assert L[1][0] == float(s.c[HISTORY] >= s.o[HISTORY])      # horizon 1 is this minute's own candle


def test_every_minute_is_a_decision_time():
    s = flat()
    D = features_all(s)
    assert len(D) == len(s.c) - HISTORY
    assert (np.diff(D.i.values) == 1).all()
