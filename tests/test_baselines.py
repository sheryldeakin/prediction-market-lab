import numpy as np
import pandas as pd

from models.btc_15m.evaluate import add_baseline_columns, baseline_name, baseline_walk_forward, runs_for, walk_forward


def frame(n_months=6, per_month=400, seed=0, reversal=0.1):
    """Windows over calendar months where up-rate depends on the previous window."""
    rng = np.random.default_rng(seed)
    t = np.concatenate([int(pd.Timestamp(f"2026-{m:02d}-01").timestamp()) + 900 * np.arange(per_month) for m in range(1, n_months + 1)])
    n = len(t)
    win1 = rng.normal(0, 10, n)
    y = (rng.uniform(size=n) < np.where(win1 >= 0, 0.5 - reversal, 0.5 + reversal)).astype(int)
    return pd.DataFrame({"t": t, "y": y, "win1": win1, "lead": rng.normal(0, 5, n), "vol60": rng.gamma(4, 1, n)})


def test_prev_window_bit_calls_the_reversal_and_uses_training_rates_only():
    D = add_baseline_columns(frame(), 0)
    pred, y, month, t = walk_forward(D, ["prev_up"], "bitrate")
    prev_up = D.set_index("t").prev_up.reindex(t).values
    assert ((pred > 0.5) == (prev_up == 0)).all()           # calls the opposite of the previous window
    m = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    first_test = sorted(m.unique())[3]
    tr = (m < first_test).values
    want = D.y[tr & (D.prev_up == 1).values].mean()
    got = pred[(month == first_test).values & (prev_up == 1)]
    assert np.allclose(got, want)                           # the rate comes from the earlier months


def test_lead_z_scales_the_lead_by_the_remaining_volatility():
    D = pd.DataFrame({"win1": [1.0, -1.0], "lead": [6.0, 6.0], "vol60": [1.0, 2.0]})
    Z = add_baseline_columns(D, 11)                          # four minutes remain
    assert np.allclose(Z.lead_z, [6.0 / (1.0 * 2.0), 6.0 / (2.0 * 2.0)], rtol=1e-6)
    assert list(Z.prev_up) == [1, 0]
    assert "lead_z" not in D                                 # the caller's frame is not modified


def test_baseline_per_minute_is_one_of_the_runs():
    assert baseline_name(0) == "prev-window" and baseline_name(3) == "lead-z"
    for k in (0, 1, 3, 8):
        assert baseline_name(k) in [r[0] for r in runs_for(k)]
    assert "lead-only" not in [r[0] for r in runs_for(0)]


def test_baseline_walk_forward_matches_walk_forward_on_the_derived_column():
    D = frame()
    p1, y1, _, t1 = baseline_walk_forward(D, 0)
    p2, y2, _, t2 = walk_forward(add_baseline_columns(D, 0), ["prev_up"], "bitrate")
    assert np.array_equal(t1, t2) and np.allclose(p1, p2)
    assert ((p1 > 0.5) == y1).mean() > 0.55                 # the planted reversal is found
