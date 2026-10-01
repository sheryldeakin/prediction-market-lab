import numpy as np

from models.btc_15m.delayed_entry import call_return, implied_up


def test_implied_price_is_half_with_no_lead_and_moves_with_it():
    assert np.allclose(implied_up(np.array([0.0]), np.array([5.0]), 5), 0.5)
    up, down = implied_up(np.array([10.0, -10.0]), np.array([5.0, 5.0]), 5)
    assert up > 0.5 > down and np.isclose(up + down, 1.0)
    assert implied_up(np.array([10.0]), np.array([5.0]), 600) > implied_up(np.array([10.0]), np.array([5.0]), 5)   # less time left, surer


def test_call_return_pays_one_minus_price_when_right():
    pred = np.array([0.6, 0.6, 0.4, 0.4])
    y = np.array([1, 0, 0, 1])
    q = np.full(4, 0.7)                       # up costs 0.70, down costs 0.30
    assert np.allclose(call_return(pred, y, q), [0.3, -0.7, 0.7, -0.3])


def test_a_call_that_only_copies_the_lead_earns_nothing_on_average():
    rng = np.random.default_rng(0)
    n = 200_000
    lead = rng.normal(0, 5, n)
    q = implied_up(lead, np.full(n, 5.0), 30)
    y = (rng.random(n) < q).astype(int)       # outcomes drawn at the implied probability
    r = call_return(np.where(lead > 0, 0.6, 0.4), y, q)
    assert abs(r.mean()) < 0.005
