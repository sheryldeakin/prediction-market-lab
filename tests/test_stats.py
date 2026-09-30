import numpy as np

from models.btc_15m.stats import block_bootstrap_ci, paired_difference_ci, permutation_pvalue


def times(n_days, per_day=96):
    return np.repeat(np.arange(n_days) * 86400, per_day) + np.tile(np.arange(per_day) * 900, n_days)


def test_bootstrap_ci_contains_mean_and_narrows_with_days():
    rng = np.random.default_rng(1)
    t_small, t_big = times(10), times(200)
    h_small = rng.random(len(t_small)) < 0.52
    h_big = rng.random(len(t_big)) < 0.52
    m1, lo1, hi1 = block_bootstrap_ci(h_small.astype(float), t_small)
    m2, lo2, hi2 = block_bootstrap_ci(h_big.astype(float), t_big)
    assert lo1 <= m1 <= hi1 and lo2 <= m2 <= hi2
    assert (hi2 - lo2) < (hi1 - lo1)


def test_bootstrap_respects_day_clustering():
    """Windows identical within a day: the CI must be as wide as a 10-observation sample, not 960."""
    t = times(10)
    hits = np.repeat(np.array([1, 1, 1, 1, 1, 1, 0, 0, 0, 0], dtype=float), 96)
    _, lo, hi = block_bootstrap_ci(hits, t)
    assert hi - lo > 0.4


def test_paired_difference_zero_for_identical():
    t = times(20)
    h = (np.random.default_rng(2).random(len(t)) < 0.5).astype(float)
    m, lo, hi = paired_difference_ci(h, h, t)
    assert m == 0 and lo == 0 and hi == 0


def test_permutation_pvalue_detects_signal_and_not_noise():
    rng = np.random.default_rng(3)
    t = times(60)
    y = (rng.random(len(t)) < 0.5).astype(int)
    good = np.where(rng.random(len(t)) < 0.6, y, 1 - y).astype(float)   # 60% right
    noise = rng.random(len(t))
    _, p_good = permutation_pvalue(good, y, t, n_perm=300)
    _, p_noise = permutation_pvalue(noise, y, t, n_perm=300)
    assert p_good < 0.01
    assert p_noise > 0.05


def test_permutation_gives_no_credit_for_day_drift():
    """A model that only knows each day's majority direction scores well on raw accuracy
    but must not look significant under within-day permutation."""
    rng = np.random.default_rng(4)
    t = times(60)
    day_bias = np.repeat(rng.choice([0.3, 0.7], 60), 96)
    y = (rng.random(len(t)) < day_bias).astype(int)
    drift_only = np.repeat([(y[d * 96:(d + 1) * 96].mean() > 0.5) for d in range(60)], 96).astype(float)
    obs, p = permutation_pvalue(drift_only, y, t, n_perm=300)
    assert obs > 0.55
    assert p > 0.05
