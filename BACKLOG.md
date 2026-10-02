# Backlog

Deferred work, each with a size and the trigger that makes it worth doing. Finishing an item removes its line. Known limits that are deliberate are listed at the end so they are not rediscovered as bugs.

## Studies

- **HMM variants not yet tried.** An HMM observing order-flow imbalance rather than returns; a non-homogeneous transition matrix driven by time of day; a hidden semi-Markov model with explicit durations. Size: a day. Trigger: a reason to believe the states would be anything but volatility states (studies 29 and 30 say they are).
- **Derivatives and tick events for the library.** Funding extremes, open-interest spikes, liquidation signatures, large-trade bursts, as events in the price-action library. Size: half a day plus a nine-year run. Trigger: the tick-data mechanism study below, which needs the same plumbing.
- **The mechanism of the reversal.** Order-book replenishment and inventory after a sharp move, from the tick history (2017-08 to 2026-08 is downloaded). Size: one to two days. Trigger: the live view exists, so the result has somewhere to go.
- **Longer histories for the other coins and venues.** ETH, SOL and DOGE klines back to listing, the futures series from 2019, Coinbase and Bitstamp histories. Size: a day of downloads and a multi-asset rerun. Trigger: the refinement list for the current data is finished (owner's call, 2026-10-01: refine before extending).
- **Real quotes for the cost question.** The 5-basis-point bounces cannot be traded on spot (horizons.md); whether a window contract carries the edge after its spread and fee needs quotes this repo does not have. Size: unknown. Trigger: a quote source that fits the repo's rule of no venue code in the models.

## Product

- **Live view on the tracking page.** Every minute: the active patterns, their next-5-minute probability and years held, the implied contract move, shown separately from the window call; reads the same tables and the forward log. Size: a week with the design frames. Trigger: the owner's design frames are ready.

## Known limits

- XGBoost fits differ slightly between GPU and CPU, so a model's accuracy can differ by a few hundredths of a point between tables generated on different devices; the walk-forward table is the reference.
- September 2026 is a holdout, not forward: the log was first written after the month had passed. The forward log proper begins 2026-10-01.
- The first year of every nine-year study takes its volatility cutoffs from its own first quarter, because no earlier year exists; later years use the previous year.
- The tercile cutoffs in the volatility table come from the previous year, so a calm year after a wild one has most of its minutes in the low tercile. This is deliberate: the tercile must be known at the time.
- Background runs are launched through `scripts/run_queue.py`, which waits for load; a job that seems not to start is usually waiting.
