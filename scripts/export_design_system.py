"""Write docs/design-system.md from a design-system tokens file, so the tokens the site
uses are the ones on record and nothing is typed by hand.

    python scripts/export_design_system.py path/to/tokens.json
"""
import json
import sys
from pathlib import Path

src = Path(sys.argv[1])
t = json.loads(src.read_text(encoding="utf-8"))
out = ["# Glacier design system", "",
       "Tokens and rules for the tracking page. Generated from the design system's `tokens.json` by `scripts/export_design_system.py`; edit the tokens there, not here.", "",
       "## Colour", "", "| token | light | dark | usage |", "|---|---|---|---|"]
for c in t["color"]["tokens"]:
    v = c["value"]
    out.append(f"| `{c['name']}` | `{v['light']}` | `{v['dark']}` | {c['usage']} |")
out += ["", "## Type", "", f"Families: sans `{t['type']['families']['sans']}`; mono `{t['type']['families']['mono']}`.", "",
        "| style | family | size | line height | weight | usage |", "|---|---|---|---|---|---|"]
for g in t["type"]["groups"]:
    for s in g["styles"]:
        out.append(f"| `{s['name']}` | {g['family']} | {s['fontSize']} | {s['lineHeight']} | {s['fontWeight']} | {s.get('usage', '')} |")
for fam in ("spacing", "radius", "shadow"):
    if fam in t:
        out += ["", f"## {fam.capitalize()}", "", "| token | value | usage |", "|---|---|---|"]
        for s in t[fam]["tokens"]:
            v = s["value"] if isinstance(s["value"], str) else f"light `{s['value']['light']}`, dark `{s['value']['dark']}`"
            out.append(f"| `{s['name']}` | {v if v.startswith('light') else f'`{v}`'} | {s['usage']} |")
Path("docs/design-system.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("wrote docs/design-system.md")
