import numpy as np
import pandas as pd

from models.btc_15m.cells_model import previous_h_rule
from models.btc_15m.features import HISTORY, Series


def test_previous_h_rule_calls_the_opposite_of_the_last_h_minutes():
    n = HISTORY + 50
    t0 = 1_700_000_000 - 1_700_000_000 % 900
    c = np.full(n, 100.0); c[HISTORY + 10:] = 101.0                           # a rise at minute HISTORY+10
    s = Series(pd.DataFrame({"t": t0 + 60 * np.arange(n), "open": c, "high": c, "low": c, "close": c, "volume": 1.0, "trades": 1.0, "taker_buy": 0.5, "ok": True}))
    idx = np.array([HISTORY + 5, HISTORY + 12, HISTORY + 20])
    r = previous_h_rule(s, idx, 5)
    assert r.tolist() == [0.0, 0.0, 0.0]                                       # flat or rising last 5 minutes: call down
    c2 = c.copy(); c2[HISTORY + 10:] = 99.0
    s2 = Series(pd.DataFrame({"t": t0 + 60 * np.arange(n), "open": c2, "high": c2, "low": c2, "close": c2, "volume": 1.0, "trades": 1.0, "taker_buy": 0.5, "ok": True}))
    assert previous_h_rule(s2, np.array([HISTORY + 12]), 5)[0] == 1.0        # the last 5 minutes fell: call up
