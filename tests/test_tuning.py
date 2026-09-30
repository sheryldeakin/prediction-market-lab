import numpy as np
import pandas as pd

import models.btc_15m.tuning as tuning


def synthetic_months(n_per_month=400, seed=0):
    rng = np.random.default_rng(seed)
    months = pd.period_range("2026-01", "2026-06", freq="M")
    rows = []
    for m in months:
        t0 = int(m.to_timestamp().timestamp())
        t = t0 + 900 * np.arange(n_per_month)
        x = rng.normal(size=(n_per_month, 3))
        y = (x[:, 0] + 0.5 * rng.normal(size=n_per_month) > 0).astype(int)
        rows.append(pd.DataFrame({"t": t, "a": x[:, 0], "b": x[:, 1], "c": x[:, 2], "y": y}))
    return pd.concat(rows, ignore_index=True)


def test_honest_search_never_sees_the_test_month(monkeypatch):
    """Record every validation set handed to the search; for the honest variant the latest
    validation timestamp must be before the test month starts."""
    D = synthetic_months()
    seen = []
    real_search = tuning.search

    def spy(Xtr, ytr, Xva, yva, trials, seed=0):
        seen.append((Xtr.index.max(), Xva.index.max()))
        return {"max_depth": 2, "learning_rate": 0.1, "n_estimators": 50, "min_child_weight": 5,
                "subsample": 1.0, "colsample_bytree": 1.0, "reg_lambda": 1.0}

    monkeypatch.setattr(tuning, "search", spy)
    res, chosen = tuning.nested_walk_forward(D, ["a", "b", "c"], trials=1, log=lambda x: None)
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    months = sorted(month.unique())
    # calls alternate honest, cheat per test month, starting at the 4th month
    for i, m in enumerate(months[3:]):
        honest_tr, honest_va = seen[2 * i]
        test_start = D.index[(month == m).values].min()
        assert honest_va < test_start and honest_tr < test_start
        cheat_tr, cheat_va = seen[2 * i + 1]
        assert cheat_va >= test_start            # the deliberately leaky variant does see it
    for v in res:
        pred, y, t = res[v]
        assert len(pred) == len(y) == len(t) and not np.isnan(pred).any()


def test_search_returns_params_inside_the_space():
    D = synthetic_months(n_per_month=150)
    X, y = D[["a", "b", "c"]], D.y.values
    p = tuning.search(X[:600], y[:600], X[600:], y[600:], trials=3)
    for k, (lo, hi) in tuning.SPACE.items():
        assert lo <= p[k] <= hi, k
