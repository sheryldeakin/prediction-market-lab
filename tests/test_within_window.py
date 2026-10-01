import numpy as np

from models.btc_15m.within_window import implied_move


def test_implied_move_shrinks_as_the_window_runs_out_and_the_lead_grows():
    v = np.array([5.0, 5.0, 5.0])                      # bp per minute
    k = np.array([2, 2, 12])
    lead = np.array([0.0, 40.0, 0.0])
    m = implied_move(lead, v, k, 5.0)
    assert m[0] > 0 and m[1] > 0 and m[2] > 0
    assert m[1] < m[0]                                  # far ahead already: a bounce changes less
    assert m[2] > m[0]                                  # little time left: the same bounce is worth more
    assert np.allclose(implied_move(lead, v, k, 0.0), 0.0)
