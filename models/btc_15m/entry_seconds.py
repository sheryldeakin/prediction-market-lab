"""The window call made seconds after the open, from the per-second tick aggregates.

Study 24 priced an entry N seconds after the open; this study asks what the call itself is
worth there. At N = 10, 30 and 60 seconds the window's own lead is a handful of trades old,
and the question is how fast it becomes informative: a one-bit rule on its sign, the
one-feature logistic on the lead scaled by the volatility left in the window, and the forest
and XGBoost on the minute-0 feature set plus the tick features.

Per-window tick features at N seconds (seconds are counted from the window open t):

    lead_N     (VWAP of the second [t+N-1, t+N) / open reference - 1) in bp. The open
               reference is the VWAP of the first traded second at or after t. When the
               second [t+N-1, t+N) has no trades the last VWAP before it is used (the
               fallback of study 24, which looked back five seconds; here any distance,
               never before t), and the share of windows that needed it is reported.
               A window with no trade at all in [t, t+N) gets lead 0 and is counted.
    flow_N     signed volume / volume over [t, t+N)
    n_N        trades over [t, t+N)
    big_N      large trades (previous day's 99th percentile, see ticks.py) over [t, t+N)
    lead_z_N   lead_N / (vol60 * sqrt(WINDOW - N / 60)), vol60 from the minute-0 features

The tick pass runs month by month and is cached per month under data/feature_cache, one row
per quarter-hour window, so reruns skip it.

Part (a) is the study period of the main table (walk-forward by month, test months after the
first three, the same windows as walk_forward.md) with the open and minute-3 rows read from
the existing out-of-fold predictions on the same windows. Part (b) is the rule only, year by
year from 2018, day-clustered intervals.

    python -m models.btc_15m.entry_seconds --start 2025-10 --end 2026-08
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m import evaluate
from models.btc_15m.data import load
from models.btc_15m.evaluate import ALL, N_JOBS, add_baseline_columns, format_p, score, walk_forward
from models.btc_15m.features import CACHE_DIR, WINDOW, Series, dataset
from models.btc_15m.log import current_model_id
from models.btc_15m.stats import block_bootstrap_ci, day_sign_test, paired_difference_ci
from models.btc_15m.ticks import load_seconds, tick_path

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
ENTRIES = (10, 30, 60)
CACHE_VERSION = 1
TICK_COLS = ["tk_lead", "tk_flow", "tk_n", "tk_big", "tk_leadz"]
LADDER = {"open": 0, "10 s": 10, "30 s": 30, "60 s": 60, "minute 3": 180}


# ---------------------------------------------------------------- pure pieces (tested)

def tick_entry_features(r: pd.DataFrame, t_open: np.ndarray, n_sec: int) -> pd.DataFrame:
    """Tick features at n_sec seconds after each window open in t_open, from the per-second
    table r (columns sec, vol, qty, svol, n, big_n). One row per window, in t_open's order."""
    r = r[r.qty > 0].sort_values("sec")
    sec = r.sec.values.astype(np.int64)
    vw = (r.vol.values / r.qty.values).astype(float)
    cum = {k: np.concatenate([[0.0], np.cumsum(r[k].values)]) for k in ("vol", "svol", "n", "big_n")}
    t = np.asarray(t_open, dtype=np.int64)
    last = max(len(sec) - 1, 0)
    if len(sec) == 0:
        z = np.zeros(len(t))
        return pd.DataFrame({"open_px": np.nan, "px": np.nan, "lead": z, "flow": z, "n": z, "big": z,
                             "fallback": False, "nodata": True}, index=range(len(t)))
    i0 = np.searchsorted(sec, t, "left")                          # first traded second at or after t
    has_open = (i0 < len(sec)) & (sec[np.minimum(i0, last)] < t + n_sec)
    i1 = np.searchsorted(sec, t + n_sec - 1, "left")              # first traded second at or after t+N-1
    exact = (i1 < len(sec)) & (sec[np.minimum(i1, last)] == t + n_sec - 1)
    j = np.maximum(i1 - 1, 0)                                     # last traded second before t+N-1
    back = (i1 - 1 >= 0) & (sec[j] >= t) & ~exact
    px = np.where(exact, vw[np.minimum(i1, last)], np.where(back, vw[j], np.nan))
    open_px = np.where(has_open, vw[np.minimum(i0, last)], np.nan)
    lead = np.where(has_open, (px / open_px - 1) * 1e4, 0.0)
    end = np.searchsorted(sec, t + n_sec, "left")
    s = {k: np.where(has_open, c[end] - c[np.minimum(i0, len(sec))], 0.0) for k, c in cum.items()}
    flow = np.where(s["vol"] > 0, s["svol"] / np.where(s["vol"] > 0, s["vol"], 1.0), 0.0)
    return pd.DataFrame({"open_px": open_px, "px": px, "lead": lead, "flow": flow, "n": s["n"], "big": s["big_n"],
                         "fallback": has_open & back, "nodata": ~has_open})


def lead_z(lead_bp: np.ndarray, vol60: np.ndarray, n_sec: float) -> np.ndarray:
    """The lead in units of the volatility expected over the rest of the window; the same
    scaling as evaluate.add_baseline_columns with k = n_sec / 60 minutes."""
    return lead_bp / (vol60 * np.sqrt(WINDOW - n_sec / 60) + 1e-9)


def lead_sign_call(lead_bp: np.ndarray, prev_up: np.ndarray) -> np.ndarray:
    """The one-bit rule at an entry: 1 (up) if the lead is above zero, 0 (down) if below,
    and the previous-window rule (the opposite of the previous window) when exactly zero."""
    lead_bp, prev_up = np.asarray(lead_bp), np.asarray(prev_up)
    return np.where(lead_bp > 0, 1, np.where(lead_bp < 0, 0, 1 - prev_up)).astype(int)


def join_existing(oof: pd.DataFrame, t: np.ndarray) -> pd.DataFrame:
    """The existing out-of-fold predictions on exactly the windows t, in t's order."""
    missing = np.setdiff1d(t, oof.t.values)
    if len(missing):
        raise ValueError(f"{len(missing)} windows have no out-of-fold prediction (first t={missing[0]}); rerun evaluate.py")
    return oof.set_index("t").loc[t].reset_index()


def month_starts(month: str) -> np.ndarray:
    p = pd.Period(month, "M")
    return np.arange(p.start_time.value // 10**9, (p + 1).start_time.value // 10**9, 900)


# ---------------------------------------------------------------- tick pass, cached per month

def month_table(month: str) -> pd.DataFrame:
    """Tick features at every entry for every quarter-hour window opening in the month."""
    path = tick_path(month)
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing; this study does not download data")
    cache = CACHE_DIR / f"entry_seconds-v{CACHE_VERSION}-{month}-{path.stat().st_size}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    t = month_starts(month)
    r = load_seconds(month, month)
    out = {"t": t}
    for n in ENTRIES:
        f = tick_entry_features(r, t, n)
        for c in f.columns:
            out[f"{c}_{n}"] = f[c].values
    T = pd.DataFrame(out)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    T.to_parquet(cache, index=False)
    return T


def tick_table(months: list[str]) -> pd.DataFrame:
    return pd.concat([month_table(m) for m in months], ignore_index=True)


# ---------------------------------------------------------------- part (a)

def _fmt_ci(m, lo, hi, pct=True, sign=False):
    f = (lambda x: f"{x*100:+.2f}") if sign else (lambda x: f"{x*100:.2f}")
    return f"{f(m)}{'%' if pct and not sign else ''} [{f(lo)}, {f(hi)}]"


def ladder_row(entry: str, model: str, y, t, prob, call_up, base_hits, base_name, n_draws=2000) -> dict:
    hits = (call_up == y).astype(float)
    m, lo, hi = block_bootstrap_ci(hits, t)
    sc = score(prob, y)
    r = {"entry": entry, "entry_seconds": LADDER[entry], "model": model, "n": len(y), "accuracy": m, "ci_low": lo, "ci_high": hi,
         "auc": sc["auc"], "log_loss": sc["log_loss"], "baseline": base_name}
    if base_hits is not None:
        d, dlo, dhi = paired_difference_ci(hits, base_hits, t)
        sg = day_sign_test(hits, base_hits, t, n_draws=n_draws)
        r.update({"diff": d, "diff_low": dlo, "diff_high": dhi, "days_better": sg["share_days_a_better"], "sign_p": sg["p"]})
    return r


def study_period(start: str, end: str, log=print):
    """Rows of the ladder table, the per-entry tick diagnostics and the checks that the joins are sound."""
    s = Series(load(start, end))
    D = add_baseline_columns(dataset(s, 0), 0)
    months = [str(p) for p in pd.period_range(start, end, freq="M")]
    T = tick_table(months)
    D = D.merge(T, on="t", how="left")
    assert not D[[f"lead_{n}" for n in ENTRIES]].isna().any().any(), "windows without tick rows"
    pb, y, _, t = walk_forward(D, ["prev_up"], "bitrate")
    E = D.set_index("t").loc[t]
    reversal_agrees = float(((pb > 0.5) == (E.prev_up.values == 0)).mean())
    oof0 = join_existing(pd.read_parquet(OUT / "oof_k0.parquet"), t)
    assert (oof0.y.values == y).all(), "stored out-of-fold labels disagree with the rebuilt windows"
    rows, diag = [], []
    rows.append(ladder_row("open", "prev-window", y, t, oof0["prev-window"].values, oof0["prev-window"].values > 0.5, None, "prev-window"))
    base = ((oof0["prev-window"].values > 0.5) == y).astype(float)
    rows.append(ladder_row("open", "forest", y, t, oof0["forest"].values, oof0["forest"].values > 0.5, base, "prev-window"))
    ix = np.searchsorted(s.t, E.index.values)
    for n in ENTRIES:
        lab = f"{n} s"
        D["tk_lead"], D["tk_flow"], D["tk_n"], D["tk_big"] = D[f"lead_{n}"], D[f"flow_{n}"], D[f"n_{n}"], D[f"big_{n}"]
        D["tk_leadz"] = lead_z(D.tk_lead.values, D.vol60.values, n)
        D["ls_call"] = lead_sign_call(D.tk_lead.values, D.prev_up.values)
        p_ls, _, _, t1 = walk_forward(D, ["ls_call"], "bitrate")
        assert (t1 == t).all()
        call = D.set_index("t").loc[t, "ls_call"].values
        rule_hits = (call == y).astype(float)
        rows.append(ladder_row(lab, "lead-sign", y, t, p_ls, call, None, "lead-sign"))
        for name, cols, kind in (("lead-z", ["tk_leadz"], "logistic"), ("forest+ticks", ALL + TICK_COLS, "forest"), ("xgb+ticks", ALL + TICK_COLS, "xgb")):
            p, _, _, t2 = walk_forward(D, cols, kind)
            assert (t2 == t).all()
            rows.append(ladder_row(lab, name, y, t, p, p > 0.5, rule_hits, "lead-sign"))
            log(f"{lab} {name}: {rows[-1]['accuracy']*100:.2f}%")
        kl = (E[f"px_{n}"].values / s.o[ix] - 1) * 1e4
        tl = E[f"lead_{n}"].values
        diag.append({"entry": lab, "windows": len(t), "fallback": float(E[f"fallback_{n}"].mean()), "no_trade_at_all": float(E[f"nodata_{n}"].mean()),
                     "lead_zero": float((tl == 0).mean()), "sign_differs_from_candle_open": float((np.sign(tl) != np.sign(np.where(E[f"nodata_{n}"].values, 0.0, kl))).mean())})
    # minute 3, from the klines and the stored predictions
    D3 = add_baseline_columns(dataset(s, 3), 3)
    D3["ls_call"] = lead_sign_call(D3.lead.values, D3.prev_up.values)
    p3, y3, _, t3 = walk_forward(D3, ["ls_call"], "bitrate")
    oof3 = join_existing(pd.read_parquet(OUT / "oof_k3.parquet"), t)
    assert (t3 == t).all() and (oof3.y.values == y).all(), "minute-3 windows differ from the minute-0 windows"
    base3 = ((oof3["lead-z"].values > 0.5) == y).astype(float)
    rows.append(ladder_row("minute 3", "lead-z", y, t, oof3["lead-z"].values, oof3["lead-z"].values > 0.5, None, "lead-z"))
    rows.append(ladder_row("minute 3", "lead-sign", y, t, p3, D3.set_index("t").loc[t, "ls_call"].values, base3, "lead-z"))
    rows.append(ladder_row("minute 3", "xgb-all", y, t, oof3["xgb-all"].values, oof3["xgb-all"].values > 0.5, base3, "lead-z"))
    checks = {"windows": int(len(t)), "reversal_agrees_with_prev_window_rule": reversal_agrees, "first_test_month": str(pd.to_datetime(t[0], unit="s").to_period("M")),
              "last_test_month": str(pd.to_datetime(t[-1], unit="s").to_period("M"))}
    wf = OUT / "walk_forward.csv"
    if wf.exists():
        W = pd.read_csv(wf)
        w0 = W[(W.minute == 0) & (W.model == "prev-window")]
        if len(w0) and int(w0.n_test.iloc[0]) == len(t):
            checks["matches_walk_forward_csv"] = bool(abs(float(w0.accuracy.iloc[0]) - rows[0]["accuracy"]) < 1e-9)
            assert checks["matches_walk_forward_csv"], "stored predictions do not reproduce walk_forward.csv"
    return rows, diag, checks


def write_ladder(rows: list[dict], diag: list[dict], out: Path, start: str, end: str):
    R = pd.DataFrame(rows)
    R.to_csv(out / "entry_seconds.csv", index=False)
    widths = (R.diff_high - R.diff_low).dropna()
    with open(out / "entry_seconds.md", "w") as f:
        f.write(f"The window call by entry time, walk-forward by month, {start} to {end}, test months after the first three (the windows of the main table). "
                "Open and minute 3 are the stored out-of-fold predictions of the main table on the same windows. Entries at 10, 30 and 60 seconds: lead-sign calls up when the lead at that second is above the open, down when below, and the previous-window rule when exactly zero (its AUC and log loss use the training up-rate of each call); lead-z is the one-feature logistic on the lead scaled by the volatility left in the window; "
                "forest+ticks and xgb+ticks are the minute-0 feature set plus the tick features at that second (lead, signed-volume share, trades, large trades, lead-z), on CPU. "
                "Accuracy has a day-block 95% interval. The last columns are accuracy minus the entry's one-bit rule on the same windows (named in the cell; at minute 3 it is the lead z-score, as in checks.md), day-block interval, share of days better, sign-flip p.\n\n")
        f.write("| entry | model | n | accuracy [95% CI] | AUC | log loss | vs one-bit rule | days better | sign p |\n|---|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            acc = _fmt_ci(r["accuracy"], r["ci_low"], r["ci_high"])
            if "diff" in r and not pd.isna(r.get("diff")):
                vs = f"{_fmt_ci(r['diff'], r['diff_low'], r['diff_high'], sign=True)} vs {r['baseline']}"
                days, p = f"{r['days_better']*100:.0f}%", format_p(r['sign_p'], 2000)
            else:
                vs, days, p = "baseline" if r["model"] == r["baseline"] else "", "", ""
            f.write(f"| {r['entry']} | {r['model']} | {r['n']} | {acc} | {r['auc']:.3f} | {r['log_loss']:.4f} | {vs} | {days} | {p} |\n")
        f.write(f"\nWhat these windows could detect: the day-block interval on a difference from the entry's rule is {widths.min()*100:.2f} to {widths.max()*100:.2f} points wide across the rows above, "
                f"so an increment smaller than about {widths.min()*50:.2f} to {widths.max()*50:.2f} points could not be told from zero. A null here is a bound of that width, not a verdict.\n\n")
        vs_rule = R[(R.baseline == "lead-sign") & (R.model != "lead-sign")].dropna(subset=["diff"])
        hit = vs_rule[(vs_rule.diff_low > 0) | (vs_rule.diff_high < 0)]
        listed = "; ".join(f"{r.model} at {r.entry} ({r.diff*100:+.2f})" for r in hit.itertuples()) or "none"
        f.write(f"Of the {len(vs_rule)} comparisons with the lead-sign rule at 10, 30 and 60 seconds, {len(hit)} have a day-block interval that excludes zero: {listed}. "
                "The intervals are not adjusted for the number of comparisons. The fitted models differ from the rule in two ways at once, they use the tick features and they use the minute-0 features, and no row separates the two.\n\n")
        f.write("Tick coverage at each entry over the scored windows: the share whose second [t+N-1, t+N) had no trade (the last earlier VWAP was used), the share with no trade at all in [t, t+N), the share whose lead is exactly zero, and the share whose lead has a different sign when measured against the candle open instead of the first traded second's VWAP.\n\n")
        f.write("| entry | windows | fallback used | no trade in [t, t+N) | lead exactly zero | sign differs from candle-open lead |\n|---|---|---|---|---|---|\n")
        for d in diag:
            f.write(f"| {d['entry']} | {d['windows']} | {d['fallback']*100:.2f}% | {d['no_trade_at_all']*100:.2f}% | {d['lead_zero']*100:.2f}% | {d['sign_differs_from_candle_open']*100:.2f}% |\n")


# ---------------------------------------------------------------- part (b)

def year_windows(year: int, last: str) -> pd.DataFrame:
    """Quarter-hour windows opening in `year` (up to month `last`) whose own candles and the
    previous window's are all present: the label, the previous window's direction and the
    candle lead at minutes 1 and 3."""
    f = load(f"{year - 1}-12", min(f"{year}-12", last))
    t, o, c, ok = f.t.values.astype(np.int64), f.open.values, f.close.values, f.ok.values
    bad = np.concatenate([[0], np.cumsum(~ok)])
    i = np.nonzero(t % 900 == 0)[0]
    i = i[(i >= WINDOW) & (i + WINDOW <= len(t))]
    i = i[(bad[i + WINDOW] - bad[i - WINDOW]) == 0]
    i = i[pd.to_datetime(t[i], unit="s").year == year]
    return pd.DataFrame({"t": t[i], "y": (c[i + WINDOW - 1] >= o[i]).astype(int), "prev_up": (c[i - 1] >= o[i - WINDOW]).astype(int),
                         "lead_m1": (c[i] / o[i] - 1) * 1e4, "lead_m3": (c[i + 2] / o[i] - 1) * 1e4})


def years_table(first: int, last: str, log=print) -> pd.DataFrame:
    rows = []
    for year in range(first, int(last[:4]) + 1):
        W = year_windows(year, last)
        months = [str(p) for p in pd.period_range(f"{year}-01", min(f"{year}-12", last), freq="M")]
        W = W.merge(tick_table(months), on="t", how="inner")
        had = len(W)
        W = W[~np.any([W[f"nodata_{n}"].values for n in ENTRIES], axis=0)]
        hits = {"open": ((1 - W.prev_up.values) == W.y.values)}
        for n in ENTRIES:
            hits[f"{n} s"] = lead_sign_call(W[f"lead_{n}"].values, W.prev_up.values) == W.y.values
        hits["minute 1"] = lead_sign_call(W.lead_m1.values, W.prev_up.values) == W.y.values
        hits["minute 3"] = lead_sign_call(W.lead_m3.values, W.prev_up.values) == W.y.values
        r = {"year": year, "windows": len(W), "dropped_no_trade": had - len(W), "fallback_10": float(W.fallback_10.mean())}
        for k, h in hits.items():
            m, lo, hi = block_bootstrap_ci(h.astype(float), W.t.values)
            r[k], r[f"{k} lo"], r[f"{k} hi"] = m, lo, hi
        rows.append(r)
        W["year"] = year
        log(f"{year}: {len(W)} windows, open {r['open']*100:.2f}%, 10 s {r['10 s']*100:.2f}%, 60 s {r['60 s']*100:.2f}%, minute 3 {r['minute 3']*100:.2f}%")
        rows[-1]["_t"], rows[-1]["_hits"] = W.t.values, {k: h.astype(float) for k, h in hits.items()}
        rows[-1]["_fb"] = W.fallback_10.values
    allw = {"year": "all", "windows": sum(r["windows"] for r in rows), "dropped_no_trade": sum(r["dropped_no_trade"] for r in rows)}
    tt = np.concatenate([r["_t"] for r in rows])
    allw["fallback_10"] = float(np.concatenate([r["_fb"] for r in rows]).mean())
    for k in rows[0]["_hits"]:
        h = np.concatenate([r["_hits"][k] for r in rows])
        m, lo, hi = block_bootstrap_ci(h, tt)
        allw[k], allw[f"{k} lo"], allw[f"{k} hi"] = m, lo, hi
    for r in rows:
        r.pop("_t"), r.pop("_hits"), r.pop("_fb")
    return pd.DataFrame(rows + [allw])


def write_years(Y: pd.DataFrame, out: Path, first: int, last: str):
    Y.to_csv(out / "entry_seconds_years.csv", index=False)
    cols = ["open", "10 s", "30 s", "60 s", "minute 1", "minute 3"]
    with open(out / "entry_seconds_years.md", "w") as f:
        f.write(f"The one-bit rules by year, {first} to {last}, quarter-hour windows whose own and previous candles are present and that have a trade in the first 60 seconds. "
                "Open: the opposite of the previous window. 10 s, 30 s, 60 s: up if the tick lead at that second is above the open, down if below, the open rule if exactly zero. Minute 1 and minute 3: the same rule on the candle lead (close of the last closed minute against the window open). "
                "Accuracy with day-block 95% intervals; the last column is the share of windows whose second 10 had no trade, so the last VWAP before it was used.\n\n")
        f.write("| year | windows | " + " | ".join(cols) + " | no trade at second 10 |\n|---|---|" + "---|" * (len(cols) + 1) + "\n")
        for _, r in Y.iterrows():
            cells = [_fmt_ci(r[c], r[f"{c} lo"], r[f"{c} hi"]) for c in cols]
            f.write(f"| {r['year']} | {int(r['windows'])} | " + " | ".join(cells) + f" | {r['fallback_10']*100:.2f}% |\n")
        Z = Y[Y.year != "all"]
        f.write("\nSpread across years for each column: the year with the lowest and the year with the highest accuracy, and whether their day-block intervals overlap.\n\n"
                "| column | lowest year | its accuracy | highest year | its accuracy | intervals overlap |\n|---|---|---|---|---|---|\n")
        for c in cols:
            lo_r, hi_r = Z.loc[Z[c].idxmin()], Z.loc[Z[c].idxmax()]
            overlap = lo_r[f"{c} hi"] >= hi_r[f"{c} lo"]
            f.write(f"| {c} | {lo_r['year']} | {lo_r[c]*100:.2f}% | {hi_r['year']} | {hi_r[c]*100:.2f}% | {'yes' if overlap else 'no'} |\n")
        f.write(f"\nIn {int((Z.apply(lambda r: all(r[a] < r[b] for a, b in zip(cols[1:], cols[2:])), axis=1)).sum())} of the {len(Z)} years the accuracy rises at every step from 10 s to 30 s, 60 s, minute 1 and minute 3.\n")


# ---------------------------------------------------------------- entry point

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--years-from", type=int, default=2018)
    ap.add_argument("--out", default=str(OUT), help="output directory (a smoke run points this elsewhere)")
    a = ap.parse_args()
    evaluate.XGB_DEVICE = "cpu"                     # this study is CPU only
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "models"], capture_output=True, text=True).stdout.strip())
    rows, diag, checks = study_period(a.start, a.end, log=lambda m: print(m, flush=True))
    write_ladder(rows, diag, out, a.start, a.end)
    print(f"part (a) done in {time.time()-t0:.0f}s", flush=True)
    Y = years_table(a.years_from, a.end, log=lambda m: print(m, flush=True))
    write_years(Y, out, a.years_from, a.end)
    (out / "entry_seconds.json").write_text(json.dumps({
        "ran_at": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "commit": commit, "dirty": dirty, "model_id": current_model_id(),
        "device": "cpu", "threads": N_JOBS, "seconds": round(time.time() - t0), "start": a.start, "end": a.end, "years_from": a.years_from,
        "checks": checks, "coverage": diag}, indent=2))
    print(f"wrote entry_seconds.md, entry_seconds_years.md, .csv and .json to {out} in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
