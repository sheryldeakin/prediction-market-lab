import numpy as np
import pandas as pd
import pytest

from models.btc_15m import confidence_by_minute as C


def probs(*per_window):
    """Windows as columns: each argument is one window's probabilities at minutes 0, 1, 2."""
    return np.array(per_window, dtype=float).T


# ---------------- first crossing ----------------

def test_first_crossing_takes_the_first_minute_at_the_threshold_on_that_minutes_side():
    p = probs(
        [0.50, 0.62, 0.90],    # 0: crosses at minute 1, up
        [0.52, 0.53, 0.54],    # 1: never reaches 0.55
        [0.40, 0.70, 0.95],    # 2: crosses at minute 0, down (0.60 on the down side)
        [0.50, 0.50, 0.50],    # 3: exactly 0.5 throughout
        [0.52, 0.30, 0.20],    # 4: crosses at minute 1, down, and later minutes do not move the call
        [0.54, 0.54, 0.80],    # 5: crosses at minute 2, up
    )
    minute, side = C.first_crossing(p, 0.55)
    assert minute.tolist() == [1, -1, 0, -1, 1, 2]
    assert side.tolist() == [1, -1, 0, -1, 0, 1]


def test_an_exact_half_is_not_a_call_even_at_a_threshold_of_one_half():
    p = probs([0.50, 0.50, 0.50], [0.50, 0.51, 0.50])
    minute, side = C.first_crossing(p, 0.5)
    assert minute.tolist() == [-1, 1] and side.tolist() == [-1, 1]


def test_a_probability_at_the_threshold_counts_whichever_side_it_is_on():
    p = probs([0.45, 0.50, 0.50], [0.55, 0.50, 0.50], [0.4499, 0.5, 0.5])
    minute, side = C.first_crossing(p, 0.55)
    assert minute.tolist() == [0, 0, 0] and side.tolist() == [0, 1, 0]
    # 1 - 0.0257 is 0.9742999999999999 in floating point, a hair under the 0.9743 it means; without the tolerance it would miss the call
    assert 1 - 0.0257 < 0.9743
    minute, side = C.first_crossing(probs([0.0257, 0.5, 0.5]), 0.9743)
    assert minute.tolist() == [0] and side.tolist() == [0]


def test_the_rules_call_is_its_side_at_the_crossing_minute_and_not_at_any_other():
    rule = probs([0.4, 0.7, 0.3], [0.6, 0.4, 0.6], [0.5, 0.5, 0.5])
    minute = np.array([1, 2, -1])
    assert C.rule_side_at(rule, minute).tolist() == [1, 1, -1]       # window 0 at minute 1: up; window 1 at minute 2: up; no call: -1
    assert C.rule_side_at(rule, np.array([0, 0, 0])).tolist() == [0, 1, 0]     # an exact 0.5 calls down, as accuracy in the walk-forward does


# ---------------- paired accuracy and no-call accounting ----------------

def day_times(n_days, per_day):
    return np.repeat(np.arange(n_days) * 86400, per_day) + np.tile(np.arange(per_day) * 900, n_days)


def test_paired_difference_on_a_case_with_a_known_answer():
    # eight windows over four days; window 7 is never called.
    t = day_times(4, 2)
    y = np.array([1, 0, 1, 1, 0, 0, 1, 1])
    minute = np.array([1, 1, 2, 2, 3, 3, 4, -1])
    pred = np.array([1, 0, 1, 0, 0, 1, 1, -1])      # hits on windows 0,1,2,4,6 -> 5 of 7
    rule = np.array([0, 0, 1, 1, 1, 1, 1, -1])      # hits on windows 1,2,3,6 -> 4 of 7
    r = C.paired_accuracy(y, t, minute, pred, rule, n_boot=200, n_draws=500)
    assert r["windows"] == 8 and r["called"] == 7
    assert r["share_called"] == pytest.approx(7 / 8)
    assert r["acc_predictor"] == pytest.approx(5 / 7) and r["acc_rule"] == pytest.approx(4 / 7)
    assert r["diff"] == pytest.approx(1 / 7)
    assert r["mean_minute"] == pytest.approx(16 / 7) and r["median_minute"] == 2
    assert r["low"] <= r["diff"] <= r["high"] and 0 < r["p"] <= 1


def test_the_minute_filter_keeps_the_windows_called_inside_it_and_the_share_stays_on_all_windows():
    t = day_times(4, 2)
    y = np.array([1, 0, 1, 1, 0, 0, 1, 1])
    minute = np.array([1, 1, 2, 2, 3, 3, 4, -1])
    pred = np.array([1, 0, 1, 0, 0, 1, 1, -1])
    rule = np.array([0, 0, 1, 1, 1, 1, 1, -1])
    r = C.paired_accuracy(y, t, minute, pred, rule, minutes=(1, 3), n_boot=200, n_draws=500)
    assert r["windows"] == 8 and r["called"] == 6                   # window 6 (minute 4) and the uncalled one are out
    assert r["share_called"] == pytest.approx(6 / 8)
    assert r["acc_predictor"] == pytest.approx(4 / 6) and r["acc_rule"] == pytest.approx(3 / 6)


def test_no_calls_gives_a_share_of_zero_no_accuracy_and_a_p_of_one_without_dropping_the_windows():
    t = day_times(3, 2)
    y = np.array([1, 0, 1, 1, 0, 0])
    none = np.full(6, -1)
    r = C.paired_accuracy(y, t, none, none, none, n_boot=50, n_draws=50)
    assert r["windows"] == 6 and r["called"] == 0 and r["share_called"] == 0.0
    assert np.isnan(r["diff"]) and np.isnan(r["acc_predictor"]) and r["p"] == 1.0


def test_the_rule_against_itself_differs_by_exactly_zero_with_a_p_of_one():
    rng = np.random.default_rng(0)
    t = day_times(30, 8)
    y = rng.integers(0, 2, len(t))
    side = rng.integers(0, 2, len(t))
    minute = rng.integers(0, 15, len(t))
    r = C.paired_accuracy(y, t, minute, side, side, n_boot=100, n_draws=100)
    assert r["diff"] == 0.0 and r["p"] == 1.0 and r["low"] == 0.0 and r["high"] == 0.0


def test_day_flip_p_is_small_for_a_steady_gain_and_one_for_nothing():
    t = day_times(60, 4)
    assert C.day_flip_p(np.ones(len(t)), t, n_draws=2000) < 0.01
    assert C.day_flip_p(np.zeros(len(t)), t, n_draws=500) == 1.0
    mixed = np.tile([1.0, -1.0], len(t) // 2)                         # every day sums to zero
    assert C.day_flip_p(mixed, t, n_draws=500) == 1.0


def test_holm_on_a_known_vector():
    assert C.holm([0.01, 0.04, 0.03, 0.2]) == pytest.approx([0.04, 0.09, 0.09, 0.2])
    assert C.holm([0.5]) == [0.5]


# ---------------- calibration ----------------

def test_calibration_reports_share_and_hit_rate_of_the_called_side_per_minute():
    p = probs([0.80, 0.60, 0.9], [0.30, 0.50, 0.1], [0.55, 0.70, 0.5], [0.20, 0.45, 0.5])
    y = np.array([1, 1, 0, 0])
    c = C.calibration(p, y, 0.75)
    assert c.minute.tolist() == [0, 1, 2]
    # minute 0: called-side probabilities .8, .7, .55, .8 -> windows 0 and 3 are at 0.75 or more; window 0 up (y=1, hit), window 3 down (y=0, hit)
    assert c.loc[0, "n_called"] == 2 and c.loc[0, "share"] == pytest.approx(2 / 4) and c.loc[0, "hit"] == pytest.approx(1.0)
    # minute 1: .6, .5, .7, .55 -> none at 0.75
    assert c.loc[1, "n_called"] == 0 and c.loc[1, "share"] == 0.0 and np.isnan(c.loc[1, "hit"])
    # minute 2: window 0 at .9 calls up and y=1 (hit); window 1 at .1 calls down and y=1 (miss); windows 2 and 3 are exact 0.5, no call
    assert c.loc[2, "n_called"] == 2 and c.loc[2, "hit"] == pytest.approx(0.5)


def test_calibration_at_the_threshold_of_a_constant_half_never_calls():
    p = np.full((3, 5), 0.5)
    c = C.calibration(p, np.array([1, 0, 1, 0, 1]), 0.55)
    assert (c.n_called == 0).all() and (c.share == 0).all()


# ---------------- stacking, cells and engagement ----------------

def frames(n=40, minutes=15, seed=0, shift=0):
    rng = np.random.default_rng(seed)
    t = np.arange(n) * 900 + 1_700_000_000
    y = rng.integers(0, 2, n)
    out = {}
    for k in range(minutes):
        cols = C.slot_columns(k)
        df = pd.DataFrame({"t": t, "y": y})
        for c in cols.values():
            df[c] = np.clip(0.5 + 0.1 * (2 * y - 1) * (k / 14) + rng.normal(0, 0.1, n), 0.01, 0.99)
        df["majority"] = 0.4987
        out[k] = df.iloc[shift:]
    return out


def test_slot_columns_name_eight_predictors_at_every_minute():
    for k in (0, 1, 7, 14):
        cols = C.slot_columns(k)
        assert list(cols) == [s for s, *_ in C.SLOTS] and len(cols) == 8
    assert C.slot_columns(0)["rule"] == "prev-window" and C.slot_columns(5)["rule"] == "lead-z"
    assert C.slot_columns(0)["other one-feature"] == "win1-logistic" and C.slot_columns(5)["other one-feature"] == "lead-only"


def test_stack_joins_on_t_and_refuses_a_set_of_windows_that_differs_between_minutes():
    f = frames()
    t, y, P, rule = C.stack(f)
    assert P["xgb-all"].shape == (15, 40) and rule.shape == (15, 40) and len(t) == len(y) == 40
    assert np.array_equal(rule[0], f[0]["prev-window"].values) and np.array_equal(rule[3], f[3]["lead-z"].values)
    f[3] = f[3].iloc[1:]
    with pytest.raises(AssertionError):
        C.stack(f)


def test_cells_cover_eight_predictors_by_six_thresholds_and_pass_the_engagement_checks():
    f = frames(n=480)
    t, y, P, rule = C.stack(f)
    cells = C.run_cells(t, y, P, rule, n_boot=50, n_draws=200)
    assert len(cells) == 48 and set(cells.threshold) == set(C.THRESHOLDS)
    assert (cells.p_holm >= cells.p).all() and (cells.p_holm <= 1).all()
    own = cells[cells.predictor == "rule"]
    assert own.called.max() > 0 and (own["diff"].dropna() == 0).all()
    assert (cells[cells.predictor == "majority"].called == 0).all()
    C.check_engaged(cells)


def test_engagement_check_fails_when_the_rule_differs_from_itself_or_the_constant_predictor_calls():
    f = frames(n=480)
    t, y, P, rule = C.stack(f)
    cells = C.run_cells(t, y, P, rule, n_boot=50, n_draws=200)
    bad = cells.copy()
    bad.loc[bad.predictor == "rule", "diff"] = 0.01
    with pytest.raises(AssertionError):
        C.check_engaged(bad)
    bad = cells.copy()
    bad.loc[bad.predictor == "majority", "called"] = 3
    with pytest.raises(AssertionError):
        C.check_engaged(bad)
