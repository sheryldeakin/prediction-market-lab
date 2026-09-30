import numpy as np
import pandas as pd

from models.btc_15m.drift import decay_study, training_months, window_study


def test_training_months_window_and_expanding():
    months = list(pd.period_range("2026-01", "2026-08", freq="M"))
    m = pd.Period("2026-06", "M")
    assert training_months(months, m, None) == months[:5]
    assert training_months(months, m, 2) == [pd.Period("2026-04", "M"), pd.Period("2026-05", "M")]
    assert training_months(months, m, 10) == months[:5]        # window longer than history -> all earlier
    assert m not in training_months(months, m, 3)


def synthetic(n_per_month=300, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for m in pd.period_range("2026-01", "2026-06", freq="M"):
        t = int(m.to_timestamp().timestamp()) + 900 * np.arange(n_per_month)
        x = rng.normal(size=(n_per_month, 2))
        rows.append(pd.DataFrame({"t": t, "a": x[:, 0], "b": x[:, 1], "y": (x[:, 0] > 0).astype(int)}))
    return pd.concat(rows, ignore_index=True)


def test_window_study_shapes_and_no_test_leak():
    D = synthetic()
    res = window_study(D, ["a", "b"], kind="logistic", windows=(2, None))
    for name, (pred, y, t) in res.items():
        assert len(pred) == len(y) == len(t)
        assert pd.to_datetime(t, unit="s").min() >= pd.Timestamp("2026-04-01")   # first three months are training only
        assert ((pred > 0.5) == y).mean() > 0.9                                  # separable label is learned


def test_decay_study_ages_and_counts():
    D = synthetic()
    dec = decay_study(D, ["a", "b"], kind="logistic", horizon=3)
    assert sorted(dec) == [0, 1, 2]
    # start months: Apr, May, Jun -> age 0 has 3 start months, age 1 has 2, age 2 has 1
    assert dec[0].start.nunique() == 3 and dec[1].start.nunique() == 2 and dec[2].start.nunique() == 1
    # a model trained before April must never be scored on a month before April
    assert pd.to_datetime(dec[0].t, unit="s").min() >= pd.Timestamp("2026-04-01")
