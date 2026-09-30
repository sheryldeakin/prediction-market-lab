import numpy as np
import pandas as pd

import models.btc_15m.event_portfolio as EP


def frame(n=1000, seed=0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({"t": 900 * np.arange(n), "y": rng.integers(0, 2, n), "a": rng.normal(size=n), "b": rng.normal(size=n)})


def test_strongest_event_decides_direction(monkeypatch):
    D = frame()
    fake_events = lambda D, k: {"e_up": D.a.values > 1.0, "e_down": D.a.values > 1.5}     # e_down is a subset of e_up
    monkeypatch.setattr(EP, "events", fake_events)
    act, up = EP.decide(D, 0, {"e_up": +0.03, "e_down": -0.10}, mode="strongest")
    assert act.sum() == (D.a.values > 1.0).sum()
    assert (~up[D.a.values > 1.5]).all()          # where both fire, the stronger (down) wins
    assert up[(D.a.values > 1.0) & (D.a.values <= 1.5)].all()


def test_min_dev_filters_weak_events(monkeypatch):
    D = frame()
    monkeypatch.setattr(EP, "events", lambda D, k: {"weak": D.a.values > 0, "strong": D.b.values > 1.5})
    act, _ = EP.decide(D, 0, {"weak": +0.02, "strong": -0.08}, min_dev=0.05, mode="strongest")
    assert act.sum() == (D.b.values > 1.5).sum()


def test_votes_mode_abstains_on_disagreement(monkeypatch):
    D = frame()
    monkeypatch.setattr(EP, "events", lambda D, k: {"e1": D.a.values > 0, "e2": D.b.values > 0})
    act, up = EP.decide(D, 0, {"e1": +0.05, "e2": -0.05}, mode="votes")
    both = (D.a.values > 0) & (D.b.values > 0)
    assert not act[both].any()
    only1 = (D.a.values > 0) & ~(D.b.values > 0)
    assert act[only1].all() and up[only1].all()


def test_score_returns_blank_when_too_few():
    y = np.zeros(50, int); t = 900 * np.arange(50)
    act = np.zeros(50, bool); act[:10] = True
    assert EP.score(act, np.ones(50, bool), y, t)[2] == ""
