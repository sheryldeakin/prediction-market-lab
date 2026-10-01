import numpy as np
import pandas as pd

from models.btc_15m.experiments import EMBARGO_S, magnitude_label, purged_train_mask
from models.btc_15m.features import HISTORY, Series


def test_purged_cv_keeps_no_training_row_within_the_lookback_of_a_test_block():
    """A 4-hour embargo was shorter than the 24-hour volume baseline, so training windows
    shared feature history with test windows (council review, 2026-09-30)."""
    assert EMBARGO_S >= 24 * 3600
    t = 900 * np.arange(6000)
    groups = pd.qcut(t, 6, labels=False)
    for test_groups in [(1, 4), (0, 5), (2, 3)]:
        tr = purged_train_mask(t, groups, test_groups, EMBARGO_S)
        te = np.isin(groups, test_groups)
        assert not (tr & te).any()
        gaps = np.abs(t[tr][:, None] - t[te][None, :])
        assert gaps.min() > EMBARGO_S


def test_magnitude_label_at_minute_3_ignores_the_move_already_made():
    """Measured from the open, a 20 bp move in the first minutes made the label 1 at
    minute 3 although the lead is a feature (council review, 2026-09-30)."""
    n = HISTORY + 60
    t0 = 1_700_000_000 - 1_700_000_000 % 900
    close = np.full(n, 100.0)
    s = Series(pd.DataFrame({"t": t0 + 60 * np.arange(n), "open": close, "high": close, "low": close,
                             "close": close, "volume": 1.0, "trades": 1.0, "taker_buy": 0.5, "ok": True}))
    i = next(iter(s.window_starts()))
    s.c[i:i + 15] = 100.2                     # +20 bp in the first minute, flat after
    D = pd.DataFrame({"t": [int(s.t[i])]})
    assert magnitude_label(s, D, 0, 10.0)[0] == 1
    assert magnitude_label(s, D, 3, 10.0)[0] == 0
    s.c[i + 14] = 100.2 * 1.0015              # +15 bp after entry
    assert magnitude_label(s, D, 3, 10.0)[0] == 1
