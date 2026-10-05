# Backlog

Deferred work, each with a size and the trigger that makes it worth doing. Finishing an item removes its line. Known limits that are deliberate are listed at the end so they are not rediscovered as bugs.

## Studies

- **HMM variants not yet tried.** An HMM observing order-flow imbalance rather than returns; a non-homogeneous transition matrix driven by time of day; a hidden semi-Markov model with explicit durations. Size: a day. Trigger: the dashboard and viewing layer are built (owner, 2026-10-01: tabled until then, not dropped, against the outside review's advice to drop; studies 29 and 30 say the states are volatility states).
- **Derivatives and tick events for the library.** Funding extremes, open-interest spikes, liquidation signatures, large-trade bursts, as events in the price-action library. Size: half a day plus a nine-year run. Trigger: the dashboard and viewing layer are built (owner, 2026-10-01: tabled, not dropped), and the tick-data mechanism study below, which needs the same plumbing.
- **Which part of the seconds-entry gain is the tick features.** Study 31 found the forest and XGBoost above the lead-sign rule at 10 and 30 seconds, but they also carry the minute-0 features the rule lacks. Ablation: the forest on the minute-0 set plus the lead alone, against plus all tick features, same windows, plus a month-block interval. Size: an hour (the tick table is cached). Trigger: before anyone cites the 10 or 30 second increments, or before a seconds-after-open entry is added to the forward log.
- **The mechanism of the reversal.** Order-book replenishment and inventory after a sharp move, from the tick history (2017-08 to 2026-08 is downloaded). Size: one to two days, as two pre-specified hypotheses only (bid-ask bounce against transient liquidity impact; per-second trade aggregates cannot see the order book, so inventory and replenishment stay out of reach). Trigger: the live view exists, so the result has somewhere to go.
- **Longer histories for the other coins and venues.** ETH, SOL and DOGE klines back to listing, the futures series from 2019, Coinbase and Bitstamp histories. Size: a day of downloads and a multi-asset rerun, as one bounded replication matrix with frozen definitions, evaluated by period and leave-one-venue-out rather than pooled (correlated venues are robustness, not independent evidence). Trigger: the dashboard and viewing layer are built (owner, 2026-10-01: tabled, not dropped).
- **Real quotes for the cost question.** The 5-basis-point bounces cannot be traded on spot (horizons.md); whether a window contract carries the edge after its spread and fee needs quotes this repo does not have. Size: unknown. Decided 2026-10-01: the tracking layer (not the models) collects a binary-contract venue's quotes beside the forward log, so the forward period can measure information beyond the contract price (log loss and Brier against the quote, value at the displayed bid and ask, not the midpoint). Trigger: the tracking layer exists.

## Product

- **Link to the site.** Once calledit.money is deployed, the README and the forward-log section of the report link to it (the site is built in a separate private repo that reads this log). Size: ten minutes. Trigger: the deploy.
- **Live view on the tracking page.** Every minute: the active patterns, their next-5-minute probability and years held, the implied contract move, shown separately from the window call; reads the same tables and the forward log. Shipped as a pre-registered forward experiment: frozen rule set, probabilities shrunk by the forward calibration and the calibration slope, a stated stopping rule (about twelve months for a two-standard-error call on a one-point increment at 96 windows a day), and a decay forecast beside each cell. Size: a week with the design frames. Trigger: the owner's design frames are ready (owner, 2026-10-01: fleshed out, more to add).

## Known limits

- XGBoost fits differ slightly between GPU and CPU, so a model's accuracy can differ by a few hundredths of a point between tables generated on different devices; the walk-forward table is the reference.
- September 2026 is a holdout, not forward: the log was first written after the month had passed. The forward log proper begins 2026-10-01.
- The first year of every nine-year study takes its volatility cutoffs from its own first quarter, because no earlier year exists; later years use the previous year.
- The tercile cutoffs in the volatility table come from the previous year, so a calm year after a wild one has most of its minutes in the low tercile. This is deliberate: the tercile must be known at the time.
- The forward log is computed on GitHub Actions, not on the owner's machine; the CSV in the repo is the serving copy until the per-window runner brings the database (the site repo's batch 2).
- Background runs are launched through `scripts/run_queue.py`, which waits for load; a job that seems not to start is usually waiting.
