"""Statistical checks used by the evaluation. Pure functions, tested in tests/test_stats.py.

Windows in one day share market conditions, so plain standard errors overstate the
evidence. Everything here resamples or permutes whole days.
"""
from __future__ import annotations

import numpy as np


def _by_day(t: np.ndarray):
    days = t // 86400
    uniq, inv = np.unique(days, return_inverse=True)
    return uniq, inv


def block_bootstrap_ci(hits: np.ndarray, t: np.ndarray, n_boot: int = 2000, seed: int = 0, level: float = 0.95):
    """CI for a mean (e.g. accuracy) resampling days with replacement.

    hits: per-window 0/1 (or any value), t: per-window epoch seconds.
    Returns (mean, low, high).
    """
    uniq, inv = _by_day(t)
    sums = np.bincount(inv, weights=hits)
    counts = np.bincount(inv)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(uniq), size=(n_boot, len(uniq)))
    boots = sums[idx].sum(axis=1) / counts[idx].sum(axis=1)
    a = (1 - level) / 2
    return float(hits.mean()), float(np.quantile(boots, a)), float(np.quantile(boots, 1 - a))


def paired_difference_ci(hits_a: np.ndarray, hits_b: np.ndarray, t: np.ndarray, **kw):
    """CI for accuracy(a) - accuracy(b) on the same windows, resampling days."""
    return block_bootstrap_ci(hits_a.astype(float) - hits_b.astype(float), t, **kw)


def permutation_pvalue(pred: np.ndarray, y: np.ndarray, t: np.ndarray, n_perm: int = 1000, seed: int = 0):
    """One-sided p-value for accuracy above chance, permuting labels within each day.

    Within-day permutation keeps each day's up/down count, so a model that only
    learned the day's drift gets no credit.
    """
    calls = pred > 0.5
    obs = (calls == y).mean()
    uniq, inv = _by_day(t)
    rng = np.random.default_rng(seed)
    order = np.argsort(inv, kind="stable")
    bounds = np.searchsorted(inv[order], np.arange(len(uniq) + 1))
    y_sorted = y[order]
    calls_sorted = calls[order]
    count = 0
    for _ in range(n_perm):
        perm = y_sorted.copy()
        for s, e in zip(bounds[:-1], bounds[1:]):
            perm[s:e] = rng.permutation(perm[s:e])
        if (calls_sorted == perm).mean() >= obs:
            count += 1
    return float(obs), (count + 1) / (n_perm + 1)


# ---------------- tests that respect serial dependence (council review, 2026-09-30) ----------------
#
# The within-day permutation above shuffles labels inside a day, which destroys the
# dependence between neighbouring windows; under that null, a statistic that leans on
# serial structure looks more significant than it is. The tests below keep the structure.

def _by_month(t: np.ndarray):
    months = t.astype("datetime64[s]").astype("datetime64[M]").astype(np.int64)
    uniq, inv = np.unique(months, return_inverse=True)
    return uniq, inv


def month_block_bootstrap_ci(hits: np.ndarray, t: np.ndarray, n_boot: int = 2000, seed: int = 0, level: float = 0.95):
    """Like block_bootstrap_ci with whole calendar months as the blocks. With about eight
    test months this is wide; it is the honest width if regimes last a month."""
    uniq, inv = _by_month(t)
    sums = np.bincount(inv, weights=hits)
    counts = np.bincount(inv)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(uniq), size=(n_boot, len(uniq)))
    boots = sums[idx].sum(axis=1) / counts[idx].sum(axis=1)
    a = (1 - level) / 2
    return float(hits.mean()), float(np.quantile(boots, a)), float(np.quantile(boots, 1 - a))


def day_sign_test(hits_a: np.ndarray, hits_b: np.ndarray, t: np.ndarray, n_draws: int = 2000, seed: int = 0) -> dict:
    """Day-level test of accuracy(a) > accuracy(b) on the same windows. Each day gives one
    number, the difference of the two accuracies that day; under the null of no
    difference each day's sign is equally likely to flip. Returns the share of days where
    a beats b (ties excluded), the mean daily difference, and the one-sided p of the mean
    under random sign flips."""
    uniq, inv = _by_day(t)
    d = np.bincount(inv, weights=hits_a.astype(float) - hits_b.astype(float)) / np.bincount(inv)
    obs = d.mean()
    rng = np.random.default_rng(seed)
    signs = rng.choice([-1.0, 1.0], size=(n_draws, len(d)))
    null = (signs * d).mean(axis=1)
    nz = d[d != 0]
    return {"days": int(len(d)), "share_days_a_better": float((nz > 0).mean()) if len(nz) else 0.5,
            "mean_daily_diff": float(obs), "p": float((np.sum(null >= obs) + 1) / (n_draws + 1))}


def circular_shift_pvalue(pred: np.ndarray, y: np.ndarray, t: np.ndarray, n_draws: int = 2000, seed: int = 0):
    """One-sided p for accuracy above what the labels' own structure gives. Within each
    month the label sequence is rotated by a random offset, which keeps its serial
    dependence and base rate but breaks its alignment with the calls."""
    calls = (pred > 0.5).astype(int)
    obs = float((calls == y).mean())
    _, inv = _by_month(t)
    order = np.argsort(t, kind="stable")
    calls_o, y_o, inv_o = calls[order], y[order], inv[order]
    groups = [np.where(inv_o == g)[0] for g in np.unique(inv_o)]
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_draws):
        right = 0
        for idx in groups:
            n = len(idx)
            if n < 2:
                right += int(calls_o[idx[0]] == y_o[idx[0]])
                continue
            shift = int(rng.integers(1, n))
            right += int((calls_o[idx] == np.roll(y_o[idx], shift)).sum())
        count += right / len(y) >= obs
    return obs, (count + 1) / (n_draws + 1)


def cluster_diff_pvalue(mask: np.ndarray, y: np.ndarray, t: np.ndarray) -> tuple[float, float, float]:
    """Up-rate when the event fires minus up-rate when it does not, with a day-clustered
    (CR0 sandwich) standard error from the regression y = a + b * mask. Returns (b, se, two-sided p).
    Unlike testing the event's up-rate against a fixed base rate, the comparison group is
    estimated too, and its uncertainty enters the error."""
    from scipy.stats import norm
    m = mask.astype(float)
    y = y.astype(float)
    n1 = m.sum(); n0 = len(m) - n1
    if n1 < 2 or n0 < 2:
        return 0.0, float("inf"), 1.0
    a = y[m == 0].mean()
    b = y[m == 1].mean() - a
    e = y - a - b * m
    _, inv = _by_day(t)
    s0 = np.bincount(inv, weights=e)
    s1 = np.bincount(inv, weights=e * m)
    XtX = np.array([[len(m), n1], [n1, n1]])
    meat = np.array([[np.sum(s0 * s0), np.sum(s0 * s1)], [np.sum(s0 * s1), np.sum(s1 * s1)]])
    inv_xtx = np.linalg.inv(XtX)
    V = inv_xtx @ meat @ inv_xtx
    se = float(np.sqrt(max(V[1, 1], 0.0)))
    if se == 0:
        return float(b), 0.0, 1.0 if b == 0 else 0.0
    return float(b), se, float(2 * (1 - norm.cdf(abs(b) / se)))


def paired_cluster_se(d: np.ndarray, cluster: np.ndarray) -> float:
    """Standard error of the mean of per-pair differences d with clusters (CR0 sandwich, no small-sample
    correction, as cluster_diff_pvalue): sqrt(sum over clusters of (sum of the cluster's d - mean)^2) / n.
    Infinite with fewer than two clusters, where the clustered error is not defined."""
    d = np.asarray(d, float)
    _, inv = np.unique(cluster, return_inverse=True)
    if len(d) < 2 or inv.max() < 1:
        return float("inf")
    s = np.bincount(inv, weights=d - d.mean())
    return float(np.sqrt(np.sum(s * s)) / len(d))


def _logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def calibration_slope(p: np.ndarray, y: np.ndarray, iters: int = 50) -> tuple[float, float]:
    """(intercept, slope) of the logistic regression of y on logit(p). A calibrated model
    has slope 1 and intercept 0; slope < 1 means its probabilities are too extreme."""
    x = _logit(p)
    X = np.column_stack([np.ones_like(x), x])
    beta = np.zeros(2)
    for _ in range(iters):
        mu = 1 / (1 + np.exp(-X @ beta))
        w = np.clip(mu * (1 - mu), 1e-9, None)
        step = np.linalg.solve(X.T @ (X * w[:, None]), X.T @ (y - mu))
        beta += step
        if np.max(np.abs(step)) < 1e-10:
            break
    return float(beta[0]), float(beta[1])


def calibration_slope_ci(p: np.ndarray, y: np.ndarray, t: np.ndarray, n_boot: int = 500, seed: int = 0, level: float = 0.95):
    """Calibration slope with a day-block bootstrap interval. Returns (slope, low, high)."""
    _, slope = calibration_slope(p, y)
    uniq, inv = _by_day(t)
    rows = [np.where(inv == g)[0] for g in range(len(uniq))]
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        pick = np.concatenate([rows[g] for g in rng.integers(0, len(uniq), len(uniq))])
        boots.append(calibration_slope(p[pick], y[pick])[1])
    a = (1 - level) / 2
    return slope, float(np.quantile(boots, a)), float(np.quantile(boots, 1 - a))
