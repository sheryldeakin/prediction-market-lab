# Design brief: the tracking page

A public web page that shows, for every model in this repo, what it predicted and what happened. It is the live counterpart of the reports in `docs/`: the reports say what the backtests found, the page says how the models are doing since they were frozen.

## Who reads it and what they need in the first ten seconds

- **A recruiter or hiring manager** with no background in forecasting. Needs: what is being predicted, is it working, and evidence that the numbers are honest. They will not read a table; they will read one chart and one sentence.
- **A quantitative reader** who does know the field. Needs: sample sizes, intervals, the baseline, the training cutoff, and a way to see the raw record.
- **The owner**, checking each morning whether the forward log moved.

The page must serve the first reader on the first screen and the second reader one scroll down.

## What it shows now

One model: BTC 15-minute direction. Data since 2026-09-01, about 96 windows a day at each of two entry points (the open, and three minutes in). Backtest reference levels: 53.0% at the open, 66.3% at minute 3, 50.1% majority baseline.

### Sections, in order

1. **Header.** Site name, one line saying what the site is, a models switcher (one entry today), light and dark toggle.
2. **Stat tiles** for the selected model: forward accuracy at the open, forward accuracy at minute 3, windows logged, days since the training cutoff, last update time. Each tile carries its comparison in small text (the backtest level, the baseline, the interval).
3. **The control chart** (the main element). Time on the x-axis, accuracy on the y-axis. Series: rolling 7-day accuracy and cumulative accuracy, one line each per entry point. Reference lines: the backtest level and the 50% baseline. A band for the 95% interval around the cumulative line. Hover gives the date, the rolling and cumulative values and the count. This chart is the answer to "is it working".
4. **Calibration.** Predicted probability against observed rate, ten deciles, forward period as dots and the backtest as a faint reference line. A perfectly calibrated model sits on the diagonal.
5. **Monthly table.** Month, windows, accuracy, interval, backtest level for that month where it exists.
6. **How to read this.** Four short paragraphs in plain language: what a window is, what "frozen after August" means, why the interval matters, why 53% is the number and not 80%. Written for the first reader.
7. **The record.** A link to the raw log (CSV in the repo, with its git history) and to the full report. A quantitative reader wants to be able to check.

### States the design must cover

- **No data yet** for a model (a model added today has zero forward windows): tiles show the backtest levels with a "no forward data yet" label, the chart shows the reference lines only.
- **One day of data**: the rolling line does not exist yet; only cumulative.
- **Many models**: the switcher becomes a list grouped by category (crypto, sports, other). Each model has the same sections.
- **Mobile**: the control chart must still read at phone width; tiles wrap; the table scrolls horizontally or collapses to the three most important columns.

## What comes later (design for it, do not build it)

- **More models** in other categories. The same sections repeat; the category matters only in the switcher and the header.
- **A comparison view**: several models' cumulative accuracy on one chart, each against its own baseline. Categorical hues in a fixed order, at most six.
- **A trade record**: what the owner actually traded against what the models said. Separate section or page; different visual weight (money, not accuracy).
- **Model report links**: each model's `docs/<model>.md` rendered as a page in the same system.

## Design system to produce

This page does not fit the existing personal-project palettes. It needs its own small system, derived with the same method (one accent hue; ink is a hard dark shade of that hue, never neutral black; dividers are breathing-edge gradients; surfaces and text tokens follow from the accent). Deliver:

- **Tokens.** One accent hue, ink, three surface levels, primary/secondary/muted text, a divider gradient, a focus ring. Light and dark, where dark is its own set of steps, not an inverted light.
- **Type.** One family for text, one monospace for numbers in tiles and tables (numbers must align). A scale of four sizes is enough.
- **Chart palette.** Four to six categorical hues in a fixed order for model series, one sequential hue for magnitude, a diverging pair for calibration error, and the reference-line grey. These go through the palette validator before they are final: adjacent pairs must be separable for colour-blind readers and readable on both surfaces.
- **Components.** Stat tile (value, label, comparison line, optional interval), chart frame (title, subtitle, legend row, plot, footnote with n), monthly table, model switcher, "how to read this" text block, footer with links.
- **Layout.** A single column that holds the chart at full width, tiles in a row above it, the rest below. Maximum content width around 1100px; 16px gutters on phones.

## Rules the page follows regardless of design

- One y-axis per chart, never two. Two measures of different scale get two charts.
- Thin marks, recessive grid, direct labels on at most four series, a legend whenever there are two or more.
- Every number on the page comes from the data store; nothing is typed into the page.
- Every accuracy is shown next to its baseline and its sample size. A number without both is not shown.
- Text carries text colours; series colours belong to marks only.
- No emojis, no exclamation marks, no words like "amazing". The tone is a lab notebook that someone else may read.

## Data contract

The page reads from a database populated by the daily runner. One document per prediction:

| field | type | example |
|---|---|---|
| model | string | `btc_15m` |
| category | string | `crypto` |
| t | integer, epoch seconds of the window open | 1788220800 |
| minute | integer, entry minute | 0 |
| prob_up | float | 0.4273 |
| outcome_up | 0 or 1 | 1 |
| trained_through | string, month | `2026-08` |

And one document per model with its name, category, question, backtest reference levels per minute, training cutoff, and links to the report and the log. Aggregates (rolling accuracy, calibration deciles, monthly rows) are computed by the site's API, not stored, so the page cannot drift from the record.

## Hosting

Vercel for the site (serverless routes read MongoDB Atlas directly; no separate server). The daily runner on the owner's machine writes each new window to the database and to the CSV in the repo; the CSV's git history is the audit trail and the database is the serving copy.
