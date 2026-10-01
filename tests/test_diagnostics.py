import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from models.btc_15m.diagnostics import brier_decomposition, conformal_sets, ece, permutation_importance, recalibrate


def test_brier_decomposition_identity():
    rng = np.random.default_rng(0)
    p = rng.uniform(0, 1, 5000)
    y = (rng.uniform(0, 1, 5000) < p).astype(int)
    d = brier_decomposition(p, y)
    assert abs(d["brier"] - (d["reliability"] - d["resolution"] + d["uncertainty"])) < 5e-3
    assert d["reliability"] < 0.003              # calibrated by construction


def test_ece_zero_for_perfect_and_large_for_shifted():
    rng = np.random.default_rng(1)
    p = rng.uniform(0.05, 0.95, 20000)
    y = (rng.uniform(0, 1, 20000) < p).astype(int)
    assert ece(p, y) < 0.02
    assert ece(np.clip(p + 0.3, 0, 1), y) > 0.2


def test_recalibration_fixes_a_known_shift():
    rng = np.random.default_rng(2)
    p_true = rng.uniform(0.1, 0.9, 6000)
    y = (rng.uniform(0, 1, 6000) < p_true).astype(int)
    p_shifted = np.clip(p_true - 0.2, 0.01, 0.99)          # systematically too low
    for method in ("platt", "isotonic"):
        fixed = recalibrate(p_shifted[:3000], y[:3000], p_shifted[3000:], method)
        assert ece(fixed, y[3000:]) < ece(p_shifted[3000:], y[3000:]) / 2, method


def test_conformal_coverage_meets_target():
    rng = np.random.default_rng(3)
    p = rng.uniform(0.2, 0.8, 8000)
    y = (rng.uniform(0, 1, 8000) < p).astype(int)
    for alpha in (0.1, 0.3):
        up, down = conformal_sets(p[:4000], y[:4000], p[4000:], alpha)
        truth_in = np.where(y[4000:] == 1, up, down)
        assert truth_in.mean() >= 1 - alpha - 0.02
        assert (up | down).all()                             # a set is never empty at these alphas


def test_conformal_abstains_more_at_higher_coverage():
    rng = np.random.default_rng(4)
    p = rng.uniform(0.2, 0.8, 8000)
    y = (rng.uniform(0, 1, 8000) < p).astype(int)
    both = []
    for alpha in (0.4, 0.2, 0.1):
        up, down = conformal_sets(p[:4000], y[:4000], p[4000:], alpha)
        both.append((up & down).mean())
    assert both[0] <= both[1] <= both[2]


def test_permutation_importance_is_zero_for_an_unused_feature():
    rng = np.random.default_rng(5)
    X = pd.DataFrame({"a": rng.normal(size=4000), "b": rng.normal(size=4000)})
    y = (X.a > 0).astype(int).values
    model = LogisticRegression().fit(X[["a", "b"]], y)
    imp = permutation_importance(model, X, y, ["a", "b"])
    assert imp["a"] > 0.3 and abs(imp["b"]) < 0.02


def test_conformal_empty_sets_are_counted_and_are_misses():
    """Below 50% target coverage the threshold falls under 0.5 and some sets hold neither
    class; they were reported only as single or double (council review, 2026-09-30)."""
    from models.btc_15m.diagnostics import conformal_summary
    rng = np.random.default_rng(0)
    p_cal = rng.uniform(0.4, 0.6, 4000); y_cal = (rng.uniform(size=4000) < p_cal).astype(int)
    p_new = rng.uniform(0.4, 0.6, 4000); y_new = (rng.uniform(size=4000) < p_new).astype(int)
    up, down = conformal_sets(p_cal, y_cal, p_new, alpha=0.6)
    s = conformal_summary(up, down, y_new)
    assert s["empty"] > 0
    assert s["empty"] + s["single"] + s["double"] == s["n"]
    empty = ~up & ~down
    assert s["covered"] == int(np.where(y_new == 1, up, down).sum()) and s["covered"] <= s["n"] - s["empty"]


def test_brier_residual_is_small_for_calibrated_probabilities_and_bins_are_filled():
    rng = np.random.default_rng(1)
    p = rng.uniform(0.45, 0.55, 50_000)                  # the narrow range seen at the open
    y = (rng.uniform(size=p.size) < p).astype(int)
    d = brier_decomposition(p, y)
    assert d["bins"] == 10                               # equal-width bins would use two of ten
    assert abs(d["residual"]) < 1e-4
    assert abs(d["brier"] - (d["reliability"] - d["resolution"] + d["uncertainty"] + d["residual"])) < 1e-12
