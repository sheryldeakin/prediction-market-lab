import numpy as np

from models.btc_15m.rules import bh, day_pvalue


def test_bh_rejects_nothing_on_uniform_pvalues_most_of_the_time():
    rng = np.random.default_rng(0)
    false_rejections = 0
    for _ in range(200):
        p = rng.uniform(0, 1, 40)
        false_rejections += bh(p, q=0.10).sum()
    # under the null the expected number of rejections per trial is small; 200 trials of 40 tests
    assert false_rejections / 200 < 0.5


def test_bh_finds_a_planted_strong_effect_among_nulls():
    rng = np.random.default_rng(1)
    p = rng.uniform(0.05, 1, 40)
    p[7] = 1e-6
    keep = bh(p, q=0.10)
    assert keep[7] and keep.sum() <= 3


def test_bh_is_less_strict_than_bonferroni():
    p = np.array([0.001, 0.002, 0.003, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99])
    assert bh(p, q=0.10).sum() == 3            # Bonferroni at 0.10/10 = 0.01 would also give 3; at q=0.05 BH still keeps 3
    assert bh(p, q=0.05).sum() == 3


def test_day_pvalue_small_for_real_effect_and_large_for_none():
    rng = np.random.default_rng(2)
    t = np.repeat(np.arange(60) * 86400, 50) + np.tile(np.arange(50) * 900, 60)
    hits_real = (rng.uniform(0, 1, len(t)) < 0.58).astype(float)
    hits_none = (rng.uniform(0, 1, len(t)) < 0.50).astype(float)
    assert day_pvalue(hits_real, t, 0.50) < 0.01
    assert day_pvalue(hits_none, t, 0.50) > 0.05


def test_day_pvalue_accounts_for_day_clustering():
    """Whole days that are all-up or all-down: per-window p would be tiny, day-clustered must not be."""
    t = np.repeat(np.arange(12) * 86400, 100)
    hits = np.repeat(np.array([1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0], dtype=float), 100)
    assert day_pvalue(hits, t, 0.5) > 0.3


def event_frame(n_months=8, per_month=600, seed=0):
    """A feature frame with every column events() reads, spread over calendar months."""
    import pandas as pd
    rng = np.random.default_rng(seed)
    t = np.concatenate([int(pd.Timestamp(f"2025-{m:02d}-01").timestamp()) + 900 * np.arange(per_month) for m in range(1, n_months + 1)])
    n = len(t)
    cols = ["rangepos", "ret5", "ret15", "ret240", "win1", "win2", "win3", "rsi14", "rsi60", "macd_hist", "bb_pctb", "ema_cross", "adx14",
            "flow15", "vratio5", "nratio5", "obv_slope60", "vwap_dev60", "lead"]
    D = pd.DataFrame({c: rng.normal(size=n) for c in cols})
    D["vol60"] = rng.gamma(2, 1, n)
    D["wday"] = rng.integers(0, 7, n)
    D["hour"] = rng.integers(0, 24, n)
    D["t"] = t
    D["y"] = rng.integers(0, 2, n)
    return D


def test_volatility_deciles_do_not_move_with_later_months():
    """The deciles were cut on whatever frame was passed, so test-month rows set their own
    cutoffs (council review, 2026-09-30)."""
    from models.btc_15m.rules import events, reference_rows, vol_cutoffs
    D = event_frame()
    ref = reference_rows(D)
    before = events(D, 0)["high volatility (vol60 in top decile)"]
    D2 = D.copy(); D2.loc[~ref, "vol60"] *= 10.0
    after = events(D2, 0)["high volatility (vol60 in top decile)"]
    assert (before[ref] == after[ref]).all()
    cut = vol_cutoffs(D[ref])
    test = D[~ref]
    assert (events(test, 0, cut)["high volatility (vol60 in top decile)"] == (test.vol60.values > cut[1])).all()


def test_a_rule_mined_as_up_that_scores_down_is_not_stable():
    import pandas as pd
    from models.btc_15m.patterns import score_masks
    from models.btc_15m.rules import is_stable, month_agreement
    D = event_frame(n_months=4)
    m = np.zeros(len(D), bool); m[::4] = True
    D.loc[m, "y"] = 0                                     # the rule fires and the window goes down every month
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    agree, tot, _ = month_agreement(m, D.y.values, month, sorted(month.unique()), +1)
    assert tot == 4 and agree == 0 and not is_stable(agree, tot, +1)
    rows = score_masks([("r", m)], D, [+0.05])
    assert rows[0][9] == ""                               # never "stable", although it is consistently down
    assert score_masks([("r", m)], D, [-0.05])[0][9] == "stable"


def test_reference_direction_needs_firings():
    from models.btc_15m.rules import is_stable, reference_sign
    y = np.array([1, 0] * 50); ref = np.zeros(100, bool); ref[:50] = True
    m = np.zeros(100, bool); m[60:] = True                # never fires in the reference rows
    assert reference_sign(m, y, ref) == 0 and not is_stable(5, 5, 0)


def test_day_pvalue_is_zero_not_one_for_an_identical_deviation_every_day():
    """Zero spread across days made the clustered SE zero, and the function returned p = 1
    for the most consistent effect possible (found 2026-10-01 while testing stability)."""
    t = 900 * np.arange(960)                     # ten days
    assert day_pvalue(np.zeros(960), t, 0.4) == 0.0
    assert day_pvalue(np.full(960, 0.4), t, 0.4) == 1.0
