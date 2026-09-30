import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from models.btc_15m.patterns import describe_shape, leaf_rules, rule_mask, simplify


def test_leaf_rules_reproduce_the_leaf_membership():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(3000, 3))
    y = ((X[:, 0] > 0.5) & (X[:, 1] < 0)).astype(int)
    cols = ["a", "b", "c"]
    f = RandomForestClassifier(n_estimators=3, max_depth=3, min_samples_leaf=50, random_state=0).fit(X, y)
    rules = leaf_rules(f, cols, X, y, min_support=50, min_lift=0.0)
    assert rules
    D = pd.DataFrame(X, columns=cols)
    for conds, dev, n in rules:
        m = rule_mask(conds, D)
        assert m.sum() == n                              # the conditions select exactly the leaf's training rows
        assert abs((y[m].mean() - y.mean()) - dev) < 1e-9


def test_leaf_rules_respect_support_and_lift():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(2000, 2)); y = rng.integers(0, 2, 2000)
    f = RandomForestClassifier(n_estimators=2, max_depth=3, min_samples_leaf=20, random_state=0).fit(X, y)
    for conds, dev, n in leaf_rules(f, ["a", "b"], X, y, min_support=200, min_lift=0.05):
        assert n >= 200 and abs(dev) >= 0.05


def test_simplify_merges_bounds():
    conds = [("a", ">", 1.0), ("a", ">", 2.0), ("b", "<=", 5.0), ("b", "<=", 3.0), ("c", ">", 0.0), ("c", "<=", 4.0)]
    assert simplify(conds) == "a > 2 and b <= 3 and 0 < c <= 4"


def test_describe_shape_words():
    center = np.concatenate([np.full(15, 0.2), np.zeros(15), np.full(15, -0.2), np.zeros(15)])
    d = describe_shape(center)
    assert d.startswith("net +0.0 sd") and "first quarter up" in d and "third down" in d and "last quarter flat" in d
