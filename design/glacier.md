# Glacier

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
