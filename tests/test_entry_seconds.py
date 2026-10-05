from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from models.btc_15m import entry_seconds as es
from models.btc_15m.evaluate import add_baseline_columns, walk_forward


def seconds(prices: dict, qty=2.0, signed=0.0, big=()):
    """A per-second table with a trade only at the seconds in `prices`."""
    s = sorted(prices)
    return pd.DataFrame({"sec": s, "vol": [prices[x] * qty for x in s], "qty": qty, "svol": [prices[x] * qty * signed for x in s],
                         "n": 3.0, "big_n": [1.0 if x in big else 0.0 for x in s]})


def test_lead_is_the_second_before_the_entry_against_the_first_traded_second():
    prices = {x: 100.0 for x in range(0, 30)}
    prices[9] = 101.0                                     # the second [t+9, t+10)
    f = es.tick_entry_features(seconds(prices), np.array([0]), 10)
    assert np.isclose(f.lead[0], 100.0)                   # 1% = 100 bp
    assert not f.fallback[0] and not f.nodata[0]
    assert np.isclose(f.open_px[0], 100.0) and np.isclose(f.px[0], 101.0)
    # a later second changes nothing
    prices[10] = 150.0
    assert np.isclose(es.tick_entry_features(seconds(prices), np.array([0]), 10).lead[0], 100.0)


def test_a_second_with_no_trades_falls_back_to_the_last_vwap_before_it_and_is_counted():
    prices = {x: 100.0 for x in range(0, 30)}
    prices[7] = 100.5
    del prices[8], prices[9]                              # nothing traded at seconds 8 and 9
    f = es.tick_entry_features(seconds(prices), np.array([0]), 10)
    assert f.fallback[0] and np.isclose(f.lead[0], 50.0)  # last VWAP before the second, second 7
    # the fallback never reaches back before the window opens
    r = seconds({5: 100.0, 40: 100.0})
    g = es.tick_entry_features(r, np.array([20]), 10)     # window [20, 30) has no trade at all
    assert g.nodata[0] and g.lead[0] == 0.0 and not g.fallback[0]


def test_open_reference_is_the_first_traded_second_not_the_boundary_second():
    prices = {x: 100.0 for x in range(3, 30)}
    prices[3] = 99.0                                      # first trades arrive at second 3
    prices[9] = 100.0
    f = es.tick_entry_features(seconds(prices), np.array([0]), 10)
    assert np.isclose(f.open_px[0], 99.0)
    assert np.isclose(f.lead[0], (100.0 / 99.0 - 1) * 1e4)


def test_sums_cover_exactly_the_first_n_seconds():
    prices = {x: 100.0 for x in range(0, 40)}
    r = seconds(prices, qty=1.0, signed=0.5, big={2, 12})
    f = es.tick_entry_features(r, np.array([0, 10]), 10)
    assert f.n.tolist() == [30.0, 30.0] and f.big.tolist() == [1.0, 1.0]   # seconds 0-9 hold second 2; seconds 10-19 hold second 12
    assert np.allclose(f.flow, 0.5)
    none = es.tick_entry_features(seconds({x: 100.0 for x in (5,)}), np.array([0]), 10)
    assert none.n[0] == 3.0 and none.flow[0] == 0.0       # no signed volume -> 0, not a division error


def test_lead_sign_call_uses_the_previous_window_rule_only_on_an_exact_zero():
    lead = np.array([3.0, -3.0, 0.0, 0.0, 1e-9])
    prev_up = np.array([1, 0, 1, 0, 1])
    assert es.lead_sign_call(lead, prev_up).tolist() == [1, 0, 0, 1, 1]       # zero: opposite of the previous window


def test_lead_z_matches_the_main_tables_scaling_and_shrinks_with_volatility():
    D = pd.DataFrame({"lead": [4.0, -2.0], "win1": [1.0, -1.0], "vol60": [2.0, 4.0]})
    k = 1
    ref = add_baseline_columns(D, k).lead_z.values        # N = 60 s is minute 1
    assert np.allclose(es.lead_z(D.lead.values, D.vol60.values, 60), ref)
    assert np.isclose(es.lead_z(np.array([4.0]), np.array([4.0]), 10)[0] * 2, es.lead_z(np.array([4.0]), np.array([2.0]), 10)[0])
    assert es.lead_z(np.array([4.0]), np.array([2.0]), 60)[0] > es.lead_z(np.array([4.0]), np.array([2.0]), 10)[0]   # less time left, surer


def test_each_ablation_variant_has_exactly_its_intended_columns():
    from models.btc_15m.evaluate import ALL
    lead = es.variant_columns("+lead")
    assert lead == ALL + ["tk_lead", "tk_leadz"]
    assert not {"tk_flow", "tk_n", "tk_big"} & set(lead)                        # no flow, trade count or large-trade features
    assert es.variant_columns("+ticks") == ALL + es.TICK_COLS                    # the main table's models
    only = es.variant_columns("ticks-only")
    assert set(only) == {"tk_lead", "tk_leadz", "tk_flow", "tk_n", "tk_big"} and len(only) == 5
    assert not set(only) & set(ALL)                                              # no minute-0 feature
    assert set(es.variant_columns("+lead")) < set(es.variant_columns("+ticks"))  # +lead is nested in +ticks
    for v in es.VARIANTS:
        assert len(es.variant_columns(v)) == len(set(es.variant_columns(v)))     # no column twice
    with pytest.raises(ValueError):
        es.variant_columns("everything")


def test_paired_row_gives_both_intervals_and_the_month_interval_is_the_wider_one_on_month_level_differences():
    rng = np.random.default_rng(1)
    t = np.arange(0, 6 * 30 * 86400, 900)
    month = pd.to_datetime(t, unit="s").to_period("M").astype(str)
    shift = pd.Series(month).map({m: s for m, s in zip(sorted(set(month)), [-0.2, 0.3, -0.1, 0.25, -0.3, 0.1])}).values   # each month has its own gap
    a = (rng.random(len(t)) < 0.5 + shift * 0.1).astype(float)
    b = (rng.random(len(t)) < 0.5).astype(float)
    r = es.paired_row(a, b, t, n_draws=200)
    assert r["diff_low"] <= r["diff"] <= r["diff_high"] and r["diff_month_low"] <= r["diff"] <= r["diff_month_high"]
    assert r["diff_month_high"] - r["diff_month_low"] > r["diff_high"] - r["diff_low"]
    same = es.paired_row(a, a, t, n_draws=200)
    assert same["diff"] == 0 and same["diff_low"] == 0 == same["diff_month_high"]    # a model against itself


def test_excludes_zero_keeps_only_intervals_that_do_not_contain_it():
    rows = [{"lo": 0.1, "hi": 0.3}, {"lo": -0.1, "hi": 0.3}, {"lo": -0.3, "hi": -0.1}, {"lo": 0.0, "hi": 0.2}]
    assert es.excludes_zero(rows, "lo", "hi") == [rows[0], rows[2]]               # touching zero counts as containing it


def test_write_ablation_names_the_comparisons_it_counts(tmp_path):
    def row(entry, model, variant, diff, dlo, dhi, mlo, mhi):
        return {"entry": entry, "entry_seconds": 10, "n": 100, "model": model, "variant": variant, "accuracy": 0.55, "ci_low": 0.5, "ci_high": 0.6, "auc": 0.55,
                "log_loss": 0.69, "diff": diff, "diff_low": dlo, "diff_high": dhi, "diff_month_low": mlo, "diff_month_high": mhi, "days_better": 0.55, "sign_p": 0.01}
    rows = [{**row("10 s", "lead-sign", "rule", 0, 0, 0, 0, 0)},
            row("10 s", "forest", "+lead", 0.01, 0.002, 0.02, -0.01, 0.03),
            row("10 s", "forest", "+ticks", 0.02, 0.005, 0.03, 0.001, 0.04)]
    incs = [{k: v for k, v in row("10 s", "forest", "x", 0.01, -0.005, 0.02, -0.01, 0.03).items() if k != "variant"}]
    es.write_ablation(rows, incs, {"plus_ticks_rows_reproduce_main_table": True}, tmp_path, "2025-10", "2026-08")
    md = (tmp_path / "entry_seconds_ablation.md").read_text()
    assert "outside the day-block interval for 2 of the 2 comparisons with the lead-sign rule (forest +lead at 10 s (+1.00); forest +ticks at 10 s (+2.00))" in md
    assert "outside the month-block interval for 1 (forest +ticks at 10 s (+2.00))" in md
    assert "outside the day-block interval for 0 of the 1 comparisons of +ticks with +lead (none)" in md and "reproduce" in md
    assert len(pd.read_csv(tmp_path / "entry_seconds_ablation.csv")) == 4


def test_join_returns_the_stored_predictions_on_the_walk_forward_windows_in_order():
    rng = np.random.default_rng(0)
    t = np.arange(0, 7 * 30 * 86400, 900)                                    # about seven months of quarter hours
    D = pd.DataFrame({"t": t, "y": rng.integers(0, 2, len(t)), "prev_up": rng.integers(0, 2, len(t))})
    pred, y, _, tw = walk_forward(D, ["prev_up"], "bitrate")
    oof = pd.DataFrame({"t": tw[::-1], "y": y[::-1], "prev-window": pred[::-1]})  # stored in a different order
    j = es.join_existing(oof, tw)
    assert (j.t.values == tw).all() and np.allclose(j["prev-window"].values, pred) and (j.y.values == y).all()
    with pytest.raises(ValueError):
        es.join_existing(oof.iloc[1:], tw)                                    # a missing window is an error, not a silent drop


def test_stored_windows_are_all_covered_by_the_tick_months():
    p = Path("results/btc_15m/oof_k0.parquet")
    if not p.exists():
        pytest.skip("out-of-fold predictions not generated here")
    t = pd.read_parquet(p).t.values
    assert (t % 900 == 0).all()
    months = pd.to_datetime(t, unit="s").to_period("M").unique()
    for m in months:
        s = es.month_starts(str(m))
        assert np.isin(t[pd.to_datetime(t, unit="s").to_period("M") == m], s).all()


def test_month_starts_are_the_quarter_hours_of_the_month():
    s = es.month_starts("2026-02")
    assert len(s) == 28 * 96 and (s % 900 == 0).all() and s[1] - s[0] == 900


def test_the_month_cache_is_written_once_and_a_rerun_is_identical(tmp_path, monkeypatch):
    tick = tmp_path / "ticks.parquet"
    tick.write_bytes(b"x")
    month = "2026-02"
    t0 = int(es.month_starts(month)[0])
    r = seconds({x: 100.0 + (x - t0) * 0.001 for x in range(t0, t0 + 3600)})
    calls = []
    monkeypatch.setattr(es, "tick_path", lambda m: tick)
    monkeypatch.setattr(es, "load_seconds", lambda a, b: calls.append(1) or r)
    monkeypatch.setattr(es, "CACHE_DIR", tmp_path / "cache")
    first = es.month_table(month)
    second = es.month_table(month)
    assert len(calls) == 1                                                    # the second call read the cache
    pd.testing.assert_frame_equal(first, second)
    assert {"lead_10", "lead_30", "lead_60", "fallback_10", "nodata_60"} <= set(first.columns)
    assert first.lead_10.iloc[0] > 0                                          # rising prices inside the first window
    assert first.nodata_10.iloc[-1]                                           # no trades in the last window
    monkeypatch.setattr(es, "tick_path", lambda m: tmp_path / "missing.parquet")
    with pytest.raises(FileNotFoundError):
        es.month_table("2026-03")                                             # never downloads
