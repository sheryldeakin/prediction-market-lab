import numpy as np

from models.btc_15m.cells_decay_forecast import predict, record, weighted_line


def test_weighted_line_recovers_a_straight_trend():
    years = np.arange(2018, 2027, dtype=float)
    dev = 0.12 - 0.01 * (years - 2018)
    a, b, cov = weighted_line(years, dev, np.full(len(years), 0.005))
    assert np.isclose(a + b * 2018, 0.12) and np.isclose(b, -0.01)
    mean, lo, hi = predict(a, b, cov, 2027, len(years) - 2)
    assert np.isclose(mean, 0.12 - 0.09) and lo < mean < hi


def test_record_compares_the_line_with_the_naive_forecasts():
    years = np.arange(2018, 2027, dtype=float)
    dev = 0.12 - 0.01 * (years - 2018)
    r = record(years, dev, np.full(len(years), 0.005), first_test=2022)
    assert r["tests"] == 5
    assert r["mae_line"] < 1e-9                 # a straight trend is forecast exactly by the line
    assert np.isclose(r["mae_last"], 0.01)      # 'same as last year' is one step behind
    assert r["mae_mean"] > r["mae_last"]        # the mean of earlier years lags further


def test_record_needs_three_training_years():
    years = np.array([2020.0, 2021.0, 2022.0])
    assert record(years, np.array([0.1, 0.1, 0.1]), np.full(3, 0.01), first_test=2021)["tests"] == 0
