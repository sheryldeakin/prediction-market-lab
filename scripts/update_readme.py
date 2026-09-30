"""Splice generated tables into README.md between markers, so every number in the
README is one a script wrote.

    <!-- table:NAME:start --> ... <!-- table:NAME:end -->   <- results/btc_15m/NAME.md
    <!-- forward:start --> ... <!-- forward:end -->         <- results/btc_15m/predictions.csv

    python scripts/update_readme.py
"""
import re
from pathlib import Path

import pandas as pd

readme = Path("README.md")
original = readme.read_text()
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
    L = pd.read_csv(log)
    lines = [f"Trained through {L.trained_through.iloc[0]}, scored on {L.time_utc.min()[:10]} to {L.time_utc.max()[:10]}.", "",
             "| minute | model | windows | accuracy |", "|---|---|---|---|"]
    for k, g in L.groupby("minute"):
        acc = ((g.prob_up > 0.5) == (g.outcome_up == 1)).mean()
        lines.append(f"| {k} | {g.model.iloc[0]} | {len(g):,} | {acc*100:.2f}% |")
    text = re.sub(r"<!-- forward:start -->.*?<!-- forward:end -->",
                  "<!-- forward:start -->\n" + "\n".join(lines) + "\n<!-- forward:end -->", text, flags=re.S)

readme.write_text(text)
print("README updated" if text != original else "README already current")
