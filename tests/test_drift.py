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


def test_decay_study_scores_every_age_on_the_same_rows():
    """Ages were pooled over different target months, so staleness was confounded with
    which months each age was scored on (council review, 2026-09-30)."""
    from models.btc_15m.evaluate import make_model
    D = synthetic()
    D["y"] = np.where(pd.to_datetime(D.t, unit="s") < pd.Timestamp("2026-05-01"), D.a > 0, D.b > 0).astype(int)
    dec = decay_study(D, ["a", "b"], kind="logistic", horizon=2)
    # with 3 training months minimum, the age-1 model needs May as target at the earliest
    assert sorted(dec.target.unique()) == ["2026-05", "2026-06"]
    assert {"hit_0", "hit_1"} <= set(dec.columns) and dec[["hit_0", "hit_1"]].notna().all().all()
    # the age-1 score on June comes from a model trained on months before May
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    tr, te = (month < pd.Period("2026-05", "M")).values, (month == pd.Period("2026-06", "M")).values
    p = make_model("logistic").fit(D.loc[tr, ["a", "b"]], D.y[tr]).predict_proba(D.loc[te, ["a", "b"]])[:, 1]
    june = dec[dec.target == "2026-06"]
    assert np.array_equal(june.hit_1.values, ((p > 0.5) == D.y.values[te]).astype(float))
    assert june.hit_0.mean() > june.hit_1.mean()             # the fresh model has seen May, where the rule changed
