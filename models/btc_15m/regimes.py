"""Market regimes 2017 to 2026: when they were, what distinguishes them beyond direction,
and whether the short-horizon effects depend on them.

Three parts.

  dating      bull and bear phases on daily closes by a threshold rule (Lunde and
              Timmermann 2004: a bull ends when the price falls BEAR_DROP from its running
              peak, a bear ends when it rises BULL_RISE from its running trough; phases are
              dated at the peak and the trough, so this uses the future and describes
              history only). Table: each phase with its dates, length, return and drawdown.
  states      a Gaussian hidden Markov model with N_STATES states on daily features (log
              return and log realised volatility, standardised on the training years), fit
              walk-forward by year and run FORWARD only (filtered probabilities), so the
              state assigned to a day uses that day and earlier days. The state of day d-1
              is the regime label for every minute of day d. States are named by their mean
              return and volatility in the training years.
  fingerprint for each dated phase type and each HMM state: realised volatility at one
              minute and one day, volume and trade count per minute, taker imbalance,
              1-minute and 15-minute return autocorrelation (the reversal), tail frequency,
              the hour of day with the most volatility, the weekend-to-weekday volatility
              ratio, and the one-bit reversal rule's accuracy. The last column is what the
              horizon cells need: the conditional cells scored within each HMM state.

    python -m models.btc_15m.regimes --start 2017-08 --end 2026-08
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM

from models.btc_15m.data import load
from models.btc_15m.features import HISTORY, Series, features_all
from models.btc_15m.horizons import candidates, labels
from models.btc_15m.rules import vol_cutoffs
from models.btc_15m.stats import block_bootstrap_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
BEAR_DROP, BULL_RISE = 0.15, 0.20
N_STATES = 3
TOP_CELLS = 24


# ---------------- daily series ----------------

def daily(frame: pd.DataFrame) -> pd.DataFrame:
    """One row per UTC day: close, log return, realised volatility from 1-minute returns
    (annualised not needed; bp per minute), volume, trades, taker imbalance."""
    f = frame[frame.ok].copy()
    f["day"] = f.t // 86400
    f["r1"] = np.log(f.close).diff() * 1e4
    g = f.groupby("day")
    d = pd.DataFrame({"t": g.t.max() + 60, "close": g.close.last(), "rv": g.r1.std(), "volume": g.volume.sum(), "trades": g.trades.sum(),
                      "taker": (2 * g.taker_buy.sum() - g.volume.sum()) / g.volume.sum(), "n_min": g.size()})
    d = d[d.n_min >= 1000].copy()                      # days with most minutes present
    d["ret"] = np.log(d.close).diff()
    return d.dropna().reset_index(drop=True)


# ---------------- dating ----------------

def date_phases(close: np.ndarray, t: np.ndarray, bear_drop=BEAR_DROP, bull_rise=BULL_RISE) -> pd.DataFrame:
    """Lunde-Timmermann threshold dating. Returns phases with start/end indexes, type,
    length in days, return and the largest drawdown (bull) or rally (bear) inside."""
    phases = []
    state = "bull" if close[np.argmax(close[:60])] > close[0] else "bear"
    start = 0
    ext_i = 0                                           # running peak (bull) or trough (bear)
    for i in range(1, len(close)):
        if state == "bull":
            if close[i] > close[ext_i]:
                ext_i = i
            elif close[i] <= close[ext_i] * (1 - bear_drop):
                phases.append((start, ext_i, "bull"))
                state, start, ext_i = "bear", ext_i, i
        else:
            if close[i] < close[ext_i]:
                ext_i = i
            elif close[i] >= close[ext_i] * (1 + bull_rise):
                phases.append((start, ext_i, "bear"))
                state, start, ext_i = "bull", ext_i, i
    phases.append((start, len(close) - 1, state + " (open)"))
    rows = []
    for a, b, kind in phases:
        seg = close[a:b + 1]
        if kind.startswith("bull"):
            inside = (seg / np.maximum.accumulate(seg) - 1).min()
        else:
            inside = (seg / np.minimum.accumulate(seg) - 1).max()
        rows.append({"start": pd.to_datetime(t[a], unit="s").date(), "end": pd.to_datetime(t[b], unit="s").date(), "phase": kind, "days": b - a,
                     "return": seg[-1] / seg[0] - 1, "largest_move_against": inside, "a": a, "b": b})
    return pd.DataFrame(rows)


def phase_label_per_day(P: pd.DataFrame, n: int) -> np.ndarray:
    lab = np.array([""] * n, dtype=object)
    for r in P.itertuples():
        lab[r.a:r.b + 1] = r.phase.split(" ")[0]
    return lab


# ---------------- HMM ----------------

def hmm_states(D: pd.DataFrame, n_states=N_STATES, seed=0) -> tuple[np.ndarray, pd.DataFrame]:
    """Filtered (forward-only) state per day, walk-forward by calendar year: the model for
    year Y is fit on all days before Y; the state of day d uses days <= d. Returns the state
    per day (NaN for the first training years) and a table naming the states."""
    years = pd.to_datetime(D.t, unit="s").dt.year.values
    X_raw = np.column_stack([D.ret.values, np.log(D.rv.values)])
    state = np.full(len(D), np.nan)
    names = {}
    for Y in sorted(set(years))[2:]:
        tr = years < Y
        mu, sd = X_raw[tr].mean(0), X_raw[tr].std(0)
        Xtr = (X_raw[tr] - mu) / sd
        m = GaussianHMM(n_components=n_states, covariance_type="full", n_iter=200, random_state=seed).fit(Xtr)
        # name states by training mean return and volatility, so labels are comparable across years
        means = m.means_
        order = np.argsort(means[:, 1])                  # by volatility
        label = {}
        for rank, k in enumerate(order):
            vol = ["low", "mid", "high"][rank] if n_states == 3 else f"v{rank}"
            label[k] = f"{vol} vol, {'up' if means[k, 0] > 0.05 else 'down' if means[k, 0] < -0.05 else 'flat'}"
        # forward filtering through year Y given all history: use the model on the full sequence up to each day
        upto = years <= Y
        Xall = (X_raw[upto] - mu) / sd
        fwd = forward_filter(m, Xall)                      # filtered, not smoothed: no look-ahead inside the year
        st = fwd.argmax(axis=1)
        sel = np.where(upto)[0]
        this_year = years[sel] == Y
        state[sel[this_year]] = st[this_year]
        names[Y] = label
    # make the state index meaningful across years by mapping each year's states to their names
    named = np.array([""] * len(D), dtype=object)
    for i in range(len(D)):
        if not np.isnan(state[i]):
            named[i] = names[years[i]][int(state[i])]
    return named, pd.DataFrame([{"year": y, **{f"state {k}": v for k, v in lab.items()}} for y, lab in names.items()])


def forward_filter(model: GaussianHMM, X: np.ndarray) -> np.ndarray:
    """P(state_t | x_1..x_t) for each t: the forward algorithm, normalised at each step."""
    from scipy.stats import multivariate_normal
    n, k = len(X), model.n_components
    B = np.column_stack([multivariate_normal(model.means_[j], model.covars_[j], allow_singular=True).pdf(X) for j in range(k)])
    B = np.maximum(B, 1e-300)
    alpha = np.zeros((n, k))
    a = model.startprob_ * B[0]
    alpha[0] = a / a.sum()
    for t in range(1, n):
        a = (alpha[t - 1] @ model.transmat_) * B[t]
        alpha[t] = a / a.sum()
    return alpha


# ---------------- fingerprints ----------------

def fingerprint(s: Series, minute_label: np.ndarray, label_values: list[str]) -> list[list]:
    """One row per regime label with the microstructure characteristics."""
    r1 = s.r1
    ok = s.ok
    hours = (s.t // 3600) % 24
    wday = (s.t // 86400 + 3) % 7
    rows = []
    # 15-minute returns on the quarter-hour grid and the reversal rule
    grid = np.where((s.t % 900 == 0) & (np.arange(len(s.t)) + 15 <= len(s.t)))[0]
    r15 = (s.c[grid + 14] / s.o[grid] - 1) * 1e4
    prev15 = np.concatenate([[np.nan], r15[:-1]])
    for lab in label_values:
        m = (minute_label == lab) & ok
        if m.sum() < 10_000:
            continue
        x = r1[m]
        tail = np.mean(np.abs(x) > 4 * x.std())
        ac1 = np.corrcoef(r1[:-1][m[1:] & m[:-1]], r1[1:][m[1:] & m[:-1]])[0, 1]
        mg = m[grid]
        gg = mg[1:] & mg[:-1]
        ac15 = np.corrcoef(prev15[1:][gg], r15[1:][gg])[0, 1]
        hit = (np.sign(r15[1:][gg]) == -np.sign(prev15[1:][gg])).astype(float)
        acc, lo, hi = block_bootstrap_ci(hit, s.t[grid][1:][gg])
        hv = pd.Series(x).groupby(hours[m]).std()
        wk = r1[m & (wday >= 5)].std() / r1[m & (wday < 5)].std()
        days = len(np.unique(s.t[m] // 86400))
        rows.append([lab, days, f"{x.std():.2f}", f"{(x.std() * np.sqrt(1440)):.0f}", f"{s.v[m].mean():.1f}", f"{s.n[m].mean():.0f}",
                     f"{((2 * s._raw[1][m] - s.v[m]).sum() / s.v[m].sum())*100:+.1f}%", f"{ac1:+.3f}", f"{ac15:+.3f}", f"{tail*100:.2f}%",
                     f"{int(hv.idxmax()):02d}:00", f"{wk:.2f}", f"{acc*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]"])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2017-08")
    ap.add_argument("--end", default="2026-08")
    a = ap.parse_args()
    frame = load(a.start, a.end)
    s = Series(frame)
    D = daily(frame)
    P = date_phases(D.close.values, D.t.values)
    P_wide = date_phases(D.close.values, D.t.values, bear_drop=0.30, bull_rise=0.40)
    named, names = hmm_states(D)
    D["phase"] = phase_label_per_day(P, len(D))
    D["hmm"] = named
    D.to_csv(OUT / "regimes_daily.csv", index=False)

    # per-minute labels from the PREVIOUS day's state (known at the time) and the dated phase
    day_of_minute = s.t // 86400
    day_index = pd.Series(np.arange(len(D)), index=(D.t.values - 60) // 86400)     # D.t is the day's last close time
    prev_day_row = day_index.reindex(day_of_minute - 1).values
    hmm_minute = np.array([D.hmm.iloc[int(k)] if not np.isnan(k) else "" for k in prev_day_row], dtype=object)
    phase_minute = np.array([D.phase.iloc[int(k)] if not np.isnan(k) else "" for k in day_index.reindex(day_of_minute).values], dtype=object)

    hmm_labels = sorted(x for x in set(hmm_minute) if x)
    fp_phase = fingerprint(s, phase_minute, ["bull", "bear"])
    fp_hmm = fingerprint(s, hmm_minute, hmm_labels)

    # the horizon cells within each HMM state (pooled over years, filtered state known at the time)
    cell_rows = []
    F = features_all(s)
    F = F[F.t >= int(pd.Timestamp("2018-01-01").timestamp())].reset_index(drop=True)
    cut = vol_cutoffs(F[pd.to_datetime(F.t, unit="s").dt.year == 2018])
    C = candidates(F, cut)
    L = labels(s, F.i.values)
    st = pd.Series(hmm_minute, index=np.arange(len(s.t))).reindex(F.i.values).values
    top = pd.read_csv(OUT / "horizons_summary.csv")
    top = top[top.years_held == top.years].sort_values("deviation", key=np.abs, ascending=False).head(TOP_CELLS)
    for r in top.itertuples():
        m = C[r.pattern]
        y = L[int(r.horizon)]
        ok = ~np.isnan(y)
        row = [r.pattern, int(r.horizon), f"{r.deviation*100:+.1f}"]
        for lab in hmm_labels:
            sel = ok & (st == lab)
            if (m & sel).sum() < 300:
                row.append("")
                continue
            dev = y[m & sel].mean() - y[sel].mean()
            _, lo, hi = block_bootstrap_ci(y[m & sel] - y[sel].mean(), F.t.values[m & sel], n_boot=500)
            row.append(f"{dev*100:+.1f} [{lo*100:+.1f}, {hi*100:+.1f}] n={int((m & sel).sum()):,}")
        cell_rows.append(row)

    with open(OUT / "regimes.md", "w") as f:
        f.write(f"Bull and bear phases on daily closes, {a.start} to {a.end}, by the threshold rule: a bull ends when the price falls {BEAR_DROP*100:.0f}% from its running peak, a bear ends when it rises {BULL_RISE*100:.0f}% from its running trough; phases are dated at the peak and trough, so this table uses the future and describes history only.\n\n")
        f.write("| start | end | phase | days | return | largest move against |\n|---|---|---|---|---|---|\n")
        for r in P.itertuples():
            f.write(f"| {r.start} | {r.end} | {r.phase} | {r.days} | {r._5*100:+.0f}% | {r.largest_move_against*100:+.0f}% |\n")
        f.write("\nThe same rule with wider thresholds (a 30% fall ends a bull, a 40% rise ends a bear), for the major cycles.\n\n| start | end | phase | days | return | largest move against |\n|---|---|---|---|---|---|\n")
        for r in P_wide.itertuples():
            f.write(f"| {r.start} | {r.end} | {r.phase} | {r.days} | {r._5*100:+.0f}% | {r.largest_move_against*100:+.0f}% |\n")
        f.write(f"\nHidden Markov model with {N_STATES} states on daily log return and log realised volatility, fit walk-forward on all earlier years and run forward only (the state of a day uses that day and earlier ones). States are named by their training-year mean return and volatility; the names can differ slightly between years.\n\n")
        f.write("| year | " + " | ".join(names.columns[1:]) + " |\n|---|" + "---|" * (len(names.columns) - 1) + "\n")
        for r in names.itertuples(index=False):
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        hdr = "| regime | days | 1-min vol (bp) | daily vol (bp) | volume per min | trades per min | taker imbalance | 1-min autocorr | 15-min autocorr | tail share | peak hour (UTC) | weekend/weekday vol | reversal rule [95% CI] |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
        f.write("\nFingerprint by dated phase (minutes inside bull and bear phases). Tail share is the share of minutes moving more than four of that regime's standard deviations; the reversal rule is 'call the opposite of the previous 15 minutes' on the quarter-hour grid.\n\n" + hdr)
        for r in fp_phase:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        f.write("\nFingerprint by HMM state (the previous day's filtered state, known at the time).\n\n" + hdr)
        for r in fp_hmm:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        f.write(f"\nThe {TOP_CELLS} strongest conditional cells (from horizons.md) within each HMM state, 2018 onward: deviation of the up-rate from the state's own unconditional rate, points, day-block 95% interval, firings.\n\n")
        f.write("| pattern | horizon (min) | all states | " + " | ".join(hmm_labels) + " |\n|---|---|---|" + "---|" * len(hmm_labels) + "\n")
        for r in cell_rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print("wrote regimes.md")


if __name__ == "__main__":
    main()
