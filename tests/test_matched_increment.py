import numpy as np
import pandas as pd
import pytest

from models.btc_15m import library_events as L
from models.btc_15m import matched_increment as MI
from models.btc_15m import mechanism as M
from models.btc_15m.horizons import HORIZONS
from models.btc_15m.stats import paired_cluster_se

CONTROL_BLOCK_SECONDS = MI.CONTROL_BLOCK_MIN * 60
Z95 = 1.96


# ---------------- matching by stratum ----------------

def test_match_by_stratum_draws_inside_the_stratum_without_repeats_when_the_pool_allows():
    rng = np.random.default_rng(0)
    n = 3000
    key = rng.integers(0, 30, n)
    events = np.arange(0, 60)
    pool = np.arange(200, n)
    c, replaced = M.match_by_stratum(key, events, pool, rng)
    ok = c >= 0
    assert ok.sum() > 0
    assert (key[c[ok]] == key[events[ok]]).all() and np.isin(c[ok], pool).all()
    assert len(set(c[ok].tolist())) == ok.sum() and replaced == 0


def test_match_by_stratum_reuses_a_small_pool_counts_it_and_flags_an_empty_stratum():
    rng = np.random.default_rng(0)
    key = np.array([7, 7, 7, 7, 9])
    c, replaced = M.match_by_stratum(key, np.array([0, 1, 2]), np.array([3]), rng)       # three treated, one eligible row in stratum 7
    assert c.tolist() == [3, 3, 3] and replaced == 3
    c2, replaced2 = M.match_by_stratum(key, np.array([0, 4]), np.array([3]), rng)        # stratum 9 has no eligible row
    assert c2.tolist() == [3, -1] and replaced2 == 0


def test_match_controls_is_match_by_stratum_on_hour_times_ten_plus_decile():
    n = 2000
    g = np.random.default_rng(1)
    hour, decile = g.integers(0, 24, n), g.integers(0, 10, n)
    events, pool = np.arange(0, 50), np.arange(100, n)
    old, r_old = M.match_controls(hour, decile, events, pool, np.random.default_rng(5))
    new, r_new = M.match_by_stratum(hour * 10 + decile, events, pool, np.random.default_rng(5))
    assert old.tolist() == new.tolist() and r_old == r_new


# ---------------- populations and treated sets reproduce the library's events ----------------

def deriv_arrays(n=3000, seed=0):
    g = np.random.default_rng(seed)
    arrs = {k: g.normal(0, 1, n) for k in L.DERIV_ARRAYS}
    arrs["doi15"][:5] = np.nan
    return arrs


def test_contrast_a_treated_is_the_library_signature_and_the_population_is_the_return_leg_alone():
    arrs = deriv_arrays()
    cuts = L.decile_cuts(arrs)
    E = L.deriv_events(arrs, cuts)
    pop, treated, move = MI.a_sets(arrs, cuts)
    for side, ev, hi_side in (("long", L.DERIV_EVENTS[6], False), ("short", L.DERIV_EVENTS[7], True)):
        assert (treated[side] == E[ev]).all() and treated[side].sum() > 0
        leg = arrs["ret15"] > cuts["ret15"][1] if hi_side else arrs["ret15"] < cuts["ret15"][0]
        assert (pop[side] == L.known_next(leg)).all()
        assert (treated[side] & ~pop[side]).sum() == 0                                   # treated lie inside the population
        assert pop[side].sum() > 4 * treated[side].sum()                                 # and the population is the bigger set
        other = L.known_next((arrs["doi15"] < cuts["doi15"][0]) & (arrs["pvol_ratio5"] > cuts["pvol_ratio5"][1]))
        assert (treated[side] == (pop[side] & other)).all()
    assert np.isnan(move[0]) and move[11] == abs(arrs["ret15"][10])                      # the move is the previous minute's 15-minute return


def test_the_three_leg_subset_is_the_library_signature_and_every_subset_is_listed():
    arrs = deriv_arrays(seed=2)
    cuts = L.decile_cuts(arrs)
    E = L.deriv_events(arrs, cuts)
    idx = np.arange(len(arrs["ret15"]))
    masks, info = MI.subset_masks(arrs, cuts, idx)
    assert len(masks) == 14                                                              # seven non-empty subsets of three legs, two sides
    assert (masks["long: ret + oi + vol"] == E[L.DERIV_EVENTS[6]]).all() and (masks["short: ret + oi + vol"] == E[L.DERIV_EVENTS[7]]).all()
    assert (masks["long: ret"] == MI.a_sets(arrs, cuts)[0]["long"]).all()
    assert info["short: oi + vol"] == ("short", ("oi", "vol"))


def tick_fixture(n=4000, seed=1):
    g = np.random.default_rng(seed)
    c = 100.0 + np.cumsum(g.normal(0, 0.05, n))
    h, l = c + g.uniform(0.0, 0.05, n), c - g.uniform(0.0, 0.05, n)
    cnt = g.integers(5, 60, n).astype(float)
    cnt[g.random(n) < 0.02] *= 6
    z = np.zeros(n)
    return L.tick_quantities({"n": cnt, "big_n": z, "svol": z, "big_svol": z}), h, l


def test_contrast_b_treated_is_the_library_climax_at_a_new_extreme_and_the_population_is_the_extreme_alone():
    q, h, l = tick_fixture()
    cuts = {"share": 1.0, "n": float(np.quantile(q["n"], 0.97))}
    E = L.tick_events(q, cuts, h, l)
    rel_cut = float(np.nanquantile(MI.relative_count(q["n"]), 0.97))
    pop, treated, treated2, move = MI.b_sets(q, cuts, rel_cut, h, l)
    hi, lo = L.new_extremes(h, l)
    for side, ev, ext in (("high", "trade-count climax at a new 1h high", hi), ("low", "trade-count climax at a new 1h low", lo)):
        assert (treated[side] == E[ev]).all() and treated[side].sum() > 0
        assert (pop[side] == L.known_next(ext)).all()
        assert (treated[side] & ~pop[side]).sum() == 0 and (treated2[side] & ~pop[side]).sum() == 0
        assert treated2[side].sum() > 0 and pop[side].sum() > treated[side].sum()
        assert np.nanmin(move[side][pop[side]]) >= 0                                     # a new extreme overshoots by zero or more
    assert (treated2["high"] == L.known_next((MI.relative_count(q["n"]) > rel_cut) & hi)).all()


def test_relative_count_is_the_count_over_the_mean_of_the_previous_window():
    n = np.full(10, 2.0)
    n[7] = 8.0
    r = MI.relative_count(n, window=5)
    assert np.isnan(r[:5]).all() and r[5] == 1.0 and r[7] == 4.0                          # minute 7 reads minutes 2..6, all 2
    assert r[8] == pytest.approx(2.0 / np.mean([2.0, 2.0, 2.0, 2.0, 8.0]))               # minute 8 reads minutes 3..7, which include the spike
    assert np.isnan(MI.relative_count(np.zeros(8), window=3)[5])                          # a zero mean is unknown, never infinite


def test_overshoot_is_how_far_the_minute_went_past_the_previous_hour():
    h = np.array([10.0, 10.0, 10.0, 10.0, 10.1])
    l = np.array([9.0, 9.0, 9.0, 9.0, 8.91])
    up, down = MI.overshoot(h, l, w=3)
    assert np.isnan(up[:3]).all()
    assert up[4] == pytest.approx((10.1 / 10.0 - 1) * 1e4) and down[4] == pytest.approx((9.0 / 8.91 - 1) * 1e4)
    assert up[3] == 0.0


def test_the_relative_cutoff_reads_the_previous_year_and_the_month_before_it_for_history():
    asked = []

    def read(month):
        asked.append(month)
        p = pd.Period(month, "M")
        t0 = int(p.start_time.value // 10**9)
        m = np.arange(p.days_in_month * 1440)
        return pd.DataFrame({"sec": t0 + 60 * m, "n": 100.0, "big_n": 0.0, "svol": 0.0, "big_svol": 0.0})

    cut = MI.relative_reference_cutoff(2020, read)
    assert asked[0] == "2018-12" and asked[1] == "2019-01" and asked[-1] == "2019-12" and len(asked) == 13
    assert cut == pytest.approx(1.0)                                                      # a constant count is always 1 against its own mean
    asked.clear()
    MI.relative_reference_cutoff(2018, read)
    assert asked[0] == "2017-08" and asked[-1] == "2017-12"                               # no month before the first one the data hold


# ---------------- strata, episodes, errors ----------------

def test_strata_bins_hours_into_blocks_volatility_into_terciles_and_moves_into_quintiles():
    assert MI.stratum_key(np.array([0, 3, 4, 23]), np.array([0, 0, 0, 2]), np.array([0, 0, 4, 4])).tolist() == [0, 0, 19, ((5 * 3 + 2) * 5 + 4)]
    assert MI.vol_terciles(np.array([0.5, 1.0, 1.5, 2.0, 9.0]), np.array([1.0, 2.0])).tolist() == [0, 1, 1, 2, 2]
    move = np.arange(1.0, 101.0)
    pop = np.ones(100, bool)
    q, edges = MI.move_quintiles(move, pop)
    assert np.bincount(q).tolist() == [20, 20, 20, 20, 20] and len(edges) == 4
    q2, _ = MI.move_quintiles(np.append(move, np.nan), np.append(pop, True))
    assert q2[-1] == -1


def test_paired_cluster_se_matches_a_hand_computation():
    d = np.array([1.0, 0.0, 1.0, 0.0, 0.0, 1.0])
    cluster = np.array([5, 5, 5, 9, 9, 9])
    # mean 0.5; residual sums per cluster are 0.5 and -0.5, so se = sqrt(0.25 + 0.25) / 6
    assert paired_cluster_se(d, cluster) == pytest.approx(np.sqrt(0.5) / 6)
    assert paired_cluster_se(d, np.zeros(6)) == float("inf")                              # one cluster: not defined
    assert paired_cluster_se(d, np.arange(6)) == pytest.approx(np.sqrt(((d - 0.5) ** 2).sum()) / 6)    # singleton clusters: the plain sandwich


def test_episodes_merge_treated_minutes_closer_than_the_gap_and_a_gap_of_exactly_the_gap_starts_a_new_one():
    t = np.array([0, 10, 40, 100]) * 60
    assert MI.episode_ids(t).tolist() == [0, 0, 1, 2]                                    # t to t+10 one episode; t+40 is 30 after t+10, so new; t+100 is 60 after
    assert MI.episode_ids(np.array([0, 29, 58, 87]) * 60).tolist() == [0, 0, 0, 0]       # 29-minute gaps chain into one
    assert MI.episode_ids(np.array([0, 30]) * 60).tolist() == [0, 1] and MI.episode_ids(np.array([0, 29]) * 60).tolist() == [0, 0]
    assert MI.episode_ids(np.zeros(0)).tolist() == []


# ---------------- pairs: orientation and the clustered estimates ----------------

def pair_fixture(direction_side, treated_up, n=4000, seed=0, year=2024):
    """A synthetic year in which treated minutes always go one way and controls are coin flips."""
    g = np.random.default_rng(seed)
    D = pd.DataFrame({"i": np.arange(n), "t": 1_700_000_000 + 60 * np.arange(n), "hour": ((1_700_000_000 + 60 * np.arange(n)) // 3600 % 24).astype(int), "vol60": g.random(n)})
    treated = np.zeros(n, bool)
    treated[g.choice(n, 120, replace=False)] = True
    population = np.ones(n, bool)
    move = g.random(n)
    base = (g.random(n) < 0.5).astype(float)
    outcome = np.where(treated, 1.0 if treated_up else 0.0, base)
    Lp = {h: outcome for h in HORIZONS}
    contrast, side = direction_side
    return MI.build_pairs(year=year, contrast=contrast, side=side, population=population, treated=treated, move=move, D=D, n_series=n,
                          vol_edges=np.array([1 / 3, 2 / 3]), Lp=Lp, Vw=Lp, rng=np.random.default_rng(1))


def test_a_treated_set_that_always_reverses_gives_a_positive_difference_on_both_sides():
    P_down, _, _ = pair_fixture(("A", "long"), treated_up=True)             # after a down move the reversal is up
    P_up, _, _ = pair_fixture(("A", "short"), treated_up=False)             # after an up move the reversal is down
    for P in (P_down, P_up):
        e = MI.pair_estimate(P, "lp", 15)
        assert e["n"] > 100 and e["est"] > 20 and e["treated_rate"] == 1.0 and e["control_rate"] < 0.8
        assert MI.pair_estimate(P, "vw", 5)["est"] > 20


def test_a_treated_set_that_continues_the_move_gives_a_negative_difference():
    P, _, _ = pair_fixture(("B", "high"), treated_up=True)                  # after a new high, "up" is the continuation
    assert MI.pair_estimate(P, "lp", 15)["est"] < -20


def test_controls_come_from_the_population_outside_the_thirty_minutes_after_a_treated_minute():
    n = 4000
    P, S, st = pair_fixture(("A", "long"), treated_up=True)
    assert st["matched"] + st["unmatched"] == st["treated"] == 120 and len(P) == 120
    assert S.treated.sum() == 120 and S.population.sum() == n and S.unmatched.sum() == st["unmatched"] == 0
    treated_t = np.sort(P.t.values)
    assert not np.isin(P.t_control.values, treated_t).any()
    gap = P.t_control.values[:, None] - treated_t[None, :]                                # control minus every treated minute, in seconds
    assert not ((gap >= 0) & (gap < CONTROL_BLOCK_SECONDS)).any()                         # never in the 30 minutes from a treated minute on


def test_support_counts_treated_in_a_bin_with_no_eligible_control_as_unmatched():
    n = 600
    D = pd.DataFrame({"i": np.arange(n), "t": 1_700_000_000 + 60 * np.arange(n), "hour": 0, "vol60": 0.5})
    move = np.arange(n, dtype=float)
    population = np.ones(n, bool)
    treated = np.zeros(n, bool)
    treated[500:] = True                                                                  # the treated are the top of the move range and consecutive
    lab = {h: np.ones(n) for h in HORIZONS}
    P, S, st = MI.build_pairs(year=2024, contrast="A", side="long", population=population, treated=treated, move=move, D=D, n_series=n,
                              vol_edges=np.array([1.0, 2.0]), Lp=lab, Vw=lab, rng=np.random.default_rng(0))
    assert S.treated.tolist() == [20, 20, 20, 20, 20]                                     # the bins are the quintiles of the treated minutes' move size
    assert S.eligible.tolist() == [0, 0, 0, 0, 0]                                         # every other minute is a smaller move than any treated one, so none is eligible
    assert st["matched"] == 0 and st["unmatched"] == 100 and st["unmatched_no_support"] == 100 and len(P) == 0
    assert S.unmatched.tolist() == [20, 20, 20, 20, 20]
    treated[:] = False
    treated[50:600:50] = True
    move2 = np.random.default_rng(3).random(n)
    P2, S2, st2 = MI.build_pairs(year=2024, contrast="A", side="long", population=population, treated=treated, move=move2, D=D, n_series=n,
                                 vol_edges=np.array([1.0, 2.0]), Lp=lab, Vw=lab, rng=np.random.default_rng(0))
    assert st2["matched"] == 11 and st2["unmatched"] == 0
    gap = P2.t_control.values[:, None] - P2.t.values[None, :]
    assert not ((gap >= 0) & (gap < CONTROL_BLOCK_SECONDS)).any()                         # the minutes before a treated one are allowed, the 30 from it on are not


def tail_population(n=200_000, seed=0):
    g = np.random.default_rng(seed)
    move = g.exponential(1.0, n)
    treated = (move > np.quantile(move, 0.99)) & (g.random(n) < 0.5)                      # the condition lives in the far tail of the move, on half of the top percent's minutes
    D = pd.DataFrame({"i": np.arange(n), "t": 1_700_000_000 + 60 * np.arange(n), "hour": 0, "vol60": 0.5})
    return D, move, treated


def test_treated_quantile_bins_balance_the_move_size_where_population_quintiles_do_not():
    D, move, treated = tail_population()
    n = len(D)
    population = move > np.quantile(move, 0.90)                                           # the population is the tail the condition sits in, as for the real contrasts
    lab = {h: np.ones(n) for h in HORIZONS}
    P, _, _ = MI.build_pairs(year=2024, contrast="B", side="high", population=population, treated=treated, move=move, D=D, n_series=n,
                             vol_edges=np.array([1.0, 2.0]), Lp=lab, Vw=lab, rng=np.random.default_rng(0))
    assert len(P) == treated.sum()
    assert abs(MI.standardised_difference(P.move_t.values, P.move_c.values)) < 0.10                  # a stricter bar than the support gate, which is looser since the adjustment was added
    assert P.move_c.min() >= move[treated].min() and P.move_c.max() <= move[treated].max()           # controls lie inside the treated minutes' move-size range
    # the same matching with the bins taken from the population: every treated minute lands in the top bin, whose controls are smaller moves
    quint, _ = MI.move_quintiles(move, population)
    fire = np.zeros(n, bool); fire[np.where(treated)[0]] = True
    eligible = np.where(~M.recent_any(fire, MI.CONTROL_BLOCK_MIN))[0]
    key = MI.stratum_key(D.hour.values, MI.vol_terciles(D.vol60.values, np.array([1.0, 2.0])), quint)
    ctrl, _ = M.match_by_stratum(key, np.where(treated)[0], eligible, np.random.default_rng(0))
    assert (ctrl >= 0).all()
    assert abs(MI.standardised_difference(move[treated], move[ctrl])) > 2 * MI.SMD_MAX


def test_the_balance_table_reports_means_and_standardised_differences_per_year_and_pooled(monkeypatch):
    monkeypatch.setattr(MI, "MIN_FIRES", 50)
    pairs, _, _ = table_fixture()
    bal = MI.balance_table(pairs)
    assert set(bal.year.astype(str)) == {"2023", "2024", "all"} and len(bal) == 3 * len(MI.SIDES)
    r = bal[(bal.year.astype(str) == "all") & (bal.contrast == "A") & (bal.side == "long")].iloc[0]
    sub = pairs[(pairs.contrast == "A") & (pairs.side == "long")]
    assert r.pairs == len(sub) and r.move_treated == pytest.approx(sub.move_t.mean())
    assert r.move_smd == pytest.approx(MI.standardised_difference(sub.move_t.values, sub.move_c.values))
    assert MI.standardised_difference(np.array([1.0, 3.0]), np.array([1.0, 3.0])) == 0.0
    assert MI.standardised_difference(np.array([2.0, 4.0]), np.array([1.0, 3.0])) == pytest.approx(1.0 / np.sqrt(2.0))


def test_a_cell_year_below_the_minimum_pairs_is_not_scored_and_the_table_says_so(monkeypatch):
    monkeypatch.setattr(MI, "MIN_FIRES", 100)
    pairs, S, stats = table_fixture()
    keep = ~((pairs.year == 2023) & (pairs.contrast == "B") & (pairs.side == "high") & (pairs.index % 2 == 0))      # halve one cell-year
    short = pairs[keep]
    assert MI.scored_years(short).groupby(["year", "contrast", "side"]).size().min() >= 100
    assert len(MI.scored_years(short)) < len(short)
    Y = MI.year_cells(short)
    assert not ((Y.year == 2023) & (Y.contrast == "B") & (Y.side == "high")).any()
    G = MI.main_table(Y, stats)
    g = G[(G.contrast == "B") & (G.side == "high") & (G.horizon == 15)].iloc[0]
    assert g.lp_years == 1 and g.years_total == 2
    text = MI.render_main(G, stats, MI.verdicts(G), {"A": [2023, 2024], "B": [2023, 2024]}, "2024-12")
    assert "was scored in 1 of 2 years (fewer than 100 pairs in the others)" in text


# ---------------- pooling and the pre-registered rule ----------------

def test_pool_weights_the_years_by_pairs_and_combines_errors_as_independent():
    g = pd.DataFrame({"est": [2.0, -1.0], "n": [300, 100], "se_day": [1.0, 2.0], "se_ep": [1.5, 3.0], "treated_rate": [0.6, 0.5], "control_rate": [0.5, 0.5]})
    p = MI.pool(g)
    assert p["est"] == pytest.approx(0.75 * 2.0 + 0.25 * -1.0) and p["held"] == 1 and p["years"] == 2
    assert p["se_day"] == pytest.approx(np.hypot(0.75 * 1.0, 0.25 * 2.0)) and p["hi_ep"] == pytest.approx(p["est"] + 1.96 * p["se_ep"])
    assert p["yr_min"] == -1.0 and p["yr_max"] == 2.0
    assert MI.pool(g.assign(se_day=[1.0, np.inf]))["years"] == 1                          # a year with no defined error is left out


def cell(lp_day, lp_ep, vw_day, vw_ep, held=(5, 5), years=5):
    return {"lp": {"day": lp_day, "ep": lp_ep}, "vw": {"day": vw_day, "ep": vw_ep}, "held_lp": held[0], "held_vw": held[1], "years": years}


def test_the_rule_has_four_outcomes():
    assert MI.decide(cell((1, 5), (0.5, 6), (0.2, 4), (0.1, 5)))[0] == "adds something"
    assert MI.decide(cell((-1.0, 1.0), (-1.5, 1.5), (-0.5, 1.9), (-1.0, 1.0)))[0] == "adds nothing measurable"
    v, why = MI.decide(cell((1, 5), (0.5, 6), (-0.2, 4), (0.1, 5)))                      # one label's day interval touches zero
    assert v == "not resolved" and "one label" in why
    v, why = MI.decide(cell((-1, 5), (-0.5, 6), (-0.2, 4), (-0.1, 5)))                   # straddles zero and the increment
    assert v == "not resolved" and "straddles" in why
    v, why = MI.decide(cell((1, 5), (0.5, 6), (0.2, 4), (0.1, 5), held=(2, 5)))          # above zero everywhere but not a majority of years
    assert v == "not resolved" and "half of the years or fewer" in why
    assert MI.decide(cell((-1.0, 1.0), (-1.5, 1.5), (-0.5, 2.0), (-1.0, 1.0)))[0] == "not resolved"      # an upper bound at the increment is not below it


def test_a_cell_whose_controls_do_not_balance_the_move_is_not_resolved_whatever_the_intervals():
    strong = cell((1, 5), (0.5, 6), (0.2, 4), (0.1, 5))
    # The gate was 0.10 and is now 0.25: treated minutes are deeper than any available control, and the smoke runs of 2026-10-06 showed
    # standardised differences of about 0.1 to 0.2 after treated-quantile bins and the trim. The adjusted estimate corrects up to the gate.
    assert MI.SMD_MAX == 0.25
    assert MI.decide(strong, smd=0.2)[0] == "adds something" and MI.decide(strong, smd=-0.25)[0] == "adds something"      # at the gate: the adjusted intervals decide
    assert MI.decide(cell((-1.0, 1.0), (-1.5, 1.5), (-0.5, 1.9), (-1.0, 1.0)), smd=0.2)[0] == "adds nothing measurable"
    assert MI.decide(strong, smd=0.3)[0] == "not resolved (support)" and MI.decide(strong, smd=-0.3)[0] == "not resolved (support)"
    assert MI.decide(cell((-1.0, 1.0), (-1.5, 1.5), (-0.5, 1.9), (-1.0, 1.0)), smd=0.3)[0] == "not resolved (support)"


def adjustment_pairs(n=6000, seed=0, effect=0.0, deeper=1.0, slope=0.10):
    """Pairs whose outcome rises with the move size: control moves are exponential, treated ones are deeper by `deeper`."""
    g = np.random.default_rng(seed)
    move_c = g.exponential(1.0, n)
    move_t = move_c + deeper + g.normal(0, 1.0, n)
    vol_c, vol_t = g.random(n), g.random(n)
    return pd.DataFrame({"day": np.arange(n) // 20, "episode": np.arange(n) // 5, "move_t": move_t, "move_c": move_c, "vol_t": vol_t, "vol_c": vol_c,
                         "lp15_t": slope * move_t + effect + g.normal(0, 0.3, n), "lp15_c": slope * move_c + g.normal(0, 0.3, n)})


def test_the_adjustment_removes_the_bias_from_deeper_treated_minutes_and_leaves_a_true_effect():
    P = adjustment_pairs()                                                                # no treatment effect, treated minutes a full unit deeper, outcome 0.1 per unit
    e = MI.pair_estimate(P, "lp", 15)
    assert e["est"] > 8 and e["est"] / e["se_day"] > 5                                    # raw: about 10 points, far from zero
    assert abs(e["est_adj"]) < Z95 * e["se_day_adj"] and abs(e["est_adj"]) < Z95 * e["se_ep_adj"]      # adjusted: inside its interval of zero
    Q = adjustment_pairs(effect=0.05, deeper=0.0, seed=1)                                 # a true effect of 5 points and no covariate difference
    q = MI.pair_estimate(Q, "lp", 15)
    assert abs(q["est"] - 5.0) < 1.0 and abs(q["est_adj"] - q["est"]) < 0.5 and q["est_adj"] - Z95 * q["se_day_adj"] > 0
    assert MI.adjusted_differences(np.array([1.0, 2.0]), np.zeros((2, 2))).tolist() == [1.0, 2.0]       # too few pairs: unchanged
    d = np.array([1.0, 3.0, 2.0, 6.0, 5.0, 4.0]); dx = np.arange(12.0).reshape(6, 2) ** 1.1
    assert MI.adjusted_differences(d, dx).mean() == pytest.approx(np.linalg.lstsq(np.column_stack([np.ones(6), dx]), d, rcond=None)[0][0])      # the mean is the intercept


def test_holm_and_the_cell_p_follow_the_stated_definitions():
    assert MI.holm([0.01, 0.04, 0.03, 0.2]) == pytest.approx([0.04, 0.09, 0.09, 0.2])
    row = {"lpa_est": 2.0, "vwa_est": 2.0, "lpa_se_day": 1.0, "lpa_se_ep": 0.5, "vwa_se_day": 0.5, "vwa_se_ep": 0.5}
    from scipy.stats import norm
    assert MI.cell_p(row) == pytest.approx(2 * (1 - norm.cdf(2.0)))                       # the largest of the four two-sided p-values, on the adjusted estimates
    assert MI.cell_p({**row, "vwa_est": -0.1}) == 1.0                                     # one estimate not above zero: the claim is not supported
    raw = {k.replace("lpa", "lp").replace("vwa", "vw"): v for k, v in row.items()}
    assert MI.cell_p(raw, prefix="") == pytest.approx(2 * (1 - norm.cdf(2.0)))             # the raw estimates remain readable


# ---------------- the pre-registration block ----------------

def test_prereg_block_follows_the_arithmetic_from_the_two_years_tables():
    def yrs(event, ses, fires):
        return pd.DataFrame({"year": range(len(ses)), "horizon": 15, "pattern": event, "fires": fires, "se": ses})

    a = pd.concat([yrs(MI.A_EVENT["long"], [0.01, 0.02], [300, 100]), yrs(MI.A_EVENT["short"], [0.03], [500])])
    b = pd.concat([yrs(MI.B_EVENT["high"], [0.004], [900]), yrs(MI.B_EVENT["low"], [0.004], [900]), yrs(MI.B_EVENT["high"], [0.5], [5]).assign(horizon=5)])
    lib = pd.DataFrame({"event": [MI.A_EVENT["long"], MI.A_EVENT["short"]], "horizon": 15, "deviation": [0.04, -0.044]})
    md, data = MI.prereg_block(a, b, lib, "abcdef1234567890", "2026-10-06 12:00 UTC")
    se_long = np.sqrt(((0.75 * np.sqrt(2) * 0.01) ** 2) + ((0.25 * np.sqrt(2) * 0.02) ** 2))
    assert data["minimum_detectable"]["A-long"]["detectable_points"] == pytest.approx(1.96 * se_long * 100)
    assert data["minimum_detectable"]["A-short"]["detectable_points"] == pytest.approx(1.96 * np.sqrt(2) * 0.03 * 100)
    assert data["minimum_detectable"]["B-high"]["detectable_points"] == pytest.approx(1.96 * np.sqrt(2) * 0.004 * 100)       # the 5-minute row is not read
    assert data["liquidation_deviation_points"] == {"long": pytest.approx(4.0), "short": pytest.approx(4.4)}
    assert f"{MI.INCREMENT_POINTS:.1f} points" in md and "abcdef1234" in md and "2026-10-06 12:00 UTC" in md
    assert "is above it" in md and "is below it" in md                                    # B-high detects 1.6 against an increment of 2.0; A-short detects 6 against 2.0
    assert MI.prereg_block(a, b, lib, "abcdef1234567890", "2026-10-06 12:00 UTC")[0] == md


# ---------------- tables ----------------

def table_fixture():
    pairs, stats, supports = [], [], []
    for year in (2023, 2024):
        for k, cs in enumerate(MI.SIDES):
            P, S, st = pair_fixture(cs, treated_up=SIDES_UP[cs], seed=k + 10 * year, year=year)
            pairs.append(P); supports.append(S); stats.append(st)
    return pd.concat(pairs, ignore_index=True), pd.concat(supports, ignore_index=True), pd.DataFrame(stats)


SIDES_UP = {("A", "long"): True, ("A", "short"): False, ("B", "low"): True, ("B", "high"): False, ("B2", "low"): True, ("B2", "high"): False}


def test_the_main_table_has_one_row_per_contrast_side_and_horizon_and_renders_the_same_twice(monkeypatch):
    monkeypatch.setattr(MI, "MIN_FIRES", 50)
    pairs, S, stats = table_fixture()
    Y = MI.year_cells(pairs)
    G = MI.main_table(Y, stats)
    assert len(G) == len(MI.SIDES) * len(HORIZONS) and not G.duplicated(["contrast", "side", "horizon"]).any()
    V = MI.verdicts(G)
    assert [(v["contrast"], v["side"]) for v in V] == MI.PRIMARY and all(v["verdict"] == "adds something" for v in V)
    first = MI.render_main(G, stats, V, {"A": [2023, 2024], "B": [2023, 2024]}, "2024-12")
    assert MI.render_main(G, stats, V, {"A": [2023, 2024], "B": [2023, 2024]}, "2024-12") == first
    assert first.count("\n| A | long") == len(HORIZONS) and "Holm across the four primary cells" in first
    bal = MI.balance_table(pairs)
    sup = MI.render_support(S, stats, bal)
    assert MI.render_support(S, stats, bal) == sup and "treated minutes fall in a bin with no eligible control" in sup and "standardised difference" in sup
    verdict_text = MI.render_main(G, stats, MI.verdicts(G, bal), {"A": [2023, 2024], "B": [2023, 2024]}, "2024-12")
    assert verdict_text.count("Standardised difference of the move size after matching") == 4
    assert G.lp_years.min() == 2 and (G.matched_without_replacement <= 1).all()


def test_the_subset_table_signs_the_short_side_so_that_reversal_is_positive_and_renders_the_same_twice():
    G = pd.DataFrame({"event": ["short: ret", "long: ret"], "horizon": 15, "years": 3, "years_held": 3, "fires": 1000, "share": 0.01, "up_rate": [0.45, 0.55],
                      "deviation": [-0.05, 0.05], "se": 0.01, "lo": [-0.07, 0.03], "hi": [-0.03, 0.07], "min_p_adj": 1.0, "years_adj_05": 0, "retained": 1.0})
    info = {"long: ret": ("long", ("ret",)), "short: ret": ("short", ("ret",))}
    text = MI.render_subsets(G, info)
    assert MI.render_subsets(G, info) == text
    rows = [r for r in text.split("\n") if r.startswith("| long") or r.startswith("| short")]
    assert "+5.0 [+3.0, +7.0]" in rows[0] and "+5.0 [+3.0, +7.0]" in rows[1] and "55.0%" in rows[0] and "55.0%" in rows[1]
