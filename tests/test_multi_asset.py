import numpy as np
import pandas as pd

from models.btc_15m.multi_asset import CROSS_COLS, cross_features, walk_forward_pooled


def frame(ts, seed, y=None):
    rng = np.random.default_rng(seed)
    d = pd.DataFrame({"t": ts, "lead": rng.normal(size=len(ts)), "ret5": rng.normal(size=len(ts)), "ret15": rng.normal(size=len(ts)),
                      "ret60": rng.normal(size=len(ts)), "flow5": rng.uniform(-1, 1, len(ts)), "flow15": rng.uniform(-1, 1, len(ts)),
                      "vol60": rng.gamma(2, 1, len(ts))})
    d["y"] = rng.integers(0, 2, len(ts)) if y is None else y
    return d


def test_cross_features_align_on_open_time():
    ts = np.arange(0, 900 * 10, 900)
    btc = frame(ts, 0)
    eth = frame(ts[::2], 1)            # eth missing every other window
    out = cross_features(btc, {"eth": eth})
    assert len(out) == len(eth)
    for c in CROSS_COLS:
        merged = out.set_index("t")[f"eth_{c}"]
        assert np.allclose(merged.values, eth.set_index("t").loc[merged.index, c].values)
    assert set(out.t) == set(eth.t)


def test_cross_features_do_not_touch_target_columns():
    ts = np.arange(0, 900 * 10, 900)
    btc = frame(ts, 0)
    out = cross_features(btc, {"eth": frame(ts, 1)})
    assert np.allclose(out.lead.values, btc.lead.values)


def test_pooled_walk_forward_never_trains_on_test_month_or_later():
    """Plant a label that is only learnable in months >= the test month; the pooled model
    must not benefit, because it may only train on earlier months of any coin."""
    months = pd.period_range("2026-01", "2026-06", freq="M")
    ts = np.concatenate([np.arange(int(m.to_timestamp().timestamp()), int((m + 1).to_timestamp().timestamp()), 900 * 8) for m in months])
    rng = np.random.default_rng(0)
    frames = {}
    for i, sym in enumerate(("a", "b")):
        d = frame(ts, i)
        month = pd.to_datetime(d.t, unit="s").dt.to_period("M")
        # label = sign(lead) only from May on; pure noise before
        d["y"] = np.where(month >= pd.Period("2026-05", "M"), (d.lead > 0).astype(int), rng.integers(0, 2, len(d)))
        frames[sym] = d
    pred, y, t = walk_forward_pooled(frames, ["lead", "ret5"], "logistic", "a")
    may = pd.to_datetime(t, unit="s").to_period("M") == pd.Period("2026-05", "M")
    acc_may = ((pred[may] > 0.5) == y[may]).mean()
    assert acc_may < 0.62          # a model that had seen May-or-later rows would score near 100%
