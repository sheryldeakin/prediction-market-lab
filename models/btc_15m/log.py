"""Forward prediction log.

Freezes models trained through a cutoff month, then scores every window in the days
after it as Binance publishes them (daily files, about a day behind). Each window is
written once to results/btc_15m/predictions.csv with the model's probability and the
outcome, so the file is a forward record the backtest cannot touch.

    python -m models.btc_15m.log --train-start 2025-10 --train-end 2026-08

Re-running only appends windows not yet logged. Delete the saved models under
results/btc_15m/models/ to retrain (the log keeps the cutoff month it was made with).
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import joblib
import pandas as pd

from models.btc_15m.data import load, load_days
from models.btc_15m.evaluate import ALL, make_model
from models.btc_15m.features import HISTORY, Series, dataset

OUT = Path("results/btc_15m")
MODELS = OUT / "models"
LOG = OUT / "predictions.csv"
LOCKED = {0: ("forest", ALL), 3: ("xgb-all", ALL)}      # entry minute -> (model, features)


def train_or_load(train_start: str, train_end: str):
    MODELS.mkdir(parents=True, exist_ok=True)
    meta = MODELS / "trained_through.txt"
    if meta.exists() and meta.read_text().strip() == train_end and all((MODELS / f"k{k}.joblib").exists() for k in LOCKED):
        return {k: joblib.load(MODELS / f"k{k}.joblib") for k in LOCKED}
    s = Series(load(train_start, train_end))
    fitted = {}
    for k, (name, cols) in LOCKED.items():
        D = dataset(s, k)
        kind = {"forest": "forest", "xgb-all": "xgb", "hgb-all": "hgb"}[name]
        fitted[k] = make_model(kind).fit(D[cols], D.y)
        joblib.dump(fitted[k], MODELS / f"k{k}.joblib")
    meta.write_text(train_end)
    return fitted


def merge_log(existing: pd.DataFrame | None, new: pd.DataFrame) -> pd.DataFrame:
    """Append rows whose (t, minute) is not already logged; never change existing rows."""
    if existing is None or existing.empty:
        return new.sort_values(["t", "minute"]).reset_index(drop=True)
    key = set(zip(existing.t, existing.minute))
    add = new[[(t, m) not in key for t, m in zip(new.t, new.minute)]]
    return pd.concat([existing, add]).sort_values(["t", "minute"]).reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-start", default="2025-10")
    ap.add_argument("--train-end", default="2026-08")
    ap.add_argument("--through", default=None, help="last day to score, YYYY-MM-DD (default: yesterday UTC)")
    a = ap.parse_args()
    models = train_or_load(a.train_start, a.train_end)

    first = (pd.Period(a.train_end, freq="M") + 1).to_timestamp().date()
    last = dt.date.fromisoformat(a.through) if a.through else dt.datetime.utcnow().date() - dt.timedelta(days=1)
    days = [str(first + dt.timedelta(days=i)) for i in range((last - first).days + 1)]
    frame = load_days([a.train_end], days)                        # cutoff month supplies the history
    s = Series(frame)
    start_t = int(pd.Timestamp(first).timestamp())

    rows = []
    for k, (name, cols) in LOCKED.items():
        D = dataset(s, k)
        D = D[D.t >= start_t]
        if D.empty:
            continue
        prob = models[k].predict_proba(D[cols])[:, 1].astype(float)
        rows.append(pd.DataFrame({"t": D.t.values, "time_utc": pd.to_datetime(D.t, unit="s").dt.strftime("%Y-%m-%d %H:%M"),
                                  "minute": k, "model": name, "trained_through": a.train_end,
                                  "prob_up": prob.round(4), "outcome_up": D.y.values}))
    new = pd.concat(rows) if rows else pd.DataFrame(columns=["t", "minute"])
    existing = pd.read_csv(LOG) if LOG.exists() else None
    log = merge_log(existing, new)
    log.to_csv(LOG, index=False)
    added = len(log) - (0 if existing is None else len(existing))
    print(f"logged {added} new windows; {len(log)} total")
    for k in LOCKED:
        L = log[log.minute == k]
        if len(L):
            acc = ((L.prob_up > 0.5) == (L.outcome_up == 1)).mean()
            print(f"  minute {k}: {len(L)} windows, {L.time_utc.min()} to {L.time_utc.max()}, accuracy {acc*100:.2f}%")


if __name__ == "__main__":
    main()
