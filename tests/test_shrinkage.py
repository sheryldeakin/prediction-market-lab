import numpy as np

from models.btc_15m.shrinkage import selection_corrected


def test_selection_bias_is_positive_for_equal_models_and_small_for_a_clear_winner():
    rng = np.random.default_rng(0)
    t = np.repeat(np.arange(200) * 86400, 96)
    noise = rng.choice([-1.0, 0.0, 1.0], size=(len(t), 6), p=[0.25, 0.5, 0.25])      # six models, no real difference
    r = selection_corrected(noise, t, list("abcdef"), n_boot=300)
    assert r["bias"] > 0 and r["corrected"] < r["observed"]
    assert r["low"] <= 0 <= r["high"]
    clear = noise.copy(); clear[:, 2] += 0.2                                            # one model is truly better
    r2 = selection_corrected(clear, t, list("abcdef"), n_boot=300)
    assert r2["best"] == "c" and r2["bias"] < r["bias"] and r2["low"] > 0
