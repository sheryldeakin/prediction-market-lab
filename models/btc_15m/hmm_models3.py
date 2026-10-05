"""Hidden Markov models, round three: the variants study 30 left open.

Every variant is a way of turning a hidden-state model into columns (or a mixture) for the
forest on price, flow and indicators, walk-forward by month on the windows of the main table.
Each test month's HMM is fit on the minutes (or windows) of the months before it only, then
filtered forward (no smoothing), so a window's state uses nothing after its own last closed
minute. Pre-registered success, written into docs/btc_15m.md before the run: a variant adds
something when its day-block AND month-block paired interval over the one-feature baseline
(prev-window at minute 0, lead-z at minute 3) lies entirely above zero.

  reference   the forest with no HMM columns (the control for everything below)
  control     study 30's three-state homogeneous minute-scale HMM, posteriors as columns
  (a)         a 5-state Gaussian HMM whose emissions are the WINDOW features (the 34 columns
              of the forest's input, reduced to 8 whitened principal components fit on the
              training windows), one observation per window; posteriors as columns, and a
              forest per state mixed by the posterior
  (b)         a non-homogeneous minute-scale HMM: the control's emissions with a transition
              matrix per bucket of (time of day x trailing volatility); posteriors as columns
  (c)         a hidden semi-Markov model by duration-augmented state expansion over the
              control's emissions; posteriors and the expected elapsed duration as columns
  (d)         the daily regime state of the regime study and the minute-scale state together:
              study 30's concatenation, and the joint (minute state x daily regime) products

    python -m models.btc_15m.hmm_models3 --start 2025-10 --end 2026-08 --minutes 0,3
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.decomposition import PCA
from sklearn.metrics import log_loss, roc_auc_score

import models.btc_15m.evaluate as evaluate
from models.btc_15m.data import load
from models.btc_15m.evaluate import N_JOBS, add_baseline_columns, baseline_name, baseline_walk_forward, format_p, make_model
from models.btc_15m.features import Series, _rolling_std_before, dataset
from models.btc_15m.hmm_models import N_STATES, minute_matrix
from models.btc_15m.hmm_models2 import COLS, daily_regime_columns
from models.btc_15m.regimes import forward_filter
from models.btc_15m.stats import block_bootstrap_ci, day_sign_test, month_block_bootstrap_ci, paired_difference_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")

WINDOW_STATES = 5          # (a) between the four and six the brief allows
WINDOW_COMPONENTS = 8      # (a) whitened principal components of the 34 window features
WINDOW_RESTARTS = 5        # (a) seeds tried per fit; the highest training log likelihood is kept
WINDOW_CLIP = 5.0         # standardised features are clipped here before the PCA (heavy tails)
HOUR_BUCKETS = 4           # (b) six-hour blocks of the UTC day
VOL_BUCKETS = 3            # (b) terciles of the trailing 60-minute volatility, cut points from the training minutes
VOL_SPAN = 60
NHMM_EM_ROUNDS = 3         # (b) EM rounds for the bucketed transition matrices (emissions held fixed)
NHMM_PRIOR = 100.0         # (b) pseudo-counts pulling each bucket's row toward the pooled row
DURATION_CAP = 60          # (c) elapsed minutes tracked exactly; longer sojourns share one geometric tail
DURATION_PRIOR = 5.0       # (c) pseudo-observations pulling each hazard toward the state's pooled hazard
MIN_STATE_WINDOWS = 500    # a per-state forest needs this many training windows, else the base forest stands in

# row ids: (variant, model name)
REF = ("reference", "forest, no HMM columns")
CONTROL = ("control", "minute HMM, 3 states, homogeneous (study 30 columns)")
A_FEAT = ("a", "window HMM, 5 states: posteriors as features")
A_MIX = ("a", "window HMM, 5 states: forest per state")
B_FEAT = ("b", "non-homogeneous minute HMM: posteriors as features")
C_FEAT = ("c", "duration-expanded minute HMM: posteriors and duration as features")
D_BOTH = ("d", "daily regime + minute state as features (study 30 set)")
D_JOINT = ("d", "daily regime x minute state, joint products added")
ROW_IDS = [REF, CONTROL, A_FEAT, A_MIX, B_FEAT, C_FEAT, D_BOTH, D_JOINT]
VARIANT_LETTERS = ("a", "b", "c", "d")


# ---------------------------------------------------------------- emissions and the minute-scale fit

def log_emission(model: GaussianHMM, Z: np.ndarray) -> np.ndarray:
    """(n, K) log density of each row under each state of a diagonal-covariance fit."""
    cov = np.asarray(model.covars_)
    var = np.array([np.diag(c) for c in cov]) if cov.ndim == 3 else cov
    d = Z[:, None, :] - model.means_[None]
    return -0.5 * (np.sum(d * d / var[None], axis=2) + np.sum(np.log(2 * np.pi * var), axis=1)[None])


def scaled_emission(model: GaussianHMM, Z: np.ndarray) -> np.ndarray:
    """exp(log density) with each row divided by its largest entry, which cancels in every
    normalised forward step and keeps rare minutes from underflowing."""
    lb = log_emission(model, Z)
    return np.exp(lb - lb.max(axis=1, keepdims=True))


def fit_minute_hmm(X: np.ndarray, fit_mask: np.ndarray, n_states: int = N_STATES, seed: int = 0):
    """Standardise on the rows in fit_mask, fit a diagonal Gaussian HMM on them, return (model, Z)
    with Z the standardised matrix for ALL rows. Rows outside the mask are never seen by the fit."""
    mu, sd = X[fit_mask].mean(0), X[fit_mask].std(0) + 1e-9
    Z = (X - mu) / sd
    m = GaussianHMM(n_components=n_states, covariance_type="diag", n_iter=100, random_state=seed).fit(Z[fit_mask])
    return m, Z


# ---------------------------------------------------------------- (b) transition buckets

def vol_cut_points(vol_before: np.ndarray, fit_mask: np.ndarray, n_buckets: int = VOL_BUCKETS) -> tuple[np.ndarray, float]:
    """Volatility cut points (terciles) and the fill value for minutes without a trailing
    window, both from the training minutes only."""
    v = vol_before[fit_mask & np.isfinite(vol_before)]
    qs = np.linspace(0, 1, n_buckets + 1)[1:-1]
    return np.quantile(v, qs), float(np.median(v))


def transition_buckets(t: np.ndarray, vol_before: np.ndarray, cuts: np.ndarray, fill: float, hour_buckets: int = HOUR_BUCKETS) -> np.ndarray:
    """Bucket of the transition INTO each minute, from what is known before that minute closes:
    its UTC hour block and the volatility of the 60 minutes before it."""
    hour = (t // 3600) % 24
    tod = hour * hour_buckets // 24
    v = np.where(np.isfinite(vol_before), vol_before, fill)
    return (tod * (len(cuts) + 1) + np.searchsorted(cuts, v, side="right")).astype(int)


def forward_bucketed(B: np.ndarray, A: np.ndarray, bucket: np.ndarray, pi: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Filtered state probabilities and the per-step scale for a chain whose transition into
    minute t is A[bucket[t]]. B is the (scaled) emission matrix."""
    n, K = B.shape
    alpha, c = np.empty((n, K)), np.empty(n)
    a = pi * B[0]
    c[0] = a.sum(); alpha[0] = a / c[0]
    for t in range(1, n):
        a = (alpha[t - 1] @ A[bucket[t]]) * B[t]
        c[t] = a.sum(); alpha[t] = a / c[t]
    return alpha, c


def backward_bucketed(B: np.ndarray, A: np.ndarray, bucket: np.ndarray, c: np.ndarray) -> np.ndarray:
    n, K = B.shape
    beta = np.ones((n, K))
    for t in range(n - 2, -1, -1):
        beta[t] = (A[bucket[t + 1]] @ (B[t + 1] * beta[t + 1])) / c[t + 1]
    return beta


def fit_bucket_transitions(B: np.ndarray, bucket: np.ndarray, n_buckets: int, A0: np.ndarray, pi: np.ndarray,
                           rounds: int = NHMM_EM_ROUNDS, prior: float = NHMM_PRIOR) -> tuple[np.ndarray, dict]:
    """EM for the transition matrix of each bucket with the emissions held fixed (a generalised
    EM step: the transition parameters decouple from the emission parameters). Every bucket's
    rows are shrunk toward the pooled rows with `prior` pseudo-counts, so a thin bucket cannot
    run away. Returns the (n_buckets, K, K) matrices and diagnostics."""
    K = B.shape[1]
    A = np.repeat(A0[None], n_buckets, axis=0)
    for _ in range(rounds):
        alpha, c = forward_bucketed(B, A, bucket, pi)
        beta = backward_bucketed(B, A, bucket, c)
        xi = alpha[:-1, :, None] * A[bucket[1:]] * (B[1:] * beta[1:])[:, None, :] / c[1:, None, None]
        counts = np.stack([xi[bucket[1:] == b].sum(0) if (bucket[1:] == b).any() else np.zeros((K, K)) for b in range(n_buckets)])
        pooled = counts.sum(0)
        pooled = pooled / np.maximum(pooled.sum(1, keepdims=True), 1e-12)
        A = (counts + prior * pooled[None]) / (counts.sum(2, keepdims=True) + prior)
    diag = A[:, np.arange(K), np.arange(K)]
    return A, {"stay_min": float(diag.min()), "stay_max": float(diag.max()), "stay_spread": float((diag.max(0) - diag.min(0)).max()),
               "bucket_minutes_min": int(np.bincount(bucket, minlength=n_buckets).min())}


# ---------------------------------------------------------------- (c) duration expansion

def run_lengths(path: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(state, length) of each maximal run in a hard state path."""
    change = np.flatnonzero(np.diff(path)) + 1
    starts = np.concatenate([[0], change]); ends = np.concatenate([change, [len(path)]])
    return path[starts], ends - starts


def duration_model(path: np.ndarray, n_states: int, cap: int = DURATION_CAP, prior: float = DURATION_PRIOR) -> tuple[np.ndarray, np.ndarray]:
    """Per-state discrete hazards of the sojourn length and the jump chain between states, from a
    hard state path. hazard[s, d-1] is the chance a run in s ends after exactly d minutes given
    it lasted d; hazard[s, cap-1] is the geometric tail for runs of cap minutes or more. The
    first and last runs are dropped (they are cut by the ends of the sample). Each hazard is
    pulled toward the state's pooled hazard (1 / mean run length) by `prior` pseudo-observations."""
    st, ln = run_lengths(path)
    st, ln = st[1:-1], ln[1:-1]
    K = n_states
    haz = np.zeros((K, cap))
    for s in range(K):
        L = ln[st == s]
        h0 = 1.0 / L.mean() if len(L) else 1.0 / cap
        for d in range(1, cap):
            haz[s, d - 1] = ((L == d).sum() + prior * h0) / ((L >= d).sum() + prior)
        tail = L[L >= cap]
        haz[s, cap - 1] = (len(tail) + prior * h0) / ((tail - cap + 1).sum() + prior)
    haz = np.clip(haz, 1e-4, 1 - 1e-4)
    nxt = st[1:]
    J = np.ones((K, K)) - np.eye(K)                       # one pseudo-transition to every other state
    for a, b in zip(st[:-1], nxt):
        if a != b:
            J[a, b] += 1
    return haz, J / J.sum(1, keepdims=True)


def forward_hsmm(B: np.ndarray, haz: np.ndarray, jump: np.ndarray, pi: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Filtered state probabilities and the filtered expected elapsed minutes in the current state,
    for the chain on (state, elapsed minutes) pairs: a pair advances its counter with probability
    1 - hazard and otherwise jumps to another state (by `jump`) with the counter reset to one; the
    counter saturates at the cap. B is the (scaled) emission matrix of the states."""
    n, K = B.shape
    cap = haz.shape[1]
    stay = 1.0 - haz
    dvec = np.arange(1, cap + 1, dtype=float)
    marg, dur = np.empty((n, K)), np.empty(n)
    alpha = np.zeros((K, cap))
    alpha[:, 0] = pi * B[0]
    alpha /= alpha.sum()
    marg[0], dur[0] = alpha.sum(1), (alpha * dvec).sum()
    for t in range(1, n):
        cont = alpha * stay
        new = np.empty_like(alpha)
        new[:, 1:] = cont[:, :-1]
        new[:, -1] += cont[:, -1]
        new[:, 0] = (alpha * haz).sum(1) @ jump
        new *= B[t][:, None]
        alpha = new / new.sum()
        marg[t], dur[t] = alpha.sum(1), (alpha * dvec).sum()
    return marg, dur


# ---------------------------------------------------------------- (a) HMM on window features

def window_hmm_posteriors(D: pd.DataFrame, cols: list[str], fit_mask: np.ndarray, n_states: int = WINDOW_STATES,
                          n_components: int = WINDOW_COMPONENTS, seed: int = 0) -> tuple[np.ndarray, dict]:
    """One observation per window (rows of D in time order). Standardise, clip, reduce to whitened
    principal components and fit a diagonal Gaussian HMM, all on the rows in fit_mask; return the
    filtered posteriors for every row and diagnostics of the fit."""
    assert np.all(np.diff(D.t.values) > 0), "windows must be in time order"
    X = D[cols].values.astype(float)
    mu, sd = X[fit_mask].mean(0), X[fit_mask].std(0) + 1e-9
    Z = np.clip((X - mu) / sd, -WINDOW_CLIP, WINDOW_CLIP)
    pca = PCA(n_components=n_components, whiten=True, svd_solver="full", random_state=0).fit(Z[fit_mask])
    W = pca.transform(Z)
    # EM on a few thousand windows lands in poor local optima for some seeds (two of five on planted clusters in
    # tests/test_hmm_models3.py), so the fit with the highest training log likelihood of WINDOW_RESTARTS seeds is kept.
    fits = [GaussianHMM(n_components=n_states, covariance_type="diag", n_iter=100, random_state=seed + r).fit(W[fit_mask]) for r in range(WINDOW_RESTARTS)]
    scores = [f.score(W[fit_mask]) for f in fits]
    m = fits[int(np.argmax(scores))]
    P = forward_filter(m, W)
    hard = P[fit_mask].argmax(1)
    share = np.bincount(hard, minlength=n_states) / fit_mask.sum()
    return P, {"explained": float(pca.explained_variance_ratio_.sum()), "converged": bool(m.monitor_.converged),
               "restart_spread": float(max(scores) - min(scores)),
               "min_state_share": float(share.min()), "means": m.means_.tolist(), "n_states_used": int((share > 0.01).sum())}


# ---------------------------------------------------------------- mixtures and joint columns

def mixture_of_experts(D: pd.DataFrame, tr: np.ndarray, te: np.ndarray, y: np.ndarray, cols: list[str], P_tr: np.ndarray,
                       P_te: np.ndarray, fallback: np.ndarray, make, min_n: int = MIN_STATE_WINDOWS) -> tuple[np.ndarray, int]:
    """A model per state fit on the training windows whose most likely state it is, mixed by the
    test windows' posteriors. A state with fewer than min_n training windows (or one class)
    uses `fallback` (the base model's test predictions). Returns (predictions, states that fell back)."""
    hard = P_tr.argmax(axis=1)
    K = P_tr.shape[1]
    mix = np.zeros((te.sum(), K))
    fell = 0
    for j in range(K):
        sel = hard == j
        if sel.sum() < min_n or len(np.unique(y[tr][sel])) < 2:
            mix[:, j] = fallback
            fell += 1
            continue
        mix[:, j] = make("forest").fit(D.loc[tr, cols][sel], y[tr][sel]).predict_proba(D.loc[te, cols])[:, 1]
    return (P_te * mix).sum(axis=1), fell


def joint_columns(P: np.ndarray, onehot: np.ndarray, regime_names: list[str]) -> tuple[np.ndarray, list[str]]:
    """The joint (minute state j, daily regime r) probability, P[:, j] * 1[regime == r]: the daily
    regime is known, so this is the minute posterior routed into the day's regime column."""
    cols, names = [], []
    for j in range(P.shape[1]):
        for r, name in enumerate(regime_names):
            cols.append(P[:, j] * onehot[:, r])
            names.append(f"joint: minute state {j} x {name}")
    return np.column_stack(cols), names


# ---------------------------------------------------------------- the walk-forward

def _month_start(m: pd.Period) -> int:
    """Epoch seconds (UTC) of the first instant of a month."""
    return int((m.start_time - pd.Timestamp(0)).total_seconds())


def walk_forward_variants(s: Series, Ds: dict[int, pd.DataFrame], make=make_model, log=print):
    """For each minute in Ds: predictions of every row in ROW_IDS on the walk-forward windows (test
    months after the first three of that minute's windows), plus diagnostics of each fit. The
    minute-scale HMMs are fit once per test month on the minutes before the month and shared by the
    entry minutes; the window HMM is fit per month and entry minute on that minute's training windows."""
    X = minute_matrix(s)
    vol_b = _rolling_std_before(s.r1, VOL_SPAN)
    ix = {int(t): i for i, t in enumerate(s.t)}
    state = {}
    for k, D in Ds.items():
        D = D.copy()
        D, reg_cols = daily_regime_columns(D)
        month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
        state[k] = {"D": D, "reg_cols": reg_cols, "month": month, "y": D.y.values,
                    "last_closed": np.array([ix[int(t)] + k - 1 for t in D.t.values]),
                    "preds": {r: np.full(len(D), np.nan) for r in ROW_IDS}}
    months = sorted(set().union(*[set(st["month"].unique()) for st in state.values()]))[3:]
    diag = {"months": {}}
    for mth in months:
        t_fit = _month_start(mth)
        t_end = _month_start(mth + 1)
        fit_mask = s.t < t_fit
        upto = int(np.searchsorted(s.t, t_end))
        t0 = time.time()
        model, Z = fit_minute_hmm(X, fit_mask)
        P_ctl = forward_filter(model, Z[:upto])
        # (b) bucketed transitions on the same emissions
        cuts, fill = vol_cut_points(vol_b, fit_mask)
        bucket = transition_buckets(s.t, vol_b, cuts, fill)
        nb = HOUR_BUCKETS * VOL_BUCKETS
        Bsc = scaled_emission(model, Z[:upto])
        A_b, nh = fit_bucket_transitions(Bsc[: fit_mask.sum()], bucket[: fit_mask.sum()], nb, model.transmat_, model.startprob_)
        P_b, _ = forward_bucketed(Bsc, A_b, bucket[:upto], model.startprob_)
        # (c) duration expansion on the same emissions
        haz, jump = duration_model(model.predict(Z[fit_mask]), N_STATES)
        P_c, dur_c = forward_hsmm(Bsc, haz, jump, model.startprob_)
        d_m = {"minute_means": model.means_.tolist(), "bucket": nh, "hazard_first": haz[:, 0].tolist(), "hazard_tail": haz[:, -1].tolist(),
               "mean_elapsed_minutes": float(dur_c[fit_mask.sum():].mean()), "seconds_minute_models": round(time.time() - t0, 1), "windows": {}}
        for k, st in state.items():
            D, month, y, lc = st["D"], st["month"], st["y"], st["last_closed"]
            tr, te = (month < mth).values, (month == mth).values
            if te.sum() == 0 or tr.sum() == 0:
                continue
            rows = tr | te
            def take(P):
                out = np.full((len(D), P.shape[1]), np.nan)
                out[rows] = P[lc[rows]]
                return out
            T0 = time.time()
            def put(cols, arr):
                for i, c in enumerate(cols):
                    D[c] = arr[:, i]
            ctl_cols, nh_cols = [f"hmm_p{j}" for j in range(N_STATES)], [f"nhmm_p{j}" for j in range(N_STATES)]
            hs_cols = [f"hsmm_p{j}" for j in range(N_STATES)] + ["hsmm_logdur"]
            win_cols = [f"whmm_p{j}" for j in range(WINDOW_STATES)]
            ctl = take(P_ctl)
            put(ctl_cols, ctl)
            put(nh_cols, take(P_b))
            put(hs_cols, take(np.column_stack([P_c, np.log(dur_c)])))
            Pw, wd = window_hmm_posteriors(D, COLS, tr)
            put(win_cols, Pw)
            names = [c[len("regime: "):] for c in st["reg_cols"]]
            joint, joint_cols = joint_columns(ctl, D[st["reg_cols"]].values, names)
            put(joint_cols, joint)
            fit_fit = lambda cols: make("forest").fit(D.loc[tr, cols], y[tr]).predict_proba(D.loc[te, cols])[:, 1]
            P = st["preds"]
            P[REF][te] = fit_fit(COLS)
            P[CONTROL][te] = fit_fit(COLS + ctl_cols)
            P[A_FEAT][te] = fit_fit(COLS + win_cols)
            P[A_MIX][te], fell = mixture_of_experts(D, tr, te, y, COLS, Pw[tr], Pw[te], P[REF][te], make)
            P[B_FEAT][te] = fit_fit(COLS + nh_cols)
            P[C_FEAT][te] = fit_fit(COLS + hs_cols)
            P[D_BOTH][te] = fit_fit(COLS + ctl_cols + st["reg_cols"])
            P[D_JOINT][te] = fit_fit(COLS + ctl_cols + st["reg_cols"] + joint_cols)
            d_m["windows"][str(k)] = {**wd, "per_state_fallbacks": fell, "seconds": round(time.time() - T0, 1)}
            log(f"  {mth} k={k}: window HMM converged={wd['converged']}, {wd['n_states_used']} states used, {fell} fell back; {time.time()-T0:.0f}s")
        diag["months"][str(mth)] = d_m
        log(f"{mth}: minute-scale models {d_m['seconds_minute_models']}s; bucketed stay-prob spread {nh['stay_spread']:.3f}; mean elapsed {d_m['mean_elapsed_minutes']:.1f} min")
    out = {}
    for k, st in state.items():
        keep = ~np.isnan(st["preds"][REF])
        out[k] = ({r: p[keep] for r, p in st["preds"].items()}, st["y"][keep], st["D"].t.values[keep])
    return out, diag


# ---------------------------------------------------------------- scoring and the table

def adds_something(lo_day: float, lo_month: float) -> bool:
    """The pre-registered test: both paired intervals lie entirely above zero."""
    return lo_day > 0 and lo_month > 0


def score_rows(k: int, preds: dict, y: np.ndarray, t: np.ndarray, bp: np.ndarray, n_draws: int = 2000) -> list[dict]:
    hb = ((bp > 0.5) == y).astype(float)
    hr = ((preds[REF] > 0.5) == y).astype(float)
    rows = []
    def row(variant, model, p, base):
        h = ((p > 0.5) == y).astype(float) if p is not None else hb
        m, lo, hi = block_bootstrap_ci(h, t)
        pp = p if p is not None else bp
        r = {"minute": k, "variant": variant, "model": model, "n": len(y), "accuracy": m, "ci_low": lo, "ci_high": hi,
             "auc": float(roc_auc_score(y, pp)), "log_loss": float(log_loss(y, np.clip(pp, 1e-6, 1 - 1e-6)))}
        if not base:
            d, dlo, dhi = paired_difference_ci(h, hb, t)
            _, mlo, mhi = month_block_bootstrap_ci(h - hb, t)
            sg = day_sign_test(h, hb, t, n_draws=n_draws)
            r.update({"diff": d, "diff_low": dlo, "diff_high": dhi, "diff_month_low": mlo, "diff_month_high": mhi,
                      "days_better": sg["share_days_a_better"], "sign_p": sg["p"], "adds": adds_something(dlo, mlo)})
            if (variant, model) != REF:
                dr, rlo, rhi = paired_difference_ci(h, hr, t)
                r.update({"vs_ref": dr, "vs_ref_low": rlo, "vs_ref_high": rhi})
        return r
    rows.append(row("baseline", baseline_name(k), None, True))
    for variant, model in ROW_IDS:
        rows.append(row(variant, model, preds[(variant, model)], False))
    return rows


def _ci(m, lo, hi, sign=False):
    f = (lambda x: f"{x*100:+.2f}") if sign else (lambda x: f"{x*100:.2f}")
    return f"{f(m)}{'' if sign else '%'} [{f(lo)}, {f(hi)}]"


def _label(r) -> str:
    return f"{r['variant']}: {r['model']} at minute {int(r['minute'])} ({r['diff']*100:+.2f})"


def sentences(R: pd.DataFrame) -> str:
    """The generated findings under the table: which variant rows meet the pre-registered test, which
    meet each interval alone, what the reference forest does, attribution to the HMM columns, and the
    increment these windows could have detected."""
    V = R[R.variant.isin(VARIANT_LETTERS)]
    ref = R[R.variant == "reference"]
    day = V[V.diff_low > 0]
    month = V[V.diff_month_low > 0]
    both = V[V.adds.astype(bool)]
    names = lambda X: "; ".join(_label(r) for _, r in X.iterrows()) or "none"
    out = [f"The pre-registered test (the day-block and the month-block interval over the one-feature baseline both entirely above zero) is met by {len(both)} of the {len(V)} variant rows: {names(both)}. "
           f"The day-block interval alone is above zero for {len(day)} ({names(day)}) and the month-block interval alone for {len(month)} ({names(month)}). "
           "The intervals are not adjusted for the number of comparisons."]
    out.append("The forest without any HMM column, on the same windows: " + "; ".join(
        f"minute {int(r['minute'])} {r['diff']*100:+.2f} over the baseline, day blocks [{r['diff_low']*100:+.2f}, {r['diff_high']*100:+.2f}], month blocks [{r['diff_month_low']*100:+.2f}, {r['diff_month_high']*100:+.2f}]" for _, r in ref.iterrows()) +
        ". A variant built on this forest can meet the test through the forest alone, so the last column of the table attributes: it compares each row with this forest.")
    vr = V[(V.vs_ref_low > 0) | (V.vs_ref_high < 0)]
    vr_names = "; ".join("%s: %s at minute %d (%+.2f)" % (r.variant, r.model, r.minute, r.vs_ref * 100) for r in vr.itertuples())
    out.append("Against the forest without HMM columns, the day-block interval excludes zero for " + (f"{len(vr)} variant rows ({vr_names})" if len(vr) else "none of the variant rows") + ".")
    not_met = V[~V.adds.astype(bool)]
    if len(not_met):
        out.append("Rows that do not meet the test close with the upper end of their intervals over the baseline (day blocks, month blocks, points): " +
                   "; ".join(f"{r.variant}: {r.model} at minute {int(r.minute)} {r.diff_high*100:+.2f}, {r.diff_month_high*100:+.2f}" for r in not_met.itertuples()) + ".")
    wd, wm = (V.diff_high - V.diff_low) * 100, (V.diff_month_high - V.diff_month_low) * 100
    out.append(f"What these windows could detect: across the variant rows a day-block interval on a difference from the baseline is {wd.min():.2f} to {wd.max():.2f} points wide and a month-block interval is {wm.min():.2f} to {wm.max():.2f} points wide, "
               f"so an increment smaller than about {wd.min()/2:.2f} to {wd.max()/2:.2f} points (day blocks) or {wm.min()/2:.2f} to {wm.max()/2:.2f} points (month blocks) could not be told from zero. A null here is a bound of that width, not a verdict.")
    return "\n\n".join(out) + "\n"


def write_table(R: pd.DataFrame, out: Path, start: str, end: str, diag: dict):
    R.to_csv(out / "hmm_models3.csv", index=False)
    inst = [m["windows"] for m in diag["months"].values()]
    fell = sum(w["per_state_fallbacks"] for ws in inst for w in ws.values())
    total = sum(1 for ws in inst for _ in ws.values()) * WINDOW_STATES
    unconv = sum(1 for ws in inst for w in ws.values() if not w["converged"])
    spreads = [m["bucket"]["stay_spread"] for m in diag["months"].values()]
    with open(out / "hmm_models3.md", "w") as f:
        f.write(f"Hidden Markov models, round three: the tabled variants (forest on price + flow + indicators, walk-forward by month, {start} to {end}, test months after the first three). "
                "Each test month's HMM is fit on the minutes (b, c, d and the control) or the windows (a) of earlier months only and filtered forward. "
                f"(a) a {WINDOW_STATES}-state Gaussian HMM on the window features, reduced to {WINDOW_COMPONENTS} whitened principal components; "
                f"(b) the minute-scale HMM with a transition matrix for each of {HOUR_BUCKETS * VOL_BUCKETS} buckets of UTC six-hour block and trailing-hour volatility tercile; "
                f"(c) the same HMM expanded to (state, elapsed minutes) pairs with a discrete hazard per minute up to {DURATION_CAP} and a geometric tail; "
                "(d) the daily regime of the regime study with the minute-scale state, concatenated and as joint products. "
                "Accuracy has a day-block 95% interval. \"vs baseline\" is accuracy minus the one-feature baseline on the same windows (prev-window at minute 0, lead-z at minute 3) with a day-block and a month-block interval, the share of days better and the sign-flip p. "
                "\"vs forest without HMM\" is accuracy minus the forest with no HMM column, day blocks.\n\n")
        f.write("| minute | variant | model | n | accuracy [95% CI] | AUC | log loss | vs baseline, day blocks | vs baseline, month blocks | days better | sign p | vs forest without HMM |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for r in R.itertuples(index=False):
            r = r._asdict()
            acc = _ci(r["accuracy"], r["ci_low"], r["ci_high"])
            if r["variant"] == "baseline":
                cells = ["baseline", "", "", "", ""]
            else:
                ref = "reference" if r["variant"] == "reference" else _ci(r["vs_ref"], r["vs_ref_low"], r["vs_ref_high"], sign=True)
                cells = [_ci(r["diff"], r["diff_low"], r["diff_high"], sign=True), _ci(r["diff"], r["diff_month_low"], r["diff_month_high"], sign=True),
                         f"{r['days_better']*100:.0f}%", format_p(r["sign_p"], 2000), ref]
            f.write(f"| {int(r['minute'])} | {r['variant']} | {r['model']} | {int(r['n'])} | {acc} | {r['auc']:.3f} | {r['log_loss']:.4f} | " + " | ".join(cells) + " |\n")
        f.write("\n" + sentences(R))
        f.write(f"\nWhat the fits did: the window HMM did not converge in {unconv} of {sum(len(ws) for ws in inst)} fits; the per-state forests fell back to the base forest for {fell} of {total} state-fits (a state with under {MIN_STATE_WINDOWS} training windows); "
                f"the bucketed transition matrices differ across buckets by up to {max(spreads)*100:.1f} points in a state's stay probability (smallest month {min(spreads)*100:.1f}).\n")


def reference_check(R: pd.DataFrame, path: Path) -> dict:
    """Whether the forest with no HMM columns reproduces study 30's base row to the printed digit
    (same model, same windows), read from results/btc_15m/hmm_models2.md when it is there."""
    if not path.exists():
        return {"reference_matches_study_30": None}
    text = path.read_text()
    ok = []
    for r in R[R.variant == "reference"].itertuples():
        m = re.search(rf"^\| {int(r.minute)} \| base \| (\d+) \| ([\d.]+)%", text, flags=re.M)
        ok.append(bool(m) and int(m.group(1)) == r.n and abs(float(m.group(2)) - r.accuracy * 100) < 0.005)
    return {"reference_matches_study_30": all(ok) if ok else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--minutes", default="0,3")
    ap.add_argument("--out", default=str(OUT), help="output directory (a smoke run points this elsewhere)")
    a = ap.parse_args()
    evaluate.XGB_DEVICE = "cpu"                     # this study is CPU only
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    s = Series(load(a.start, a.end))
    minutes = [int(x) for x in a.minutes.split(",")]
    Ds = {k: add_baseline_columns(dataset(s, k), k) for k in minutes}
    print(f"datasets built in {time.time()-t0:.0f}s", flush=True)
    base = {}
    for k in minutes:
        bp, _, _, bt = baseline_walk_forward(Ds[k].copy(), k)
        base[k] = pd.Series(bp, index=bt)
    res, diag = walk_forward_variants(s, Ds, log=lambda m: print(m, flush=True))
    rows = []
    for k in minutes:
        preds, y, t = res[k]
        rows += score_rows(k, preds, y, t, base[k].reindex(t).values)
    R = pd.DataFrame(rows)
    checks = reference_check(R, OUT / "hmm_models2.md")
    write_table(R, out, a.start, a.end, diag)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "models"], capture_output=True, text=True).stdout.strip())
    (out / "hmm_models3.json").write_text(json.dumps({
        "ran_at": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "commit": commit, "dirty": dirty, "device": "cpu", "threads": N_JOBS,
        "seconds": round(time.time() - t0), "start": a.start, "end": a.end, "minutes": minutes,
        "config": {"window_states": WINDOW_STATES, "window_components": WINDOW_COMPONENTS, "hour_buckets": HOUR_BUCKETS, "vol_buckets": VOL_BUCKETS,
                   "nhmm_em_rounds": NHMM_EM_ROUNDS, "nhmm_prior": NHMM_PRIOR, "window_restarts": WINDOW_RESTARTS, "duration_cap": DURATION_CAP, "duration_prior": DURATION_PRIOR, "minute_states": N_STATES},
        "checks": checks, "fits": diag}, indent=2))
    print(f"wrote hmm_models3.md, .csv and .json to {out} in {time.time()-t0:.0f}s (checks: {checks})")


if __name__ == "__main__":
    main()
