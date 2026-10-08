import numpy as np
import pandas as pd
import pytest

from models.btc_15m import walk_forward_by_minute as W


def rows():
    out = []
    for k in (0, 1, 2, 3):
        for m, acc in (("majority", 0.5014), ("logistic-all", 0.52 + 0.01 * k)):
            out.append({"minute": k, "model": m, "n_test": 23328, "accuracy": acc, "auc": 0.55, "log_loss": 0.69})
    return pd.DataFrame(out)


def test_the_published_table_keeps_only_the_published_minutes_and_the_full_table_has_all():
    pub, full = W.render_walk_forward(rows(), "2025-10", "2026-08", W.PUBLISHED_MINUTES), W.render_walk_forward(rows(), "2025-10", "2026-08")
    minutes_in = lambda text: sorted({int(l.split("|")[1]) for l in text.splitlines() if l.startswith("| ") and l.split("|")[1].strip().isdigit()})
    assert minutes_in(pub) == [0, 1, 3] and minutes_in(full) == [0, 1, 2, 3]
    assert set(pub.splitlines()[4:]) <= set(full.splitlines())          # every published row is a row of the full table, unchanged
    assert "| 1 | logistic-all | 23,328 | 53.00% | 0.550 | 0.6900 |" in pub


def frames(n_days=40, seed=0):
    rng = np.random.default_rng(seed)
    n = n_days * 96
    t = np.repeat(np.arange(n_days) * 86400, 96) + np.tile(np.arange(96) * 900, n_days)
    y = rng.integers(0, 2, n)
    out = {}
    for k in (0, 1, 2):
        f = pd.DataFrame({"t": t, "y": y})
        f[W.rule_name(k)] = np.where(y == 1, 0.6, 0.4)                       # the rule is right on every window ...
        flip = rng.random(n) < 0.1
        for m in W.FITTED:
            f[m] = np.where(flip ^ (y == 1), 0.6, 0.4)                       # ... and each family is wrong on the same tenth of the windows
        f["xgb-all"] = f[W.rule_name(k)]                                      # except xgb-all, which equals the rule
        out[k] = f
    return out


def test_best_fitted_minus_rule_picks_the_best_family_and_pairs_with_the_rule():
    T = W.by_minute_table(frames(), n_boot=100)
    assert T.minute.tolist() == [0, 1, 2] and (T.rule == ["prev-window", "lead-z", "lead-z"]).all()
    assert (T.rule_accuracy == 1.0).all()
    assert (T.best == "xgb-all").all() and (T.best_minus_rule == 0).all()    # the family equal to the rule is the best, at zero
    f = frames()
    f[1]["forest"] = np.where(f[1].y == 1, 0.9, 0.1)                           # make one family perfect where the rule is perfect: still zero
    f[1][W.rule_name(1)] = np.where(f[1].y == 1, 0.4, 0.6)                     # now the rule is wrong everywhere and the forest is right everywhere
    T = W.by_minute_table(f, n_boot=100)
    r = T[T.minute == 1].iloc[0]
    assert r.best == "forest" and r.rule_accuracy == 0.0 and r.best_minus_rule == pytest.approx(1.0) and r.low <= 1.0 <= r.high


def test_the_rendered_sentences_name_the_largest_and_smallest_minute_after_the_open_and_the_open_itself():
    T = pd.DataFrame({"minute": [0, 1, 2, 3], "rule": ["prev-window", "lead-z", "lead-z", "lead-z"], "rule_accuracy": [0.52, 0.59, 0.63, 0.66],
                      **{m: [0.53, 0.60, 0.63, 0.66] for m in W.FITTED}, "best": ["forest"] * 4,
                      "best_minus_rule": [0.0069, 0.0015, -0.0003, 0.0030], "low": [-0.0001, -0.0020, -0.0030, 0.0001], "high": [0.0137, 0.0050, 0.0020, 0.0060], "n": [100] * 4})
    text = W.render_by_minute(T, "2025-10", "2026-08")
    assert "the largest best-fitted-minus-rule difference is +0.30 [+0.01, +0.60] points at minute 3" in text
    assert "the smallest is -0.03 [-0.30, +0.20] points at minute 2" in text
    assert "at minute 0 it is +0.69 [-0.01, +1.37] points" in text
    assert "entirely above zero at 1 of the 4 minutes (minute 3) and entirely below zero at 0 (no minute)" in text
