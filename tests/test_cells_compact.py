import numpy as np
import pandas as pd

from models.btc_15m.cells_compact import COMPACT, compact_matrix, compact_model
from models.btc_15m.features import features_all
from tests.test_horizons import flat


def test_compact_matrix_reads_the_last_closed_candle_and_scales_returns_by_volatility():
    s = flat()
    D = features_all(s)
    X = compact_matrix(s, D)
    assert X.shape == (len(D), len(COMPACT)) and np.isfinite(X).all()
    k = 10
    j = D.i.values[k] - 1
    o, h, l, c = s.o[j], s.h[j], s.l[j], s.c[j]
    assert np.isclose(X[k, 6], (h - max(o, c)) / (h - l), atol=1e-6) and np.isclose(X[k, 7], (min(o, c) - l) / (h - l), atol=1e-6)
    assert X[k, 8] == np.sign(c - o)
    assert np.isclose(X[k, 0], D.ret5.values[k] / (D.vol60.values[k] * np.sqrt(5)), rtol=1e-4)
    assert np.isclose(X[k, 4], D.rangepos.values[k], atol=1e-6)


def test_compact_model_fits_and_returns_probabilities():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(2000, len(COMPACT))).astype(np.float32)
    y = (X[:, 0] + rng.normal(size=2000) < 0).astype(int)        # a negative first column means up
    p = compact_model().fit(X, y).predict_proba(X)[:, 1]
    assert ((p > 0.5) == y).mean() > 0.7
