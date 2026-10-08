"""The one-bit rule at minute 0 as a fitted estimator, so it can be frozen and loaded like any model.

It lives in its own module and not in log.py because log.py is also run as __main__ (python -m
models.btc_15m.log), and a class defined there would be pickled under the name __main__.
"""
from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin


class PrevWindow(BaseEstimator, ClassifierMixin):
    """The training up-rate after an up window and after a down window.

    The rule evaluate.walk_forward calls "bitrate" on the column prev_up: for each value of the
    single binary column, the share of training windows that closed up."""

    def fit(self, X, y):
        x = np.asarray(X).reshape(len(X), -1)[:, 0]
        y = np.asarray(y)
        self.classes_ = np.array([0, 1])
        self.rates_ = {v: float(y[x == v].mean()) for v in (0, 1)}
        return self

    def predict_proba(self, X):
        x = np.asarray(X).reshape(len(X), -1)[:, 0]
        p = np.where(x == 1, self.rates_[1], self.rates_[0])
        return np.column_stack([1 - p, p])

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] > 0.5).astype(int)
