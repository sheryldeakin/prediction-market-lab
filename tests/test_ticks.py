import numpy as np
import pandas as pd

from models.btc_15m.ticks import TICK_FEATURES, TickFlow


def frame(n_sec=100_000, seed=0):
    rng = np.random.default_rng(seed)
    sec = np.arange(n_sec)
    vol = rng.gamma(2, 1, n_sec)
    return pd.DataFrame({"sec": sec, "vol": vol, "svol": vol * rng.uniform(-1, 1, n_sec), "n": rng.integers(1, 20, n_sec).astype(float),
                         "big_n": rng.integers(0, 2, n_sec).astype(float), "big_svol": rng.normal(0, 1, n_sec)})


def test_range_sums_match_direct_sums():
    f = frame()
    tf = TickFlow(f)
    a, b = 5000, 5060
    s = tf.sums(a, b)
    direct = f[(f.sec >= a) & (f.sec < b)]
    assert np.isclose(s["vol"], direct.vol.sum()) and np.isclose(s["svol"], direct.svol.sum()) and np.isclose(s["n"], direct.n.sum())


def test_missing_seconds_are_skipped():
    f = frame().iloc[::3]           # only every third second has trades
    tf = TickFlow(f)
    s = tf.sums(3000, 3009)
    assert np.isclose(s["n"], f[(f.sec >= 3000) & (f.sec < 3009)].n.sum())


def test_features_use_nothing_at_or_after_the_entry_minute():
    f = frame()
    t_open, k = 90_000, 3
    now = t_open + 60 * k
    before = TickFlow(f).features(t_open, k)
    g = f.copy()
    g.loc[g.sec >= now, ["vol", "svol", "n", "big_n", "big_svol"]] *= 5.0
    after = TickFlow(g).features(t_open, k)
    assert before == after
    h = f.copy()
    h.loc[h.sec == now - 1, "svol"] += 100.0          # the last second before the entry must count
    assert TickFlow(h).features(t_open, k)["tick_imb5"] != before["tick_imb5"]


def test_feature_names_and_bounds():
    f = frame()
    out = TickFlow(f).features(90_000, 0)
    assert set(out) == set(TICK_FEATURES)
    for w in (5, 15, 30, 60, 300):
        assert -1 <= out[f"tick_imb{w}"] <= 1
    assert 0 <= out["tick_big_share60"] <= 1
