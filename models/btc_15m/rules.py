"""Event-conditioned predictions: "if X happens, is the window more likely up or down?"

Part 1, an event library. Each event is a boolean condition on the features known at the
entry minute (all scale-free or in basis points). For every event: how often it fires,
the up-rate when it fires, a day-block 95% interval, and the two-sided p-value of the
up-rate against the unconditional rate. With dozens of events tested at once, chance
alone produces a few "significant" ones, so p-values are corrected (Benjamini-Hochberg,
false discovery rate 10%) and the survivors are re-checked month by month: an event
counts as stable only if the direction it had in the first three months (the reference
months, which every walk-forward uses for training only) holds in at least three quarters
of the later months. The reference direction is fixed before the later months are seen;
comparing months against the pooled direction would count each month against a sign it
helped set. Volatility deciles are cut on the reference months for the same reason.

Part 2, learned rules. A depth-2 decision tree per test month, trained on earlier
months, printed as readable rules. A rule is reported when the same split appears in
most months.

    python -m models.btc_15m.rules --start 2025-10 --end 2026-08 --minutes 0,3
"""
from __future__ import annotations

import argparse
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.tree import DecisionTreeClassifier, export_text

from models.btc_15m.data import load
from models.btc_15m.features import FLOW_FEATURES, PRICE_FEATURES, Series, dataset
from models.btc_15m.indicators import INDICATOR_FEATURES
from models.btc_15m.stats import block_bootstrap_ci, cluster_diff_pvalue

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
COLS = PRICE_FEATURES + FLOW_FEATURES + INDICATOR_FEATURES


REF_MONTHS = 3


def vol_cutoffs(D: pd.DataFrame) -> tuple[float, float]:
    """10th and 90th percentiles of vol60 on the frame given (pass training rows only)."""
    return float(np.quantile(D.vol60.values, 0.1)), float(np.quantile(D.vol60.values, 0.9))


def reference_rows(D: pd.DataFrame) -> np.ndarray:
    """Rows in the first REF_MONTHS calendar months of D."""
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    return (month < sorted(month.unique())[0] + REF_MONTHS).values


def events(D: pd.DataFrame, k: int, cutoffs: tuple[float, float] | None = None) -> dict[str, np.ndarray]:
    """Boolean conditions on the feature frame. Names are the rule text. cutoffs are the
    vol60 decile cutoffs, computed on training rows (default: D's reference months)."""
    lo10, hi90 = cutoffs if cutoffs is not None else vol_cutoffs(D[reference_rows(D)])
    e = {}
    v = D.vol60.values + 1e-9
    e["price at 4h high (rangepos >= 0.98)"] = D.rangepos.values >= 0.98
    e["price at 4h low (rangepos <= 0.02)"] = D.rangepos.values <= 0.02
    e["upper quarter of 4h range"] = D.rangepos.values >= 0.75
    e["lower quarter of 4h range"] = D.rangepos.values <= 0.25
    e["last 5 min up more than 2 sd"] = D.ret5.values > 2 * v * np.sqrt(5)
    e["last 5 min down more than 2 sd"] = D.ret5.values < -2 * v * np.sqrt(5)
    e["last 15 min up more than 2 sd"] = D.ret15.values > 2 * v * np.sqrt(15)
    e["last 15 min down more than 2 sd"] = D.ret15.values < -2 * v * np.sqrt(15)
    e["4h return above +50 bp"] = D.ret240.values > 50
    e["4h return below -50 bp"] = D.ret240.values < -50
    e["previous window up"] = D.win1.values > 0
    e["previous window down"] = D.win1.values <= 0
    e["two windows up in a row"] = (D.win1.values > 0) & (D.win2.values > 0)
    e["two windows down in a row"] = (D.win1.values <= 0) & (D.win2.values <= 0)
    e["three windows up in a row"] = (D.win1.values > 0) & (D.win2.values > 0) & (D.win3.values > 0)
    e["three windows down in a row"] = (D.win1.values <= 0) & (D.win2.values <= 0) & (D.win3.values <= 0)
    e["RSI14 above 70"] = D.rsi14.values > 70
    e["RSI14 below 30"] = D.rsi14.values < 30
    e["RSI60 above 65"] = D.rsi60.values > 65
    e["RSI60 below 35"] = D.rsi60.values < 35
    e["MACD histogram positive"] = D.macd_hist.values > 0
    e["MACD histogram negative"] = D.macd_hist.values < 0
    e["above upper Bollinger band"] = D.bb_pctb.values > 1
    e["below lower Bollinger band"] = D.bb_pctb.values < 0
    e["EMA9 above EMA21 by 10 bp"] = D.ema_cross.values > 10
    e["EMA9 below EMA21 by 10 bp"] = D.ema_cross.values < -10
    e["ADX14 above 30 (trending)"] = D.adx14.values > 30
    e["ADX14 below 15 (ranging)"] = D.adx14.values < 15
    e["taker buying 60 pct+ of last 15 min"] = D.flow15.values > 0.2
    e["taker selling 60 pct+ of last 15 min"] = D.flow15.values < -0.2
    e["volume last 5 min 3x the daily average"] = D.vratio5.values > 3
    e["trade count last 5 min 3x average"] = D.nratio5.values > 3
    e["OBV rising over 60 min"] = D.obv_slope60.values > 0.3
    e["OBV falling over 60 min"] = D.obv_slope60.values < -0.3
    e["price 30 bp+ above 60-min VWAP"] = D.vwap_dev60.values > 30
    e["price 30 bp+ below 60-min VWAP"] = D.vwap_dev60.values < -30
    e["high volatility (vol60 in top decile)"] = D.vol60.values > hi90
    e["low volatility (vol60 in bottom decile)"] = D.vol60.values < lo10
    e["weekend"] = D.wday.values >= 5
    e["US afternoon (14-17 UTC)"] = (D.hour.values >= 14) & (D.hour.values <= 17)
    e["Asia early (0-3 UTC)"] = D.hour.values <= 3
    if k > 0:
        e["leading by 10 bp+ at entry"] = D.lead.values > 10
        e["trailing by 10 bp+ at entry"] = D.lead.values < -10
        e["within 2 bp of the open at entry"] = np.abs(D.lead.values) < 2
        e["led early, now back below the open"] = (D.lead1.values > 3) & (D.lead.values < 0) if "lead1" in D else np.zeros(len(D), bool)
        e["trailed early, now back above the open"] = (D.lead1.values < -3) & (D.lead.values > 0) if "lead1" in D else np.zeros(len(D), bool)
    return e


def reference_sign(mask: np.ndarray, y: np.ndarray, ref: np.ndarray, min_fires: int = 30) -> int:
    """Direction of the event's deviation from the base rate on the reference rows: +1 up,
    -1 down, 0 when it fires fewer than min_fires times there (no direction to hold)."""
    if (mask & ref).sum() < min_fires:
        return 0
    return int(np.sign(y[mask & ref].mean() - y[ref].mean()))


def month_agreement(mask: np.ndarray, y: np.ndarray, month: pd.Series, months, sign: int, min_fires: int = 30):
    """(agreeing months, months with enough firings, per-month deviations as text) for the
    months given, each compared with sign."""
    agree = tot = 0
    per = []
    for mm in months:
        mo = (month == mm).values
        if (mask & mo).sum() < min_fires:
            per.append("-")
            continue
        dev = y[mask & mo].mean() - y[mo].mean()
        per.append(f"{dev*100:+.1f}")
        tot += 1
        agree += int(sign != 0 and np.sign(dev) == sign)
    return agree, tot, per


def is_stable(agree: int, tot: int, sign: int, share: float = 0.75) -> bool:
    return bool(sign != 0 and tot and agree >= share * tot)


def bh(pvals: np.ndarray, q: float = 0.10) -> np.ndarray:
    """Benjamini-Hochberg: True where the hypothesis is rejected at FDR q."""
    n = len(pvals)
    order = np.argsort(pvals)
    thresh = q * (np.arange(1, n + 1) / n)
    passed = pvals[order] <= thresh
    k = np.where(passed)[0].max() + 1 if passed.any() else 0
    out = np.zeros(n, bool)
    out[order[:k]] = True
    return out


def event_pvalue(mask: np.ndarray, y: np.ndarray, t: np.ndarray) -> float:
    """Two-sided p for the up-rate when the event fires against the up-rate when it does
    not, day-clustered (stats.cluster_diff_pvalue). Replaced day_pvalue on 2026-10-01:
    that tested the firing windows against a base rate treated as known, and the base
    rate includes the firing windows themselves."""
    return cluster_diff_pvalue(mask, y, t)[2]


def day_pvalue(hits: np.ndarray, t: np.ndarray, base: float) -> float:
    """Two-sided p for mean(hits) != base with day-clustered standard error. Superseded by
    event_pvalue for events; kept for its tests."""
    days = t // 86400
    uniq, inv = np.unique(days, return_inverse=True)
    sums = np.bincount(inv, weights=hits - base)
    counts = np.bincount(inv)
    k = len(uniq)
    if k < 3:
        return 1.0
    mu = sums.sum() / counts.sum()
    # cluster-robust variance of the mean
    resid = sums - mu * counts
    se = np.sqrt((resid ** 2).sum()) / counts.sum()
    if se == 0:
        return 1.0 if mu == 0 else 0.0          # identical deviation every day: no spread, not no effect
    return float(2 * (1 - norm.cdf(abs(mu) / se)))


def tree_rules(D: pd.DataFrame, cols, depth: int = 2):
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    months = sorted(month.unique())
    y = D.y.values
    rules, accs = [], []
    for m in months[3:]:
        tr, te = (month < m).values, (month == m).values
        tree = DecisionTreeClassifier(max_depth=depth, min_samples_leaf=500, random_state=0).fit(D.loc[tr, cols], y[tr])
        accs.append(((tree.predict(D.loc[te, cols]) == y[te]).mean(), str(m)))
        rules.append((str(m), export_text(tree, feature_names=list(cols), decimals=1, show_weights=False)))
        # the root split as the rule signature
    return rules, accs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--minutes", default="0,3")
    a = ap.parse_args()
    s = Series(load(a.start, a.end))
    ev_rows, stable_rows, tree_rows = [], [], []
    for k in [int(x) for x in a.minutes.split(",")]:
        D = dataset(s, k)
        y, t = D.y.values, D.t.values
        month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
        months = sorted(month.unique())
        base = y.mean()
        E = events(D, k)
        names, stats = [], []
        for name, mask in E.items():
            if mask.sum() < 300:
                continue
            m_, lo, hi = block_bootstrap_ci(y[mask].astype(float), t[mask])
            p = event_pvalue(mask, y, t)
            names.append(name)
            stats.append((mask, m_, lo, hi, p))
        pvals = np.array([st[4] for st in stats])
        keep = bh(pvals) if len(pvals) else np.array([], bool)
        for name, (mask, m_, lo, hi, p), kp in sorted(zip(names, stats, keep), key=lambda x: x[1][4]):
            ev_rows.append([k, name, int(mask.sum()), f"{100*mask.mean():.1f}%", f"{m_*100:.1f}% [{lo*100:.1f}, {hi*100:.1f}]", f"{(m_-base)*100:+.1f}", f"{p:.3f}", "yes" if kp else ""])
        # stability of survivors: later months against the direction in the reference months
        ref = reference_rows(D)
        for name, (mask, m_, lo, hi, p), kp in zip(names, stats, keep):
            if not kp:
                continue
            sign = reference_sign(mask, y, ref)
            agree, tot, per = month_agreement(mask, y, month, months[REF_MONTHS:], sign)
            ref_dir = {1: "up", -1: "down", 0: "too few firings"}[sign]
            stable_rows.append([k, name, f"{'up' if m_ > base else 'down'} by {abs(m_-base)*100:.1f} points overall", ref_dir, f"{agree}/{tot}", " ".join(per), "stable" if is_stable(agree, tot, sign) else "not stable"])
            print(stable_rows[-1], flush=True)
        rules, accs = tree_rules(D, COLS)
        roots = Counter(r.split("\n")[0].strip().lstrip("|-").strip().split(" ")[0] for _, r in rules)
        for (mth, r), (acc, _) in zip(rules, accs):
            tree_rows.append([k, mth, f"{acc*100:.2f}%", r.replace("\n", "<br>").replace("|", "&#124;")])
        print(f"minute {k}: root features across months: {dict(roots)}", flush=True)
    with open(OUT / "rules.md", "w") as f:
        f.write("Event library: up-rate of the window when the condition holds at the entry minute, against the unconditional rate. Day-block 95% intervals; p compares windows where the event fires with windows where it does not, with day-clustered errors; 'survives FDR' marks events that pass Benjamini-Hochberg at a 10% false discovery rate across all events tested at that minute. Events that fire fewer than 300 times are omitted.\n\n")
        f.write("| minute | if | fires | share | up-rate [95% CI] | vs base (points) | p | survives FDR |\n|---|---|---|---|---|---|---|---|\n")
        for r in ev_rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        f.write("\nStability of the survivors: the deviation of the up-rate from that month's base rate, month by month after the three reference months, and how many of those months agree with the direction the event had in the reference months. Stable means at least three quarters agree.\n\n")
        f.write("| minute | if | overall | direction in reference months | months agreeing | deviation by month (points) | verdict |\n|---|---|---|---|---|---|---|\n")
        for r in stable_rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        f.write("\nLearned rules: a depth-2 decision tree per test month (leaves of at least 500 windows), trained on earlier months, and its accuracy on the test month. The same root split in most months is a stable rule; a different root each month means there is none.\n\n")
        f.write("| minute | month | accuracy | tree |\n|---|---|---|---|\n")
        for r in tree_rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print("wrote rules.md")


if __name__ == "__main__":
    main()
