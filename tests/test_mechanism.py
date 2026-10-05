import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from models.btc_15m import mechanism as M
from models.btc_15m import mechanism_tables as T
from models.btc_15m.features import HISTORY, Series, features_all

ROOT = Path(__file__).resolve().parent.parent


# ---------------- event selection ----------------

def test_first_in_window_keeps_the_first_firing_and_waits_the_full_gap():
    i = np.array([10, 11, 12, 39, 40, 41, 70, 71])
    keep = M.first_in_window(i, 30)
    assert i[keep].tolist() == [10, 40, 70]                  # 39 is 29 minutes after 10: blocked; 40 is 30 after: allowed
    assert M.first_in_window(np.array([], dtype=int), 30).tolist() == []


def test_a_blocked_firing_does_not_extend_the_block():
    i = np.array([0, 20, 40])                                # 20 is blocked; 40 is 40 after the kept event, not 20 after 20
    assert i[M.first_in_window(i, 30)].tolist() == [0, 40]


def masks_of(n, **fires):
    out = {k: np.zeros(n, bool) for k in M.SIX}
    for k, pos in fires.items():
        out[k][pos] = True
    return out


def test_event_sets_dedupe_each_slice_and_the_union_separately():
    n = 200
    i = np.arange(n)
    masks = masks_of(n, drop5=[10, 50], rsi_lo=[20, 90], high4h=[120])
    sets, direction, ambiguous = M.event_sets(masks, i)
    assert sets["drop5"].tolist() == [10, 50]
    assert sets["rsi_lo"].tolist() == [20, 90]
    assert sets["union"].tolist() == [10, 50, 90, 120]       # the rsi_lo firing at 20 is inside the 30 minutes after 10
    assert direction[10] == 1 and direction[120] == -1 and direction[0] == 0 and ambiguous == 0


def test_a_minute_where_both_directions_fire_is_nobodys_event():
    n = 100
    masks = masks_of(n, drop5=[10, 60], rise5=[10])
    sets, direction, ambiguous = M.event_sets(masks, np.arange(n))
    assert ambiguous == 1 and direction[10] == 0
    assert sets["drop5"].tolist() == [60] and sets["rise5"].tolist() == [] and sets["union"].tolist() == [60]


def test_recent_any_covers_the_minute_and_the_window_before_it():
    fire = np.zeros(100, bool)
    fire[40] = True
    r = M.recent_any(fire, 30)
    assert not r[39] and r[40] and r[69] and not r[70]       # 40 itself through 40 + 29
    assert not M.recent_any(np.zeros(5, bool), 30).any()


def synthetic_series(n_min, drops=(), seed=0, hour_shift=0):
    rng = np.random.default_rng(seed)
    t0 = 1_700_000_000 - 1_700_000_000 % 900 + 3600 * hour_shift
    ret = rng.normal(0, 5e-4, n_min)
    for at in drops:
        ret[at:at + 5] = -0.002                              # 20 bp a minute for five minutes: far past 3 sd
    close = 50_000 * np.exp(np.cumsum(ret))
    open_ = np.concatenate([[close[0]], close[:-1]])
    vol = rng.gamma(2, 1, n_min)
    return pd.DataFrame({"t": t0 + 60 * np.arange(n_min), "open": open_, "high": np.maximum(open_, close) * 1.0002,
                         "low": np.minimum(open_, close) * 0.9998, "close": close, "volume": vol,
                         "trades": rng.integers(50, 500, n_min).astype(float), "taker_buy": vol * rng.uniform(0.3, 0.7, n_min), "ok": True})


def seconds_for(frame, seed=1):
    """A per-second table whose second-level price runs from each minute's open to its close."""
    rng = np.random.default_rng(seed)
    n = len(frame)
    sec = (frame.t.values[:, None] + np.arange(60)[None, :]).ravel()
    o, c = frame.open.values[:, None], frame.close.values[:, None]
    price = (o + (c - o) * (np.arange(60)[None, :] / 59.0)).ravel()
    qty = rng.uniform(0.5, 1.5, n * 60)
    sign = np.where(rng.random(n * 60) < 0.5, -1.0, 1.0)
    big = rng.random(n * 60) < 0.02
    return pd.DataFrame({"sec": sec, "vol": price * qty, "qty": qty, "svol": sign * price * qty, "n": 2.0,
                         "big_n": big.astype(float), "big_svol": np.where(big, sign * price * qty, 0.0)})


def test_the_six_masks_are_the_librarys_own_definitions():
    s = Series(synthetic_series(HISTORY + 400, drops=(1700,)))
    D = features_all(s)
    m = M.six_masks(D, (0.0, 1e9))
    v = D.vol60.values + 1e-9
    assert (m["drop5"] == (D.ret5.values < -3 * v * np.sqrt(5))).all()
    assert (m["rise5"] == (D.ret5.values > 3 * v * np.sqrt(5))).all()
    assert (m["low4h"] == (D.rangepos.values <= 0.02)).all() and (m["high4h"] == (D.rangepos.values >= 0.98)).all()
    assert (m["rsi_lo"] == (D.rsi14.values < 25)).all() and (m["rsi_hi"] == (D.rsi14.values > 75)).all()
    assert m["drop5"].any()                                   # the planted drop fires it


# ---------------- controls ----------------

def test_match_controls_share_the_stratum_come_from_the_pool_and_never_repeat_when_the_pool_is_big():
    rng = np.random.default_rng(0)
    n = 2000
    hour = rng.integers(0, 24, n)
    decile = rng.integers(0, 10, n)
    events = np.arange(0, 40)
    pool = np.arange(100, n)
    c, replaced = M.match_controls(hour, decile, events, pool, rng)
    ok = c >= 0
    assert ok.sum() > 0
    assert (hour[c[ok]] == hour[events[ok]]).all() and (decile[c[ok]] == decile[events[ok]]).all()
    assert np.isin(c[ok], pool).all()
    assert len(set(c[ok].tolist())) == ok.sum() and replaced == 0


def test_match_controls_reuse_a_small_pool_and_report_it_and_flag_an_empty_stratum():
    rng = np.random.default_rng(0)
    hour = np.array([1, 1, 1, 1, 2])
    decile = np.zeros(5, int)
    c, replaced = M.match_controls(hour, decile, np.array([0, 1, 2]), np.array([3]), rng)    # three events, one eligible row in the stratum
    assert c.tolist() == [3, 3, 3] and replaced == 3
    c2, _ = M.match_controls(hour, decile, np.array([0]), np.array([4]), rng)                # no eligible row at hour 1
    assert c2.tolist() == [-1]


def test_vol_decile_uses_the_given_edges():
    edges = np.arange(1, 10, dtype=float)
    assert M.vol_decile(np.array([0.5, 1.0, 5.5, 9.0, 20.0]), edges).tolist() == [0, 1, 5, 9, 9]


# ---------------- per-second table ----------------

def test_seccum_sums_cover_the_half_open_range_and_vwap_is_notional_over_quantity():
    r = pd.DataFrame({"sec": [10, 11, 13], "vol": [100.0, 220.0, 400.0], "qty": [1.0, 2.0, 4.0], "svol": [100.0, -220.0, 0.0],
                      "n": [1.0, 1.0, 2.0], "big_n": [0.0, 1.0, 0.0], "big_svol": [0.0, -220.0, 0.0]})
    c = M.SecCum(r)
    s = c.sums(np.array([10, 11]), np.array([13, 14]))
    assert s["vol"].tolist() == [320.0, 620.0] and s["n"].tolist() == [2.0, 3.0]            # [10,13) excludes second 13
    assert c.vwap(np.array([10]), np.array([12]))[0] == pytest.approx(320.0 / 3.0)
    assert np.isnan(c.vwap(np.array([20]), np.array([30]))[0])                                # no trades


def test_flow_bins_are_signed_imbalance_per_bin_and_nan_when_empty():
    sec = np.arange(0, 200)
    r = pd.DataFrame({"sec": sec, "vol": 10.0, "qty": 1.0, "svol": np.where(sec < 5, 10.0, -5.0), "n": 1.0, "big_n": 0.0, "big_svol": 0.0})
    F = M.flow_bins(M.SecCum(r), np.array([0]), edges=[0, 1, 5, 10, 400])
    assert F[0, 0] == 1.0 and F[0, 1] == 1.0 and F[0, 2] == -0.5 and F[0, 3] == -0.5       # the last bin has data only up to second 199
    assert np.isnan(M.flow_bins(M.SecCum(r), np.array([5000]), edges=[0, 1])[0, 0])


def test_minute_flow_reads_only_the_minute_before_and_the_previous_day_for_the_baseline():
    sec = np.arange(0, 2 * 86400)
    n = np.where((sec >= 86400 + 600 - 60) & (sec < 86400 + 600), 3.0, 1.0)
    big = np.where((sec >= 86400 + 600 - 60) & (sec < 86400 + 600) & (sec % 4 == 0), 1.0, 0.0)       # 15 large trades in the event minute
    r = pd.DataFrame({"sec": sec, "vol": 10.0, "qty": 1.0, "svol": 6.0, "n": n, "big_n": big, "big_svol": 0.0})
    mf = M.minute_flow(M.SecCum(r), np.array([86400 + 600]))
    assert mf["imb"][0] == pytest.approx(0.6)
    assert mf["nratio"][0] == pytest.approx(3.0)             # 180 trades in the minute against 60 per minute before it
    assert mf["big"][0] == pytest.approx(15.0 / 180.0)


def test_path_windows_trail_the_lag_up_to_sixty_seconds():
    sec = np.arange(0, 4000)
    price = sec.astype(float) + 1.0
    r = pd.DataFrame({"sec": sec, "vol": price, "qty": 1.0, "svol": 0.0, "n": 1.0, "big_n": 0.0, "big_svol": 0.0})
    P = M.path_prices(M.SecCum(r).vwap, np.array([0]), lags=[(1, "1"), (10, "10"), (120, "120")])
    assert P[0, 0] == 1.0                                    # second 0 only
    assert P[0, 1] == pytest.approx(5.5)                     # seconds 0..9
    assert P[0, 2] == pytest.approx(np.mean(np.arange(60, 120) + 1.0))   # the minute ending at 120, not the whole two minutes


# ---------------- labels and orientation ----------------

def test_embargo_labels_enter_g_minutes_later_and_exit_at_minute_g_plus_h_minus_one():
    price_by_minute = np.array([100.0, 101, 102, 103, 99, 98, 97, 96])
    sec = np.arange(len(price_by_minute) * 60)
    price = np.repeat(price_by_minute, 60)
    r = pd.DataFrame({"sec": sec, "vol": price, "qty": 1.0})
    class V:
        sec_ = r.sec.values
        def __call__(self, a, b):
            i, j = np.searchsorted(self.sec_, a), np.searchsorted(self.sec_, b)
            cv = np.concatenate([[0.0], np.cumsum(r.vol.values)])
            q = (j - i).astype(float)
            return np.where(q > 0, (cv[j] - cv[i]) / np.where(q > 0, q, 1), np.nan)
    T0 = np.array([0])
    assert M.embargo_up(V(), T0, 0, 3)[0] == 1.0             # minute 0 (100) to minute 2 (102)
    assert M.embargo_up(V(), T0, 1, 3)[0] == 1.0             # minute 1 (101) to minute 3 (103)
    assert M.embargo_up(V(), T0, 2, 3)[0] == 0.0             # minute 2 (102) to minute 4 (99)
    assert np.isnan(M.embargo_up(V(), T0, 2, 30)[0])         # the exit minute has no trades


def test_orient_complements_after_an_up_move_and_keeps_missing_values_missing():
    x = np.array([1.0, 0.0, np.nan, 1.0])
    d = np.array([1, 1, 1, -1])
    out = M.orient(x, d)
    assert out[:2].tolist() == [1.0, 0.0] and np.isnan(out[2]) and out[3] == 0.0


def test_path_in_basis_points_is_positive_when_the_price_reverses():
    P = np.array([[101.0], [99.0], [99.0], [101.0]])
    p0 = np.array([100.0] * 4)
    d = np.array([1, 1, -1, -1])                             # down-move events expect up, up-move events expect down
    assert M.path_bp(P, p0, d)[:, 0].tolist() == pytest.approx([100.0, -100.0, 100.0, -100.0])


def test_terciles_split_by_the_reference_distribution_and_flag_missing():
    ref = np.arange(30, dtype=float)
    out = M.tercile(np.array([0.0, 9.0, 10.0, 15.0, 20.0, 29.0, np.nan]), ref)
    assert out.tolist() == [0, 0, 1, 1, 2, 2, -1]


# ---------------- pooling and the rule ----------------

def planted(years=(2020, 2021, 2022), n=600, effect=0.10, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for y in years:
        for kind in (True, False):
            p = 0.5 + (effect if kind else 0.0)
            rows.append(pd.DataFrame({"year": y, "is_event": kind, "pair": np.arange(n), "t": 1_600_000_000 + (y - 2020) * 31_536_000 + np.arange(n) * 3600 * 7,
                                      "m_union": True, "lp_15": (rng.random(n) < p).astype(float)}))
    F = pd.concat(rows, ignore_index=True)
    return F, {y: g for y, g in F.groupby("year")}


def test_the_pooled_contrast_recovers_a_planted_effect_and_no_effect():
    F, Fy = planted(effect=0.10)
    c = T.cell(Fy, "union", "lp_15")
    assert c["years"] == 3 and c["lo"] < 0.10 < c["hi"] and c["lo"] > 0 and c["held"] == 3
    F0, Fy0 = planted(effect=0.0, seed=3)
    c0 = T.cell(Fy0, "union", "lp_15")
    assert c0["lo"] < 0 < c0["hi"]


def test_a_slice_year_with_too_few_events_is_not_scored():
    _, Fy = planted(n=60)                                    # 60 events a year, under the 100 required
    assert T.cell(Fy, "union", "lp_15") is None


def test_the_difference_between_two_subsets_pools_their_independent_errors():
    F, Fy = planted(n=900, effect=0.10)
    Fy = {y: g.assign(half=np.arange(len(g)) % 2 == 0) for y, g in Fy.items()}
    c = T.diff_cell(Fy, "union", "lp_15", lambda d: d.half, lambda d: ~d.half)
    assert c["lo"] < 0 < c["hi"]                             # the two halves carry the same effect


def test_retention_class_compares_the_whole_interval_with_half_of_the_reference():
    ref = {"mu": 0.08, "lo": 0.06, "hi": 0.10}
    assert T.retention_class({"mu": 0.01, "lo": -0.01, "hi": 0.03}, ref) == "under half"
    assert T.retention_class({"mu": 0.07, "lo": 0.05, "hi": 0.09}, ref) == "over half"
    assert T.retention_class({"mu": 0.04, "lo": 0.00, "hi": 0.08}, ref) == "unresolved"
    assert T.retention_class({"mu": 0.04, "lo": 0.0, "hi": 0.08}, {"mu": -0.01, "lo": -0.03, "hi": 0.01}) == "no reversal"


def rule(**kw):
    base = dict(a1=["unresolved"] * 3, a2_share=0.2, a3=[(0.05, 0.0, 0.1, 0.06)] * 3, b_embargo=["unresolved"] * 3,
                b1_lo={"x": 1.0, "y": 1.0, "z": 1.0}, b3_lo={"p": -1.0, "q": -1.0})
    base.update(kw)
    return T.apply_rule(**base)


def test_the_rule_names_a_when_the_embargo_keeps_little_and_the_path_is_done_in_a_minute():
    r = rule(a1=["under half", "under half", "unresolved"], a2_share=0.9)
    assert r["A_supported"] and not r["B_supported"] and r["verdict"].startswith("A supported")


def test_the_rule_names_b_when_the_embargo_keeps_most_flow_is_extreme_and_recovery_grows():
    r = rule(b_embargo=["over half", "over half", "over half"], b3_lo={"p": 0.1, "q": 0.2})
    assert r["B_supported"] and not r["A_supported"] and r["verdict"].startswith("B supported")


def test_the_rule_says_unidentified_when_the_patterns_conflict_or_neither_holds():
    both = rule(a1=["under half"] * 3, a2_share=0.9, b_embargo=["over half"] * 3, b3_lo={"p": 0.1, "q": 0.2})
    assert both["verdict"] == "unidentified with this data"
    assert rule()["verdict"] == "unidentified with this data"
    # one criterion of B missing is not enough: flow is extreme and the embargo keeps most, but recovery does not grow
    assert rule(b_embargo=["over half"] * 3)["verdict"] == "unidentified with this data"
    # a path that is complete in a minute is not enough for A without the embargo
    assert rule(a2_share=0.95)["verdict"] == "unidentified with this data"


def test_the_third_check_of_a_corroborates_but_does_not_decide():
    far_only = [(0.0, -0.03, 0.03, 0.08)] * 3                # near half shows nothing, far half carries it
    r = rule(a1=["under half"] * 3, a2_share=0.9, a3=far_only)
    assert r["A3"] and r["A_supported"]
    no_corroboration = rule(a1=["under half"] * 3, a2_share=0.9, a3=[(0.06, 0.02, 0.1, 0.07)] * 3)
    assert not no_corroboration["A3"] and no_corroboration["A_supported"]


def test_the_thresholds_in_the_doc_are_the_ones_the_code_uses():
    text = (ROOT / "docs" / "horizons.md").read_text(encoding="utf-8")
    assert T.PATH_COMPLETE_SHARE == 0.8 and "four fifths" in text
    assert T.HORIZONS_NEEDED == 2 and "two of the three horizons" in text
    section = text[text.index("## The mechanism"):]
    marker = section.find("<!-- table:mechanism_embargo:start -->")        # absent in the commit that fixed the rule before the run
    assert section.index("Decision rule") < (marker if marker >= 0 else len(section)), "the rule must be stated before the tables"


# ---------------- a whole synthetic year ----------------

def build(seed=0):
    frame = synthetic_series(HISTORY + 6500, drops=(2200, 3300, 4400, 5300, 6300), seed=seed)
    series = Series(frame)
    D = features_all(series)
    cum = M.SecCum(seconds_for(frame))
    edges = np.quantile(D.vol60.values, np.linspace(0.1, 0.9, 9))
    return series, D, cum, edges


def test_a_built_year_has_one_matched_control_per_event_and_no_contaminated_controls():
    series, D, cum, edges = build()
    f, st = M.build_year(series, D, cum, edges, np.random.default_rng(0), 2023)
    assert len(f) > 0 and st["events"]["drop5"] >= 3
    ev, ct = f[f.is_event].set_index("pair"), f[~f.is_event].set_index("pair")
    assert (ev.index == ct.index).all() and len(ev) == len(ct)
    assert (ev.hour == ct.hour).all()                        # same hour of day
    assert (ev.dir == ct.dir).all()                          # the control carries the event's orientation
    fired = np.zeros(len(series.c), bool)
    masks = M.six_masks(D, (float(edges[0]), float(edges[-1])))
    fired[D.i.values[np.any([masks[k] for k in M.SIX], axis=0)]] = True
    recent = M.recent_any(fired, M.BLOCK_MIN)
    assert not recent[ct.i.values].any()                     # no control fired, or sits in the 30 minutes after a firing
    assert fired[ev[ev.m_union].i.values].all()
    u = np.sort(ev[ev.m_union].i.values)
    assert (np.diff(u) >= M.BLOCK_MIN).all()                 # union events are 30 minutes apart
    d = ev.dir.values
    assert set(np.unique(d)) <= {-1, 1}
    for k in M.SLICES:                                       # a control belongs to the slices of its event
        assert (ev[f"m_{k}"].values == ct[f"m_{k}"].values).all()


def test_building_a_year_twice_gives_the_identical_frame():
    series, D, cum, edges = build()
    a, _ = M.build_year(series, D, cum, edges, np.random.default_rng(7), 2023)
    b, _ = M.build_year(series, D, cum, edges, np.random.default_rng(7), 2023)
    assert a.equals(b)


def test_the_built_frame_labels_agree_with_a_direct_computation():
    series, D, cum, edges = build()
    f, _ = M.build_year(series, D, cum, edges, np.random.default_rng(0), 2023)
    row = f[f.is_event & f.m_drop5].iloc[0]
    i, d = int(row.i), int(row.dir)
    up = float(series.c[i + 14] >= series.o[i])
    assert row.lp_15 == (up if d > 0 else 1 - up)
    T0 = series.t[i]
    entry, exit_ = cum.vwap(T0 + 60, T0 + 120)[()], cum.vwap(T0 + 60 * 15, T0 + 60 * 16)[()]
    up1 = float(exit_ >= entry)
    assert row.vw1_15 == (up1 if d > 0 else 1 - up1)
    assert row.path_8 == pytest.approx(d * (cum.vwap(T0 + 1740, T0 + 1800)[()] / series.c[i - 1] - 1) * 1e4)
    s = cum.sums(T0 - 60, T0)
    assert row.ev_imb == pytest.approx(-d * s["svol"][()] / s["vol"][()])


# ---------------- the data-root override ----------------

def test_the_data_root_override_moves_every_raw_reader_and_not_the_feature_cache():
    code = ("from models.btc_15m import data, ticks, derivatives, venues, features\n"
            "print(data.CACHE.as_posix(), ticks.CACHE.as_posix(), derivatives.CACHE.as_posix(), venues.CACHE.as_posix(), features.CACHE_DIR.as_posix())")
    env_default = {k: v for k, v in os.environ.items() if k != "LAB_DATA_ROOT"}
    default = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env_default, capture_output=True, text=True).stdout.split()
    assert default == ["data/binance_klines", "data/binance_ticks", "data/binance_futures", "data/venues", "data/feature_cache"]
    over = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env={**env_default, "LAB_DATA_ROOT": "elsewhere"}, capture_output=True, text=True).stdout.split()
    assert over == ["elsewhere/binance_klines", "elsewhere/binance_ticks", "elsewhere/binance_futures", "elsewhere/venues", "data/feature_cache"]


def test_the_study_refuses_to_download_when_raw_files_are_missing(tmp_path, monkeypatch):
    from models.btc_15m import data, ticks
    monkeypatch.setattr(data, "CACHE", tmp_path)
    monkeypatch.setattr(ticks, "CACHE", tmp_path)
    with pytest.raises(FileNotFoundError):
        T.require_files("2026-01", "2026-02")
    assert not list(tmp_path.iterdir())                      # nothing was written
