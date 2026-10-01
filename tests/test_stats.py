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


def test_permutation_p_at_its_floor_is_reported_as_below_the_floor():
    """p = 0.002 was the floor at 500 permutations and was printed as if exact
    (council review, 2026-09-30)."""
    from models.btc_15m.evaluate import format_p
    assert format_p(1 / 501, 500) == "< 0.0020"
    assert format_p(1 / 2001, 2000) == "< 0.0005"
    assert format_p(0.0312, 2000) == "0.0312"


# ---------------- Section 3 statistics ----------------

def month_times(n_months=8, per_month=600):
    import pandas as pd
    return np.concatenate([int(pd.Timestamp(f"2026-{m:02d}-01").timestamp()) + 900 * np.arange(per_month) for m in range(1, n_months + 1)])


def test_month_bootstrap_is_wider_than_day_bootstrap_when_months_differ():
    from models.btc_15m.stats import month_block_bootstrap_ci
    t = month_times()
    rng = np.random.default_rng(0)
    month_rate = np.repeat(rng.choice([0.45, 0.6], 8), 600)
    hits = (rng.random(len(t)) < month_rate).astype(float)
    _, dlo, dhi = block_bootstrap_ci(hits, t)
    _, mlo, mhi = month_block_bootstrap_ci(hits, t)
    assert (mhi - mlo) > (dhi - dlo)


def test_day_sign_test_finds_a_real_increment_and_not_a_null_one():
    from models.btc_15m.stats import day_sign_test
    rng = np.random.default_rng(1)
    t = times(120)
    b = (rng.random(len(t)) < 0.52).astype(float)
    better = np.where(rng.random(len(t)) < 0.05, 1.0, b)          # a fixes 5% of windows
    same = np.where(rng.random(len(t)) < 0.5, b, (rng.random(len(t)) < 0.52).astype(float))
    assert day_sign_test(better, b, t)["p"] < 0.01
    assert day_sign_test(better, b, t)["share_days_a_better"] > 0.8
    assert day_sign_test(same, b, t)["p"] > 0.01


def test_circular_shift_gives_no_credit_for_label_autocorrelation():
    """Labels in long runs. Rotating them keeps the runs, so random calls stay
    insignificant, while calls aligned with the runs (the previous label) stay significant."""
    from models.btc_15m.stats import circular_shift_pvalue
    rng = np.random.default_rng(2)
    t = month_times(per_month=800)
    runs = np.repeat(rng.integers(0, 2, len(t) // 20), 20)[:len(t)]
    aligned = np.r_[runs[0], runs[:-1]].astype(float)             # previous label: right inside every run
    obs, p = circular_shift_pvalue(aligned, runs, t, n_draws=300)
    assert obs > 0.9 and p < 0.01
    random_calls = rng.random(len(t))
    _, p0 = circular_shift_pvalue(random_calls, runs, t, n_draws=300)
    assert p0 > 0.05


def test_cluster_diff_counts_the_comparison_group_uncertainty():
    from models.btc_15m.stats import cluster_diff_pvalue
    rng = np.random.default_rng(3)
    t = times(100)
    mask = rng.random(len(t)) < 0.1
    y = (rng.random(len(t)) < np.where(mask, 0.6, 0.5)).astype(int)
    b, se, p = cluster_diff_pvalue(mask, y, t)
    assert abs(b - (y[mask].mean() - y[~mask].mean())) < 1e-12
    assert p < 0.001 and se > 0
    y0 = (rng.random(len(t)) < 0.5).astype(int)
    assert cluster_diff_pvalue(mask, y0, t)[2] > 0.01
    # day-level shocks shared by event and non-event windows widen the error
    day_shift = np.repeat(rng.choice([0.2, 0.8], 100), 96)
    yd = (rng.random(len(t)) < day_shift).astype(int)
    m2 = np.repeat(rng.random(100) < 0.1, 96)                    # the event fires on whole days
    _, se_clustered, _ = cluster_diff_pvalue(m2, yd, t)
    naive = np.sqrt(yd[m2].var() / m2.sum() + yd[~m2].var() / (~m2).sum())
    assert se_clustered > 2 * naive


def test_calibration_slope_is_one_for_calibrated_and_below_one_for_overconfident():
    from models.btc_15m.stats import calibration_slope, calibration_slope_ci
    rng = np.random.default_rng(4)
    t = times(200)
    p = rng.uniform(0.2, 0.8, len(t))
    y = (rng.random(len(t)) < p).astype(int)
    a, s = calibration_slope(p, y)
    assert abs(s - 1) < 0.1 and abs(a) < 0.1
    over = 1 / (1 + np.exp(-3 * np.log(p / (1 - p))))            # same ranking, three times too extreme
    assert abs(calibration_slope(over, y)[1] - 1 / 3) < 0.05
    s, lo, hi = calibration_slope_ci(p, y, t, n_boot=100)
    assert lo < 1 < hi
