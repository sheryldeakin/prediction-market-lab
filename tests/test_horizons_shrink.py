import numpy as np

from models.btc_15m.horizons_shrink import random_effects


def test_homogeneous_years_give_no_between_year_variance_and_full_shrinkage():
    d = np.array([0.05, 0.051, 0.049, 0.05]); se = np.array([0.01] * 4)
    r = random_effects(d, se)
    assert r["tau"] < 1e-6 and np.allclose(r["shrunk"], r["mu"])
    assert abs(r["mu"] - 0.05) < 1e-3


def test_heterogeneous_years_keep_weight_on_their_own_data():
    d = np.array([0.10, 0.02, 0.08, 0.00]); se = np.array([0.005] * 4)
    r = random_effects(d, se)
    assert r["tau"] > 0.02
    assert (r["shrink_weight"] > 0.9).all()                       # precise, different years: shrink little
    assert np.all(np.abs(r["shrunk"] - d) < np.abs(d - r["mu"]) + 1e-12)   # shrinks toward the pool, never past it
