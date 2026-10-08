"""Is an early confident call worth more than the window's own move? (docs/btc_15m.md, study 33)

The walk-forward stores an out-of-fold probability for every window at every entry minute 0 to 14
(results/btc_15m/oof_k<k>.parquet). For each predictor and each threshold, a window's call is made at the
FIRST minute at which the probability of the called side reaches the threshold, on that minute's side. It
is compared with the one-feature rule's call at that same minute (prev-window at minute 0, lead-z after),
on the same windows, paired by window: accuracy of the predictor's calls minus accuracy of the rule's
calls, with a day-block interval and a day-level sign-flip p, Holm over the 48 (predictor, threshold) cells.
A window that never reaches the threshold makes no call: it counts in the share called and is left out of
the accuracies.

The eight predictors are the eight rows runs_for gives at every minute, matched by position, because two of
them are different models at minute 0 and after (see SLOTS). The design is fixed in the pre-registration,
written before any result file:

    python -m models.btc_15m.confidence_by_minute --prereg
    python -m models.btc_15m.confidence_by_minute
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.matched_increment import holm            # one Holm in the repo; imported so the two cannot drift apart
from models.btc_15m.stats import paired_difference_ci

OUT = Path("results/btc_15m")
STEM = "confidence_by_minute"
MINUTES = tuple(range(15))
THRESHOLDS = (0.55, 0.60, 0.65, 0.70, 0.75, 0.80)
CALIBRATION_THRESHOLDS = (0.65, 0.75)
CALIBRATION_MODEL = "xgb-all"
EARLY = (1, 3)                  # the secondary difference counts only calls made at these minutes
MIN_CALLS = 200                 # a cell with fewer calls is listed but not ranked in the largest / smallest sentences
LEVEL = 0.05
N_BOOT = 2000
N_DRAWS = 20000
TOL = 1e-12                     # 1 - p is not always exactly the decimal it means (1 - 0.0257 is 0.9742999999999999)

# (name, column at minute 0, column at minutes 1 to 14): the eight rows of evaluate.runs_for at every minute, by position.
SLOTS = [("majority", "majority", "majority"),
         ("rule", "prev-window", "lead-z"),
         ("other one-feature", "win1-logistic", "lead-only"),
         ("logistic-all", "logistic-all", "logistic-all"),
         ("forest", "forest", "forest"),
         ("hgb-all", "hgb-all", "hgb-all"),
         ("xgb-price", "xgb-price", "xgb-price"),
         ("xgb-all", "xgb-all", "xgb-all")]
SLOT_NOTE = {"majority": "always the training majority class, so it never reaches a threshold",
             "rule": "the one-feature rule itself: the previous window's direction at minute 0, the lead z-score after",
             "other one-feature": "win1-logistic at minute 0, lead-only after"}


def slot_columns(k: int) -> dict[str, str]:
    return {name: (c0 if k == 0 else c1) for name, c0, c1 in SLOTS}


# ---------------- the call ----------------

def first_crossing(p: np.ndarray, threshold: float) -> tuple[np.ndarray, np.ndarray]:
    """p: probabilities of 'up', shape (minutes, windows). For each window, the first minute at which the
    called-side probability max(p, 1 - p) is at or above the threshold, and that minute's side (1 up, 0 down).
    A probability of exactly 0.5 is not a call. Windows that never reach it get -1 and -1."""
    p = np.asarray(p, float)
    eligible = (p != 0.5) & (np.maximum(p, 1 - p) >= threshold - TOL)
    has = eligible.any(axis=0)
    first = eligible.argmax(axis=0)
    cols = np.arange(p.shape[1])
    minute = np.where(has, first, -1)
    side = np.where(has, (p[first, cols] > 0.5).astype(int), -1)
    return minute, side


def rule_side_at(rule_p: np.ndarray, minute: np.ndarray) -> np.ndarray:
    """The rule's own side (up when its probability is above 0.5, as the walk-forward scores it) at each
    window's crossing minute; -1 where the window made no call."""
    minute = np.asarray(minute)
    cols = np.arange(rule_p.shape[1])
    side = (np.asarray(rule_p, float)[np.maximum(minute, 0), cols] > 0.5).astype(int)
    return np.where(minute >= 0, side, -1)


def day_flip_p(d: np.ndarray, t: np.ndarray, n_draws: int = N_DRAWS, seed: int = 0) -> float:
    """Two-sided p for a mean of per-window differences d with the days as the units: the sum of each day's
    differences gets a random sign, and the p is the share of draws whose absolute total is at least the
    observed one (plus the observed draw). The smallest value is 1 / (n_draws + 1)."""
    d = np.asarray(d, float)
    _, inv = np.unique(np.asarray(t) // 86400, return_inverse=True)
    s = np.bincount(inv, weights=d)
    obs = abs(s.sum())
    rng = np.random.default_rng(seed)
    count, done = 0, 0
    while done < n_draws:
        m = min(2000, n_draws - done)
        signs = rng.integers(0, 2, size=(m, len(s))) * 2 - 1
        count += int((np.abs(signs @ s) >= obs - 1e-12).sum())
        done += m
    return (count + 1) / (n_draws + 1)


def paired_accuracy(y, t, minute, pred_side, rule_side, minutes=None, n_boot: int = N_BOOT, n_draws: int = N_DRAWS, test: bool = True) -> dict:
    """Accuracy of the predictor's calls minus accuracy of the rule's calls at the same minutes, on the called
    windows (those with a call, and inside `minutes` = (first, last) when given), paired by window. The share
    called is over ALL windows. Interval: day blocks. p: day-level sign flips (1.0 when nothing was called)."""
    y, t, minute = np.asarray(y).astype(int), np.asarray(t), np.asarray(minute)
    pred_side, rule_side = np.asarray(pred_side), np.asarray(rule_side)
    called = minute >= 0
    if minutes is not None:
        called &= (minute >= minutes[0]) & (minute <= minutes[1])
    n = int(called.sum())
    out = {"windows": int(len(y)), "called": n, "share_called": n / len(y) if len(y) else 0.0}
    if n == 0:
        nan = float("nan")
        return {**out, "mean_minute": nan, "median_minute": nan, "acc_predictor": nan, "acc_rule": nan, "diff": nan, "low": nan, "high": nan, "p": 1.0}
    hp = (pred_side[called] == y[called]).astype(float)
    hr = (rule_side[called] == y[called]).astype(float)
    diff, lo, hi = paired_difference_ci(hp, hr, t[called], n_boot=n_boot)
    return {**out, "mean_minute": float(minute[called].mean()), "median_minute": float(np.median(minute[called])),
            "acc_predictor": float(hp.mean()), "acc_rule": float(hr.mean()), "diff": diff, "low": lo, "high": hi,
            "p": day_flip_p(hp - hr, t[called], n_draws=n_draws) if test else float("nan")}


def calibration(p: np.ndarray, y: np.ndarray, threshold: float) -> pd.DataFrame:
    """Per minute: the share of windows whose called-side probability is at or above the threshold (exactly
    0.5 is not a call), and the hit rate of those calls."""
    p, y = np.asarray(p, float), np.asarray(y).astype(int)
    rows = []
    for k in range(p.shape[0]):
        sel = (p[k] != 0.5) & (np.maximum(p[k], 1 - p[k]) >= threshold - TOL)
        n = int(sel.sum())
        rows.append({"minute": k, "n_windows": int(p.shape[1]), "n_called": n, "share": n / p.shape[1],
                     "hit": float(((p[k][sel] > 0.5).astype(int) == y[sel]).mean()) if n else float("nan")})
    return pd.DataFrame(rows)


# ---------------- the 48 cells ----------------

def stack(frames: dict[int, pd.DataFrame]):
    """The fifteen out-of-fold frames joined on t. Returns t, y, {slot: (minutes, windows)} and the rule's
    probabilities (minutes, windows). Stops if the windows or labels differ between minutes."""
    ks = sorted(frames)
    assert ks == list(range(len(ks))), f"minutes {ks}"
    base = frames[ks[0]]
    for k in ks[1:]:
        assert np.array_equal(frames[k].t.values, base.t.values) and np.array_equal(frames[k].y.values, base.y.values), f"minute {k} is not on the same windows as minute 0"
    P = {name: np.vstack([frames[k][slot_columns(k)[name]].values for k in ks]).astype(float) for name, *_ in SLOTS}
    return base.t.values.astype(np.int64), base.y.values.astype(int), P, P["rule"]


def run_cells(t, y, P: dict, rule: np.ndarray, n_boot: int = N_BOOT, n_draws: int = N_DRAWS) -> pd.DataFrame:
    rows = []
    for name, *_ in SLOTS:
        for thr in THRESHOLDS:
            minute, side = first_crossing(P[name], thr)
            rs = rule_side_at(rule, minute)
            a = paired_accuracy(y, t, minute, side, rs, n_boot=n_boot, n_draws=n_draws)
            e = paired_accuracy(y, t, minute, side, rs, minutes=EARLY, n_boot=n_boot, test=False)
            rows.append({"predictor": name, "threshold": thr, "windows": a["windows"], "called": a["called"], "share_called": a["share_called"],
                         "mean_minute": a["mean_minute"], "median_minute": a["median_minute"], "acc_predictor": a["acc_predictor"], "acc_rule": a["acc_rule"],
                         "diff": a["diff"], "diff_low": a["low"], "diff_high": a["high"], "p": a["p"],
                         "early_called": e["called"], "early_acc_predictor": e["acc_predictor"], "early_acc_rule": e["acc_rule"],
                         "early_diff": e["diff"], "early_low": e["low"], "early_high": e["high"]})
    cells = pd.DataFrame(rows)
    cells["p_holm"] = holm(cells.p.tolist())
    return cells


def check_engaged(cells: pd.DataFrame) -> None:
    """The mechanism must have run before any number is read. The rule against itself differs by exactly zero
    wherever it makes a call, the constant predictor makes no call, and the rule makes calls at all."""
    assert len(cells) == len(SLOTS) * len(THRESHOLDS), f"{len(cells)} cells"
    own = cells[(cells.predictor == "rule") & (cells.called > 0)]
    assert len(own), "the rule made no call at any threshold"
    assert (own["diff"].abs() <= 1e-12).all(), "the rule differs from itself"
    assert (cells[cells.predictor == "majority"].called == 0).all(), "the constant predictor made a call"
    assert (cells[~cells.predictor.isin(["majority", "rule"])].called > 0).any(), "no fitted predictor made a call"


# ---------------- rendering ----------------

def _pct(x: float, d: int = 2) -> str:
    return "-" if not np.isfinite(x) else f"{x * 100:.{d}f}%"


def _pts(x: float) -> str:
    return f"{x * 100:+.2f}"


def _iv(r, lo="diff_low", hi="diff_high") -> str:
    return "-" if not np.isfinite(r["diff"]) else f"{_pts(r['diff'])} [{_pts(r[lo])}, {_pts(r[hi])}]"


def _holm_p(r, n_draws: int) -> str:
    if r["called"] == 0:
        return "-"
    return f"< {r['p_holm']:.4f}" if r["p"] <= 1 / (n_draws + 1) + 1e-12 else f"{r['p_holm']:.4f}"


def verdict(r) -> str:
    if r["called"] == 0 or r["p_holm"] >= LEVEL:
        return "not separated from the rule"
    return "ahead of the rule" if r["diff"] > 0 else "behind the rule"


def render_cells(cells: pd.DataFrame, info: dict) -> str:
    nd = info["n_draws"]
    intro = (f"Is an early confident call worth more than the window's own move? Out-of-fold probabilities of the walk-forward, {info['first']} to {info['last']}, {info['windows']:,} windows on {info['days']} days, entry minutes 0 to 14. "
             f"For each predictor and threshold, a window's call is made at the first minute at which the probability of the called side (the larger of p and 1 - p; exactly 0.5 is not a call) reaches the threshold, on that minute's side. "
             f"The comparison is the one-feature rule's call at the same minute (prev-window at minute 0, lead-z after), on the same windows. A window that never reaches the threshold makes no call: it counts in the share called and is left out of both accuracies. "
             f"Difference = accuracy of the predictor's calls minus accuracy of the rule's calls, in points, paired by window, with a 95% interval from resampling whole days ({info['n_boot']:,} resamples). "
             f"The p is a two-sided sign-flip test on whole-day sums of the paired differences ({nd:,} draws; a Holm-adjusted p printed with \"<\" comes from a raw p at the test's floor), adjusted by Holm over the {len(cells)} cells. "
             f"The rows named \"rule\" are the rule scored against itself and must show exactly zero; majority never reaches a threshold. \"other one-feature\" is win1-logistic at minute 0 and lead-only after. "
             f"The last two columns count only calls made at minutes 1 to 3 (descriptive, not adjusted).")
    lines = [intro, "", "| predictor | threshold | share called | crossing minute, mean / median | accuracy, predictor | accuracy, rule | difference (points) [95% interval] | Holm p | calls at minutes 1 to 3 | difference at minutes 1 to 3 (points) [95% interval] |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in cells.itertuples(index=False):
        d = r._asdict()
        mins = "-" if d["called"] == 0 else f"{d['mean_minute']:.1f} / {d['median_minute']:.0f}"
        lines.append(f"| {d['predictor']} | {d['threshold']:.2f} | {_pct(d['share_called'], 1)} | {mins} | {_pct(d['acc_predictor'])} | {_pct(d['acc_rule'])} | {_iv(d)} | {_holm_p(d, nd)} | {d['early_called']:,} | {_iv(d, 'early_low', 'early_high') if d['early_called'] else '-'} |")
    lines.append("")
    ranked = cells[cells.called >= MIN_CALLS]
    hi, lo = ranked.loc[ranked["diff"].idxmax()], ranked.loc[ranked["diff"].idxmin()]
    for word, r in (("largest", hi), ("smallest", lo)):
        under = "under" if r["p_holm"] < LEVEL else "not under"
        lines.append(f"The {word} paired difference among the cells with at least {MIN_CALLS} calls is {_iv(r)} points for {r['predictor']} at {r['threshold']:.2f} ({int(r['called']):,} calls); its Holm-adjusted p is {_holm_p(r, nd).replace('< ', 'below ')}, {under} {LEVEL}.\n")
    sig = cells[(cells.called > 0) & (cells.p_holm < LEVEL)]
    lines.append(f"{len(sig)} of the {len(cells)} cells have a Holm-adjusted p under {LEVEL}: {int((sig['diff'] > 0).sum())} with the predictor ahead of the rule and {int((sig['diff'] < 0).sum())} behind it.\n")
    own = cells[(cells.predictor == "rule") & (cells.called > 0)]
    lines.append(f"The rule scored against itself differs by exactly zero in all {len(own)} of its cells that make a call, and the constant predictor (majority) makes no call at any threshold; the run stops if either fails.\n")
    few = cells[cells.called < MIN_CALLS]
    if len(few):
        lines.append(f"{len(few)} cells make fewer than {MIN_CALLS} calls; they are listed above and left out of the two sentences that name the largest and smallest difference.\n")
    return "\n".join(lines).rstrip() + "\n"


def calibration_table(P: dict, rule: np.ndarray, y: np.ndarray) -> pd.DataFrame:
    parts = []
    for thr in CALIBRATION_THRESHOLDS:
        for who, p in ((CALIBRATION_MODEL, P[CALIBRATION_MODEL]), ("rule", rule)):
            c = calibration(p, y, thr).assign(threshold=thr, who=who)
            parts.append(c)
    return pd.concat(parts, ignore_index=True)


def calibration_sentence(cal: pd.DataFrame, minute: int) -> str:
    bits = []
    for thr in CALIBRATION_THRESHOLDS:
        g = cal[(cal.minute == minute) & (cal.threshold == thr)].set_index("who")
        x, r = g.loc[CALIBRATION_MODEL], g.loc["rule"]
        bits.append(f"at {thr:.2f}, {CALIBRATION_MODEL} has {_pct(x.share, 1)} of windows at or above it and those calls are right {_pct(x.hit, 1)} of the time ({int(x.n_called):,} calls), the rule {_pct(r.share, 1)} and {_pct(r.hit, 1)} ({int(r.n_called):,} calls)")
    return f"At minute {minute}: " + "; ".join(bits) + "."


def render_calibration(cal: pd.DataFrame, info: dict) -> str:
    intro = (f"Calibration of the confident calls by entry minute, {info['first']} to {info['last']}, {info['windows']:,} windows. For each minute and threshold: the share of windows whose called-side probability (the larger of p and 1 - p; exactly 0.5 is not a call) is at or above the threshold, "
             f"and the hit rate of those calls against the window's final direction, for {CALIBRATION_MODEL} and for the one-feature rule at that minute (prev-window at minute 0, lead-z after). A dash means no window reached the threshold. Descriptive: no test.")
    head = "| minute | " + " | ".join(f"{w}, share at {t:.2f} or more | {w}, hit rate at {t:.2f} or more" for t in CALIBRATION_THRESHOLDS for w in (CALIBRATION_MODEL, "rule")) + " |"
    lines = [intro, "", head, "|" + "---|" * (1 + 4 * len(CALIBRATION_THRESHOLDS))]
    for k in MINUTES:
        cells = []
        for thr in CALIBRATION_THRESHOLDS:
            for who in (CALIBRATION_MODEL, "rule"):
                r = cal[(cal.minute == k) & (cal.threshold == thr) & (cal.who == who)].iloc[0]
                cells += [_pct(r.share, 1), f"{_pct(r.hit, 1)} ({int(r.n_called):,})" if r.n_called else "-"]
        lines.append(f"| {k} | " + " | ".join(cells) + " |")
    lines += ["", calibration_sentence(cal, 2), "", calibration_sentence(cal, 7), ""]
    return "\n".join(lines).rstrip() + "\n"


# ---------------- data, pre-registration, run ----------------

def load_frames(out: Path = OUT) -> dict[int, pd.DataFrame]:
    return {k: pd.read_parquet(out / f"oof_k{k}.parquet") for k in MINUTES}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def data_info(frames: dict[int, pd.DataFrame]) -> dict:
    t = frames[0].t.values
    day = lambda s: dt.datetime.fromtimestamp(int(s), dt.timezone.utc).strftime("%Y-%m-%d")
    return {"windows": int(len(t)), "days": int(len(np.unique(t // 86400))), "first": day(t.min()), "last": day(t.max())}


def prereg_block(info: dict, commit: str, stamp: str) -> tuple[str, dict]:
    slots = "; ".join(f"{n} ({c0} at minute 0, {c1} after)" if c0 != c1 else f"{n} ({c0})" for n, c0, c1 in SLOTS)
    lines = [f"Pre-registration of the confidence-by-minute study, written {stamp} at commit {commit[:10]}, before any result of the study was computed. It is generated by `python -m models.btc_15m.confidence_by_minute --prereg` and is not edited afterwards.", "",
             "**Question.** Is an early confident call worth more than the window's own move?", "",
             f"**Data.** The out-of-fold probabilities (`oof_k0.parquet` to `oof_k14.parquet`) of the walk-forward on the data 2025-10 to 2026-08, whose first three months are training only, so the scored windows run from {info['first']} to {info['last']}: {info['windows']:,} windows on {info['days']} days, one row per window per entry minute 0 to 14, joined on `t`. The study stops if the windows or labels differ between minutes. The SHA-256 of each file is in the json beside this block.", "",
             f"**Predictors.** The eight rows the walk-forward fits at every minute, matched by position because two of them are different models at minute 0 and after: {slots}.", "",
             "**The rule.** The one-feature rule of the minute: the previous window's direction at minute 0, the lead z-score after. It is also one of the eight predictors, as a check: scored against itself it must differ by exactly zero.", "",
             f"**The call.** For each window, predictor and threshold in {', '.join(f'{t:.2f}' for t in THRESHOLDS)}, the called side is the side with the larger probability and its probability is max(p, 1 - p); a probability of exactly 0.5 is not a call. The call is made at the first minute from 0 to 14 at which the called-side probability reaches the threshold (at or above, within {TOL:g} for floating-point rounding), and the side is that minute's side. A window that never reaches the threshold makes no call: it counts in the share called, whose denominator is all windows, and is left out of the accuracies.", "",
             "**The comparison.** On the same windows and at the same minute, the rule's own call (up when its probability is above 0.5, down otherwise). Both calls are scored against the window's final direction.", "",
             f"**Primary statistic.** Accuracy of the predictor's calls minus accuracy of the rule's calls on the called windows, paired by window, in points. Interval: 95%, resampling whole days ({N_BOOT:,} resamples, `stats.paired_difference_ci`). p: two-sided, giving a random sign to each day's sum of the paired differences ({N_DRAWS:,} draws, seed 0, so the smallest p is {1 / (N_DRAWS + 1):.5f}). Holm's step-down adjustment across the {len(SLOTS) * len(THRESHOLDS)} (predictor, threshold) cells at level {LEVEL}; a cell with no call has p = 1.", "",
             f"**Decision rule.** A cell is 'ahead of the rule' when its Holm-adjusted p is under {LEVEL} and its difference is positive, 'behind the rule' when the p is under {LEVEL} and the difference is negative, and 'not separated from the rule' otherwise. The answer to the question is yes only if at least one cell with at least {MIN_CALLS} calls is ahead of the rule. Cells with fewer than {MIN_CALLS} calls stay in the table and are left out of the sentences that name the largest and smallest difference.", "",
             f"**Secondary.** The share called, the mean and median crossing minute, the predictor's accuracy and the rule's, and the same paired difference restricted to calls made at minutes {EARLY[0]} to {EARLY[1]} (interval from days, no adjustment, descriptive).", "",
             f"**Calibration table.** For each minute 0 to 14 and each threshold in {', '.join(f'{t:.2f}' for t in CALIBRATION_THRESHOLDS)}: the share of windows where {CALIBRATION_MODEL}'s called-side probability is at or above the threshold and the hit rate of those calls, beside the same for the rule at that minute. Descriptive, no test.", "",
             "**Checks that stop the run.** The rule scored against itself differs by exactly zero in every cell with calls, the constant predictor makes no call, and the rule and at least one fitted predictor make calls. If any fails the run stops before it writes a result file.", "",
             "**Not tested here.** The comparison is with the window's own move, not with a market price. Whether a recorded bid and ask, with fees, lags the move at minutes 1 to 3 is a separate study on the tracking side."]
    data = {"written": stamp, "commit": commit, **info, "predictors": [{"name": n, "column_minute_0": c0, "column_after": c1} for n, c0, c1 in SLOTS],
            "thresholds": list(THRESHOLDS), "calibration_thresholds": list(CALIBRATION_THRESHOLDS), "calibration_model": CALIBRATION_MODEL, "early_minutes": list(EARLY),
            "min_calls": MIN_CALLS, "level": LEVEL, "n_boot": N_BOOT, "n_draws": N_DRAWS, "cells": len(SLOTS) * len(THRESHOLDS), "tolerance": TOL}
    return "\n".join(lines) + "\n", data


def git(*args) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip()


def write_prereg(out: Path = OUT) -> None:
    frames = load_frames(out)
    md, data = prereg_block(data_info(frames), git("rev-parse", "HEAD"), dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
    data["sha256"] = {f"oof_k{k}.parquet": sha256(out / f"oof_k{k}.parquet") for k in MINUTES}
    (out / f"{STEM}_prereg.md").write_text(md, encoding="utf-8")
    (out / f"{STEM}_prereg.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


def main():
    from threadpoolctl import threadpool_limits
    threadpool_limits(2)
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--prereg", action="store_true", help="write the pre-registration and stop")
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--n-draws", type=int, default=N_DRAWS)
    a = ap.parse_args()
    out = Path(a.out)
    if a.prereg:
        write_prereg(out)
        print(f"wrote {STEM}_prereg.md and .json to {out}")
        return
    t0 = time.time()
    frames = load_frames(out)
    info = {**data_info(frames), "n_boot": a.n_boot, "n_draws": a.n_draws}
    t, y, P, rule = stack(frames)
    cells = run_cells(t, y, P, rule, n_boot=a.n_boot, n_draws=a.n_draws)
    check_engaged(cells)                                    # a run that fails its checks prints no summary and writes no file
    cal = calibration_table(P, rule, y)
    cells.to_csv(out / f"{STEM}.csv", index=False)
    (out / f"{STEM}.md").write_text(render_cells(cells, info), encoding="utf-8")
    cal.to_csv(out / f"{STEM}_calibration.csv", index=False)
    (out / f"{STEM}_calibration.md").write_text(render_calibration(cal, info), encoding="utf-8")
    dirty = bool(git("status", "--porcelain", "--untracked-files=no"))
    (out / f"{STEM}.json").write_text(json.dumps({"ran_at": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "commit": git("rev-parse", "HEAD"), "dirty": dirty, **info,
                                                  "wall_seconds": round(time.time() - t0), "sha256": {f"oof_k{k}.parquet": sha256(out / f"oof_k{k}.parquet") for k in MINUTES}}, indent=2), encoding="utf-8")
    print(f"wrote {STEM} tables to {out} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
