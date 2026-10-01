import numpy as np
import pandas as pd

from models.btc_15m.search_null import held_count, rotate_within_groups, search


def month_frame(n_months=8, per_month=800, seed=0):
    rng = np.random.default_rng(seed)
    t = np.concatenate([int(pd.Timestamp(f"2026-{m:02d}-01").timestamp()) + 900 * np.arange(per_month) for m in range(1, n_months + 1)])
    return t, rng


def test_rotation_keeps_each_months_values_and_runs_but_moves_them():
    t, rng = month_frame()
    month = pd.to_datetime(t, unit="s").to_period("M").astype(str).values
    y = np.repeat(rng.integers(0, 2, len(t) // 10), 10)
    r = rotate_within_groups(y, month, np.random.default_rng(1))
    for g in np.unique(month):
        m = month == g
        assert r[m].sum() == y[m].sum()                                   # same base rate per month
        runs = lambda v: np.sum(np.diff(v) != 0)
        assert abs(runs(r[m]) - runs(y[m])) <= 2                           # runs survive the rotation (the seam may add one)
    assert not np.array_equal(r, y)


def test_search_finds_a_planted_effect_and_little_on_rotated_labels():
    t, rng = month_frame()
    month = pd.to_datetime(pd.Series(t), unit="s").dt.to_period("M")
    months = sorted(month.unique())
    x = rng.normal(size=(len(t), 30))
    masks = [x[:, j] > 0.5 for j in range(30)]
    y = (rng.random(len(t)) < np.where(masks[0], 0.62, 0.48)).astype(int)
    real = search(masks, y, t, month, months)
    assert real.fdr.iloc[0] and real.stable.iloc[0]
    null = search(masks, rotate_within_groups(y, month.astype(str).values, np.random.default_rng(2)), t, month, months)
    assert null.stable.sum() <= 2
    assert abs(real.z.iloc[0]) > null.z.abs().max()


def test_held_count_skips_rare_masks_and_compares_signs():
    y = np.array([1, 1, 1, 0, 0, 0, 0, 0] * 10)
    up = np.array([True, True, True, False, False, False, False, False] * 10)    # fires on the up windows
    rare = np.zeros(80, bool); rare[:5] = True
    held, scored = held_count([up, up, rare], y, np.array([1, -1, 1]))
    assert scored == 2 and held == 1
