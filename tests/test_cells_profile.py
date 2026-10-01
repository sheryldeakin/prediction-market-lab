import numpy as np

from models.btc_15m.cells_profile import HMAX, MIN_FIRES, clusters_at, jaccard_matrix, labels_upto, pooled, terciles, year_stats
from models.btc_15m.horizons import HORIZONS, labels
from tests.test_horizons import flat


def test_labels_upto_agrees_with_the_horizon_labels_and_marks_the_end():
    s = flat()
    idx = np.array([300, 310, len(s.c) - 2])
    Y = labels_upto(s, idx)
    assert Y.shape == (3, HMAX) and Y.dtype == np.int8
    L = labels(s, idx)
    for h in HORIZONS:
        for k in range(3):
            if np.isnan(L[h][k]):
                assert Y[k, h - 1] == -1
            else:
                assert Y[k, h - 1] == int(L[h][k])
    assert Y[2, 0] >= 0 and Y[2, 2] == -1                     # the second-to-last minute has a 1- and 2-minute label, not a 3-minute one


def test_terciles_follow_the_cutoffs_and_skip_missing_volatility():
    v = np.array([0.1, 0.5, 0.9, np.nan, 0.3])
    assert terciles(v, (0.3, 0.6)).tolist() == [0, 1, 2, -1, 0]


def test_jaccard_is_overlap_over_union_with_ones_on_the_diagonal():
    co = np.array([[10.0, 5.0, 0.0], [5.0, 10.0, 0.0], [0.0, 0.0, 4.0]])
    J = jaccard_matrix(co)
    assert np.allclose(np.diag(J), 1.0)
    assert np.isclose(J[0, 1], 5 / 15) and J[0, 2] == 0.0


def test_identical_events_cluster_together_and_disjoint_ones_apart():
    co = np.array([[10.0, 10.0, 0.0, 3.0], [10.0, 10.0, 0.0, 3.0], [0.0, 0.0, 8.0, 0.0], [3.0, 3.0, 0.0, 10.0]])
    lab = clusters_at(jaccard_matrix(co), 0.3)
    assert lab[0] == lab[1] and lab[2] not in (lab[0], lab[3])
    assert lab[3] != lab[0]                                   # Jaccard 3/17 is under the cut
    assert clusters_at(np.array([[1.0]]), 0.3).tolist() == [1]


def test_pooled_weights_years_by_firings_and_drops_thin_years():
    dev, se, held, years = pooled([(1000, 0.04, 0.01), (3000, 0.02, 0.01), (100, -0.5, 0.01)])
    assert np.isclose(dev, (1000 * 0.04 + 3000 * 0.02) / 4000)
    assert np.isclose(se, np.sqrt((0.25 * 0.01) ** 2 + (0.75 * 0.01) ** 2))
    assert (held, years) == (2, 2)
    dev, se, held, years = pooled([(MIN_FIRES, 0.03, 0.01), (MIN_FIRES, -0.01, 0.01)])
    assert held == 1 and years == 2
    assert np.isnan(pooled([(10, 0.1, 0.01)])[0])


def test_year_stats_is_the_up_rate_difference_within_the_selection():
    rng = np.random.default_rng(1)
    n = 4000
    Y = np.full((n, HMAX), -1, np.int8)
    mask = rng.random(n) < 0.3
    sel = np.arange(n) < 2000
    y = np.where(mask, rng.random(n) < 0.7, rng.random(n) < 0.5).astype(np.int8)
    Y[:, 4] = y
    Y[-5:, 4] = -1
    t = 1_700_000_000 + 60 * np.arange(n)
    fires, dev, se = year_stats(mask, Y, t, 5)
    ok = Y[:, 4] >= 0
    assert fires == int((mask & ok).sum())
    assert np.isclose(dev, y[mask & ok].mean() - y[~mask & ok].mean()) and se > 0
    fires_s, dev_s, _ = year_stats(mask, Y, t, 5, sel)
    assert fires_s == int((mask & sel).sum())
    assert np.isclose(dev_s, y[mask & sel].mean() - y[~mask & sel].mean())
    assert year_stats(np.zeros(n, bool), Y, t, 5)[2] == float("inf")
