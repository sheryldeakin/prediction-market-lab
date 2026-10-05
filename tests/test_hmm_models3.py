import numpy as np
import pandas as pd
import pytest
from hmmlearn.hmm import GaussianHMM
from scipy.stats import multivariate_normal

import models.btc_15m.hmm_models2 as H2
import models.btc_15m.hmm_models3 as H
from models.btc_15m.evaluate import add_baseline_columns, make_model
from models.btc_15m.features import HISTORY, Series, dataset
from models.btc_15m.regimes import forward_filter


# ---------------------------------------------------------------- helpers

def two_state_chain(n, stay, seed=0, gap=3.0):
    """Hidden path with per-step stay probability stay[t], emissions N(0,1) or N(gap,1)."""
    rng = np.random.default_rng(seed)
    path = np.zeros(n, int)
    for t in range(1, n):
        path[t] = path[t - 1] if rng.random() < stay[t] else 1 - path[t - 1]
    x = rng.normal(0, 1, n) + gap * path
    return path, x[:, None]


def scaled_gauss_emission(x, means=(0.0, 3.0)):
    B = np.column_stack([np.exp(-0.5 * (x[:, 0] - m) ** 2) for m in means])
    return B / B.max(axis=1, keepdims=True)


# ---------------------------------------------------------------- emissions and the fit

def test_log_emission_matches_scipy_on_a_fitted_model():
    rng = np.random.default_rng(1)
    Z = np.column_stack([rng.normal(0, 1, 400) + (np.arange(400) % 200 > 100) * 2, rng.normal(0, 2, 400)])
    m = GaussianHMM(2, covariance_type="diag", n_iter=20, random_state=0).fit(Z)
    ref = np.column_stack([multivariate_normal(m.means_[j], m.covars_[j]).logpdf(Z) for j in range(2)])
    assert np.allclose(H.log_emission(m, Z), ref)
    B = H.scaled_emission(m, Z)
    assert np.allclose(B.max(axis=1), 1.0)


def test_minute_fit_sees_only_the_rows_in_the_mask():
    rng = np.random.default_rng(2)
    X = rng.normal(size=(3000, 3))
    mask = np.arange(3000) < 2000
    m1, Z1 = H.fit_minute_hmm(X, mask, n_states=2)
    X2 = X.copy(); X2[2000:] = rng.normal(5, 9, size=(1000, 3))             # the test month changes completely
    m2, Z2 = H.fit_minute_hmm(X2, mask, n_states=2)
    assert np.allclose(m1.means_, m2.means_) and np.allclose(m1.transmat_, m2.transmat_)
    assert np.allclose(Z1[:2000], Z2[:2000])


# ---------------------------------------------------------------- (b) transition buckets

def test_transition_buckets_follow_hour_block_and_volatility_tercile():
    vol = np.arange(1.0, 301.0)                                            # 1..300; training terciles at about 100 and 200
    fit = np.ones(300, bool)
    cuts, fill = H.vol_cut_points(vol, fit)
    assert 99 < cuts[0] < 102 and 199 < cuts[1] < 202 and fill == 150.5
    t = np.array([0, 5 * 3600, 6 * 3600, 23 * 3600, 12 * 3600])
    v = np.array([1.0, 150.0, 250.0, 150.0, np.nan])
    b = H.transition_buckets(t, v, cuts, fill)
    #   hour 0, low vol -> block 0 tercile 0; hour 5, mid -> 0,1; hour 6, high -> 1,2; hour 23, mid -> 3,1; hour 12, missing -> filled with the median: 2,1
    assert b.tolist() == [0 * 3 + 0, 0 * 3 + 1, 1 * 3 + 2, 3 * 3 + 1, 2 * 3 + 1]
    assert b.max() < H.HOUR_BUCKETS * H.VOL_BUCKETS


def test_volatility_cut_points_use_only_training_minutes():
    vol = np.concatenate([np.linspace(1, 2, 1000), np.linspace(50, 90, 500)])
    fit = np.arange(1500) < 1000
    c1, f1 = H.vol_cut_points(vol, fit)
    vol2 = vol.copy(); vol2[1000:] = 1e6
    c2, f2 = H.vol_cut_points(vol2, fit)
    assert np.allclose(c1, c2) and f1 == f2


def test_bucketed_forward_with_one_bucket_equals_the_homogeneous_filter():
    rng = np.random.default_rng(3)
    path, x = two_state_chain(1500, np.full(1500, 0.95), seed=3)
    m = GaussianHMM(2, covariance_type="diag", n_iter=30, random_state=0).fit(x)
    ref = forward_filter(m, x)
    alpha, _ = H.forward_bucketed(H.scaled_emission(m, x), m.transmat_[None], np.zeros(len(x), int), m.startprob_)
    assert np.allclose(alpha, ref, atol=1e-9)
    assert np.allclose(alpha.sum(1), 1)


def test_bucketed_filter_is_causal():
    path, x = two_state_chain(800, np.full(800, 0.95), seed=4)
    B = scaled_gauss_emission(x)
    A = np.array([[[0.95, 0.05], [0.05, 0.95]], [[0.6, 0.4], [0.4, 0.6]]])
    bucket = (np.arange(800) % 2).astype(int)
    a1, _ = H.forward_bucketed(B, A, bucket, np.array([0.5, 0.5]))
    B2 = B.copy(); B2[500:] = B2[500:][::-1]
    a2, _ = H.forward_bucketed(B2, A, bucket, np.array([0.5, 0.5]))
    assert np.allclose(a1[:500], a2[:500])


def test_bucket_transitions_recover_a_planted_dependence_and_stay_stochastic():
    n = 40000
    bucket = (np.arange(n) // 500 % 2).astype(int)                         # alternating blocks of two kinds of minutes
    stay = np.where(bucket == 0, 0.98, 0.6)
    path, x = two_state_chain(n, stay, seed=5)
    B = scaled_gauss_emission(x)
    A0 = np.array([[0.8, 0.2], [0.2, 0.8]])
    A, d = H.fit_bucket_transitions(B, bucket, 2, A0, np.array([0.5, 0.5]), rounds=4, prior=20.0)
    assert np.allclose(A.sum(2), 1)
    assert A[0, 0, 0] > 0.93 and A[0, 1, 1] > 0.93                          # the sticky bucket
    assert A[1, 0, 0] < 0.75 and A[1, 1, 1] < 0.75                          # the switchy bucket
    assert d["stay_spread"] > 0.2                                           # the diagnostic the table reports sees it


def test_a_bucket_with_no_minutes_keeps_the_pooled_matrix():
    path, x = two_state_chain(3000, np.full(3000, 0.9), seed=6)
    B = scaled_gauss_emission(x)
    A, d = H.fit_bucket_transitions(B, np.zeros(3000, int), 3, np.array([[0.9, 0.1], [0.1, 0.9]]), np.array([0.5, 0.5]), rounds=2)
    assert np.allclose(A[1], A[0]) and np.allclose(A[2], A[0])
    assert d["bucket_minutes_min"] == 0


# ---------------------------------------------------------------- (c) duration expansion

def test_run_lengths():
    st, ln = H.run_lengths(np.array([0, 0, 1, 1, 1, 2, 0]))
    assert st.tolist() == [0, 1, 2, 0] and ln.tolist() == [2, 3, 1, 1]


def test_duration_model_recovers_fixed_sojourns_and_the_jump_chain():
    path = np.repeat(np.tile([0, 1], 40), 10)                              # 80 runs of exactly ten minutes, alternating
    haz, J = H.duration_model(path, 2, cap=20)
    assert haz.shape == (2, 20)
    assert (haz[:, 9] > 0.85).all()                                        # the run ends at ten (the prior pulls the hazard a little toward 0.1)
    assert (haz[:, :9] < 0.05).all()                                       # and not before
    assert np.allclose(J.diagonal(), 0) and np.allclose(J.sum(1), 1)
    assert J[0, 1] > 0.9 and J[1, 0] > 0.9


def test_duration_hazards_are_clipped_and_the_tail_is_geometric():
    rng = np.random.default_rng(7)
    lengths = rng.geometric(0.01, 300)                                      # mean 100 minutes, most beyond a cap of 30
    path = np.repeat(np.tile([0, 1], 150), lengths)
    haz, _ = H.duration_model(path, 2, cap=30)
    assert (haz >= 1e-4).all() and (haz <= 1 - 1e-4).all()
    assert abs(haz[0, -1] - 0.01) < 0.01 and abs(haz[1, -1] - 0.01) < 0.01


def test_semi_markov_filter_with_constant_hazards_equals_the_homogeneous_chain():
    rng = np.random.default_rng(8)
    K, cap, h = 3, 12, 0.08
    haz = np.full((K, cap), h)
    jump = np.array([[0, 0.7, 0.3], [0.5, 0, 0.5], [0.2, 0.8, 0]])
    A = (1 - h) * np.eye(K) + h * jump                                     # the geometric sojourn is the plain HMM
    B = rng.uniform(0.05, 1.0, size=(600, K))
    pi = np.array([0.5, 0.3, 0.2])
    marg, dur = H.forward_hsmm(B, haz, jump, pi)
    ref, _ = H.forward_bucketed(B, A[None], np.zeros(600, int), pi)
    assert np.allclose(marg, ref, atol=1e-9)
    assert np.allclose(marg.sum(1), 1)
    assert (dur >= 1).all() and (dur <= cap).all()


def test_semi_markov_expected_duration_grows_while_a_state_persists_and_resets_on_a_switch():
    n = 400
    haz = np.full((2, 60), 0.01)
    jump = np.array([[0.0, 1.0], [1.0, 0.0]])
    B = np.full((n, 2), 1e-3)
    B[:150, 0] = 1.0; B[150:300, 1] = 1.0; B[300:, 0] = 1.0
    marg, dur = H.forward_hsmm(B, haz, jump, np.array([0.5, 0.5]))
    assert dur[140] > dur[30] > 1.5                                         # elapsed minutes accumulate
    assert dur[160] < dur[140]                                              # a switch to the other state resets the counter
    assert marg[100, 0] > 0.99 and marg[250, 1] > 0.99


# ---------------------------------------------------------------- (a) window HMM

def cluster_windows(n_blocks=12, per_block=60, seed=9, d=34):
    rng = np.random.default_rng(seed)
    centers = rng.normal(0, 3, size=(3, d))
    labels = np.repeat(np.arange(n_blocks) % 3, per_block)                  # blocks cycle through the three clusters
    X = centers[labels] + rng.normal(0, 1, size=(len(labels), d))
    D = pd.DataFrame(X, columns=[f"f{i}" for i in range(d)])
    D["t"] = 900 * np.arange(len(D)) + 1_700_000_000
    return D, labels


def test_window_posteriors_sum_to_one_and_follow_the_planted_clusters():
    D, labels = cluster_windows()
    cols = [c for c in D.columns if c != "t"]
    fit = np.arange(len(D)) < 500
    P, d = H.window_hmm_posteriors(D, cols, fit, n_states=3, n_components=3)
    assert P.shape == (len(D), 3) and np.allclose(P.sum(1), 1)
    hard = P.argmax(1)
    # windows of one planted cluster share a dominant state, windows of different clusters do not
    for a in range(3):
        for b in range(3):
            if a != b and (labels == a).any() and (labels == b).any():
                assert np.bincount(hard[labels == a], minlength=3).argmax() != np.bincount(hard[labels == b], minlength=3).argmax()
    assert 0 < d["explained"] <= 1 and d["n_states_used"] >= 2


def test_window_hmm_fit_sees_only_training_windows_and_the_filter_is_causal():
    D, _ = cluster_windows()
    cols = [c for c in D.columns if c != "t"]
    fit = np.arange(len(D)) < 500
    P1, d1 = H.window_hmm_posteriors(D, cols, fit, n_states=3, n_components=3)
    D2 = D.copy()
    D2.loc[500:, cols] = np.random.default_rng(0).normal(40, 20, size=(len(D) - 500, len(cols)))     # a different test period
    P2, d2 = H.window_hmm_posteriors(D2, cols, fit, n_states=3, n_components=3)
    assert np.allclose(d1["means"], d2["means"])                                                      # the fit did not move
    assert np.allclose(P1[:500], P2[:500])                                                            # nor did any training posterior
    D3 = D.copy()
    D3.loc[600:, cols] += 7.0                                                                          # change only later windows
    P3, _ = H.window_hmm_posteriors(D3, cols, fit, n_states=3, n_components=3)
    assert np.allclose(P1[:600], P3[:600])                                                            # earlier filtered posteriors unchanged


def test_window_hmm_refuses_windows_out_of_time_order():
    D, _ = cluster_windows(n_blocks=2)
    cols = [c for c in D.columns if c != "t"]
    D = D.iloc[::-1].reset_index(drop=True)
    with pytest.raises(AssertionError):
        H.window_hmm_posteriors(D, cols, np.ones(len(D), bool), n_states=2, n_components=3)


# ---------------------------------------------------------------- mixtures and joint columns

class MeanModel:
    def fit(self, X, y):
        self.m = float(np.mean(y)); return self
    def predict_proba(self, X):
        return np.column_stack([np.full(len(X), 1 - self.m), np.full(len(X), self.m)])


def test_mixture_of_experts_mixes_by_posterior_and_falls_back_for_small_states():
    n_tr = 1003
    # state 0: 500 windows with a 20% up-rate; state 1: 500 windows with an 80% up-rate; state 2: three windows
    y = np.concatenate([np.tile([0, 0, 0, 0, 1], 100), np.tile([1, 1, 1, 1, 0], 100), [0, 1, 0], np.zeros(10, int)])
    P_tr = np.zeros((n_tr, 3)); P_tr[:500, 0] = 1; P_tr[500:1000, 1] = 1; P_tr[1000:, 2] = 1
    D = pd.DataFrame({"x": np.zeros(n_tr + 10)})
    tr = np.arange(n_tr + 10) < n_tr
    te = ~tr
    P_te = np.zeros((10, 3)); P_te[:5, 0] = 1; P_te[5:, 1] = 0.5; P_te[5:, 2] = 0.5
    fallback = np.full(10, 0.3)
    pred, fell = H.mixture_of_experts(D, tr, te, y, ["x"], P_tr, P_te, fallback, lambda kind: MeanModel(), min_n=50)
    assert fell == 1                                                       # state 2 has three training windows
    assert np.allclose(pred[:5], 0.2)                                      # the state-0 expert
    assert np.allclose(pred[5:], 0.5 * 0.8 + 0.5 * 0.3)                    # half the state-1 expert, half the fallback


def test_joint_columns_route_the_minute_posterior_into_the_days_regime():
    P = np.array([[0.2, 0.5, 0.3], [1.0, 0.0, 0.0]])
    onehot = np.array([[0.0, 1.0], [1.0, 0.0]])
    J, names = H.joint_columns(P, onehot, ["low", "high"])
    assert J.shape == (2, 6) and len(names) == 6
    assert np.allclose(J.sum(1), 1)                                        # the joint posterior sums to one
    assert np.allclose(J[0].reshape(3, 2)[:, 1], P[0]) and np.allclose(J[0].reshape(3, 2)[:, 0], 0)
    assert names[0] == "joint: minute state 0 x low"


# ---------------------------------------------------------------- scoring, sentences, the written table

def synthetic_scores(oracle=H.A_FEAT, seed=0):
    rng = np.random.default_rng(seed)
    n = 90 * 96
    t = 1_700_006_400 + 900 * np.arange(n)
    y = rng.integers(0, 2, n)
    preds = {r: np.clip(rng.uniform(0.3, 0.7, n), 0, 1) for r in H.ROW_IDS}
    preds[oracle] = np.where(rng.random(n) < 0.9, y, 1 - y) * 0.8 + 0.1
    bp = rng.uniform(0.3, 0.7, n)
    return H.score_rows(3, preds, y, t, bp, n_draws=200), preds


def test_adds_something_needs_both_intervals_above_zero():
    assert H.adds_something(0.1, 0.2)
    assert not H.adds_something(0.1, -0.2)
    assert not H.adds_something(-0.1, 0.2)
    assert not H.adds_something(-0.5, -0.2)                                # significantly worse is not an addition


def test_score_rows_marks_only_the_planted_variant_as_adding_something():
    rows, _ = synthetic_scores()
    R = pd.DataFrame(rows)
    assert R.variant.tolist() == ["baseline", "reference", "control", "a", "a", "b", "c", "d", "d"]
    adds = R[R.adds.notna() & R.adds.astype(bool)]
    assert adds.model.tolist() == [H.A_FEAT[1]]
    assert R.loc[R.variant == "reference", "vs_ref"].isna().all()          # the reference is not compared with itself


def test_sentences_name_the_rows_that_meet_the_test_and_the_bounds_of_those_that_do_not():
    rows, _ = synthetic_scores()
    text = H.sentences(pd.DataFrame(rows))
    assert "met by 1 of the 6 variant rows" in text
    assert H.A_FEAT[1] in text.split("The day-block interval alone")[0]
    assert "close with the upper end" in text and "What these windows could detect" in text
    none_rows, _ = synthetic_scores(oracle=H.REF)                          # the oracle is the reference, which is not a variant
    assert "met by 0 of the 6 variant rows: none" in H.sentences(pd.DataFrame(none_rows))


def test_write_table_is_idempotent_and_carries_every_row(tmp_path):
    rows, _ = synthetic_scores()
    R = pd.DataFrame(rows)
    diag = {"months": {"2026-01": {"bucket": {"stay_spread": 0.05}, "windows": {"3": {"converged": True, "per_state_fallbacks": 1}}}}}
    H.write_table(R, tmp_path, "2025-10", "2026-08", diag)
    first = (tmp_path / "hmm_models3.md").read_text(), (tmp_path / "hmm_models3.csv").read_text()
    H.write_table(R, tmp_path, "2025-10", "2026-08", diag)
    assert first == ((tmp_path / "hmm_models3.md").read_text(), (tmp_path / "hmm_models3.csv").read_text())
    md = first[0]
    assert md.count("\n| 3 | ") == 9                                        # one line per row
    assert md.count("\n| 3 | a |") == 2 and "fell back to the base forest for 1 of 5 state-fits" in md
    assert len(pd.read_csv(tmp_path / "hmm_models3.csv")) == 9


def test_reference_check_reads_study_30s_base_row(tmp_path):
    R = pd.DataFrame([{"minute": 0, "variant": "reference", "n": 23328, "accuracy": 0.5348}])
    p = tmp_path / "hmm_models2.md"
    assert H.reference_check(R, p) == {"reference_matches_study_30": None}
    p.write_text("| 0 | base | 23328 | 53.48% [52.88, 54.10] | 0.547 |\n")
    assert H.reference_check(R, p) == {"reference_matches_study_30": True}
    p.write_text("| 0 | base | 23328 | 53.00% [52.88, 54.10] | 0.547 |\n")
    assert H.reference_check(R, p) == {"reference_matches_study_30": False}


# ---------------------------------------------------------------- the whole walk-forward on synthetic data

def synthetic_series(tamper_from=None, seed=0):
    t0 = int((pd.Timestamp("2025-10-01") - pd.Timestamp(0)).total_seconds())
    n = 123 * 1440                                                          # 2025-10-01 to 2026-01-31
    rng = np.random.default_rng(seed)
    vol = np.where(np.arange(n) % 4000 < 2000, 2e-4, 8e-4)
    r = rng.normal(0, vol)
    v = rng.gamma(2, 1, n) * np.where(vol > 5e-4, 3, 1)
    tk = rng.uniform(0.3, 0.7, n)
    t = t0 + 60 * np.arange(n)
    if tamper_from is not None:
        j = int(np.searchsorted(t, tamper_from))
        r[j:] = rng.normal(0, 5e-3, n - j)
        v[j:] = rng.gamma(9, 4, n - j)
        tk[j:] = rng.uniform(0.0, 1.0, n - j)
    close = 50_000 * np.exp(np.cumsum(r))
    open_ = np.concatenate([[close[0]], close[:-1]])
    return Series(pd.DataFrame({"t": t, "open": open_, "high": np.maximum(open_, close), "low": np.minimum(open_, close), "close": close,
                                "volume": v, "trades": 100.0, "taker_buy": v * tk, "ok": True}))


@pytest.fixture
def regimes(tmp_path, monkeypatch):
    first_day = int((pd.Timestamp("2025-09-25") - pd.Timestamp(0)).total_seconds()) // 86400
    days = np.arange(first_day, first_day + 200)
    R = pd.DataFrame({"t": (days + 1) * 86400, "hmm": np.take(["low vol, flat", "mid vol, flat", "high vol, flat"], (days // 3) % 3)})
    R.to_csv(tmp_path / "regimes_daily.csv", index=False)
    monkeypatch.setattr(H2, "OUT", tmp_path)


def test_walk_forward_is_causal_and_the_hmm_fits_see_only_earlier_months(regimes):
    cut = int((pd.Timestamp("2026-01-16") - pd.Timestamp(0)).total_seconds())          # inside the single test month (January)
    first_test = int((pd.Timestamp("2026-01-01") - pd.Timestamp(0)).total_seconds())
    make = lambda kind: make_model("logistic")
    runs = {}
    for name, tamper in (("clean", None), ("late", cut), ("whole month", first_test)):
        s = synthetic_series(tamper)
        Ds = {3: add_baseline_columns(dataset(s, 3, cache=False), 3)}
        runs[name] = H.walk_forward_variants(s, Ds, make=make, log=lambda m: None)
    (res, diag), (res_late, _), (res_month, diag_month) = runs["clean"], runs["late"], runs["whole month"]
    preds, y, t = res[3]
    assert set(preds) == set(H.ROW_IDS) and all(len(p) == len(y) and not np.isnan(p).any() for p in preds.values())
    assert t.min() >= first_test and (pd.to_datetime(t, unit="s").to_period("M") == pd.Period("2026-01")).all()
    # changing the second half of the test month changes no earlier prediction, for any row
    p_late, _, t_late = res_late[3]
    before = t < cut - 3600
    assert np.array_equal(t[before], t_late[t_late < cut - 3600])
    for r in H.ROW_IDS:
        assert np.allclose(preds[r][before], p_late[r][t_late < cut - 3600]), r
    assert not np.allclose(preds[H.REF][~before], p_late[H.REF][t_late >= cut - 3600])   # the tamper was felt after the cut
    # replacing the whole test month changes no fitted HMM: they were fit before it
    m0, m1 = diag["months"]["2026-01"], diag_month["months"]["2026-01"]
    assert np.allclose(m0["minute_means"], m1["minute_means"])
    assert np.allclose(m0["windows"]["3"]["means"], m1["windows"]["3"]["means"])
    assert np.allclose(m0["hazard_first"], m1["hazard_first"]) and np.allclose(m0["hazard_tail"], m1["hazard_tail"])
    assert np.isclose(m0["bucket"]["stay_spread"], m1["bucket"]["stay_spread"])


def test_rewriting_the_table_from_the_stored_csv_reproduces_it_exactly(tmp_path):
    rows, _ = synthetic_scores()
    diag = {"months": {"2026-01": {"bucket": {"stay_spread": 0.05}, "windows": {"3": {"converged": True, "per_state_fallbacks": 1}}}}}
    H.write_table(pd.DataFrame(rows), tmp_path, "2025-10", "2026-08", diag)
    first = (tmp_path / "hmm_models3.md").read_text()
    H.write_table(pd.read_csv(tmp_path / "hmm_models3.csv", float_precision="round_trip"), tmp_path, "2025-10", "2026-08", diag)     # what --rewrite does, minus the json read
    assert (tmp_path / "hmm_models3.md").read_text() == first
