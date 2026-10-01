"""Splice generated tables into the docs between markers, so every number in a document
is one a script wrote. Files: README.md and docs/*.md.

    <!-- table:NAME:start --> ... <!-- table:NAME:end -->   <- results/btc_15m/NAME.md
    <!-- forward:start --> ... <!-- forward:end -->         <- results/btc_15m/predictions.csv

    python scripts/update_readme.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models.btc_15m.log import current_rows, read_log  # noqa: E402

for readme in [Path("README.md"), *sorted(Path("docs").glob("*.md"))]:
    original = readme.read_text(encoding="utf-8")
    text = original

    for m in re.finditer(r"<!-- table:([a-z_0-9]+):start -->", text):
        name = m.group(1)
        src = Path(f"results/btc_15m/{name}.md")
        if not src.exists():
            continue
        table = src.read_text().strip()
        text = re.sub(rf"<!-- table:{name}:start -->.*?<!-- table:{name}:end -->",
                      f"<!-- table:{name}:start -->\n{table}\n<!-- table:{name}:end -->", text, flags=re.S)

    log = Path("results/btc_15m/predictions.csv")
    if log.exists():
        L = current_rows(read_log(log))
        mid = L.model_id.iloc[0] if "model_id" in L else "pre-manifest"
        FORWARD_FROM = "2026-10-01"          # the log was first committed after September 2026 had passed, so September is a holdout
        hold, fwd = L[L.time_utc < FORWARD_FROM], L[L.time_utc >= FORWARD_FROM]
        lines = [f"Models trained through {L.trained_through.iloc[0]} (model id {mid}). September 2026 is an out-of-time holdout: the log was first written after the month had passed. The forward log proper begins {FORWARD_FROM}.", ""]
        for title, part in (("Holdout (September 2026)", hold), ("Forward log (from October 2026)", fwd)):
            if part.empty:
                lines += [f"{title}: no windows yet.", ""]
                continue
            lines += [f"{title}: {part.time_utc.min()[:10]} to {part.time_utc.max()[:10]}.", "", "| minute | model | windows | accuracy |", "|---|---|---|---|"]
            for k, g in part.groupby("minute"):
                acc = ((g.prob_up > 0.5) == (g.outcome_up == 1)).mean()
                lines.append(f"| {k} | {g.model.iloc[0]} | {len(g):,} | {acc*100:.2f}% |")
            lines.append("")
        text = re.sub(r"<!-- forward:start -->.*?<!-- forward:end -->",
                      "<!-- forward:start -->\n" + "\n".join(lines) + "\n<!-- forward:end -->", text, flags=re.S)

    readme.write_text(text, encoding="utf-8")
    print(f"{readme}: " + ("updated" if text != original else "already current"))
