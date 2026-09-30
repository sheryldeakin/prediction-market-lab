"""Build the claude.ai/design cards for Glacier from design/glacier.tokens.json.

Each card is a self-contained HTML file whose first line is a @dsCard marker (group,
name, subtitle, width). Colours are inlined from the tokens file, so the cards can
never disagree with it. Output: design/cards/<group>/<name>.html.

    python scripts/build_design_cards.py
"""
import json
from pathlib import Path

T = json.loads(Path("design/glacier.tokens.json").read_text(encoding="utf-8"))
OUT = Path("design/cards")
C = {c["name"]: c["value"] for c in T["color"]["tokens"]}
L = {k: v["light"] for k, v in C.items()}
D = {k: v["dark"] for k, v in C.items()}
SANS = T["type"]["families"]["sans"]
MONO = T["type"]["families"]["mono"]
FONTS = '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">'


def page(marker, body, css, theme=L):
    return f"""<!-- @dsCard {marker} -->
<!doctype html>
<html>
<head>
<meta charset="utf-8">
{FONTS}
<style>
body{{margin:0;background:{theme['canvas']};color:{theme['ink']};font-family:{SANS};font-size:14px;line-height:1.5;padding:24px;}}
.mono{{font-family:{MONO};font-variant-numeric:tabular-nums;}}
{css}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def write(path, text):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ---- tokens/colors: light and dark side by side ----
def swatches(theme, names):
    cells = []
    for n in names:
        v = theme[n]
        usage = next(c["usage"] for c in T["color"]["tokens"] if c["name"] == n).split(".")[0]
        border = "" if n not in ("canvas", "surface", "sunken") else f"border:1px solid {theme['border']};"
        cells.append(f'<div class="sw"><div class="chip" style="background:{v};{border}"></div><span class="name">{n}</span><span class="hex mono">{v}</span><span class="use">{usage}</span></div>')
    return "".join(cells)


core = ["accent", "accent-hover", "accent-tint", "ink", "text-secondary", "text-muted", "canvas", "surface", "sunken", "border", "border-strong", "reference"]
css = """.two{display:grid;grid-template-columns:1fr 1fr;gap:24px}
.pane{border-radius:14px;padding:20px}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.sw{display:flex;flex-direction:column;gap:4px}
.chip{height:44px;border-radius:10px}
.name{font-weight:600;font-size:12px}
.hex{font-size:11px}
.use{font-size:11px;line-height:1.35}
h2{font-size:13px;font-weight:600;margin:0 0 12px}"""
body = f"""<div class="two">
<div class="pane" style="background:{L['surface']};color:{L['ink']};border:1px solid {L['border']}"><h2>Light</h2><div class="grid" style="--m:{L['text-muted']}">{swatches(L, core)}</div></div>
<div class="pane" style="background:{D['surface']};color:{D['ink']};border:1px solid {D['border']}"><h2>Dark</h2><div class="grid">{swatches(D, core)}</div></div>
</div>
<p style="font-size:12px;color:{L['text-muted']};margin:16px 0 0">Ink is a hard dark of the accent hue, never neutral black (13:1 on surface). Dark is its own set of steps validated against the dark surface, not an inverted light. Dividers are breathing-edge gradients of the separator: linear-gradient(90deg, transparent, {C['separator']['light']} 20%, {C['separator']['light']} 80%, transparent).</p>"""
write("tokens/colors.html", page('group="Colors" name="Glacier tokens" subtitle="Accent, ink, tinted neutrals, light and dark" width="760"', body, css))

# ---- tokens/charts: series palette, reference, interval, status ----
series = [f"series-{i}" for i in range(1, 7)]
css = """.row{display:flex;gap:12px;margin-bottom:16px}
.sw{flex:1;display:flex;flex-direction:column;gap:4px}
.bar{height:36px;border-radius:6px}
.name{font-size:12px;font-weight:600}.hex{font-size:11px}
.pane{border-radius:14px;padding:16px;margin-bottom:12px}
h2{font-size:13px;font-weight:600;margin:0 0 10px}
.st{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:500;margin-right:8px}"""


def bars(theme):
    return "".join(f'<div class="sw"><div class="bar" style="background:{theme[s]}"></div><span class="name">{s}</span><span class="hex mono">{theme[s]}</span></div>' for s in series)


body = f"""<div class="pane" style="background:{L['surface']};border:1px solid {L['border']}"><h2>Series, fixed order, light</h2><div class="row">{bars(L)}</div>
<div class="row"><div class="sw"><div class="bar" style="background:{L['reference']}"></div><span class="name">reference</span><span class="hex mono">{L['reference']}</span></div><div class="sw"><div class="bar" style="background:{C['interval-fill']['light']}"></div><span class="name">interval-fill</span><span class="hex mono">{C['interval-fill']['light']}</span></div></div>
<div><span class="st" style="background:{L['accent-tint']};color:{L['status-good']}">above baseline</span><span class="st" style="background:{L['accent-tint']};color:{L['status-warning']}">interval includes baseline</span><span class="st" style="background:{L['accent-tint']};color:{L['status-critical']}">below baseline</span></div></div>
<div class="pane" style="background:{D['surface']};color:{D['ink']};border:1px solid {D['border']}"><h2>Series, dark</h2><div class="row">{bars(D)}</div>
<div class="row"><div class="sw"><div class="bar" style="background:{D['reference']}"></div><span class="name">reference</span><span class="hex mono">{D['reference']}</span></div><div class="sw"><div class="bar" style="background:{C['interval-fill']['dark']}"></div><span class="name">interval-fill</span><span class="hex mono">{C['interval-fill']['dark']}</span></div></div>
<div><span class="st" style="background:{D['accent-tint']};color:{D['status-good']}">above baseline</span><span class="st" style="background:{D['accent-tint']};color:{D['status-warning']}">interval includes baseline</span><span class="st" style="background:{D['accent-tint']};color:{D['status-critical']}">below baseline</span></div></div>
<p style="font-size:12px;color:{L['text-muted']};margin:0">Six hues, assigned by entity in this order and never re-painted when a filter removes a series; a seventh folds into Other. Validated for colour-vision separation on both surfaces. Series 3, 4 and 5 are below 3:1 on the light surface, so every series is direct-labelled and every chart has a table view. Status colours always carry their word.</p>"""
write("tokens/charts.html", page('group="Colors" name="Chart palette" subtitle="Six series in fixed order, reference grey, interval band, status" width="760"', body, css))

# ---- tokens/type ----
css = """.r{display:grid;grid-template-columns:150px 1fr 200px;gap:16px;align-items:baseline;padding:10px 0;border-top:1px solid """ + L['border'] + """}
.k{font-size:12px;font-weight:600}.u{font-size:11px;color:""" + L['text-muted'] + """}"""
rows = []
for g in T["type"]["groups"]:
    fam = SANS if g["family"] == "sans" else MONO
    for s in g["styles"]:
        ls = f"letter-spacing:{s['letterSpacing']};" if s.get("letterSpacing") else ""
        color = L["text-secondary"] if s["name"] == "subtitle" else L["text-muted"] if s["name"] in ("caption", "axis") else L["ink"]
        rows.append(f'<div class="r"><span class="k">{s["name"]}<br><span class="u">{s["fontSize"]}/{s["lineHeight"]} {s["fontWeight"]}</span></span><span style="font-family:{fam};font-size:{s["fontSize"]};line-height:{s["lineHeight"]};font-weight:{s["fontWeight"]};{ls}color:{color};font-variant-numeric:tabular-nums">{s["sample"]}</span><span class="u">{s.get("usage","")}</span></div>')
body = f'<div style="background:{L["surface"]};border:1px solid {L["border"]};border-radius:14px;padding:8px 20px">{"".join(rows)}</div>'
write("tokens/type.html", page('group="Type" name="Type ramp" subtitle="Inter for words, JetBrains Mono for numbers; roles are fixed" width="760"', body, css))

# ---- components ----
tile_css = f""".row{{display:flex;gap:16px;flex-wrap:wrap}}
.tile{{background:{L['surface']};border:1px solid {L['border']};border-radius:10px;box-shadow:{T['shadow']['tokens'][0]['value']['light']};padding:16px 24px;min-width:200px}}
.v{{font-family:{MONO};font-variant-numeric:tabular-nums;font-size:28px;line-height:32px;font-weight:600;color:{L['ink']}}}
.l{{font-size:13px;line-height:18px;font-weight:500;margin-top:4px}}
.c{{font-size:12px;line-height:16px;color:{L['text-secondary']};margin-top:8px}}
.s{{font-size:12px;line-height:16px;font-weight:500;margin-top:4px}}
.empty .v{{color:{L['text-muted']}}}"""
tile_body = f"""<div class="row">
<div class="tile"><div class="v">50.41%</div><div class="l">Forward accuracy, at the open</div><div class="c">backtest 53.0%, baseline 50.1%, n 2,783</div><div class="s" style="color:{L['status-warning']}">interval includes the baseline</div></div>
<div class="tile"><div class="v">66.69%</div><div class="l">Forward accuracy, minute 3</div><div class="c">backtest 66.2%, lead-only 66.3%, n 2,783</div><div class="s" style="color:{L['status-good']}">above baseline</div></div>
<div class="tile empty"><div class="v">53.0%</div><div class="l">Backtest level</div><div class="c">no forward data yet</div></div>
</div>
<p style="font-size:12px;color:{L['text-muted']};margin:16px 0 0">A value never appears without its comparison line and sample size. Tiles hug content; two columns on phones.</p>"""
write("components/stat-tile.html", page('group="Components" name="Stat tile" subtitle="Value, label, comparison line, status word; empty state" width="760"', tile_body, tile_css))

frame_css = f""".frame{{background:{L['surface']};border:1px solid {L['border']};border-radius:14px;box-shadow:{T['shadow']['tokens'][0]['value']['light']};padding:24px}}
.t{{font-size:20px;line-height:26px;font-weight:600}}
.st{{font-size:15px;line-height:22px;color:{L['text-secondary']};margin-top:2px}}
.legend{{display:flex;gap:12px;margin:12px 0 8px;font-size:13px;line-height:18px;font-weight:500}}
.legend span::before{{content:"";display:inline-block;width:12px;height:3px;border-radius:2px;margin-right:6px;vertical-align:middle;background:{L['series-1']}}}
.legend span:nth-child(2)::before{{background:{L['series-2']}}}
.legend span:nth-child(3)::before{{background:transparent;height:0;border-top:2px dashed {L['reference']}}}
svg{{width:100%;height:190px;display:block}}
.grid{{stroke:{L['border']};stroke-width:1}}
.axis{{font-family:{MONO};font-size:11px;fill:{L['text-muted']}}}
.l1{{stroke:{L['series-1']};stroke-width:2;fill:none;stroke-linejoin:round}}
.l2{{stroke:{L['series-2']};stroke-width:2;fill:none;stroke-linejoin:round}}
.band{{fill:{C['interval-fill']['light']}}}
.ref{{stroke:{L['reference']};stroke-width:1.5;stroke-dasharray:4 4}}
.lab{{font-size:12px;font-weight:500;fill:{L['ink']}}}
.foot{{font-size:12px;line-height:16px;color:{L['text-muted']};margin-top:8px}}"""
frame_body = f"""<div class="frame">
<div class="t">Forward log</div>
<div class="st">Cumulative accuracy at the open since the training cutoff, with its 95% interval</div>
<div class="legend"><span>cumulative</span><span>rolling 7 days</span><span>backtest and 50%</span></div>
<svg viewBox="0 0 640 170" preserveAspectRatio="none">
<g class="grid"><line x1="40" y1="20" x2="600" y2="20"/><line x1="40" y1="65" x2="600" y2="65"/><line x1="40" y1="110" x2="600" y2="110"/><line x1="40" y1="155" x2="600" y2="155"/></g>
<g class="axis"><text x="8" y="24">60</text><text x="8" y="69">55</text><text x="8" y="114">50</text><text x="8" y="159">45</text></g>
<line class="ref" x1="40" y1="83" x2="600" y2="83"/><text class="axis" x="546" y="79">backtest 53.0</text>
<line class="ref" x1="40" y1="110" x2="600" y2="110"/>
<path class="band" d="M60 40 L120 60 L200 96 L300 100 L400 102 L500 104 L600 104 L600 128 L500 126 L400 122 L300 118 L200 116 L120 100 L60 80 Z"/>
<path class="l1" d="M60 60 L120 80 L200 106 L300 109 L400 112 L500 115 L600 116"/>
<path class="l2" d="M120 120 L200 90 L260 70 L320 100 L380 118 L440 108 L500 122 L560 112 L600 108"/>
<text class="lab" x="604" y="120">50.4%</text>
</svg>
<div class="foot">n = 2,783 windows, 2026-09-01 to 2026-09-29. Interval: day-block bootstrap, 95%.</div>
</div>"""
write("components/chart-frame.html", page('group="Components" name="Chart frame" subtitle="Title, subtitle, legend, plot with reference lines and interval band, footnote with n" width="760"', frame_body, frame_css))

table_css = f""".card{{background:{L['surface']};border:1px solid {L['border']};border-radius:14px;box-shadow:{T['shadow']['tokens'][0]['value']['light']};overflow:hidden}}
table{{border-collapse:collapse;width:100%;font-size:14px;line-height:20px}}
th{{background:{L['sunken']};text-align:left;font-size:13px;font-weight:500;padding:10px 16px;color:{L['text-secondary']}}}
td{{padding:10px 16px;border-top:1px solid {L['border']}}}
td.n,th.n{{text-align:right;font-family:{MONO};font-variant-numeric:tabular-nums;font-weight:500}}
td.muted{{color:{L['text-muted']}}}"""
table_body = f"""<div class="card"><table>
<tr><th>month</th><th class="n">windows</th><th class="n">accuracy [95% CI]</th><th class="n">backtest</th><th>status</th></tr>
<tr><td>2026-09</td><td class="n">2,783</td><td class="n">50.41 [49.55, 51.27]</td><td class="n">53.0</td><td style="color:{L['status-warning']};font-weight:500">interval includes baseline</td></tr>
<tr><td>2026-08</td><td class="n">2,973</td><td class="n">52.90 [52.01, 53.79]</td><td class="n">52.9</td><td style="color:{L['status-good']};font-weight:500">above baseline</td></tr>
<tr><td>2026-10</td><td class="n muted">0</td><td class="n muted">no data yet</td><td class="n">53.0</td><td class="muted">waiting</td></tr>
</table></div>"""
write("components/data-table.html", page('group="Components" name="Data table" subtitle="Sunken header, inset hairlines, mono numbers right-aligned, empty row" width="760"', table_body, table_css))

switch_css = f""".bar{{display:flex;align-items:center;gap:12px;background:{L['surface']};border:1px solid {L['border']};border-radius:14px;padding:12px 16px}}
.chip{{font-size:13px;line-height:18px;font-weight:500;padding:6px 14px;border-radius:999px;border:1px solid {L['border']};color:{L['ink']};background:{L['surface']}}}
.on{{background:{L['accent-tint']};border-color:{L['accent']};color:{L['ink']}}}
.cat{{font-size:12px;color:{L['text-muted']};margin-right:4px}}
.tog{{margin-left:auto;display:flex;border:1px solid {L['border']};border-radius:999px;overflow:hidden}}
.tog span{{font-size:12px;padding:5px 12px}}
.tog .on{{border-radius:0;border:none;background:{L['ink']};color:{L['surface']}}}
.rule{{height:1px;margin:16px 0;background:linear-gradient(90deg,transparent,{C['separator']['light']} 20%,{C['separator']['light']} 80%,transparent)}}
a{{color:{L['accent']};font-weight:500;text-decoration:none}}"""
switch_body = f"""<div class="bar"><span class="cat">crypto</span><span class="chip on">BTC 15-minute</span><span class="chip">ETH 15-minute</span><span class="cat">sports</span><span class="chip">NFL spreads</span><div class="tog"><span class="on">Light</span><span>Dark</span></div></div>
<div class="rule"></div>
<p style="margin:0;font-size:15px;line-height:24px">The models are frozen after a cutoff month; everything after it is scored as it happens. <a href="#">Raw record</a> and <a href="#">full report</a>.</p>
<p style="font-size:12px;color:{L['text-muted']};margin:12px 0 0">The accent appears once per view: the active chip, or a link. Dividers fade at both ends. Primary buttons, when there is one, are ink, not accent.</p>"""
write("components/switcher.html", page('group="Components" name="Model switcher and chrome" subtitle="Category chips, active state in accent tint, theme toggle, breathing-edge rule, links" width="760"', switch_body, switch_css))

print("cards:", sorted(str(p.relative_to(OUT)).replace("\\", "/") for p in OUT.rglob("*.html")))
