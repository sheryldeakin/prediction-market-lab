"""The walk-forward at every entry minute, as tables for the docs.

evaluate.py writes walk_forward.csv (minutes 0 to 14, every predictor) and one out-of-fold file per minute.
This module renders them without refitting anything:

    walk_forward.md            the table the report splices: the published minutes only (PUBLISHED_MINUTES)
    walk_forward_all.md        the same table for every minute
    walk_forward_by_minute.*   one row per minute: the one-feature rule, each fitted family, and the best
                               fitted family minus the rule with a day-block interval

    python -m models.btc_15m.walk_forward_by_minute
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.stats import paired_difference_ci

OUT = Path("results/btc_15m")
PUBLISHED_MINUTES = (0, 1, 3, 5, 8)            # the minutes the report's main table shows; the prose beside it is written for these
FITTED = ("logistic-all", "forest", "hgb-all", "xgb-price", "xgb-all")


def rule_name(k: int) -> str:
    """The one-feature rule of the minute (evaluate.baseline_name, restated here so this module stays light)."""
    return "prev-window" if k == 0 else "lead-z"


def render_walk_forward(rows: pd.DataFrame, start: str, end: str, minutes=None) -> str:
    """The walk-forward table as markdown. minutes: keep only these entry minutes (None keeps all)."""
    if minutes is not None:
        rows = rows[rows.minute.isin(minutes)]
    out = [f"Walk-forward results, {start} to {end}, test months after the first three.", "",
           "| minute | model | n test | accuracy | AUC | log loss |", "|---|---|---|---|---|---|"]
    for r in rows.itertuples(index=False):
        out.append(f"| {r.minute} | {r.model} | {int(r.n_test):,} | {r.accuracy * 100:.2f}% | {r.auc:.3f} | {r.log_loss:.4f} |")
    return "\n".join(out) + "\n"


def by_minute_table(frames: dict[int, pd.DataFrame], n_boot: int = 2000) -> pd.DataFrame:
    """One row per minute from the out-of-fold frames (columns t, y and one per predictor): the accuracy of
    the minute's one-feature rule and of each fitted family, and the best fitted family minus the rule with a
    day-block 95% interval from the paired per-window hits."""
    rows = []
    for k in sorted(frames):
        f = frames[k]
        y = f.y.values.astype(int)
        hits = {m: ((f[m].values > 0.5).astype(int) == y).astype(float) for m in (rule_name(k), *FITTED)}
        acc = {m: float(h.mean()) for m, h in hits.items()}
        best = max(FITTED, key=lambda m: acc[m])
        d, lo, hi = paired_difference_ci(hits[best], hits[rule_name(k)], f.t.values, n_boot=n_boot)
        rows.append({"minute": k, "rule": rule_name(k), "rule_accuracy": acc[rule_name(k)], **{m: acc[m] for m in FITTED},
                     "best": best, "best_minus_rule": d, "low": lo, "high": hi, "n": int(len(y))})
    return pd.DataFrame(rows)


def _pts(x: float) -> str:
    return f"{x * 100:+.2f}"


def _diff(r) -> str:
    return f"{_pts(r['best_minus_rule'])} [{_pts(r['low'])}, {_pts(r['high'])}]"


def render_by_minute(T: pd.DataFrame, start: str, end: str) -> str:
    n = int(T.n.iloc[0])
    intro = (f"The one-feature rule of the minute against each fitted family, accuracy at every entry minute, walk-forward {start} to {end}, test months after the first three, {n:,} windows at each minute. "
             f"The rule is the previous window's direction at minute 0 and the lead z-score after. Accuracy is the share of windows called right; the families are fitted on all features (logistic-all, forest, hgb-all) or on price (xgb-price) or price and flow (xgb-all). "
             f"The last column is the most accurate of the five families at that minute minus the rule on the same windows, in points, with a 95% interval from resampling whole days and the family's name. "
             f"The best of five is chosen on these windows, so the difference is biased upward and the interval does not correct for the choice (study 23 does, for minutes 0 and 3).")
    lines = [intro, "", "| minute | one-feature rule (prev-window at 0, lead-z after) | " + " | ".join(FITTED) + " | best fitted minus rule (points) [95% interval] |", "|---|---|" + "---|" * len(FITTED) + "---|"]
    for _, r in T.iterrows():
        lines.append(f"| {int(r['minute'])} | {r['rule_accuracy'] * 100:.2f}% | " + " | ".join(f"{r[m] * 100:.2f}%" for m in FITTED) + f" | {_diff(r)} ({r['best']}) |")
    lines.append("")
    later, first = T[T.minute >= 1], T[T.minute == 0]
    hi, lo = later.loc[later.best_minus_rule.idxmax()], later.loc[later.best_minus_rule.idxmin()]
    s = (f"Across minutes {int(later.minute.min())} to {int(later.minute.max())} the largest best-fitted-minus-rule difference is {_diff(hi)} points at minute {int(hi['minute'])} ({hi['best']}) and the smallest is {_diff(lo)} points at minute {int(lo['minute'])} ({lo['best']})")
    if len(first):
        s += f"; at minute 0 it is {_diff(first.iloc[0])} points ({first.iloc[0]['best']})"
    lines.append(s + ".\n")
    above, below = T[T.low > 0], T[T.high < 0]
    fmt = lambda d: "no minute" if not len(d) else "minute " + ", ".join(str(int(m)) for m in d.minute) if len(d) == 1 else "minutes " + ", ".join(str(int(m)) for m in d.minute)
    lines.append(f"The interval lies entirely above zero at {len(above)} of the {len(T)} minutes ({fmt(above)}) and entirely below zero at {len(below)} ({fmt(below)}). The intervals are not adjusted for the number of minutes.\n")
    return "\n".join(lines).rstrip() + "\n"


def write_tables(out: Path = OUT, start: str = "2025-10", end: str = "2026-08", n_boot: int = 2000) -> None:
    rows = pd.read_csv(out / "walk_forward.csv")
    minutes = sorted(rows.minute.unique())
    frames = {k: pd.read_parquet(out / f"oof_k{k}.parquet") for k in minutes}
    T = by_minute_table(frames, n_boot=n_boot)
    for _, r in T.iterrows():                               # the stored predictions must reproduce the table they sit beside
        for m in (r["rule"], *FITTED):
            stored = float(rows[(rows.minute == r["minute"]) & (rows.model == m)].accuracy.iloc[0])
            got = float(r[m] if m in FITTED else r["rule_accuracy"])
            assert abs(stored - got) < 1e-9, f"minute {int(r['minute'])} {m}: out-of-fold {got} against walk_forward.csv {stored}"
    T.to_csv(out / "walk_forward_by_minute.csv", index=False)
    (out / "walk_forward_by_minute.md").write_text(render_by_minute(T, start, end), encoding="utf-8")
    (out / "walk_forward.md").write_text(render_walk_forward(rows, start, end, PUBLISHED_MINUTES), encoding="utf-8")
    (out / "walk_forward_all.md").write_text(render_walk_forward(rows, start, end), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    write_tables(Path(a.out), a.start, a.end)
    print(f"wrote walk_forward.md, walk_forward_all.md and walk_forward_by_minute.md to {a.out}")


if __name__ == "__main__":
    main()
