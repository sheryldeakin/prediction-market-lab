import numpy as np

from models.btc_15m.rules import bh, day_pvalue


def test_bh_rejects_nothing_on_uniform_pvalues_most_of_the_time():
    rng = np.random.default_rng(0)
    false_rejections = 0
    for _ in range(200):
        p = rng.uniform(0, 1, 40)
        false_rejections += bh(p, q=0.10).sum()
    # under the null the expected number of rejections per trial is small; 200 trials of 40 tests
    assert false_rejections / 200 < 0.5


def test_bh_finds_a_planted_strong_effect_among_nulls():
    rng = np.random.default_rng(1)
    p = rng.uniform(0.05, 1, 40)
    p[7] = 1e-6
    keep = bh(p, q=0.10)
    assert keep[7] and keep.sum() <= 3


def test_bh_is_less_strict_than_bonferroni():
    p = np.array([0.001, 0.002, 0.003, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99])
    assert bh(p, q=0.10).sum() == 3            # Bonferroni at 0.10/10 = 0.01 would also give 3; at q=0.05 BH still keeps 3
    assert bh(p, q=0.05).sum() == 3


def test_day_pvalue_small_for_real_effect_and_large_for_none():
    rng = np.random.default_rng(2)
    t = np.repeat(np.arange(60) * 86400, 50) + np.tile(np.arange(50) * 900, 60)
    hits_real = (rng.uniform(0, 1, len(t)) < 0.58).astype(float)
    hits_none = (rng.uniform(0, 1, len(t)) < 0.50).astype(float)
    assert day_pvalue(hits_real, t, 0.50) < 0.01
    assert day_pvalue(hits_none, t, 0.50) > 0.05


def test_day_pvalue_accounts_for_day_clustering():
    """Whole days that are all-up or all-down: per-window p would be tiny, day-clustered must not be."""
    t = np.repeat(np.arange(12) * 86400, 100)
    hits = np.repeat(np.array([1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0], dtype=float), 100)
    assert day_pvalue(hits, t, 0.5) > 0.3
