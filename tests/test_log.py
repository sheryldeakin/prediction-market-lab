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


# ---------------- entry sets ----------------

import hashlib
from pathlib import Path

import numpy as np

from models.btc_15m.evaluate import ALL, add_baseline_columns, make_model, walk_forward
from models.btc_15m.features import HISTORY, WINDOW, Series, dataset

ROOT = Path(__file__).resolve().parent.parent


def test_the_committed_manifest_still_hashes_to_its_model_id():
    """The two entries frozen on 2026-10-01 are version dbba22d74696. Parameterising the entry
    set must not change a byte of the spec, or that version could no longer be recognised."""
    manifest = json.loads((ROOT / "results/btc_15m/models/manifest.json").read_text())
    assert L.model_id(manifest) == manifest["model_id"] == "dbba22d74696"
    spec = L.MAIN.spec(manifest["train_start"], manifest["train_end"])
    assert {k: manifest[k] for k in spec} == spec
    assert json.dumps(spec, sort_keys=True) == json.dumps({k: manifest[k] for k in spec}, sort_keys=True)
    assert L.spec(manifest["train_start"], manifest["train_end"]) == spec


def test_main_is_the_existing_entry_set_unchanged():
    assert L.MAIN.entries == [(0, "forest", ALL), (3, "xgb-all", ALL)]
    assert L.MAIN.models_dir == Path("results/btc_15m/models") and L.MAIN.log_path == Path("results/btc_15m/predictions.csv")
    assert L.LOCKED == {0: ("forest", ALL), 3: ("xgb-all", ALL)}
    assert L.MAIN.forward_start is None


def test_minutes_lists_thirty_entries_in_minute_order():
    E = L.MINUTES.entries
    assert len(E) == 30
    assert [e[0] for e in E] == [k for k in range(15) for _ in (0, 1)]
    assert [e[1] for e in E[:2]] == ["xgb-all", "prev-window"]
    assert all(E[2 * k][1] == "xgb-all" and E[2 * k][2] == ALL for k in range(15))
    assert all(E[2 * k + 1][1] == "lead-z" and E[2 * k + 1][2] == ["lead_z"] for k in range(1, 15))
    assert E[1][2] == ["prev_up"]
    assert L.MINUTES.models_dir == Path("results/btc_15m/models_minutes")
    assert L.MINUTES.log_path == Path("results/btc_15m/predictions_minutes.csv")
    assert L.MINUTES.forward_start == "2026-10-09"
    assert "xgb-all" in L.MINUTES.primary_comparison and "day-clustered" in L.MINUTES.primary_comparison
    spec = L.MINUTES.spec("2025-10", "2026-08")
    assert spec["forward_start"] == "2026-10-09" and spec["primary_comparison"] == L.MINUTES.primary_comparison
    assert len(spec["entries"]) == 30


def synthetic_series(n_windows=96, seed=0):
    from tests.test_features import synthetic
    return Series(synthetic(HISTORY + (n_windows + 2) * WINDOW - 1, seed))   # the grid starts one window in


def test_rule_estimators_reproduce_the_baseline_probabilities():
    """prev-window and lead-z are fitted as entries exactly as the walk-forward fits them."""
    rng = np.random.default_rng(1)
    n = 4000
    t0 = int(pd.Timestamp("2025-10-01").timestamp())
    D = pd.DataFrame({"t": t0 + 900 * np.arange(n) * 3, "win1": rng.normal(0, 5, n), "lead": rng.normal(0, 5, n),
                      "vol60": rng.uniform(1, 3, n)})
    D["y"] = ((D.win1 > 0) ^ (rng.random(n) < 0.4)).astype(int)
    month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
    first_test = sorted(month.unique())[3]
    tr, te = (month < first_test).values, (month == first_test).values
    assert tr.sum() > 200 and te.sum() > 100
    for k, name, kind in [(0, "prev-window", "bitrate"), (5, "lead-z", "logistic")]:
        E = add_baseline_columns(D, k)
        cols = ["prev_up"] if name == "prev-window" else ["lead_z"]
        pred, _, _, _ = walk_forward(E, cols, kind)
        expected = pred[(month[month >= first_test] == first_test).values]
        model = L.new_model(name).fit(E.loc[tr, cols], E.y.values[tr])
        got = model.predict_proba(E.loc[te, cols])[:, 1]
        assert len(got) == len(expected) and np.allclose(got, expected)
        assert len(np.unique(got)) >= 2                       # the estimator engaged, not a constant


class Const:
    def __init__(self, p):
        self.p = p

    def predict_proba(self, X):
        return np.column_stack([1 - self.p * np.ones(len(X)), self.p * np.ones(len(X))])


def stub_models(eset):
    return {(m, name): Const(0.6) for m, name, _ in eset.entries}


MANIFEST = {"model_id": "m1", "train_end": "2026-08"}


def test_a_one_day_batch_writes_ninety_six_windows_for_thirty_entries_and_verifies(tmp_path):
    s = synthetic_series(96)
    rows = L.score_set(L.MINUTES, stub_models(L.MINUTES), MANIFEST, s, start_t=0)
    assert len(rows) == 96 * 30
    assert set(rows.groupby(["minute", "model"]).size()) == {96}
    p = tmp_path / "predictions_minutes.csv"
    assert L.append_rows(p, rows) == 96 * 30
    log = pd.read_csv(p, dtype={"model_id": str})
    assert log.prev_hash.iloc[0] == L.GENESIS and L.verify_chain(log) is None
    assert L.append_rows(p, rows) == 0                                  # a rerun adds nothing
    assert list(log.columns) == L.DATA_COLS + ["prev_hash", "row_hash"]


def test_two_entries_at_one_minute_are_both_logged():
    a = rows([900], minute=3); b = rows([900], minute=3); b["model"] = "lead-z"
    assert len(L.merge_log(a, b)) == 1 and L.merge_log(a, b).model.item() == "lead-z"
    assert L.merge_log(pd.concat([a, b]), pd.concat([a, b])).empty


def test_windows_before_forward_start_are_never_scored():
    s = synthetic_series(96)
    t = dataset(s, 0, cache=False).t.values
    cut = int(t[40])
    rows_ = L.score_set(L.MINUTES, stub_models(L.MINUTES), MANIFEST, s, start_t=cut)
    assert rows_.t.min() == cut and rows_.t.nunique() == 96 - 40
    assert L.score_set(L.MINUTES, stub_models(L.MINUTES), MANIFEST, s, start_t=int(t[-1]) + 1).empty
    assert L.start_t(L.MINUTES, "2026-08") == int(pd.Timestamp("2026-10-09").timestamp())
    assert L.start_t(L.MAIN, "2026-08") == int(pd.Timestamp("2026-09-01").timestamp())


def test_a_minutes_run_leaves_the_existing_log_untouched(tmp_path, monkeypatch):
    main_log = tmp_path / "predictions.csv"
    L.append_rows(main_log, rows([900, 1800]))
    before = hashlib.sha256(main_log.read_bytes()).hexdigest()
    monkeypatch.setattr(L.MINUTES, "log_path", tmp_path / "predictions_minutes.csv")
    s = synthetic_series(96)
    new = L.score_set(L.MINUTES, stub_models(L.MINUTES), MANIFEST, s, start_t=0)
    L.append_rows(L.MINUTES.log_path, new)
    assert hashlib.sha256(main_log.read_bytes()).hexdigest() == before
    assert L.MINUTES.log_path != L.MAIN.log_path


def test_the_no_train_guard_covers_the_minutes_set(tmp_path, monkeypatch):
    monkeypatch.setattr(L.MINUTES, "models_dir", tmp_path)
    monkeypatch.setenv("LAB_FORWARD_NO_TRAIN", "1")
    with pytest.raises(RuntimeError, match="refusing to retrain"):
        L.train_or_load("2025-10", "2026-08", L.MINUTES)


def test_indicator_source_hash_ignores_line_endings(monkeypatch, tmp_path):
    """A checkout that converts line endings must hash the committed indicators file, or the
    frozen manifest would never match and the unattended runner would refuse to run."""
    import hashlib
    from models.btc_15m import features, indicators
    raw = Path(indicators.__file__).read_bytes()
    lf = raw.replace(b"\r\n", b"\n")
    assert features._INDICATOR_SOURCE == hashlib.sha1(lf).hexdigest()[:12]
