"""Build results/btc_15m/headline.md, the summary table the README splices in, from the
generated result files. Nothing here is typed: every cell is read from a table a study
wrote, so the README's summary cannot drift from the studies.

    python scripts/headline.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models.btc_15m.log import current_rows, read_log  # noqa: E402

R = Path("results/btc_15m")


def table_rows(path: Path, header_prefix: str) -> list[list[str]]:
    """Rows of the first markdown table in path whose header starts with header_prefix."""
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.startswith(header_prefix):
            rows = []
            for l in lines[i + 2:]:
                if not l.startswith("|"):
                    break
                rows.append([c.strip() for c in l.strip("|").split("|")])
            return rows
    raise KeyError(f"{path}: no table starting with {header_prefix!r}")


def split_after_interval(cell: str) -> tuple[str, str]:
    """'+0.08 [-0.58, +0.72], days better 50%' -> ('+0.08 [-0.58, +0.72]', 'days better 50%')."""
    head, _, tail = cell.partition("], ")
    return head + "]", tail


def pct(x: float) -> str:
    return f"{x*100:.2f}%"


def ci(lo: float, hi: float) -> str:
    return f"[{lo*100:+.2f}, {hi*100:+.2f}]"


def main():
    C = pd.read_csv(R / "checks.csv")
    rows = []

    # backtest, open: the one-bit rule and the forest (the frozen forward model), price + flow
    k0 = C[C.minute == 0].set_index("model")
    pw, fo = k0.loc["prev-window"], k0.loc["forest"]
    rows.append(["backtest 2025-10 to 2026-08, open", "previous window reversed", pct(pw.accuracy), "forest (price + flow)", pct(fo.accuracy),
                 f"{fo['diff']*100:+.2f} {ci(fo.diff_low, fo.diff_high)}", f"{ci(fo.diff_month_low, fo.diff_month_high)}, days better {fo.days_better*100:.0f}%, sign p {fo.sign_p:.3f}"])
    # backtest, open, best feature set from the ablation
    ab = [r for r in table_rows(R / "ablation.md", "| minute | features") if r[0] == "0" and r[2] in ("forest", "xgb")]
    best = max(ab, key=lambda r: float(r[4].rstrip("%")))
    rows.append(["backtest, open, richest feature set", "previous window reversed", pct(pw.accuracy), f"{best[2]} ({best[1]})", best[4], best[8], "day-block interval only"])
    # backtest, minute 3
    k3 = C[C.minute == 3].set_index("model")
    lz, xg = k3.loc["lead-z"], k3.loc["xgb-all"]
    rows.append(["backtest, minute 3", "lead z-score", pct(lz.accuracy), "xgb-all", pct(xg.accuracy), f"{xg['diff']*100:+.2f} {ci(xg.diff_low, xg.diff_high)}", f"{ci(xg.diff_month_low, xg.diff_month_high)}, days better {xg.days_better*100:.0f}%, sign p {xg.sign_p:.3f}"])

    # 2025 holdout
    h = {r[1]: r for r in table_rows(R / "holdout_2025.md", "| minute | model") if r[0] == "0"}
    for model, label in (("forest", "forest (frozen forward model)"), ("forest (price + flow + indicators)", "forest (price + flow + indicators)")):
        rows.append(["holdout 2025-01 to 2025-09, open (two declared runs; see the process log)", "previous window reversed", h["prev-window"][3].split(" [")[0], label, h[model][3].split(" [")[0], *split_after_interval(h[model][4])])

    # September 2026 holdout from the log (re-fitted models)
    L = current_rows(read_log(R / "predictions.csv"))
    L = L[L.time_utc < "2026-10-01"]
    for k, g in L.groupby("minute"):
        acc = ((g.prob_up > 0.5) == (g.outcome_up == 1)).mean()
        rows.append([f"holdout September 2026, minute {k} (re-fitted frozen models)", "", "", g.model.iloc[0], pct(acc), "", f"{len(g):,} windows; see the event rules row for the reversal in September"])

    # other venues
    v = table_rows(R / "venues.md", "| venue | model")
    for venue in ("Coinbase BTC-USD", "Bitstamp BTC-USD"):
        vr = {r[1]: r for r in v if r[0] == venue}
        rows.append([f"backtest on {venue}", "previous window reversed", vr["prev-window"][4].split(" [")[0], "forest (price only)", vr["forest, price features"][4].split(" [")[0], vr["forest, price features"][5], "day-block interval"])

    # settlement-style label
    s = {(r[0], r[3]): r for r in table_rows(R / "settlement.md", "| label | agrees")}
    rows.append(["backtest, label from 60-second VWAPs inside the window (no shared prints)", "previous window reversed (same label)", s[("vwap_in", "own previous label")][5].split(" [")[0], "forest", s[("vwap_in", "forest")][5].split(" [")[0], *split_after_interval(s[("vwap_in", "forest")][6])])

    # phases
    ph = table_rows(R / "boundary.md", "| phase (minutes)")
    pw_acc = [float(r[2].split("%")[0]) for r in ph]
    inc = [float(r[4].split(" ")[0]) for r in ph]
    rows.append(["backtest, windows shifted 0 to 14 minutes off the quarter hour", "previous window reversed", f"{min(pw_acc):.2f}% to {max(pw_acc):.2f}%", "forest (price + flow)", "", f"{min(inc):+.2f} to {max(inc):+.2f} across the 15 offsets", "an effect of any 15-minute boundary, not of the clock"])

    # event rules
    sn = (R / "search_null.md").read_text(encoding="utf-8")
    real = re.search(r"\| also stable month by month \| (\d+) \| (\d+) \| (\d+) \| (\d+) \|", sn)
    sept = re.search(r"of the (\d+) stable survivors, (\d+) fired at least 30 times and (\d+) kept their direction.*?median (\d+) and 95th percentile (\d+)", sn, re.S)
    h25 = re.search(r"(\d+) of (\d+) fired at least 30 times in the holdout, and (\d+) of those kept", (R / "holdout_2025.md").read_text(encoding="utf-8"))
    rows.append(["event rules: stable survivors of the wide search", f"{real.group(1)} real", f"null median {real.group(2)}, null maximum {real.group(4)}", "", "", "", "labels rotated within months, 200 runs"])
    rows.append(["event rules: kept their direction in September 2026", f"{sept.group(3)} of {sept.group(2)}", f"null median {sept.group(4)}, 95th percentile {sept.group(5)}", "", "", "", ""])
    rows.append(["event rules: kept their direction in 2025", f"{h25.group(3)} of {h25.group(1)}", "", "", "", "", "scored once"])

    with open(R / "headline.md", "w", encoding="utf-8") as f:
        f.write("| where | one-bit rule | its accuracy | fitted model | its accuracy | model minus rule, points [day CI] | more |\n|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(r) + " |\n")
    print(f"wrote {R / 'headline.md'} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
