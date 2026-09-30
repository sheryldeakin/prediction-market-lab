# Process log

What was decided, what went wrong, and what each mistake changed. Newest at the bottom. The point of keeping this next to the results is that a clean history would hide the part of the work that matters most: the checks.

## 2026-09-30

**Scope.** The model predicts the direction of a 15-minute window from public exchange data only. Trading venues and contract prices are deliberately out of scope; this repo is about the prediction problem.

**Baselines before models.** The first thing built was the lead-only logistic regression, because any model that cannot beat it has learned nothing the current price does not show. Most of the later studies are read against it.

**Bug: hand-typed number.** The first README draft carried an AUC of 0.526 for the boundary check; the generated table said 0.525. `scripts/update_readme.py` was written so that tables are spliced from `results/` and never typed.

**Lesson from a prototype: score on the label you mean.** A prototype that preceded this repo scored trades on the candle outcome instead of the settlement it was meant to model, and showed a +5c edge that vanished when scored on the right outcome. Carried in: the label is defined once, in `features.py`, and every study reads it from there.

**Decision: the forward log is append-only.** `log.py` freezes models trained through a cutoff month and scores each later window once. `merge_log` never changes an existing row; three tests cover it. The first forward month (September) came out at 50.4% at the open against 53% in the backtest, and the docs say so.

**Decision: day-clustered uncertainty everywhere.** Windows in one day share conditions. All intervals resample whole days and the permutation test shuffles labels within days; `tests/test_stats.py` checks that a model which only knows each day's drift gets no credit.

**Bug: triple-barrier leak at minute 3.** The first meta-labelling run showed 74% at minute 3 for fixed 10 bp barriers, up from 66%. Barriers measured from the open could be touched in minutes 1 to 3, which the model already sees at minute 3. Fixed so barriers apply from the entry price over the remaining minutes. Regression test: a window with a 30 bp spike at minute 1 must be labelled by the spike at minute 0 and not at minute 3. Corrected result: the direction of the remaining path at minute 3 is a coin flip (51%).

**Bug: feature cache collision.** To cut CPU load, features were cached to disk keyed on the series time span. Four coins over the same months share a span, so ETH, SOL and DOGE silently read BTC's file and the multi-asset table showed four identical rows. The key now includes a hash of the prices and volumes; the test builds two series on the same timestamps and asserts they get different files and different features.

**Decision: GPU for XGBoost and the GRU, host threads capped at two.** XGBoost on the GPU still used every CPU core for host-side work. With the cap an XGBoost fit averages 0.84 cores. The random forest has no GPU path and stays capped. `scripts/run_queue.py` starts jobs only when fewer than two of this repo's own jobs are running, so browser and remote-desktop load in the background do not block the queue.

**Result that changed the plan.** Honest nested tuning came out only 0.04 points below tuning on the test month. With 30 trials and a small space on a weak signal there is little to overfit; the gap that notebooks usually hide grows with trials and flexibility. Worth repeating with a larger search to show the effect.

**Ensembles found nothing to combine.** Averaging four base models equals the best single one at the open; the honest stacker is slightly behind. A test spies on the stacker's fits and asserts each one sees only the rows before the month it scores (600 rows for the first stacked month, 1,200 for the next), which is the check that makes the "slightly behind" believable.

**Database write path.** `publish.py` upserts one document per (model, window, minute) and uses `$setOnInsert` for the probability, so a re-send can never change a logged value; only the outcome field may be filled in later. The daily runner publishes when `MONGODB_URI` is set and says so when it is not. The CSV in git stays the audit record; the database is the serving copy, and the run prints a mismatch if the two counts differ.

**Four diagnostics from one set of predictions.** Calibration, conformal abstention, adversarial validation and importance-over-time all read the same walk-forward probabilities, so they were written as one module with the statistics as pure functions and the runner underneath. The tests check the Brier decomposition identity, that recalibration halves a planted error, that conformal coverage meets its target and abstains more as the target rises, and that permutation importance is zero for a feature the model never used.

**Adversarial validation reframed the drift question.** The months are easy to tell apart (AUC up to 0.84) but only by their volatility level, while the direction accuracy does not decay. Inputs drift; the relationship does not. That is a specific reason to keep every feature scale-free.
