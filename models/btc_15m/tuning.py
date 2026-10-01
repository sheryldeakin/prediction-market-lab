"""Hyperparameter search done honestly, and the size of the lie when it is not.

For each test month m, three XGBoost variants are scored on m:

  default        the fixed parameters used everywhere else in this repo
  tuned-honest   parameters chosen by Optuna on an inner split that ends before m:
                 train on months < m-1, validate on month m-1, pick the best log loss,
                 then refit on months < m
  tuned-on-test  the common mistake: the search validates on month m itself, then
                 the winner is scored on m

The gap between the last two is the optimism a reader should subtract from any
"tuned" result that does not describe its validation split.

    python -m models.btc_15m.tuning --start 2025-10 --end 2026-08 --minutes 0,3 --trials 30
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import log_loss, roc_auc_score
from xgboost import XGBClassifier

from models.btc_15m.data import load
from models.btc_15m.evaluate import N_JOBS, XGB_DEVICE, baseline_name, baseline_walk_forward, make_model
from models.btc_15m.features import FLOW_FEATURES, PRICE_FEATURES, Series, dataset
from models.btc_15m.indicators import INDICATOR_FEATURES
from models.btc_15m.stats import block_bootstrap_ci, paired_difference_ci

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)
OUT = Path("results/btc_15m")
COLS = PRICE_FEATURES + FLOW_FEATURES + INDICATOR_FEATURES
SPACE = {"max_depth": (2, 6), "learning_rate": (0.01, 0.2), "n_estimators": (100, 800),
         "min_child_weight": (5, 200), "subsample": (0.5, 1.0), "colsample_bytree": (0.4, 1.0), "reg_lambda": (0.5, 20.0)}


def build(params: dict) -> XGBClassifier:
    return XGBClassifier(**params, verbosity=0, tree_method="hist", device=XGB_DEVICE, n_jobs=N_JOBS)


def sample(trial: optuna.Trial) -> dict:
    return {"max_depth": trial.suggest_int("max_depth", *SPACE["max_depth"]),
            "learning_rate": trial.suggest_float("learning_rate", *SPACE["learning_rate"], log=True),
            "n_estimators": trial.suggest_int("n_estimators", *SPACE["n_estimators"], step=50),
            "min_child_weight": trial.suggest_int("min_child_weight", *SPACE["min_child_weight"], log=True),
            "subsample": trial.suggest_float("subsample", *SPACE["subsample"]),
            "colsample_bytree": trial.suggest_float("colsample_bytree", *SPACE["colsample_bytree"]),
            "reg_lambda": trial.suggest_float("reg_lambda", *SPACE["reg_lambda"], log=True)}


def search(Xtr, ytr, Xva, yva, trials: int, seed: int = 0) -> dict:
    """Best parameters by validation log loss. The caller decides what the validation set is."""
    def objective(trial):
        p = sample(trial)
        m = build(p).fit(Xtr, ytr)
        return log_loss(yva, np.clip(m.predict_proba(Xva)[:, 1], 1e-6, 1 - 1e-6))
    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=seed))
    study.optimize(objective, n_trials=trials)
    return study.best_params


def nested_walk_forward(D: pd.DataFrame, cols, trials: int, log=print):
    """Returns dict variant -> (pred, y, t) over the test months, plus the honest params per month."""
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    months = sorted(month.unique())
    y = D.y.values
    preds = {v: np.full(len(D), np.nan) for v in ("default", "tuned-honest", "tuned-on-test")}
    chosen = []
    for m in months[3:]:
        prev = months[months.index(m) - 1]
        tr, te = (month < m).values, (month == m).values
        inner_tr, inner_va = (month < prev).values, (month == prev).values
        preds["default"][te] = make_model("xgb").fit(D.loc[tr, cols], y[tr]).predict_proba(D.loc[te, cols])[:, 1]
        honest = search(D.loc[inner_tr, cols], y[inner_tr], D.loc[inner_va, cols], y[inner_va], trials)
        preds["tuned-honest"][te] = build(honest).fit(D.loc[tr, cols], y[tr]).predict_proba(D.loc[te, cols])[:, 1]
        cheat = search(D.loc[tr, cols], y[tr], D.loc[te, cols], y[te], trials)
        preds["tuned-on-test"][te] = build(cheat).fit(D.loc[tr, cols], y[tr]).predict_proba(D.loc[te, cols])[:, 1]
        chosen.append({"month": str(m), **honest})
        log(f"  {m}: default {((preds['default'][te] > .5) == y[te]).mean()*100:.2f}%  honest {((preds['tuned-honest'][te] > .5) == y[te]).mean()*100:.2f}%  on-test {((preds['tuned-on-test'][te] > .5) == y[te]).mean()*100:.2f}%")
    keep = ~np.isnan(preds["default"])
    return {v: (p[keep], y[keep], D.t.values[keep]) for v, p in preds.items()}, pd.DataFrame(chosen)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--minutes", default="0,3")
    ap.add_argument("--trials", type=int, default=30)
    a = ap.parse_args()
    s = Series(load(a.start, a.end))
    rows, params = [], []
    for k in [int(x) for x in a.minutes.split(",")]:
        print(f"minute {k}", flush=True)
        D = dataset(s, k)
        res, chosen = nested_walk_forward(D, COLS, a.trials, log=lambda x: print(x, flush=True))
        base_hits = None
        for v in ("default", "tuned-honest", "tuned-on-test"):
            pred, y, t = res[v]
            hits = ((pred > 0.5) == y).astype(float)
            m, lo, hi = block_bootstrap_ci(hits, t)
            if base_hits is None:
                base_hits, vs = hits, "baseline"
            else:
                d, dlo, dhi = paired_difference_ci(hits, base_hits, t)
                vs = f"{d*100:+.2f} [{dlo*100:+.2f}, {dhi*100:+.2f}]"
            rows.append([k, v, len(y), f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", f"{roc_auc_score(y, pred):.3f}",
                         f"{log_loss(y, np.clip(pred, 1e-6, 1-1e-6)):.4f}", vs])
        # the one-feature baseline on the same windows, for scale
        pred_d, y_d, t_d = res["default"]
        bp, _, _, bt = baseline_walk_forward(D, k)
        bp = pd.Series(bp, index=bt).reindex(t_d).values
        bh = ((bp > 0.5) == y_d).astype(float)
        m, lo, hi = block_bootstrap_ci(bh, t_d)
        d, dlo, dhi = paired_difference_ci(bh, base_hits, t_d)
        rows.append([k, f"one-feature baseline ({baseline_name(k)})", len(y_d), f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", f"{roc_auc_score(y_d, bp):.3f}",
                     f"{log_loss(y_d, np.clip(bp, 1e-6, 1-1e-6)):.4f}", f"{d*100:+.2f} [{dlo*100:+.2f}, {dhi*100:+.2f}]"])
        chosen.insert(0, "minute", k)
        params.append(chosen)
    with open(OUT / "tuning.md", "w") as f:
        f.write(f"XGBoost with default parameters vs Optuna search ({a.trials} trials per month) validated honestly (on the month before the test month) and validated on the test month itself. Walk-forward, price + flow + indicator features. Last column: accuracy minus default on the same windows, day-block 95% interval.\n\n")
        f.write("| minute | variant | n | accuracy [95% CI] | AUC | log loss | vs default |\n|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    pd.concat(params).to_csv(OUT / "tuning_params.csv", index=False)
    print("wrote tuning.md")


if __name__ == "__main__":
    main()
