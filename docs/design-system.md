# Glacier design system

Glacier is the design system for a public page that reports how prediction models are doing: what they predicted, what happened, and how sure the numbers are. It reads as a measuring instrument. Cool, precise, quiet; one accent, tinted neutrals, numbers that line up.

It is the fifth instance of one method: one accent hue; ink as a hard dark shade of that hue rather than neutral black; a tinted neutral ramp; dividers that fade at both ends; one radius scale; type by role. The earlier instances belong to personal tools and lean on nature palettes. Glacier does not: its subject is evidence, and its palette says so.

## Principles

1. **The number and its context arrive together.** No accuracy is shown without its baseline and its sample size. A stat tile is a value, a label and a comparison line; a chart carries its n in the footnote. A number alone is a claim; a number with its baseline is a finding.
2. **Colour means something or is not used.** Text wears text tokens. Series colours belong to marks. The accent appears once per view (the active model, a link, the primary action) or not at all. Status colours ship with a word beside them.
3. **The chart is the argument.** The control chart is the page; tiles summarise it and the table backs it up. Give the chart the full column and keep the furniture lighter than it.
4. **Honest states are designed states.** No forward data yet, one day of data, a stale log, a model below its baseline: each has a specified look, in text-muted or a status colour with its word, never an empty box.
5. **Quiet depth.** Hairline borders, one resting shadow tinted toward ink, a faint page wash. Depth implies rank; nothing is elevated for decoration.

## Colour

The accent is an indigo (`accent`, 5.2:1 on surface in light, 5.0:1 in dark). `ink` is the same hue driven to a hard dark (`#1f2d5c`, 13:1 on surface); the neutrals (`canvas`, `surface`, `sunken`, `border`) are blue-tinted, never pure grey. Dark mode is its own set of steps validated against the dark surface, not an inverted light theme: the accent lightens to `#5b7cf0`, the series shift to their dark variants, and the interval band raises its alpha.

Chart series are six hues in a fixed order (`series-1` to `series-6`): blue, orange, aqua, yellow, magenta, green. They passed the colour-vision separation check on both surfaces (worst adjacent pair 9.1 in light, 8.4 in dark, on the 0 to 100 OKLab scale, floor 8). Three of them sit below 3:1 against the light surface, so every series is direct-labelled and every chart has a table view; colour never carries identity alone. A seventh series does not get a new hue; it folds into Other or the chart becomes small multiples. `reference` is the grey for baselines and backtest levels; it recedes behind every series. `interval-fill` is the accent at low alpha for confidence bands.

Status colours (`status-good`, `status-warning`, `status-critical`) are reserved for the state of a model relative to its baseline and for a stale log. They are never reused for a series.

## Type

Inter for words, JetBrains Mono for numbers, both hosted on Google Fonts. Numbers that change or align (tile values, table cells, hover readouts, axis ticks) are always mono with tabular numerals, so a column of accuracies lines up on the decimal point. Sentence case everywhere; no uppercase letterspaced labels. Roles are fixed: `display` once per page, `title` on sections and chart frames, `subtitle` beneath a title in `text-secondary`, `body` for prose at 45 to 75 characters a line, `ui` for controls, `caption` for footnotes and timestamps in `text-muted`.

## Layout

A single column, maximum content width 1100px, 16px gutters on phones and 24px above. The control chart spans the column. Stat tiles sit in one row above it and wrap to two columns on phones. The monthly table and the plain-language explanation follow. Nothing responsive is cleverer than wrapping; the chart keeps one layout and scales.

## Components

- **StatTile**: value (`numeral-lg`), label (`ui`), comparison line (`caption` in `text-secondary`: the backtest level, the baseline, or the interval), optional status word with its colour. Tiles hug content; no minimum heights.
- **ChartFrame**: title (`title`), subtitle (`subtitle`), a legend row when two or more series are present, the plot, a footnote with n and the date range (`caption`). The plot is the consumer's; the frame is the system's. One y-axis per frame.
- **DataTable**: header row on `sunken`, hairline row separators inset to the text, numbers right-aligned in `numeral`, text cells in `body` at 14px. On phones the three most important columns stay and the rest collapse behind a disclosure.

Not yet built as components, specified in the brief: the model switcher (pill chips, `accent-tint` for the active one), the theme toggle, the "how to read this" text block, the footer with links to the raw record and the report.

## Charts, the rules the system enforces

One y-axis per chart, never two. Thin marks: 2px lines, markers 8px or larger with a 1.5px surface ring, 4px rounded bar ends anchored to the baseline. Grid and axes in `border` and `text-muted`, recessive. Direct labels on at most four series; a legend whenever there are two or more; a single series needs no legend. Hover gives a crosshair and a tooltip in `surface` with `shadow-raised`. Reference lines dashed in `reference`. Every chart has a table view.

## Voice

A lab notebook someone else may read. Plain words, short sentences, no exclamation marks, no emojis, no superlatives. "Forward accuracy at the open: 50.4% on 2,783 windows, against 53.0% in the backtest" is the register.

---


## Colour

| token | light | dark | usage |
|---|---|---|---|
| `canvas` | `#f7f8fb` | `#0f1117` | Page background. A faint vertical wash from surface to canvas is allowed; never a flat pure white page. |
| `surface` | `#ffffff` | `#161a24` | Cards, chart frames, table bodies, the app bar. |
| `sunken` | `#eef1f7` | `#1c2130` | Inputs, wells, code blocks, the table header row. One step down from surface, never a beige. |
| `border` | `#d9dde8` | `#2a3143` | Hairline borders on cards and inputs. Dividers use separator as a breathing-edge gradient instead. |
| `border-strong` | `#bfc6d8` | `#3b4459` | Hover and focus borders, table rules that must read at a glance. |
| `ink` | `#1f2d5c` | `#e7ebf6` | Headings and primary text. A hard dark shade of the accent hue, never neutral black. 13:1 on surface. |
| `text-secondary` | `#3d4870` | `#b8c0d4` | Body text of lower rank: table cells, chart footnotes, the comparison line on a stat tile. |
| `text-muted` | `#5c6685` | `#8f98b0` | Captions, axis labels, timestamps, empty-state copy. Passes 4.5:1 on surface and on sunken. |
| `accent` | `#3e63dd` | `#5b7cf0` | The one colour: links, the primary button, focus ring, the active model in the switcher, series 1. Used once per view or not at all. |
| `accent-hover` | `#3253c2` | `#7a95f4` | Hover state of anything painted accent. One step along the ramp, never a new hue. |
| `accent-tint` | `#eaf0ff` | `#1b2440` | Selected rows, the active chip, hover wash on list items. Text on it is ink. |
| `separator` | `rgba(31,45,92,0.28)` | `rgba(231,235,246,0.22)` | Breathing-edge dividers: linear-gradient(90deg, transparent, separator 20%, separator 80%, transparent). Never an edge-to-edge line. |
| `shadow-ink` | `rgba(31,45,92,0.08)` | `rgba(0,0,0,0.45)` | The colour inside every box-shadow, tinted toward ink. Alpha stays at or under 0.12 in light. |
| `reference` | `#7d859c` | `#8a92a8` | Reference lines on charts: the 50% baseline, the backtest level. A grey that recedes behind every series. |
| `series-1` | `#3e63dd` | `#5b7cf0` | Categorical series 1. Fixed order: 1 blue, 2 orange, 3 aqua, 4 yellow, 5 magenta, 6 green. Assigned by entity and never re-painted when a filter removes a series. |
| `series-2` | `#eb6834` | `#d95926` | Categorical series 2 (orange). |
| `series-3` | `#1baf7a` | `#199e70` | Categorical series 3 (aqua). Below 3:1 on the light surface: always direct-labelled, never colour alone. |
| `series-4` | `#eda100` | `#c98500` | Categorical series 4 (yellow). Below 3:1 on the light surface: always direct-labelled. |
| `series-5` | `#e87ba4` | `#d55181` | Categorical series 5 (magenta). Below 3:1 on the light surface: always direct-labelled. |
| `series-6` | `#008300` | `#3fae3f` | Categorical series 6 (green). The last slot; a seventh series folds into Other or becomes a small multiple. |
| `interval-fill` | `rgba(62,99,221,0.12)` | `rgba(91,124,240,0.18)` | The 95% interval band around a cumulative accuracy line. Series colour at low alpha, no border. |
| `status-good` | `#1a7f4b` | `#4cc38a` | A model above its baseline with the interval clear of it. Always with the word beside it, never colour alone. |
| `status-warning` | `#9f630d` | `#e0a53a` | A model whose interval includes the baseline. Always with the word. |
| `status-critical` | `#c0392b` | `#ef6b5a` | A model below its baseline, or a stale log. Always with the word. |

## Type

Families: sans `Inter, system-ui, -apple-system, "Segoe UI", sans-serif`; mono `"JetBrains Mono", ui-monospace, SFMono-Regular, Consolas, monospace`.

| style | family | size | line height | weight | usage |
|---|---|---|---|---|---|
| `display` | sans | 32px | 36px | 600 | Page title, one per page. |
| `title` | sans | 20px | 26px | 600 | Section and chart titles, left-aligned inside the frame. |
| `subtitle` | sans | 15px | 22px | 400 | The line under a title, in text-secondary. |
| `body` | sans | 15px | 24px | 400 | Prose, 45 to 75 characters a line. |
| `ui` | sans | 13px | 18px | 500 | Controls, chips, the switcher, legend labels. Sentence case, never uppercase. |
| `caption` | sans | 12px | 16px | 400 | Footnotes under charts, axis titles, timestamps, in text-muted. |
| `numeral-lg` | mono | 28px | 32px | 600 | The value on a stat tile. Tabular numerals so tiles align. |
| `numeral` | mono | 14px | 20px | 500 | Table cells, hover readouts, intervals. Right-aligned in tables. |
| `axis` | mono | 11px | 14px | 400 | Axis tick labels, in text-muted. |

## Spacing

| token | value | usage |
|---|---|---|
| `space-1` | `4px` | The grid unit; gaps inside a chip. |
| `space-2` | `8px` | Inside a control; between a value and its label. |
| `space-3` | `12px` | Between controls in a row; legend item gap. |
| `space-4` | `16px` | Page gutter on phones; between tiles. |
| `space-6` | `24px` | Card and chart-frame padding; between cards. |
| `space-8` | `32px` | Between page sections. |
| `space-12` | `48px` | Above the first section and below the last. |

## Radius

| token | value | usage |
|---|---|---|
| `radius-sm` | `6px` | Chips, inputs, table header corners. |
| `radius-md` | `10px` | Buttons, stat tiles. |
| `radius-lg` | `14px` | Chart frames and cards. Children use md (concentric: parent radius minus padding). |
| `radius-pill` | `999px` | The model switcher chips and the theme toggle. |

## Shadow

| token | value | usage |
|---|---|---|
| `shadow-resting` | light `0 1px 2px rgba(31,45,92,0.06), 0 1px 3px rgba(31,45,92,0.10)`, dark `0 1px 2px rgba(0,0,0,0.35), 0 1px 3px rgba(0,0,0,0.45)` | Cards and chart frames at rest. One overhead light source; sharp close layer plus soft ambient. |
| `shadow-raised` | light `0 2px 4px rgba(31,45,92,0.06), 0 6px 14px rgba(31,45,92,0.10)`, dark `0 2px 4px rgba(0,0,0,0.4), 0 8px 20px rgba(0,0,0,0.5)` | Menus, popovers, the hover tooltip on a chart. Never on content cards. |
