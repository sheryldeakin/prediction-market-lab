import numpy as np
import pandas as pd

from models.btc_15m.features import HISTORY, Series
from models.btc_15m.hmm_models import minute_matrix, state_probs


def synthetic(n=HISTORY + 3000, seed=0):
    rng = np.random.default_rng(seed)
    t0 = 1_700_000_000 - 1_700_000_000 % 900
    vol = np.where(np.arange(n) % 2000 < 1000, 2e-4, 1e-3)            # alternating calm and busy stretches
    close = 50_000 * np.exp(np.cumsum(rng.normal(0, vol)))
    open_ = np.concatenate([[close[0]], close[:-1]])
    v = rng.gamma(2, 1, n) * np.where(vol > 5e-4, 3, 1)
    return Series(pd.DataFrame({"t": t0 + 60 * np.arange(n), "open": open_, "high": np.maximum(open_, close), "low": np.minimum(open_, close),
                                "close": close, "volume": v, "trades": 100.0, "taker_buy": v * rng.uniform(0.3, 0.7, n), "ok": True}))


def test_state_probabilities_are_filtered_and_separate_calm_from_busy():
    s = synthetic()
    X = minute_matrix(s)
    fit = np.zeros(len(X), bool); fit[:HISTORY + 2000] = True
    P, m = state_probs(X, fit, n_states=2)
    assert np.allclose(P.sum(axis=1), 1)
    # the dominant state in a calm stretch differs from the dominant state in a busy stretch
    calm = P[HISTORY + 2200:HISTORY + 2900].mean(0).argmax()
    busy = P[HISTORY + 1200:HISTORY + 1900].mean(0).argmax()
    assert calm != busy
    # changing later minutes must not change earlier filtered probabilities
    X2 = X.copy(); X2[HISTORY + 2500:] *= 5
    P2, _ = state_probs(X2, fit, n_states=2)
    assert np.allclose(P2[:HISTORY + 2500], P[:HISTORY + 2500])
