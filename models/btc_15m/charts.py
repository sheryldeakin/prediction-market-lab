"""Charts for the README, drawn from the CSVs in results/btc_15m/ (never from
numbers typed here).

    python -m models.btc_15m.charts
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT = Path("results/btc_15m")
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#1a1a19", "#6b6a63", "#e6e5df"
SERIES = {"majority": "#6b6a63", "prev-window": "#6b6a63", "logistic-all": "#2a78d6", "forest": "#eb6834", "xgb-all": "#1baf7a",
          "lead-only": "#eda100", "one-feature baseline": "#eda100"}


def style(ax, title):
    ax.set_facecolor(SURFACE)
    ax.figure.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title(title, loc="left", color=INK, fontsize=11, pad=12)


def spread(labels, gap):
    """Nudge direct labels apart vertically so none overlap (labels: [name, y])."""
    labels = sorted(labels, key=lambda x: x[1])
    for i in range(1, len(labels)):
        if labels[i][1] - labels[i - 1][1] < gap:
            labels[i][1] = labels[i - 1][1] + gap
    return labels


def monthly():
    m = pd.read_csv(OUT / "walk_forward_monthly.csv")
    m = m[(m.minute == 0) & m.model.isin(["prev-window", "logistic-all", "forest", "xgb-all"])]
    fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
    style(ax, "Accuracy at the window open, by test month (walk-forward)")
    months = sorted(m.month.unique())
    labels = []
    for name in ["prev-window", "logistic-all", "forest", "xgb-all"]:
        d = m[m.model == name].set_index("month").reindex(months)
        ax.plot(range(len(months)), d.accuracy * 100, color=SERIES[name], linewidth=2, marker="o", markersize=5,
                markeredgecolor=SURFACE, markeredgewidth=1.5, label=name)
        labels.append([name, d.accuracy.iloc[-1] * 100])
    for lab, y in spread(labels, 0.3):
        ax.annotate(lab, (len(months) - 1 + 0.15, y), color=INK, fontsize=8, va="center")
    ax.axhline(50, color=MUTED, linewidth=1, linestyle=(0, (3, 3)))
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels(months, rotation=0)
    ax.set_xlim(-0.3, len(months) + 1.2)
    ax.set_ylabel("accuracy, %", color=MUTED, fontsize=9)
    ax.legend(frameon=False, fontsize=8, loc="lower left", ncol=4)
    fig.tight_layout()
    fig.savefig(OUT / "monthly_k0.png")


def calibration():
    c = pd.read_csv(OUT / "calibration_k0.csv")
    fig, ax = plt.subplots(figsize=(5, 4.6), dpi=150)
    style(ax, "Calibration at the open (xgb-all)")
    lo, hi = min(c.predicted.min(), c.observed.min()) - 0.01, max(c.predicted.max(), c.observed.max()) + 0.01
    ax.plot([lo, hi], [lo, hi], color=MUTED, linewidth=1, linestyle=(0, (3, 3)))
    ax.scatter(c.predicted, c.observed, s=60, color=SERIES["xgb-all"], edgecolor=SURFACE, linewidth=1.5, zorder=3)
    for _, r in c.iterrows():
        ax.annotate(f"n={int(r.n):,}", (r.predicted, r.observed), xytext=(6, -3), textcoords="offset points", fontsize=7, color=MUTED)
    ax.set_xlabel("mean predicted probability in decile", color=MUTED, fontsize=9)
    ax.set_ylabel("observed share of up windows", color=MUTED, fontsize=9)
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    fig.tight_layout()
    fig.savefig(OUT / "calibration_k0.png")


def by_minute():
    w = pd.read_csv(OUT / "walk_forward.csv")
    base = w[((w.minute == 0) & (w.model == "prev-window")) | ((w.minute > 0) & (w.model == "lead-z"))].assign(model="one-feature baseline")
    w = pd.concat([w[w.model.isin(["majority", "forest"])], base])
    last = int(w.minute.max())                       # every entry minute the walk-forward scored, 0 to 14
    fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
    style(ax, "Accuracy by entry minute against a one-feature baseline")
    labels = []
    for name in ["majority", "one-feature baseline", "forest"]:
        d = w[w.model == name].sort_values("minute")
        ax.plot(d.minute, d.accuracy * 100, color=SERIES[name], linewidth=2, marker="o", markersize=5,
                markeredgecolor=SURFACE, markeredgewidth=1.5, label=name)
        labels.append([name, d.accuracy.iloc[-1] * 100])
    for lab, y in spread(labels, 2.4):
        ax.annotate(lab, (last + 0.3, y), color=INK, fontsize=8, va="center")
    ax.set_xticks(range(last + 1))
    ax.set_ylim(48, 96)
    ax.set_xlim(-0.3, last + 3.8)
    ax.set_xlabel("minutes into the 15-minute window", color=MUTED, fontsize=9)
    ax.set_ylabel("accuracy, %", color=MUTED, fontsize=9)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT / "by_minute.png")


def forward():
    p = OUT / "predictions.csv"
    if not p.exists():
        return
    from models.btc_15m.log import current_rows, read_log
    L = current_rows(read_log(p))
    fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
    style(ax, "Forward log: cumulative accuracy on windows after the training cutoff")
    for k, color in ((0, SERIES["forest"]), (3, SERIES["xgb-all"])):
        d = L[L.minute == k].sort_values("t")
        hit = ((d.prob_up > 0.5) == (d.outcome_up == 1)).astype(float).values
        cum = pd.Series(hit.cumsum() / (1 + np.arange(len(hit))))[96:]      # start after the first day
        x = pd.Series(pd.to_datetime(d.t.values, unit="s"))[96:]
        ax.plot(x, cum * 100, color=color, linewidth=2, label=f"minute {k} ({d.model.iloc[0]})")
        ax.annotate(f"minute {k}: {cum.iloc[-1]*100:.1f}%", (x.iloc[-1], cum.iloc[-1] * 100), xytext=(6, 0),
                    textcoords="offset points", color=INK, fontsize=8, va="center")
    ax.axhline(50, color=MUTED, linewidth=1, linestyle=(0, (3, 3)))
    ax.set_ylabel("cumulative accuracy, %", color=MUTED, fontsize=9)
    ax.set_ylim(40, 80)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(OUT / "forward_log.png")


if __name__ == "__main__":
    monthly()
    calibration()
    by_minute()
    forward()
    print("wrote", ", ".join(p.name for p in OUT.glob("*.png")))
