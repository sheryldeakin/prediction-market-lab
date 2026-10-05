import numpy as np
import pandas as pd

from models.btc_15m.calendar_study import (CELLS, FAMILIES, Block, Pool, PoolBlocks, adjusted_p, cell_masks, day_starts,
                                           family_max, month_codes, rule_rows, score_pool, slice_masks, slice_matrix, slice_stats, summarise)
from models.btc_15m.features import HISTORY, features_all
from models.btc_15m.stats import cluster_diff_pvalue
from tests.test_horizons import flat


def ts(s: str) -> int:
    return int(pd.Timestamp(s, tz="UTC").timestamp())


def names_true(masks, family, t):
    """The slice names of a family that hold for a single timestamp."""
    return [n for n, m in masks[family].items() if m[0]]


def at(s):
    return slice_masks(np.array([ts(s)]))


# ---------------- slice assignments ----------------

def test_hour_weekday_and_month_follow_utc():
    m = at("2026-10-05 13:45")                                  # a Monday
    assert names_true(m, "hour", 0) == ["13:00"]
    assert names_true(m, "weekday", 0) == ["Mon"]
    assert names_true(m, "month", 0) == ["Oct"]
    assert names_true(at("2026-10-04 23:45"), "weekday", 0) == ["Sun"]         # a minute before Monday, still Sunday
    assert names_true(at("2026-10-04 23:45"), "hour", 0) == ["23:00"]
    assert names_true(at("2026-01-01 00:00"), "month", 0) == ["Jan"]
    assert names_true(at("2025-12-31 23:45"), "month", 0) == ["Dec"]


def test_session_boundaries_belong_to_the_later_session():
    expect = {"2026-10-05 00:00": "Asia 00-08", "2026-10-05 07:45": "Asia 00-08", "2026-10-05 08:00": "Europe 08-13",
              "2026-10-05 12:45": "Europe 08-13", "2026-10-05 13:00": "overlap 13-17", "2026-10-05 16:45": "overlap 13-17",
              "2026-10-05 17:00": "US 17-21", "2026-10-05 20:45": "US 17-21", "2026-10-05 21:00": "late 21-24", "2026-10-05 23:45": "late 21-24"}
    for stamp, name in expect.items():
        assert names_true(at(stamp), "session", 0) == [name], stamp


def test_partition_families_give_every_time_exactly_one_slice():
    t = ts("2025-01-01 00:00") + 900 * np.arange(96 * 400)
    masks = slice_masks(t)
    for fam in ("hour", "weekday", "session", "month"):
        counts = sum(m.astype(int) for m in masks[fam].values())
        assert (counts == 1).all(), fam
    assert set(masks) == set(FAMILIES)


def test_the_1330_slot_is_the_quarter_hour_starting_at_1330():
    key = "US equity open window (13:30 +15 min)"
    for stamp, expect in (("2026-10-05 13:15", False), ("2026-10-05 13:30", True), ("2026-10-05 13:44", True), ("2026-10-05 13:45", False), ("2026-10-05 14:30", False)):
        assert bool(at(stamp)["event slot"][key][0]) is expect, stamp
    close = "US equity close window (20:00 +15 min)"
    assert at("2026-10-05 20:00")["event slot"][close][0] and at("2026-10-05 20:14")["event slot"][close][0]
    assert not at("2026-10-05 19:45")["event slot"][close][0] and not at("2026-10-05 20:15")["event slot"][close][0]


def test_funding_hour_and_funding_window():
    hours, window = "funding hours (00, 08, 16)", "funding settlement window (00:00, 08:00, 16:00 +15 min)"
    for h in (0, 8, 16):
        assert at(f"2026-10-05 {h:02d}:45")["event slot"][hours][0]
        assert at(f"2026-10-05 {h:02d}:00")["event slot"][window][0]
        assert at(f"2026-10-05 {h:02d}:14")["event slot"][window][0]
        assert not at(f"2026-10-05 {h:02d}:15")["event slot"][window][0]
    assert not at("2026-10-05 07:45")["event slot"][hours][0] and not at("2026-10-05 07:45")["event slot"][window][0]
    assert not at("2026-10-05 12:00")["event slot"][hours][0]


def test_first_hour_of_the_week_and_the_weekend():
    first, weekend = "first hour of the week (Mon 00-01)", "weekend (Sat, Sun)"
    for stamp in ("2026-10-05 00:00", "2026-10-05 00:45"):
        assert at(stamp)["event slot"][first][0], stamp
    for stamp in ("2026-10-05 01:00", "2026-10-04 23:45", "2026-10-06 00:00"):          # after it, the Sunday before, the next Tuesday
        assert not at(stamp)["event slot"][first][0], stamp
    assert at("2026-10-03 00:00")["event slot"][weekend][0] and at("2026-10-04 23:45")["event slot"][weekend][0]
    assert not at("2026-10-02 23:45")["event slot"][weekend][0] and not at("2026-10-05 00:00")["event slot"][weekend][0]


def test_slice_matrix_columns_line_up_with_names_and_families():
    t = ts("2025-03-01 00:00") + 900 * np.arange(500)
    M, names, fam = slice_matrix(t)
    assert M.shape == (500, len(names)) == (500, len(fam))
    assert len(set(names)) == len(names)
    assert set(fam) == set(range(len(FAMILIES)))
    assert list(fam) == sorted(fam)                           # columns are grouped by family


# ---------------- the statistic ----------------

def test_slice_stats_is_the_clustered_regression_scaled_by_the_share_outside():
    rng = np.random.default_rng(3)
    t = ts("2024-01-01 00:00") + 900 * np.arange(96 * 40)
    day_effect = np.repeat(rng.normal(0, 0.1, 40), 96)
    hit = (rng.random(len(t)) < 0.5 + day_effect).astype(float)
    M = np.column_stack([slice_masks(t)["hour"]["05:00"], slice_masks(t)["weekday"]["Sat"]])
    dev, se, n1 = slice_stats(hit, M, day_starts(t), min_n=10)
    for k in range(2):
        b, s, _ = cluster_diff_pvalue(M[:, k], hit, t)
        share = M[:, k].mean()
        assert np.isclose(dev[k], (1 - share) * b) and np.isclose(se[k], (1 - share) * s)
        assert np.isclose(dev[k], hit[M[:, k]].mean() - hit.mean())          # inside minus the overall mean
        assert n1[k] == M[:, k].sum()


def test_slice_stats_leaves_out_slices_that_are_too_thin():
    t = ts("2024-01-01 00:00") + 900 * np.arange(96 * 10)
    hit = np.ones(len(t))
    M = np.column_stack([np.arange(len(t)) < 5, np.ones(len(t), dtype=bool)])        # five rows inside; and everything inside
    dev, se, _ = slice_stats(hit, M, day_starts(t))
    assert np.isnan(dev).all() and np.isnan(se).all()


# ---------------- the null is read family by family ----------------

def test_family_max_takes_the_largest_within_each_family_only():
    absz = np.zeros((2, 4)); absz[0] = [1.0, 5.0, 2.0, 0.5]; absz[1] = [3.0, 1.0, 0.5, 4.0]
    fam = np.array([0, 0, 1, 1])
    out = family_max(absz, fam)
    assert out.shape == (2, len(FAMILIES))
    assert out[:, 0].tolist() == [5.0, 3.0] and out[:, 1].tolist() == [2.0, 4.0]
    assert (out[:, 2:] == 0).all()                            # families with no slice contribute nothing


def test_a_slice_is_judged_against_its_own_familys_null_not_the_search_as_a_whole():
    absz = np.zeros((100, 4)); absz[:, 0] = np.linspace(0.1, 1.0, 100); absz[:, 2] = np.linspace(4.0, 6.0, 100)
    fam = np.array([0, 1, 2, 2])
    nm = family_max(absz, fam)
    small_family_p = adjusted_p(2.5, nm[:, 0])                # the hour-like family never gets near 2.5
    big_family_p = adjusted_p(2.5, nm[:, 2])                  # the session-like family always exceeds it
    assert small_family_p == 1 / 101 and big_family_p == 1.0
    assert adjusted_p(2.5, np.concatenate([nm[:, 0], nm[:, 2]])) > small_family_p      # pooling the families would have hidden it


# ---------------- planted effects, end to end on synthetic years ----------------

def synthetic_year(year: int, p_weekend: float, seed: int, days: int = 100):
    """Windows from the first Monday of January for `days` days; every window is called up, so a hit is the label."""
    start = pd.Timestamp(f"{year}-01-01", tz="UTC")
    start += pd.Timedelta(days=(7 - start.dayofweek) % 7)
    t = int(start.timestamp()) + 900 * np.arange(96 * days)
    rng = np.random.default_rng(seed)
    wk = slice_masks(t)["event slot"]["weekend (Sat, Sun)"]
    y = (rng.random(len(t)) < np.where(wk, p_weekend, 0.5)).astype(int)
    pool = Pool(y, month_codes(t))
    return PoolBlocks(pool, [Block("rule", pool, np.arange(len(t)), np.ones(len(t), dtype=bool), t)])


def run_synthetic(p_weekend: float, seed: int, years=(2019, 2020, 2021, 2022), runs: int = 40):
    rng = np.random.default_rng(seed)
    res = {}
    for k, y in enumerate(years):
        pb = synthetic_year(y, p_weekend, seed + k)
        res[y] = score_pool(pb, rng, runs)["rule"]
    P = pb.blocks[0].prepare()
    return summarise("rule", list(years), res, P["names"], P["fam"], hold_years=len(years))


def test_a_planted_weekend_effect_clears_the_null_and_holds_every_year():
    T = run_synthetic(0.65, seed=10)
    w = T[T["slice"] == "weekend (Sat, Sun)"].iloc[0]
    assert w.clears and w.holds and w.years_held == 4 == w.years
    assert 0.08 < w.pooled < 0.13                              # 0.15 inside the slice, times the 5/7 outside it
    assert w.p_adj <= 1 / 41 + 1e-12                           # the floor with 40 runs
    assert not T[(T.family == "hour")].clears.any()            # the effect sits in every hour equally: no hour stands out


def test_without_an_effect_nothing_stands_out_and_the_best_slice_is_not_extreme():
    T = run_synthetic(0.5, seed=20)
    assert T.p_adj.min() > 0.02                                # a chance clear would need a 1-in-40 floor value
    assert not T.holds.any()


def test_a_year_that_leans_the_other_way_is_counted_and_blocks_holds():
    runs, years = 40, (2019, 2020, 2021, 2022)
    rng = np.random.default_rng(5)
    res = {}
    for k, (y, pw) in enumerate(zip(years, (0.65, 0.65, 0.65, 0.45))):          # the last year leans the other way
        res[y] = score_pool(synthetic_year(y, pw, 30 + k), rng, runs)["rule"]
    P = synthetic_year(2019, 0.5, 0).blocks[0].prepare()
    T = summarise("rule", list(years), res, P["names"], P["fam"], hold_years=len(years))
    w = T[T["slice"] == "weekend (Sat, Sun)"].iloc[0]
    assert w.years_held == 3 and w.years == 4
    assert w.pooled > 0 and not w.holds                        # three years of four is not held when all four are required


# ---------------- the rows the study decides on ----------------

def test_rule_rows_label_and_calls_come_from_the_window_and_earlier_candles():
    s = flat()
    D = features_all(s)
    rows, t, y, rev_up, lead_up = rule_rows(s, D)
    i = D.i.values[rows]
    assert (t % 900 == 0).all() and len(rows) > 10
    assert (i >= HISTORY).all() and (i + 15 <= len(s.c)).all()
    assert (y == (s.c[i + 14] >= s.o[i])).all()                # the window label
    assert (lead_up == (s.c[i + 2] >= s.o[i])).all()           # the close of minute 2: nothing from minute 3 on
    assert (rev_up == (D.win1.values[rows] < 0)).all()         # the previous window closed down: call up


def test_windows_with_a_missing_candle_are_left_out():
    s = flat()
    s.ok[HISTORY + 20] = False                                 # inside the window opening at HISTORY + 15
    D = features_all(s)
    rows, t, *_ = rule_rows(s, D)
    i = D.i.values[rows]
    assert HISTORY in i and (HISTORY + 15) not in i


def test_cell_masks_are_the_six_cells_with_opposite_calls_for_mirrors():
    s = flat()
    D = features_all(s)
    cm = cell_masks(D)
    assert list(cm) == list(CELLS)
    calls = [cm[c][1] for c in CELLS]
    assert calls == [True, False, True, False, True, False]    # drops, lows and weak RSI call up; the mirrors call down
    assert not (cm[CELLS[0]][0] & cm[CELLS[1]][0]).any() and not (cm[CELLS[2]][0] & cm[CELLS[3]][0]).any()
    assert all(m.shape == (len(D),) for m, _ in cm.values())
