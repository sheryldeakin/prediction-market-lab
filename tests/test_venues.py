import numpy as np
import pandas as pd

from models.btc_15m.venues import MAX_FILL, to_grid


def test_short_gaps_are_filled_with_the_last_close_and_long_gaps_are_outages():
    a = 0
    have = [0, 1, 2, 5, 6] + list(range(6 + MAX_FILL + 2, 20))      # a 2-minute gap (3, 4), then a longer one
    df = pd.DataFrame({"t": [60 * m for m in have], "open": 1.0, "high": 1.0, "low": 1.0,
                       "close": [100.0 + m for m in have], "volume": 2.0})
    g = to_grid(df, a, 60 * 20)
    assert len(g) == 20 and (g.t.diff().dropna() == 60).all()
    assert g.ok[3] and g.ok[4] and g.close[4] == 102.0 and g.volume[4] == 0.0
    long_gap = range(7, 6 + MAX_FILL + 2)
    assert not all(g.ok[m] for m in long_gap)
    assert (g.taker_buy == g.volume / 2).all()
