"""Forward prediction log.

Freezes models trained through a cutoff month, then scores every window in the days
after it as Binance publishes them (daily files, about a day behind). Each window is
written once to results/btc_15m/predictions.csv with the model's probability and the
outcome, so the file is a forward record the backtest cannot touch.

    python -m models.btc_15m.log --train-start 2025-10 --train-end 2026-08
    python -m models.btc_15m.log --verify          # check the hash chain, write nothing

Integrity:
  manifest   results/btc_15m/models/manifest.json records what the frozen models are:
             training months, a SHA-256 of every candle file they were trained on, the
             feature version, the indicator code hash, each model's parameters and the
             code commit. Saved models are reused only when the manifest matches the
             request; model_id (a hash of the manifest) is written on every row.
  append     new rows are appended to the file; existing rows are never rewritten. A
             window may appear once per model_id (September 2026 does: once from the
             models frozen before the bug fixes, once from the re-fitted ones).
  chain      every row carries prev_hash (the previous row's row_hash) and row_hash
             (SHA-256 of prev_hash and the row's content), so editing, deleting or
             reordering any row breaks every hash after it. --verify checks the chain.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
from pathlib import Path

import joblib
import pandas as pd

from models.btc_15m.data import CACHE as CANDLE_CACHE, load, load_days
from models.btc_15m.evaluate import ALL, make_model
from models.btc_15m.features import _INDICATOR_SOURCE, FEATURE_VERSION, HISTORY, WINDOW, Series, dataset

OUT = Path("results/btc_15m")
MODELS = OUT / "models"
LOG = OUT / "predictions.csv"
LOCKED = {0: ("forest", ALL), 3: ("xgb-all", ALL)}      # entry minute -> (model, features)
KIND = {"forest": "forest", "xgb-all": "xgb", "hgb-all": "hgb"}
DATA_COLS = ["t", "time_utc", "minute", "model", "trained_through", "model_id", "prob_up", "outcome_up"]
GENESIS = "0" * 64
PRE_MANIFEST = "pre-manifest"          # model_id for rows logged before manifests existed


# ---------------- manifest ----------------

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def spec(train_start: str, train_end: str) -> dict:
    """The part of the manifest that decides whether saved models can be reused."""
    return {"train_start": train_start, "train_end": train_end, "feature_version": FEATURE_VERSION, "indicator_source": _INDICATOR_SOURCE,
            "history": HISTORY, "window": WINDOW, "locked": {str(k): {"model": name, "features": list(cols)} for k, (name, cols) in LOCKED.items()}}


def model_id(manifest: dict) -> str:
    keep = {k: v for k, v in manifest.items() if k not in ("trained_at", "code_commit")}
    return hashlib.sha256(json.dumps(keep, sort_keys=True).encode()).hexdigest()[:12]


def build_manifest(train_start: str, train_end: str, fitted: dict) -> dict:
    months = [str(p) for p in pd.period_range(train_start, train_end, freq="M")]
    files = {f"BTCUSDT-1m-{m}.csv": _sha256(CANDLE_CACHE / f"BTCUSDT-1m-{m}.csv") for m in months}
    m = spec(train_start, train_end)
    m["data_files"] = files
    m["params"] = {str(k): {p: repr(v) for p, v in sorted(fitted[k].get_params().items())} for k in fitted}
    m["code_commit"] = _commit()
    m["trained_at"] = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    m["model_id"] = model_id(m)
    return m


def train_or_load(train_start: str, train_end: str) -> tuple[dict, dict]:
    MODELS.mkdir(parents=True, exist_ok=True)
    mpath = MODELS / "manifest.json"
    want = spec(train_start, train_end)
    if mpath.exists() and all((MODELS / f"k{k}.joblib").exists() for k in LOCKED):
        manifest = json.loads(mpath.read_text())
        if all(manifest.get(key) == val for key, val in want.items()):
            return {k: joblib.load(MODELS / f"k{k}.joblib") for k in LOCKED}, manifest
    if os.environ.get("LAB_FORWARD_NO_TRAIN"):
        # an unattended runner must never mint a new model version: a spec mismatch is a bug to fix by hand
        raise RuntimeError("saved models do not match the spec and LAB_FORWARD_NO_TRAIN is set; refusing to retrain")
    s = Series(load(train_start, train_end))
    fitted = {}
    for k, (name, cols) in LOCKED.items():
        D = dataset(s, k)
        fitted[k] = make_model(KIND[name]).fit(D[cols], D.y)
        joblib.dump(fitted[k], MODELS / f"k{k}.joblib")
    manifest = build_manifest(train_start, train_end, fitted)
    mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    old = MODELS / "trained_through.txt"
    if old.exists():
        old.unlink()
    return fitted, manifest


# ---------------- hash chain ----------------

def row_text(r) -> str:
    """Canonical text of a row's content, stable across a CSV round trip."""
    return "|".join([str(int(r["t"])), str(r["time_utc"]), str(int(r["minute"])), str(r["model"]), str(r["trained_through"]),
                     str(r["model_id"]), f"{float(r['prob_up']):.4f}", str(int(r["outcome_up"]))])


def chain(rows: pd.DataFrame, prev: str = GENESIS) -> pd.DataFrame:
    """rows with prev_hash and row_hash columns, continuing the chain from prev."""
    out = rows[DATA_COLS].copy()
    prevs, hashes = [], []
    for _, r in out.iterrows():
        h = hashlib.sha256((prev + "|" + row_text(r)).encode()).hexdigest()
        prevs.append(prev); hashes.append(h)
        prev = h
    out["prev_hash"] = prevs
    out["row_hash"] = hashes
    return out


def verify_chain(log: pd.DataFrame) -> int | None:
    """Index of the first row whose hashes do not check out, or None if the chain holds."""
    prev = GENESIS
    for i, r in log.iterrows():
        h = hashlib.sha256((prev + "|" + row_text(r)).encode()).hexdigest()
        if r["prev_hash"] != prev or r["row_hash"] != h:
            return int(i)
        prev = h
    return None


def merge_log(existing: pd.DataFrame | None, new: pd.DataFrame) -> pd.DataFrame:
    """Rows of new whose (t, minute, model_id) is not already logged, in time order.
    Existing rows are never changed; the caller appends what this returns. A different
    model_id on an already-logged window is a new row, never a replacement: when the
    frozen models were re-fitted after the 2026-10-01 bug fixes, September was scored
    again under the new model_id beside the pre-manifest rows."""
    new = new.sort_values(["t", "minute"]).reset_index(drop=True)
    if existing is None or existing.empty:
        return new
    mid = existing.model_id if "model_id" in existing else pd.Series([PRE_MANIFEST] * len(existing))
    key = set(zip(existing.t, existing.minute, mid))
    return new[[(t, m, i) not in key for t, m, i in zip(new.t, new.minute, new.model_id)]].reset_index(drop=True)


def read_log(path: Path = LOG) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"model_id": str, "prev_hash": str, "row_hash": str})


def current_model_id() -> str | None:
    mpath = MODELS / "manifest.json"
    return json.loads(mpath.read_text())["model_id"] if mpath.exists() else None


def current_rows(log: pd.DataFrame) -> pd.DataFrame:
    """The rows scored by the current frozen models (the manifest's model_id). Before a
    manifest exists, every row. Readers of the log use this so that a window scored
    under two model versions is counted once."""
    mid = current_model_id()
    if mid is None or "model_id" not in log or not (log.model_id == mid).any():
        return log
    return log[log.model_id == mid]


def append_rows(path: Path, new: pd.DataFrame) -> int:
    """Append unlogged rows of new to the chained CSV at path. A log written before the
    chain existed is chained once in place (its rows keep their content and order)."""
    existing = pd.read_csv(path, dtype={"model_id": str, "prev_hash": str, "row_hash": str}) if path.exists() else None
    if existing is not None and "row_hash" not in existing.columns:
        if "model_id" not in existing.columns:
            existing["model_id"] = PRE_MANIFEST
        existing = chain(existing)
        existing.to_csv(path, index=False)
    if existing is not None:
        bad = verify_chain(existing)
        if bad is not None:
            raise RuntimeError(f"{path}: hash chain broken at row {bad}; refusing to append")
    add = merge_log(existing, new)
    if add.empty:
        return 0
    prev = existing.row_hash.iloc[-1] if existing is not None and len(existing) else GENESIS
    chained = chain(add, prev)
    chained.to_csv(path, mode="a", header=existing is None, index=False)
    return len(chained)


# ---------------- runner ----------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-start", default="2025-10")
    ap.add_argument("--train-end", default="2026-08")
    ap.add_argument("--through", default=None, help="last day to score, YYYY-MM-DD (default: yesterday UTC)")
    ap.add_argument("--verify", action="store_true", help="check the hash chain and exit")
    a = ap.parse_args()
    if a.verify:
        log = pd.read_csv(LOG, dtype={"model_id": str, "prev_hash": str, "row_hash": str})
        bad = verify_chain(log)
        print(f"{LOG}: {len(log)} rows, chain {'intact' if bad is None else f'BROKEN at row {bad}'}")
        raise SystemExit(0 if bad is None else 1)
    models, manifest = train_or_load(a.train_start, a.train_end)

    first = (pd.Period(a.train_end, freq="M") + 1).to_timestamp().date()
    last = dt.date.fromisoformat(a.through) if a.through else dt.datetime.utcnow().date() - dt.timedelta(days=1)
    days = [str(first + dt.timedelta(days=i)) for i in range((last - first).days + 1)]
    frame = load_days([a.train_end], days)                        # cutoff month supplies the history
    s = Series(frame)
    start_t = int(pd.Timestamp(first).timestamp())

    rows = []
    for k, (name, cols) in LOCKED.items():
        D = dataset(s, k, cache=False)
        D = D[D.t >= start_t]
        if D.empty:
            continue
        prob = models[k].predict_proba(D[cols])[:, 1].astype(float)
        rows.append(pd.DataFrame({"t": D.t.values, "time_utc": pd.to_datetime(D.t, unit="s").dt.strftime("%Y-%m-%d %H:%M"),
                                  "minute": k, "model": name, "trained_through": a.train_end, "model_id": manifest["model_id"],
                                  "prob_up": prob.round(4), "outcome_up": D.y.values}))
    new = pd.concat(rows) if rows else pd.DataFrame(columns=DATA_COLS)
    added = append_rows(LOG, new)
    log = pd.read_csv(LOG, dtype={"model_id": str})
    print(f"logged {added} new windows; {len(log)} total; models {manifest['model_id']} trained through {manifest['train_end']}")
    log = log[log.model_id == manifest["model_id"]]
    for k in LOCKED:
        L = log[log.minute == k]
        if len(L):
            acc = ((L.prob_up > 0.5) == (L.outcome_up == 1)).mean()
            print(f"  minute {k}: {len(L)} windows, {L.time_utc.min()} to {L.time_utc.max()}, accuracy {acc*100:.2f}%")


if __name__ == "__main__":
    main()
