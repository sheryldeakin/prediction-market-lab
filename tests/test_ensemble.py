import numpy as np
import pandas as pd

from models.btc_15m.ensemble import stack


def months(n_per_month=600, n_months=6):
    t = []
    for m in pd.period_range("2026-01", periods=n_months, freq="M"):
        t.append(int(m.to_timestamp().timestamp()) + 900 * np.arange(n_per_month))
    return np.concatenate(t)


def test_stacker_starts_one_month_after_base_predictions_and_uses_only_earlier_rows():
    rng = np.random.default_rng(0)
    t = months()
    y = rng.integers(0, 2, len(t))
    P = np.column_stack([np.where(y == 1, 0.7, 0.3) + rng.normal(0, 0.05, len(t)) for _ in range(3)])
    P[: 3 * 600] = np.nan                                  # no base predictions in the first three months
    out = stack(P, y, t)
    month = pd.to_datetime(t, unit="s").to_period("M")
    assert np.isnan(out[np.asarray(month <= pd.Period("2026-04", "M"))]).all()     # April is the first base month; stacking starts in May
    assert not np.isnan(out[np.asarray(month >= pd.Period("2026-05", "M"))]).any()
    assert ((out[~np.isnan(out)] > 0.5) == y[~np.isnan(out)]).mean() > 0.95


def test_stacker_fits_only_on_rows_before_the_month_it_scores(monkeypatch):
    import models.btc_15m.ensemble as E
    seen = []

    class Spy(E.LogisticRegression):
        def fit(self, X, y):
            seen.append(len(y))
            return super().fit(X, y)

    monkeypatch.setattr(E, "LogisticRegression", Spy)
    rng = np.random.default_rng(1)
    t = months()
    y = rng.integers(0, 2, len(t))
    P = np.column_stack([rng.uniform(0.2, 0.8, len(t)) for _ in range(2)])
    P[: 3 * 600] = np.nan                  # base predictions exist from April (month 4)
    E.stack(P, y, t)
    # May's stacker sees April only (600 rows); June's sees April and May (1200)
    assert seen == [600, 1200]
