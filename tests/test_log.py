import pandas as pd

from models.btc_15m.log import merge_log


def rows(ts, minute=0, prob=0.6):
    return pd.DataFrame({"t": ts, "minute": minute, "model": "m", "prob_up": prob, "outcome_up": 1})


def test_merge_appends_only_new_windows():
    old = rows([900, 1800])
    new = rows([1800, 2700], prob=0.9)
    out = merge_log(old, new)
    assert list(out.t) == [900, 1800, 2700]
    assert out.loc[out.t == 1800, "prob_up"].item() == 0.6      # existing row untouched


def test_merge_keeps_minutes_separate():
    old = rows([900], minute=0)
    new = rows([900], minute=3)
    out = merge_log(old, new)
    assert len(out) == 2 and sorted(out.minute) == [0, 3]


def test_merge_with_empty_log():
    new = rows([2700, 900])
    out = merge_log(None, new)
    assert list(out.t) == [900, 2700]
