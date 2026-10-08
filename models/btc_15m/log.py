"""Forward prediction log.

Freezes models trained through a cutoff month, then scores every window in the days
after it as Binance publishes them (daily files, about a day behind). Each window is
written once to a chained CSV with the model's probability and the outcome, so the file
is a forward record the backtest cannot touch.

There are two entry sets, each with its own models, manifest and log:

  main     minute 0 (forest) and minute 3 (xgb-all)         results/btc_15m/predictions.csv
  minutes  minutes 0 to 14, xgb-all and the minute's one-bit  results/btc_15m/predictions_minutes.csv
           rule (prev-window at 0, lead-z after); forward record starts 2026-10-09

    python -m models.btc_15m.log --train-start 2025-10 --train-end 2026-08     # both sets
    python -m models.btc_15m.log --set minutes                                  # one set
    python -m models.btc_15m.log --verify          # check the hash chains, write nothing

Integrity:
  manifest   <models dir>/manifest.json records what the frozen models are:
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
import dataclasses
import datetime as dt
import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import joblib
import pandas as pd

from models.btc_15m.data import CACHE as CANDLE_CACHE, load, load_days
from models.btc_15m.evaluate import ALL, add_baseline_columns, make_model
from models.btc_15m.features import _INDICATOR_SOURCE, FEATURE_VERSION, HISTORY, WINDOW, Series, dataset
from models.btc_15m.rule_models import PrevWindow

OUT = Path("results/btc_15m")
MODELS = OUT / "models"
LOG = OUT / "predictions.csv"
LOCKED = {0: ("forest", ALL), 3: ("xgb-all", ALL)}      # entry minute -> (model, features)
KIND = {"forest": "forest", "xgb-all": "xgb", "hgb-all": "hgb", "prev-window": "bitrate", "lead-z": "logistic"}
DATA_COLS = ["t", "time_utc", "minute", "model", "trained_through", "model_id", "prob_up", "outcome_up"]
GENESIS = "0" * 64
PRE_MANIFEST = "pre-manifest"          # model_id for rows logged before manifests existed


# ---------------- entry sets ----------------

@dataclass
class EntrySet:
    """A set of frozen entries: where its models and log live and which (minute, model, features) it holds.

    forward_start is the first day whose windows may enter the log; None means the set was
    frozen before this field existed (the main set), and its spec keeps the format it had then."""
    name: str
    models_dir: Path
    log_path: Path
    entries: list                       # [(minute, model name, feature columns)]
    forward_start: str | None = None
    primary_comparison: str | None = None

    @property
    def legacy(self) -> bool:
        return self.forward_start is None

    def minutes(self) -> list[int]:
        return sorted({m for m, _, _ in self.entries})

    def mkey(self, minute: int, name: str):
        """Key of an entry in the dict of fitted models: the minute alone for the main set."""
        return minute if self.legacy else (minute, name)

    def pkey(self, minute: int, name: str) -> str:
        """Key of an entry in the manifest's params."""
        return str(minute) if self.legacy else f"{minute}-{name}"

    def file(self, minute: int, name: str) -> Path:
        return self.models_dir / (f"k{minute}.joblib" if self.legacy else f"k{minute}-{name}.joblib")

    def spec(self, train_start: str, train_end: str) -> dict:
        """The part of the manifest that decides whether saved models can be reused."""
        s = {"train_start": train_start, "train_end": train_end, "feature_version": FEATURE_VERSION, "indicator_source": _INDICATOR_SOURCE,
             "history": HISTORY, "window": WINDOW}
        if self.legacy:
            s["locked"] = {str(k): {"model": name, "features": list(cols)} for k, name, cols in self.entries}
        else:
            s["entries"] = [{"minute": k, "model": name, "features": list(cols)} for k, name, cols in self.entries]
            s["forward_start"] = self.forward_start
            s["primary_comparison"] = self.primary_comparison
        return s


MAIN = EntrySet("main", MODELS, LOG, [(k, name, cols) for k, (name, cols) in LOCKED.items()])

MINUTES = EntrySet(
    "minutes", OUT / "models_minutes", OUT / "predictions_minutes.csv",
    [(k, name, cols) for k in range(WINDOW)
     for name, cols in (("xgb-all", ALL), (("prev-window", ["prev_up"]) if k == 0 else ("lead-z", ["lead_z"])))],
    forward_start="2026-10-09",
    primary_comparison="xgb-all against the one-bit rule at its minute, paired accuracy per minute and pooled over minutes, day-clustered")


def new_model(name: str):
    kind = KIND[name]
    return PrevWindow() if kind == "bitrate" else make_model(kind)


def entry_frame(s: Series, k: int, cache: bool = True) -> pd.DataFrame:
    """The dataset at minute k with the one-feature rule columns (prev_up, lead_z) added."""
    return add_baseline_columns(dataset(s, k, cache=cache), k)


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


def spec(train_start: str, train_end: str, eset: EntrySet | None = None) -> dict:
    """The part of the manifest that decides whether saved models can be reused."""
    return (eset or MAIN).spec(train_start, train_end)


def model_id(manifest: dict) -> str:
    keep = {k: v for k, v in manifest.items() if k not in ("trained_at", "code_commit", "model_id")}
    return hashlib.sha256(json.dumps(keep, sort_keys=True).encode()).hexdigest()[:12]


def build_manifest(train_start: str, train_end: str, fitted: dict, eset: EntrySet | None = None) -> dict:
    eset = eset or MAIN
    months = [str(p) for p in pd.period_range(train_start, train_end, freq="M")]
    files = {f"BTCUSDT-1m-{m}.csv": _sha256(CANDLE_CACHE / f"BTCUSDT-1m-{m}.csv") for m in months}
    m = eset.spec(train_start, train_end)
    m["data_files"] = files
    m["params"] = {eset.pkey(k, name): {p: repr(v) for p, v in sorted(fitted[eset.mkey(k, name)].get_params().items())}
                   for k, name, _ in eset.entries}
    m["code_commit"] = _commit()
    m["trained_at"] = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    m["model_id"] = model_id(m)
    return m


def train_or_load(train_start: str, train_end: str, eset: EntrySet | None = None) -> tuple[dict, dict]:
    eset = eset or dataclasses.replace(MAIN, models_dir=MODELS)         # MODELS read at call time
    eset.models_dir.mkdir(parents=True, exist_ok=True)
    mpath = eset.models_dir / "manifest.json"
    want = eset.spec(train_start, train_end)
    if mpath.exists() and all(eset.file(k, name).exists() for k, name, _ in eset.entries):
        manifest = json.loads(mpath.read_text())
        if all(manifest.get(key) == val for key, val in want.items()):
            return {eset.mkey(k, name): joblib.load(eset.file(k, name)) for k, name, _ in eset.entries}, manifest
    if os.environ.get("LAB_FORWARD_NO_TRAIN"):
        # an unattended runner must never mint a new model version: a spec mismatch is a bug to fix by hand
        raise RuntimeError("saved models do not match the spec and LAB_FORWARD_NO_TRAIN is set; refusing to retrain")
    s = Series(load(train_start, train_end))
    fitted = {}
    for k in eset.minutes():
        D = entry_frame(s, k)
        for m, name, cols in eset.entries:
            if m != k:
                continue
            fitted[eset.mkey(k, name)] = new_model(name).fit(D[cols], D.y)
            joblib.dump(fitted[eset.mkey(k, name)], eset.file(k, name))
    manifest = build_manifest(train_start, train_end, fitted, eset)
    mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    old = eset.models_dir / "trained_through.txt"
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
    """Rows of new whose (t, minute, model, model_id) is not already logged, in time order.
    Existing rows are never changed; the caller appends what this returns. A different
    model_id on an already-logged window is a new row, never a replacement: when the
    frozen models were re-fitted after the 2026-10-01 bug fixes, September was scored
    again under the new model_id beside the pre-manifest rows. The model is part of the
    key because the minutes set logs two entries at one minute."""
    new = new.sort_values(["t", "minute", "model"]).reset_index(drop=True)
    if existing is None or existing.empty:
        return new
    mid = existing.model_id if "model_id" in existing else pd.Series([PRE_MANIFEST] * len(existing))
    key = set(zip(existing.t, existing.minute, existing.model, mid))
    return new[[(t, m, n, i) not in key for t, m, n, i in zip(new.t, new.minute, new.model, new.model_id)]].reset_index(drop=True)


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

def start_t(eset: EntrySet, train_end: str) -> int:
    """Open time of the first window the set may log: the month after the training cutoff,
    or the set's forward_start if that is later."""
    first = (pd.Period(train_end, freq="M") + 1).to_timestamp().date()
    if eset.forward_start:
        first = max(first, dt.date.fromisoformat(eset.forward_start))
    return int(pd.Timestamp(first).timestamp())


def score_set(eset: EntrySet, models: dict, manifest: dict, s: Series, start_t: int, frames: dict | None = None) -> pd.DataFrame:
    """One row per entry per window opening at or after start_t. frames shares the datasets between sets."""
    frames = {} if frames is None else frames
    rows = []
    for k in eset.minutes():
        if k not in frames:
            frames[k] = entry_frame(s, k, cache=False)
        D = frames[k]
        D = D[D.t >= start_t]
        if D.empty:
            continue
        for m, name, cols in eset.entries:
            if m != k:
                continue
            prob = models[eset.mkey(m, name)].predict_proba(D[cols])[:, 1].astype(float)
            rows.append(pd.DataFrame({"t": D.t.values, "time_utc": pd.to_datetime(D.t, unit="s").dt.strftime("%Y-%m-%d %H:%M"),
                                      "minute": k, "model": name, "trained_through": manifest["train_end"], "model_id": manifest["model_id"],
                                      "prob_up": prob.round(4), "outcome_up": D.y.values}))
    return pd.concat(rows) if rows else pd.DataFrame(columns=DATA_COLS)


def _accuracy(L: pd.DataFrame) -> float:
    return float(((L.prob_up > 0.5) == (L.outcome_up == 1)).mean())


def summarise(eset: EntrySet, log: pd.DataFrame) -> None:
    if eset.legacy:
        for k in eset.minutes():
            L = log[log.minute == k]
            if len(L):
                print(f"  minute {k}: {len(L)} windows, {L.time_utc.min()} to {L.time_utc.max()}, accuracy {_accuracy(L)*100:.2f}%")
        return
    for k in eset.minutes():
        parts = []
        for m, name, _ in eset.entries:
            L = log[(log.minute == k) & (log.model == name)] if m == k else log.iloc[0:0]
            if len(L):
                parts.append((name, len(L), _accuracy(L)))
        if len(parts) == 2:
            (a, n, pa), (b, _, pb) = parts
            print(f"  minute {k}: {n} windows, {a} {pa*100:.2f}%, {b} {pb*100:.2f}%, difference {100*(pa-pb):+.2f} points")


def run_set(eset: EntrySet, a, ctx: dict) -> None:
    print(f"[{eset.name}]")
    models, manifest = train_or_load(a.train_start, a.train_end, eset)
    first = (pd.Period(a.train_end, freq="M") + 1).to_timestamp().date()
    last = dt.date.fromisoformat(a.through) if a.through else dt.datetime.utcnow().date() - dt.timedelta(days=1)
    start = start_t(eset, a.train_end)
    if pd.Timestamp(start, unit="s").date() > last:
        print(f"  no windows to score yet: the record starts {pd.Timestamp(start, unit='s'):%Y-%m-%d}; models {manifest['model_id']}")
        return
    if (a.train_end, last) not in ctx:
        days = [str(first + dt.timedelta(days=i)) for i in range((last - first).days + 1)]
        ctx[(a.train_end, last)] = (Series(load_days([a.train_end], days)), {})        # cutoff month supplies the history
    s, frames = ctx[(a.train_end, last)]
    new = score_set(eset, models, manifest, s, start, frames)
    added = append_rows(eset.log_path, new)
    log = pd.read_csv(eset.log_path, dtype={"model_id": str})
    print(f"logged {added} new windows; {len(log)} total; models {manifest['model_id']} trained through {manifest['train_end']}")
    summarise(eset, log[log.model_id == manifest["model_id"]])


def main():
    sets = {"main": MAIN, "minutes": MINUTES}
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-start", default="2025-10")
    ap.add_argument("--train-end", default="2026-08")
    ap.add_argument("--through", default=None, help="last day to score, YYYY-MM-DD (default: yesterday UTC)")
    ap.add_argument("--set", default="all", choices=["all", *sets], help="entry set to run (default: both)")
    ap.add_argument("--verify", action="store_true", help="check the hash chains and exit")
    a = ap.parse_args()
    chosen = list(sets.values()) if a.set == "all" else [sets[a.set]]
    if a.verify:
        ok = True
        for eset in chosen:
            if not eset.log_path.exists():
                print(f"{eset.log_path}: no rows yet")
                continue
            log = read_log(eset.log_path)
            bad = verify_chain(log)
            ok &= bad is None
            print(f"{eset.log_path}: {len(log)} rows, chain {'intact' if bad is None else f'BROKEN at row {bad}'}")
        raise SystemExit(0 if ok else 1)
    ctx: dict = {}
    for eset in chosen:
        run_set(eset, a, ctx)


if __name__ == "__main__":
    main()
