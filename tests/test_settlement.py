import numpy as np
import pandas as pd

from models.btc_15m.settlement import Vwap, previous_label, vwap_labels


def seconds(n=4000, seed=0):
    rng = np.random.default_rng(seed)
    price = 100 + np.cumsum(rng.normal(0, 0.01, n))
    qty = rng.gamma(2, 1, n)
    return pd.DataFrame({"sec": np.arange(n), "vol": price * qty, "qty": qty}), price, qty


def test_vwap_matches_a_direct_weighted_mean_and_skips_empty_seconds():
    r, price, qty = seconds()
    vw = Vwap(r.iloc[::2])                                  # only even seconds traded
    a, b = np.array([100]), np.array([160])
    sel = (np.arange(len(price)) >= 100) & (np.arange(len(price)) < 160) & (np.arange(len(price)) % 2 == 0)
    assert np.isclose(vw(a, b)[0], (price[sel] * qty[sel]).sum() / qty[sel].sum())
    assert np.isnan(Vwap(r[r.sec < 50])(np.array([100]), np.array([160]))[0])     # no trades in range


def test_vwap_labels_ignore_trades_between_their_reference_minutes():
    """Only the reference minutes may decide a VWAP label: [T-60, T) and [T+840, T+900)
    for the boundary version, [T, T+60) and [T+840, T+900) for the inside version."""
    r, price, qty = seconds()
    T = np.array([1200])
    before = vwap_labels(T, Vwap(r))
    r2 = r.copy()
    middle = (r2.sec >= 1260) & (r2.sec < 2040)
    r2.loc[middle, "vol"] *= 3.0
    after = vwap_labels(T, Vwap(r2))
    for k in ("vwap_end", "vwap_in"):
        assert before[k][0] == after[k][0]
    r3 = r.copy()
    r3.loc[(r3.sec >= 2040) & (r3.sec < 2100), "vol"] *= 0.5            # halve the price in the closing minute
    assert vwap_labels(T, Vwap(r3))["vwap_end"][0] == 0.0


def test_previous_label_aligns_by_time_not_by_row():
    t = np.array([900, 1800, 3600])                          # the window at 2700 is missing
    y = np.array([1.0, 0.0, 1.0])
    prev = previous_label(t, y)
    assert np.isnan(prev[0]) and prev[1] == 1.0 and np.isnan(prev[2])
