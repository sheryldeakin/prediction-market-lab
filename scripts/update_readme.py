"""Splice results/btc_15m/walk_forward.md into README.md between the results markers,
so the README table is always the one the evaluation script wrote.

    python scripts/update_readme.py
"""
import re
from pathlib import Path

readme = Path("README.md")
table = Path("results/btc_15m/walk_forward.md").read_text().strip()
text = readme.read_text()
new = re.sub(r"<!-- results:start -->.*?<!-- results:end -->",
             f"<!-- results:start -->\n{table}\n<!-- results:end -->", text, flags=re.S)
readme.write_text(new)
print("README updated" if new != text else "README already current")
