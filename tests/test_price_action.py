import numpy as np
import pandas as pd

from models.btc_15m.features import HISTORY, Series
from models.btc_15m.price_action import minute_events


def flat(n=HISTORY + 400):
    t0 = 1_700_000_000 - 1_700_000_000 % 86400 + 3600 * 5          # 05:00 UTC, away from the round-the-clock flags
    c = np.full(n, 100.0)
    return Series(pd.DataFrame({"t": t0 + 60 * np.arange(n), "open": c.copy(), "high": c.copy(), "low": c.copy(), "close": c.copy(),
                                "volume": 1.0, "trades": 1.0, "taker_buy": 0.5, "ok": True}))


def test_failed_breakout_and_wick_rejection_read_only_earlier_candles():
    s = flat()
    i = HISTORY + 300
    # the 1h high stood at 100 fifteen minutes before i; a close at 100.5 ten minutes ago broke it; the last close is back at 99.9
    s.h[i - 10] = s.c[i - 10] = 100.5
    s.c[i - 1] = s.o[i - 1] = 99.9; s.h[i - 1] = 99.95; s.l[i - 1] = 99.85
    E = minute_events(s)
    assert E["failed breakout above the 1h high"][1][i]
    assert not E["failed breakout above the 1h high"][1][i - 11]       # before the break happened
    # a wick: the last minute's high crossed the prior 1h high, its close did not
    s2 = flat(); j = HISTORY + 300
    s2.h[j - 1] = 100.3; s2.c[j - 1] = 99.98; s2.o[j - 1] = 100.0; s2.l[j - 1] = 99.97
    E2 = minute_events(s2)
    assert E2["wick rejection at the 1h high"][1][j]
    assert not E2["wick rejection at the 1h high"][1][j + 1]            # the minute after: the high is now part of the level
    # nothing in the future may change the flag at j
    s3 = flat(); s3.h[j - 1] = 100.3; s3.c[j - 1] = 99.98; s3.o[j - 1] = 100.0; s3.l[j - 1] = 99.97
    s3.c[j:] = 150.0; s3.h[j:] = 150.0
    assert minute_events(s3)["wick rejection at the 1h high"][1][j]


def test_engulfing_and_time_flags():
    s = flat(); i = HISTORY + 200
    s.o[i - 2], s.c[i - 2] = 100.2, 100.0                                   # a down candle
    s.o[i - 1], s.c[i - 1] = 99.9, 100.3                                    # an up candle covering it
    s.h[i - 1], s.l[i - 1] = 100.3, 99.9
    E = minute_events(s)
    assert E["bullish engulfing"][1][i] and not E["bearish engulfing"][1][i]
    hour = (s.t // 3600) % 24; minute = (s.t // 60) % 60
    k = int(np.where((hour == 8) & (minute == 3))[0][0])
    assert E["10 minutes after funding settlement (08:00 UTC)"][1][k]
    assert not E["10 minutes after funding settlement (08:00 UTC)"][1][k + 10]
