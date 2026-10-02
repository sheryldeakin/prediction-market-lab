import numpy as np
import pandas as pd

from models.btc_15m.regimes_era import ERAS, cell_table, minute_states, ratios, vol_group


def test_vol_group_keeps_the_volatility_word_and_merges_the_down_state():
    assert vol_group("low vol, flat") == "low" and vol_group("high vol, down") == "high" and vol_group("") == ""


def test_minute_states_use_the_previous_days_state():
    R = pd.DataFrame({"t": [86400 * 2, 86400 * 3], "hmm": ["low vol, flat", "high vol, flat"]})    # days 1 and 2 (t is the next midnight)
    t = np.array([86400 * 2 + 600, 86400 * 3 + 600, 86400 * 4 + 600])                               # minutes on days 2, 3, 4
    assert minute_states(R, t).tolist() == ["low", "high", ""]


def test_within_era_ratio_removes_an_era_effect_that_the_all_years_ratio_shows():
    rng = np.random.default_rng(0)
    n = 40000
    year = np.where(np.arange(n) < n // 2, 2020, 2025)
    # high-volatility days exist only in 2020; the cell works in 2020 (both states alike) and not in 2025
    state = np.where(year == 2020, np.where(rng.random(n) < 0.5, "high", "low"), "low")
    m = rng.random(n) < 0.3
    size = np.where(year == 2020, 0.2, 0.0)
    y = (rng.random(n) < 0.5 + m * size).astype(float)
    t = 1_600_000_000 + 60 * np.arange(n)
    tab = cell_table(y, m, state, year, t)
    r_all, r_within, used = ratios(tab)
    assert r_all > 1.6                           # low-volatility minutes pool both eras, high-volatility ones only 2020: a false doubling
    assert used == 1
    assert 0.8 < r_within < 1.25                 # inside 2020 both states carry the same effect


def test_cell_table_blank_when_too_few_firings():
    n = 2000
    y = np.ones(n); m = np.zeros(n, bool); m[:10] = True
    tab = cell_table(y, m, np.full(n, "low"), np.full(n, 2020), 1_600_000_000 + 60 * np.arange(n))
    assert np.isnan(tab[("2020-21", "low")][0]) and tab[("2020-21", "low")][3] == 10
    assert set(e for e, _ in tab) == set(ERAS) | {"all"}
