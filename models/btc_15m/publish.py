"""Publish the forward log to the database the tracking page reads.

Two collections, matching docs/design-brief.md:

  predictions   one document per (model, t, minute): prob_up, outcome_up, trained_through,
                category, time_utc. Upserted by key, so re-running never duplicates and
                never changes a logged row's probability (only outcome fields may be
                filled in later if a window was logged before it settled).
  models        one document per model: name, category, question, backtest reference
                levels per minute, training cutoff, links to the report and the log.

The CSV in the repo stays the audit record; this is the serving copy. After a run the
counts in both are compared and any mismatch is printed.

Config: MONGODB_URI in the environment or a .env file (gitignored); MONGODB_DB defaults
to prediction_market_lab. With --dry-run nothing is written and the documents that
would be sent are counted.

    python -m models.btc_15m.publish [--dry-run]
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

LOG = Path("results/btc_15m/predictions.csv")
WALK = Path("results/btc_15m/walk_forward.csv")
MODEL_ID = "btc_15m"
MODEL_DOC = {
    "_id": MODEL_ID, "name": "BTC 15-minute direction", "category": "crypto",
    "question": "Does Bitcoin close a 15-minute window at or above where it opened?",
    "report": "docs/btc_15m.md", "log": "results/btc_15m/predictions.csv",
}


def load_env():
    p = Path(".env")
    if p.exists():
        for line in p.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def prediction_docs(log: pd.DataFrame) -> list[dict]:
    """One document per row of the forward log, keyed for idempotent upserts."""
    docs = []
    for r in log.itertuples(index=False):
        docs.append({"_id": f"{MODEL_ID}:{int(r.t)}:{int(r.minute)}", "model": MODEL_ID, "category": "crypto",
                     "t": int(r.t), "time_utc": str(r.time_utc), "minute": int(r.minute), "model_name": str(r.model),
                     "prob_up": float(r.prob_up), "outcome_up": int(r.outcome_up), "trained_through": str(r.trained_through)})
    return docs


def model_doc(log: pd.DataFrame, walk: pd.DataFrame | None) -> dict:
    d = dict(MODEL_DOC)
    d["trained_through"] = str(log.trained_through.iloc[0]) if len(log) else None
    d["minutes"] = sorted(int(m) for m in log.minute.unique()) if len(log) else []
    d["backtest"] = {}
    if walk is not None:
        for k, g in log.groupby("minute"):
            name = g.model.iloc[0]
            row = walk[(walk.minute == k) & (walk.model == name)]
            base = walk[(walk.minute == k) & (walk.model == ("majority" if k == 0 else "lead-only"))]
            d["backtest"][str(int(k))] = {"model": name, "accuracy": float(row.accuracy.iloc[0]) if len(row) else None,
                                          "baseline": float(base.accuracy.iloc[0]) if len(base) else None, "baseline_name": "majority" if k == 0 else "lead-only"}
    return d


def upsert_all(predictions, models, pred_docs: list[dict], mdoc: dict) -> dict:
    """Write with duck-typed collections (pymongo or a fake). Returns counts."""
    from pymongo import UpdateOne
    ops = [UpdateOne({"_id": doc["_id"]}, {"$setOnInsert": {k: v for k, v in doc.items() if k not in ("outcome_up",)},
                                            "$set": {"outcome_up": doc["outcome_up"]}}, upsert=True) for doc in pred_docs]
    n_up = 0
    for i in range(0, len(ops), 1000):
        r = predictions.bulk_write(ops[i:i + 1000], ordered=False)
        n_up += r.upserted_count
    models.replace_one({"_id": mdoc["_id"]}, mdoc, upsert=True)
    return {"sent": len(ops), "inserted": n_up, "in_db": predictions.count_documents({"model": MODEL_ID})}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    load_env()
    log = pd.read_csv(LOG)
    walk = pd.read_csv(WALK) if WALK.exists() else None
    docs = prediction_docs(log)
    mdoc = model_doc(log, walk)
    if a.dry_run:
        print(f"dry run: {len(docs)} prediction documents, model document: {mdoc['name']}, backtest {mdoc['backtest']}")
        return
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        raise SystemExit("MONGODB_URI is not set (put it in .env, which is gitignored)")
    from pymongo import MongoClient
    db = MongoClient(uri)[os.environ.get("MONGODB_DB", "prediction_market_lab")]
    db.predictions.create_index([("model", 1), ("t", 1), ("minute", 1)])
    counts = upsert_all(db.predictions, db.models, docs, mdoc)
    print(f"sent {counts['sent']}, inserted {counts['inserted']}, now {counts['in_db']} in the database; {len(log)} in the CSV"
          + ("" if counts["in_db"] == len(log) else "  MISMATCH"))


if __name__ == "__main__":
    main()
