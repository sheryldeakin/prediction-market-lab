import numpy as np
import pandas as pd

from models.btc_15m.events2 import all_candidates, base_events
from models.btc_15m.rulefit import fit_rulefit


def frame(n=3000, seed=0):
    rng = np.random.default_rng(seed)
    cols = {"rsi14": rng.uniform(0, 100, n), "rsi60": rng.uniform(0, 100, n), "rangepos": rng.uniform(0, 1, n), "vol60": np.full(n, 5.0),
            "ret5": rng.normal(0, 10, n), "ret15": rng.normal(0, 18, n), "ret240": rng.normal(0, 60, n), "flow15": rng.uniform(-1, 1, n),
            "vwap_dev60": rng.normal(0, 30, n), "win1": rng.normal(size=n), "win2": rng.normal(size=n), "macd_hist": rng.normal(size=n),
            "obv_slope60": rng.normal(0, 0.5, n), "ema_cross": rng.normal(0, 15, n), "size5": rng.uniform(0.5, 2, n), "nratio5": rng.uniform(0.5, 3, n),
            "hour": rng.integers(0, 24, n)}
    return pd.DataFrame(cols)


def test_pairs_are_conjunctions_and_families_are_not_paired_with_themselves():
    D = frame()
    base = base_events(D)
    C = all_candidates(D, list(base))
    assert "RSI14 < 30 AND RSI14 < 35" not in C
    name = next(n for n in C if " AND " in n)
    a, b = name.split(" AND ")
    assert np.array_equal(C[name], base[a] & base[b])


def test_session_conditioning_restricts_hours():
    D = frame()
    C = all_candidates(D, [])
    m = C["previous window up, Asia (0-7 UTC)"]
    assert (D.hour.values[m] <= 7).all()
    assert m.sum() < C["previous window up"].sum()


def test_rulefit_l1_drops_useless_columns_and_keeps_the_useful_one():
    rng = np.random.default_rng(0)
    n = 4000
    useful = (rng.uniform(size=n) < 0.5).astype(float)
    noise = (rng.uniform(size=(n, 20)) < 0.5).astype(float)
    y = np.where(useful == 1, rng.uniform(size=n) < 0.75, rng.uniform(size=n) < 0.25).astype(int)
    raw = rng.normal(size=(n, 3))
    model, _ = fit_rulefit(np.column_stack([useful, noise]), raw, y, C=0.05)
    coef = model.coef_[0][:21]
    assert coef[0] > 0.5
    assert (np.abs(coef[1:]) < 0.15).all()
