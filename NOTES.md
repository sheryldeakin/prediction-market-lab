# Notes

Execution notes (`note:`) and learnings (`learned:`), written in the session they happened. A learning stays here until it would change what a session does; then it moves to the working conventions or becomes a test.

- 2026-10-08 note: a build brief stated that `model_id(manifest)` recomputed on the committed manifest equals the id on the rows (`dbba22d74696`). It did not: `model_id()` hashed the stored manifest including its own `model_id` field, and the indicator-source hash read raw file bytes, so a CRLF checkout gave a different value from the LF one. The regression test written first caught both before any new model was frozen. Cost: an hour of the build. Next time: a premise about a committed file is checked against that file before it goes into a brief.
- 2026-10-08 learned: a class that is pickled from a module that also runs as `__main__` is saved as `__main__.<Class>` and cannot be loaded elsewhere. The rule estimators live in `models/btc_15m/rule_models.py` for that reason.
- 2026-10-08 learned: the indicator-source hash in `features.py` must normalise line endings, or a worktree with `autocrlf` writes a manifest the main checkout refuses; it now hashes with CRLF turned into LF, and a test pins that.
