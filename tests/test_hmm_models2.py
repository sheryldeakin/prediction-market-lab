import numpy as np
import pandas as pd

import models.btc_15m.hmm_models2 as H


def test_daily_regime_columns_use_the_previous_days_state(tmp_path, monkeypatch):
    R = pd.DataFrame({"t": [86400 * 2, 86400 * 3, 86400 * 4], "hmm": ["low vol, flat", "high vol, flat", "low vol, flat"]})   # day 1, 2, 3 (t is the next day's 00:00)
    R.to_csv(tmp_path / "regimes_daily.csv", index=False)
    monkeypatch.setattr(H, "OUT", tmp_path)
    D = pd.DataFrame({"t": [86400 * 2 + 900, 86400 * 3 + 900, 86400 * 4 + 900]})                 # minutes on days 2, 3, 4
    D2, cols = H.daily_regime_columns(D)
    assert cols == ["regime: high vol, flat", "regime: low vol, flat"]
    assert D2["regime: low vol, flat"].tolist() == [1.0, 0.0, 1.0]          # day 2 reads day 1's state, day 3 reads day 2's, day 4 reads day 3's
    assert D2["regime: high vol, flat"].tolist() == [0.0, 1.0, 0.0]
