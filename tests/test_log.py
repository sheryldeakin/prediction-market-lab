import json

import pandas as pd
import pytest

from models.btc_15m import log as L


def rows(ts, minute=0, prob=0.6):
    return pd.DataFrame({"t": ts, "time_utc": "x", "minute": minute, "model": "m", "trained_through": "2026-08",
                         "model_id": "abc", "prob_up": prob, "outcome_up": 1})


def test_merge_returns_only_unlogged_windows_in_time_order():
    old = rows([900, 1800])
    new = rows([2700, 1800], prob=0.9)
    out = L.merge_log(old, new)
    assert list(out.t) == [2700]


def test_merge_keeps_minutes_separate():
    out = L.merge_log(rows([900], minute=0), rows([900], minute=3))
    assert len(out) == 1 and out.minute.item() == 3


def test_merge_with_empty_log():
    assert list(L.merge_log(None, rows([2700, 900])).t) == [900, 2700]


def test_append_never_rewrites_existing_rows(tmp_path):
    p = tmp_path / "log.csv"
    assert L.append_rows(p, rows([900, 1800])) == 2
    first = p.read_bytes()
    assert L.append_rows(p, rows([1800, 2700], prob=0.9)) == 1
    after = p.read_bytes()
    assert after.startswith(first)                         # the earlier bytes are untouched
    log = pd.read_csv(p, dtype={"model_id": str})
    assert list(log.t) == [900, 1800, 2700] and log.loc[log.t == 1800, "prob_up"].item() == 0.6
    assert L.verify_chain(log) is None


def test_tampering_with_one_row_breaks_the_chain(tmp_path):
    """The log was append-only by convention only; the file was rewritten on every run
    (council review, 2026-09-30)."""
    p = tmp_path / "log.csv"
    L.append_rows(p, rows([900, 1800, 2700, 3600]))
    log = pd.read_csv(p, dtype={"model_id": str})
    edited = log.copy(); edited.loc[1, "prob_up"] = 0.4
    assert L.verify_chain(edited) == 1
    dropped = log.drop(index=2).reset_index(drop=True)
    assert L.verify_chain(dropped) == 2
    edited.to_csv(p, index=False)
    with pytest.raises(RuntimeError):
        L.append_rows(p, rows([4500]))


def test_a_log_from_before_the_chain_is_chained_in_place(tmp_path):
    p = tmp_path / "log.csv"
    rows([900, 1800]).drop(columns="model_id").to_csv(p, index=False)
    L.append_rows(p, rows([2700]))
    log = pd.read_csv(p, dtype={"model_id": str})
    assert list(log.model_id) == [L.PRE_MANIFEST, L.PRE_MANIFEST, "abc"]
    assert L.verify_chain(log) is None


def test_saved_models_are_reused_only_when_the_manifest_matches(tmp_path, monkeypatch):
    """Reuse was keyed only on the training end month (council review, 2026-09-30)."""
    monkeypatch.setattr(L, "MODELS", tmp_path)
    for k in L.LOCKED:
        (tmp_path / f"k{k}.joblib").write_bytes(b"")
    (tmp_path / "manifest.json").write_text(json.dumps(L.spec("2025-10", "2026-08")))
    loaded = []
    monkeypatch.setattr(L.joblib, "load", lambda path: loaded.append(path) or "model")
    L.train_or_load("2025-10", "2026-08")
    assert len(loaded) == len(L.LOCKED)

    class Retrained(Exception):
        pass

    def no_training(a, b):
        raise Retrained((a, b))

    monkeypatch.setattr(L, "load", no_training)
    with pytest.raises(Retrained):                          # a different end month must retrain
        L.train_or_load("2025-10", "2026-09")
    stale = L.spec("2025-10", "2026-08"); stale["feature_version"] = -1
    (tmp_path / "manifest.json").write_text(json.dumps(stale))
    with pytest.raises(Retrained):                          # so must a different feature version
        L.train_or_load("2025-10", "2026-08")


def test_a_new_model_id_scores_an_already_logged_window_as_a_new_row():
    """September was scored by the pre-fix models; the re-fitted models score it again
    beside those rows rather than over them (decided 2026-10-01)."""
    old = rows([900, 1800]); old["model_id"] = L.PRE_MANIFEST
    new = rows([900, 1800, 2700], prob=0.55); new["model_id"] = "refit1"
    out = L.merge_log(old, new)
    assert len(out) == 3 and (out.model_id == "refit1").all()
    assert L.merge_log(pd.concat([old, out]), new).empty              # and only once per model_id


def test_unattended_runner_refuses_to_retrain(tmp_path, monkeypatch):
    """With LAB_FORWARD_NO_TRAIN set, a spec mismatch raises instead of fitting a new model version."""
    import models.btc_15m.log as L
    monkeypatch.setattr(L, "MODELS", tmp_path)                 # no saved models here, so the spec cannot match
    monkeypatch.setenv("LAB_FORWARD_NO_TRAIN", "1")
    with pytest.raises(RuntimeError, match="refusing to retrain"):
        L.train_or_load("2025-10", "2026-08")
