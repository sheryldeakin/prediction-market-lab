import numpy as np
import pandas as pd

from models.btc_15m.horizons_vwap import vwap_labels
from models.btc_15m.settlement import Vwap


def test_vwap_horizon_label_compares_the_decision_minute_with_the_horizons_last_minute():
    sec = np.arange(0, 3600)
    price = np.where(sec < 1800, 100.0, 101.0)              # a step up at second 1800
    r = pd.DataFrame({"sec": sec, "vol": price * 1.0, "qty": 1.0})
    L = vwap_labels(Vwap(r), np.array([1200, 1800, 3000]))
    assert L[10][1] == 1.0                                   # minute 30 onward is flat at 101: equal counts as up
    assert L[10][0] == 1.0                                   # minute 20 -> minute 29 crosses the step: up
    assert L[1][1] == 1.0 and L[1][2] == 1.0                 # flat minute: equal half-minute VWAPs count as up, like the main label
    assert L[1][0] == 1.0 or L[1][0] == 0.0                   # horizon 1 is defined (first half against second half of the minute)
    assert np.isnan(vwap_labels(Vwap(r[r.sec < 1000]), np.array([1200]))[1][0])     # no trades: no label
