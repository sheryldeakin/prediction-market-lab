"""Splice generated tables into README.md between markers, so every number in the
README is one a script wrote.

    results/btc_15m/walk_forward.md   -> <!-- results:start --> ... <!-- results:end -->
    results/btc_15m/predictions.csv   -> <!-- forward:start --> ... <!-- forward:end -->

    python scripts/update_readme.py
"""
import re
from pathlib import Path

import pandas as pd

readme = Path("README.md")
text = readme.read_text()

table = Path("results/btc_15m/walk_forward.md").read_text().strip()
text = re.sub(r"<!-- results:start -->.*?<!-- results:end -->",
              f"<!-- results:start -->\n{table}\n<!-- results:end -->", text, flags=re.S)

log = Path("results/btc_15m/predictions.csv")
if log.exists():
    L = pd.read_csv(log)
    lines = [f"Trained through {L.trained_through.iloc[0]}, scored on {L.time_utc.min()[:10]} to {L.time_utc.max()[:10]}.", "",
             "| minute | model | windows | accuracy |", "|---|---|---|---|"]
    for k, g in L.groupby("minute"):
        acc = ((g.prob_up > 0.5) == (g.outcome_up == 1)).mean()
        lines.append(f"| {k} | {g.model.iloc[0]} | {len(g):,} | {acc*100:.2f}% |")
    text = re.sub(r"<!-- forward:start -->.*?<!-- forward:end -->",
                  "<!-- forward:start -->\n" + "\n".join(lines) + "\n<!-- forward:end -->", text, flags=re.S)

changed = text != readme.read_text()
readme.write_text(text)
print("README updated" if changed else "README already current")
