import numpy as np
import pandas as pd

from models.btc_15m.regimes import date_phases, forward_filter


def test_threshold_dating_finds_the_planted_peak_and_trough():
    t = 86400 * np.arange(400) + 86399
    close = np.concatenate([np.linspace(100, 200, 150), np.linspace(200, 120, 100), np.linspace(120, 220, 150)])
    P = date_phases(close, t, bear_drop=0.15, bull_rise=0.20)
    assert list(P.phase) == ["bull", "bear", "bull (open)"]
    assert P.b.iloc[0] == 149 and P.b.iloc[1] == 249                     # dated at the peak and the trough
    assert abs(P["return"].iloc[1] - (120 / 200 - 1)) < 1e-9


def test_forward_filter_is_normalised_and_agrees_with_the_smoothed_posterior_at_the_end():
    from hmmlearn.hmm import GaussianHMM
    rng = np.random.default_rng(0)
    X = np.concatenate([rng.normal(0, 1, (300, 2)), rng.normal(3, 1, (300, 2))])
    m = GaussianHMM(n_components=2, covariance_type="full", n_iter=100, random_state=0).fit(X)
    A = forward_filter(m, X)
    assert np.allclose(A.sum(axis=1), 1)
    _, post = m.score_samples(X)
    assert np.allclose(A[-1], post[-1], atol=1e-6)                      # the last filtered row has nothing left to smooth
    # the filtered state at t must not change when later observations change
    X2 = X.copy(); X2[400:] += 10
    assert np.allclose(forward_filter(m, X2)[:400], A[:400])
