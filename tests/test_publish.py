import pandas as pd

from models.btc_15m.publish import model_doc, prediction_docs, upsert_all


class FakeCollection:
    """Enough of pymongo's Collection to test the write path without a server."""

    def __init__(self):
        self.docs = {}

    def bulk_write(self, ops, ordered=False):
        class R:
            upserted_count = 0
        r = R()
        for op in ops:
            _id = op._filter["_id"]
            if _id not in self.docs:
                self.docs[_id] = dict(op._doc["$setOnInsert"])
                r.upserted_count += 1
            self.docs[_id].update(op._doc["$set"])
        return r

    def replace_one(self, flt, doc, upsert=False):
        self.docs[flt["_id"]] = doc

    def count_documents(self, flt):
        return sum(1 for d in self.docs.values() if all(d.get(k) == v for k, v in flt.items()))


def log(rows):
    return pd.DataFrame(rows, columns=["t", "time_utc", "minute", "model", "trained_through", "prob_up", "outcome_up"])


def test_documents_are_keyed_by_model_window_and_minute():
    L = log([(900, "1970-01-01 00:15", 0, "forest", "2026-08", 0.61, 1), (900, "1970-01-01 00:15", 3, "xgb-all", "2026-08", 0.7, 1)])
    docs = prediction_docs(L)
    assert [d["_id"] for d in docs] == ["btc_15m:900:0", "btc_15m:900:3"]
    assert docs[0]["prob_up"] == 0.61 and docs[0]["outcome_up"] == 1


def test_upsert_is_idempotent_and_never_changes_a_logged_probability():
    preds, models = FakeCollection(), FakeCollection()
    L = log([(900, "x", 0, "forest", "2026-08", 0.61, 1), (1800, "y", 0, "forest", "2026-08", 0.4, 0)])
    c1 = upsert_all(preds, models, prediction_docs(L), model_doc(L, None))
    assert c1 == {"sent": 2, "inserted": 2, "in_db": 2}
    L2 = log([(900, "x", 0, "forest", "2026-08", 0.99, 1), (1800, "y", 0, "forest", "2026-08", 0.4, 0), (2700, "z", 0, "forest", "2026-08", 0.5, 1)])
    c2 = upsert_all(preds, models, prediction_docs(L2), model_doc(L2, None))
    assert c2 == {"sent": 3, "inserted": 1, "in_db": 3}
    assert preds.docs["btc_15m:900:0"]["prob_up"] == 0.61        # the re-sent 0.99 did not overwrite


def test_model_doc_carries_backtest_levels_and_baselines():
    L = log([(900, "x", 0, "forest", "2026-08", 0.6, 1), (900, "x", 3, "xgb-all", "2026-08", 0.7, 1)])
    walk = pd.DataFrame({"minute": [0, 0, 3, 3], "model": ["majority", "forest", "lead-only", "xgb-all"], "accuracy": [0.501, 0.530, 0.663, 0.662]})
    d = model_doc(L, walk)
    assert d["backtest"]["0"] == {"model": "forest", "accuracy": 0.530, "baseline": 0.501, "baseline_name": "majority"}
    assert d["backtest"]["3"]["baseline_name"] == "lead-only" and d["minutes"] == [0, 3]
