"""A second untouched holdout: January to September 2025, before the study period.

Everything in the report was built on 2025-10 to 2026-08. These nine earlier months were
never loaded by any study. This script scores them once, with the frozen models of the
forward log (trained on 2025-10 to 2026-08, models/btc_15m/log.py manifest), baselines
fitted on the same training months, and the stable event rules found by the wide search
(results/btc_15m/events2_all.csv), and records the commit it ran on. It refuses to run a
second time unless --force is given, so the result cannot be re-rolled.

Scoring months earlier than the training period is out-of-time in the other direction;
it tests whether the relationships held before they were found, which is as hard a test
as the future for a claim of a stable effect.

    python -m models.btc_15m.holdout2025
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.data import load
from models.btc_15m.evaluate import ALL, add_baseline_columns, make_model
from models.btc_15m.events2 import all_candidates, base_events
from models.btc_15m.features import FLOW_FEATURES, PRICE_FEATURES, Series, dataset
from models.btc_15m.indicators import INDICATOR_FEATURES
from models.btc_15m.log import LOCKED, train_or_load
from models.btc_15m.stats import block_bootstrap_ci, day_sign_test, month_block_bootstrap_ci, paired_difference_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
STAMP = OUT / "holdout_2025.json"


def bit_rates(D: pd.DataFrame) -> dict:
    """Training up-rate after a down (0) and an up (1) previous window."""
    return {v: float(D.y[D.prev_up == v].mean()) for v in (0, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-01")
    ap.add_argument("--end", default="2025-09")
    ap.add_argument("--train-start", default="2025-10")
    ap.add_argument("--train-end", default="2026-08")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if STAMP.exists() and not a.force:
        raise SystemExit(f"{STAMP} exists: the holdout has been scored once already ({json.loads(STAMP.read_text())['ran_at']}). Use --force only to correct a bug, and say so in the process log.")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "models"], capture_output=True, text=True).stdout.strip())
    models, manifest = train_or_load(a.train_start, a.train_end)
    train = Series(load(a.train_start, a.train_end))
    hold = Series(load(a.start, a.end))
    rows = []
    for k, (name, cols) in LOCKED.items():
        Dtr = add_baseline_columns(dataset(train, k), k)
        H = add_baseline_columns(dataset(hold, k), k)
        y, t = H.y.values, H.t.values
        preds = {name: models[k].predict_proba(H[cols])[:, 1]}
        if k == 0:
            # the model the ablation says carries an increment over the one-bit rule: added for the
            # second run (2026-10-01), declared in the process log, fit once on the training months
            rich = PRICE_FEATURES + FLOW_FEATURES + INDICATOR_FEATURES
            preds["forest (price + flow + indicators)"] = make_model("forest").fit(Dtr[rich], Dtr.y).predict_proba(H[rich])[:, 1]
            r = bit_rates(Dtr)
            preds["prev-window"] = np.where(H.prev_up.values == 1, r[1], r[0])
            base = "prev-window"
        else:
            preds["lead-z"] = make_model("logistic").fit(Dtr[["lead_z"]], Dtr.y).predict_proba(H[["lead_z"]])[:, 1]
            base = "lead-z"
        hb = ((preds[base] > 0.5) == y).astype(float)
        for n, p in preds.items():
            h = ((p > 0.5) == y).astype(float)
            m, lo, hi = block_bootstrap_ci(h, t)
            _, mlo, mhi = month_block_bootstrap_ci(h, t)
            if n == base:
                vs = "baseline"
            else:
                d, dlo, dhi = paired_difference_ci(h, hb, t)
                sg = day_sign_test(h, hb, t)
                vs = f"{d*100:+.2f} [{dlo*100:+.2f}, {dhi*100:+.2f}], days better {sg['share_days_a_better']*100:.0f}%, p {sg['p']:.4f}"
            rows.append([k, n, len(y), f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}] [{mlo*100:.2f}, {mhi*100:.2f}]", vs])
            print(rows[-1], flush=True)

    # ---- the stable event rules from the wide search ----
    ev = pd.read_csv(OUT / "events2_all.csv")
    D0 = dataset(hold, 0)
    Dtr0 = dataset(train, 0)
    frequent = [n for n, m in base_events(Dtr0).items() if m.sum() >= 600]
    C = all_candidates(D0, frequent)
    yb = D0.y.values
    held = scored = 0
    for _, r in ev.iterrows():
        m = C.get(r.event)
        if m is None or m.sum() < 30:
            continue
        scored += 1
        held += int(np.sign(yb[m].mean() - yb.mean()) == np.sign(float(r.deviation)))

    ran_at = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    with open(OUT / "holdout_2025.md", "w") as f:
        f.write(f"Second holdout: {a.start} to {a.end}, months no study had loaded, scored on {ran_at} at commit {commit[:10]}{' (with uncommitted model changes)' if dirty else ''}. Frozen models {manifest['model_id']} trained on {a.train_start} to {a.train_end}; baselines fitted on the same months; the indicator forest is fit once on the same months (see the process log for why it was added in a second run). Accuracy with day-block then month-block 95% intervals; the last column is minus the baseline on the same windows (day-block interval, share of days better, sign-flip p).\n\n")
        f.write("| minute | model | windows | accuracy [day CI] [month CI] | minus baseline |\n|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        f.write(f"\nStable event rules from the wide search: {scored} of {len(ev)} fired at least 30 times in the holdout, and {held} of those kept the direction they had in the search.\n")
    STAMP.write_text(json.dumps({"ran_at": ran_at, "commit": commit, "dirty": dirty, "model_id": manifest["model_id"]}, indent=2))
    print("wrote holdout_2025.md")


if __name__ == "__main__":
    main()
