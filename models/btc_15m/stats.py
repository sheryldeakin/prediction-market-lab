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
