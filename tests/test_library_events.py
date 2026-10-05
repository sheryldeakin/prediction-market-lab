import types

import numpy as np
import pandas as pd
import pytest

from models.btc_15m import library_events as L


def quantities(n, big_n=None, svol=None, big_svol=None):
    n = np.asarray(n, float)
    z = np.zeros(len(n))
    return L.tick_quantities({"n": n, "big_n": z if big_n is None else np.asarray(big_n, float),
                              "svol": z if svol is None else np.asarray(svol, float),
                              "big_svol": z if big_svol is None else np.asarray(big_svol, float)})


def prices(n, seed=0):
    c = 100.0 + np.random.default_rng(seed).normal(0, 0.05, n)         # continuous, so no ties with a rolling extreme
    return c + 0.01, c - 0.01


# ---------------- timing ----------------

def test_an_event_in_minute_j_is_known_at_decision_minute_j_plus_one_only():
    h, l = prices(30)
    n = np.full(30, 10.0)
    n[10] = 500.0
    ev = L.tick_events(quantities(n), {"share": 0.5, "n": 100.0}, h, l)["trade-count climax"]
    assert np.flatnonzero(ev).tolist() == [11]


def test_tick_events_never_read_the_future():
    rng = np.random.default_rng(3)
    N, k = 400, 250
    n = rng.integers(0, 40, N).astype(float)
    big = np.minimum(rng.integers(0, 5, N), n).astype(float)
    sv = rng.normal(0, 1, N)
    bsv = rng.normal(0, 1, N) * (big > 0)
    h, l = prices(N, 1)
    cuts = {"share": 0.1, "n": 30.0}
    full = L.tick_events(quantities(n, big, sv, bsv), cuts, h, l)
    cut = L.tick_events(quantities(n[:k], big[:k], sv[:k], bsv[:k]), cuts, h[:k], l[:k])
    for name in full:
        assert (full[name][:k] == cut[name]).all(), name
    assert sum(int(v.sum()) for v in cut.values()) > 0              # the comparison was not between empty arrays


# ---------------- large-trade burst ----------------

def test_burst_fires_only_above_the_cutoff_and_is_split_by_the_sign_of_large_volume():
    n = np.full(10, 100.0)
    big = np.array([1, 1, 5, 1, 9, 1, 1, 9, 1, 1], float)                 # shares 0.01 ... 0.09
    bsv = np.array([0, 0, 1.0, 0, -1.0, 0, 0, 0.0, 0, 0])
    h, l = prices(10)
    ev = L.tick_events(quantities(n, big, big_svol=bsv), {"share": 0.05, "n": 1e9}, h, l)
    assert np.flatnonzero(ev["large-trade burst"]).tolist() == [5, 8]        # minutes 4 and 7 (9%); minute 2 is 5%, not above 5%
    assert np.flatnonzero(ev["large-trade burst with net large selling"]).tolist() == [5]
    assert np.flatnonzero(ev["large-trade burst with net large buying"]).tolist() == []
    ev2 = L.tick_events(quantities(n, big, big_svol=bsv), {"share": 0.04, "n": 1e9}, h, l)
    assert np.flatnonzero(ev2["large-trade burst with net large buying"]).tolist() == [3]


def test_a_minute_with_no_trades_is_never_a_burst():
    q = quantities([0, 100, 0], [0, 0, 0])
    assert np.isnan(q["share"][0])
    h, l = prices(3)
    ev = L.tick_events(q, {"share": -1.0, "n": 1e9}, h, l)["large-trade burst"]
    assert not ev[1] and ev[2]                                    # minute 0 had no trades; minute 1 passes a cutoff below zero


# ---------------- previous-year cutoffs ----------------

def fake_month(month):
    """100 trades a minute, minute m of the month has m % 50 large ones: the share runs 0 to 0.49."""
    p = pd.Period(month, "M")
    t0 = int(p.start_time.value // 10**9)
    m = np.arange(p.days_in_month * 1440)
    return pd.DataFrame({"sec": t0 + 60 * m, "n": 100.0, "big_n": (m % 50).astype(float), "svol": 1.0, "big_svol": 0.0})


def test_cutoffs_come_from_the_previous_year_and_nothing_later():
    asked = []

    def reader(month):
        asked.append(month)
        assert month.startswith("2018"), f"asked for {month} while cutting for 2019"
        return fake_month(month)

    cuts = L.reference_cutoffs(2019, reader)
    assert asked == [f"2018-{m:02d}" for m in range(1, 13)]
    expected = np.concatenate([(np.arange(pd.Period(m, "M").days_in_month * 1440) % 50) / 100 for m in asked])
    assert cuts["share"] == pytest.approx(np.quantile(expected, 0.99))
    assert cuts["n"] == 100.0


def test_the_first_year_takes_what_the_data_hold_of_the_year_before():
    assert L.reference_months(2018) == ["2017-08", "2017-09", "2017-10", "2017-11", "2017-12"]
    assert L.reference_months(2019)[0] == "2018-01" and len(L.reference_months(2019)) == 12
    assert L.reference_months(2017) == []
    with pytest.raises(ValueError):
        L.reference_cutoffs(2017, fake_month)


def test_a_busier_current_year_does_not_move_the_cutoff():
    prev = quantities(np.arange(1, 1001))
    cuts = L.tick_cutoffs(prev)
    assert cuts["n"] == pytest.approx(np.quantile(np.arange(1, 1001), 0.99))
    now = np.full(50, 5000.0)                                    # every minute far above last year's 99th percentile
    h, l = prices(50)
    ev = L.tick_events(quantities(now), cuts, h, l)["trade-count climax"]
    assert ev[1:].all()                                           # fires on all of them, as the definition says; the cutoff is last year's
    own = L.tick_cutoffs(quantities(now))
    assert own["n"] == 5000.0 and not (now > own["n"]).any()      # a cutoff from this year's own data would never fire


def test_a_missing_tick_file_is_an_error_and_not_a_download(tmp_path, monkeypatch):
    monkeypatch.setattr(L, "tick_path", lambda m: tmp_path / f"{m}.parquet")
    with pytest.raises(FileNotFoundError):
        L.read_month("2020-01")


# ---------------- imbalance persistence ----------------

def test_persistence_needs_the_same_sign_in_every_one_of_the_last_k_minutes():
    sv = np.array([1, 1, 1, -1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1], float)
    n = np.full(len(sv), 10.0)
    h, l = prices(len(sv))
    ev = L.tick_events(quantities(n, svol=sv), {"share": 1.0, "n": 1e9}, h, l)
    buy3 = np.flatnonzero(ev["net taker buying in each of the last 3 minutes"]).tolist()
    assert buy3 == [3, 7, 8, 9, 13, 14, 15]                       # runs of three close at minutes 2, 6, 7, 8, 12, 13, 14; the sell at 3 and the zero at 9 break the runs
    buy5 = np.flatnonzero(ev["net taker buying in each of the last 5 minutes"]).tolist()
    assert buy5 == [9, 15]                                        # a run reaches five at minutes 8 and 14
    sell = np.flatnonzero(ev["net taker selling in each of the last 3 minutes"]).tolist()
    assert sell == []
    assert np.flatnonzero(L.tick_events(quantities(n, svol=-sv), {"share": 1.0, "n": 1e9}, h, l)["net taker selling in each of the last 3 minutes"]).tolist() == buy3


# ---------------- trade-count climax ----------------

def test_climax_is_split_by_whether_the_minute_made_a_new_hourly_extreme():
    N = 300
    h, l = prices(N, 2)
    a = 100
    h[a] = 120.0                                                 # a new high
    hi, lo = L.new_extremes(h, l)
    assert hi[a]
    b = next(j for j in range(150, N) if not hi[j] and not lo[j])
    c = next(j for j in range(b + 1, N) if not hi[j] and not lo[j])
    n = np.full(N, 10.0)
    n[[a, b]] = 500.0
    ev = L.tick_events(quantities(n), {"share": 1.0, "n": 100.0}, h, l)
    assert np.flatnonzero(ev["trade-count climax"]).tolist() == [a + 1, b + 1]
    assert np.flatnonzero(ev["trade-count climax at a new 1h high"]).tolist() == [a + 1]
    assert np.flatnonzero(ev["trade-count climax with no new 1h high or low"]).tolist() == [b + 1]
    assert np.flatnonzero(ev["trade-count climax at a new 1h low"]).tolist() == []
    l2 = l.copy(); l2[c] = 80.0
    n2 = np.full(N, 10.0); n2[c] = 500.0
    ev2 = L.tick_events(quantities(n2), {"share": 1.0, "n": 100.0}, h, l2)
    assert np.flatnonzero(ev2["trade-count climax at a new 1h low"]).tolist() == [c + 1]


def test_new_extreme_compares_with_the_hour_before_and_not_the_minute_itself():
    h = np.full(100, 10.0); l = np.full(100, 9.0)
    h[70] = 11.0
    hi, lo = L.new_extremes(h, l)
    assert hi[70] and not hi[71]                                   # minute 71's high (10) is below the 11 now inside its hour
    assert not hi[:60].any()                                       # no full hour behind yet


# ---------------- derivatives definitions ----------------

def deriv_arrays(n, **kw):
    base = {k: np.full(n, np.nan) for k in ("funding_bp", "doi15", "doi60", "pvol_ratio5", "ret15")}
    for k, v in kw.items():
        base[k] = np.asarray(v, float)
    return base


def test_funding_and_open_interest_use_the_previous_years_deciles():
    prev = deriv_arrays(101, funding_bp=np.linspace(-5, 5, 101), doi15=np.linspace(-2, 2, 101), doi60=np.linspace(-4, 4, 101),
                        pvol_ratio5=np.linspace(0, 10, 101), ret15=np.linspace(-50, 50, 101))
    cuts = L.decile_cuts(prev)
    assert cuts["funding_bp"] == pytest.approx((-4.0, 4.0))
    cur = deriv_arrays(6, funding_bp=[0, 4.5, -4.5, 3.9, -3.9, np.nan], doi15=[0, 0, 0, 1.7, -1.7, 0], doi60=[0, 0, 0, 0, 0, 0])
    ev = L.deriv_events(cur, cuts)
    names = L.DERIV_EVENTS
    assert np.flatnonzero(ev[names[0]]).tolist() == [2]            # funding 4.5 at minute 1, known at decision minute 2
    assert np.flatnonzero(ev[names[1]]).tolist() == [3]
    assert np.flatnonzero(ev[names[2]]).tolist() == [4]            # open interest 1.7 > 1.6
    assert np.flatnonzero(ev[names[3]]).tolist() == [5]
    own = L.decile_cuts({"funding_bp": cur["funding_bp"]})
    assert own["funding_bp"] != cuts["funding_bp"]                # this year's own deciles are not what the events use


def test_funding_at_the_exchange_default_is_not_an_extreme():
    prev = np.concatenate([np.linspace(-2, 0.9, 60), np.full(40, 1.0)])               # 40% of the year at the default
    cuts = L.decile_cuts(deriv_arrays(100, funding_bp=prev, doi15=prev, doi60=prev, pvol_ratio5=prev, ret15=prev))
    assert cuts["funding_bp"][1] == 1.0
    lo = cuts["funding_bp"][0]
    cur = deriv_arrays(7, funding_bp=[1.0, 1.5, 1.0, lo, lo - 1, 0.0, 0.0])
    ev = L.deriv_events(cur, cuts)
    assert np.flatnonzero(ev[L.DERIV_EVENTS[0]]).tolist() == [2]                      # only 1.5, known at decision minute 2
    assert np.flatnonzero(ev[L.DERIV_EVENTS[1]]).tolist() == [5]                      # only below the lower cut, not at it


def test_unknown_values_never_fire():
    cuts = {k: (-1.0, 1.0) for k in ("funding_bp", "doi15", "doi60", "pvol_ratio5", "ret15")}
    ev = L.deriv_events(deriv_arrays(5), cuts)
    assert not any(v.any() for v in ev.values())


def test_liquidation_signature_needs_all_three_conditions():
    cuts = {k: (-1.0, 1.0) for k in ("funding_bp", "doi15", "doi60", "pvol_ratio5", "ret15")}
    long_, short_ = L.DERIV_EVENTS[6], L.DERIV_EVENTS[7]
    # minute 0: all three for longs; 1: open interest not down; 2: price not extreme; 3: volume light; 4 and 5: price up hard
    cur = deriv_arrays(6, doi15=[-2, 0, -2, -2, -2, -2], ret15=[-2, -2, 0, -2, 2, 2], pvol_ratio5=[2, 2, 2, 0, 2, 2], funding_bp=np.zeros(6), doi60=np.zeros(6))
    ev = L.deriv_events(cur, cuts)
    assert np.flatnonzero(ev[long_]).tolist() == [1]
    assert np.flatnonzero(ev[short_]).tolist() == [5]              # minute 5's flag would be known at decision minute 6, outside the array


def test_spot_return15_is_known_at_the_close_of_each_minute():
    c = np.arange(1.0, 41.0)
    r = L.spot_return15(c)
    assert np.isnan(r[:15]).all()
    assert r[20] == pytest.approx((c[20] / c[5] - 1) * 1e4)


# ---------------- pooling and rendering ----------------

def year_rows(year, diff, fires=1000, share=0.1, se=0.01, p_adj=0.01):
    return {"year": year, "horizon": 5, "pattern": "e", "fires": fires, "share": share, "up_rate": 0.55, "base": 0.5, "diff": diff, "se": se, "z": diff / se, "p": 0.0, "p_adj": p_adj}


def vwap_rows(year, dp, dv, fires=1000):
    return {"year": year, "horizon": 5, "pattern": "e", "fires_print": fires, "diff_print": dp, "z_print": 1.0, "fires_vwap": fires, "diff_vwap": dv, "z_vwap": 1.0}


def test_pooling_weights_years_by_firings_and_measures_from_the_unconditional_rate():
    A = pd.DataFrame([year_rows(2020, 0.10, fires=1000, share=0.10), year_rows(2021, 0.02, fires=3000, share=0.30, p_adj=0.2), year_rows(2022, -0.01, fires=1000, share=0.10)])
    V = pd.DataFrame([vwap_rows(2020, 0.10, 0.05), vwap_rows(2021, 0.02, 0.01, fires=3000), vwap_rows(2022, -0.01, 0.0)])
    G = L.pool_cells(A, V).iloc[0]
    w = np.array([1000, 3000, 1000]) / 5000
    dev = (w * np.array([0.9 * 0.10, 0.7 * 0.02, 0.9 * -0.01])).sum()
    assert G.deviation == pytest.approx(dev)
    assert G.se == pytest.approx(np.sqrt(((w * np.array([0.9, 0.7, 0.9]) * 0.01) ** 2).sum()))
    assert (G.years, G.years_held, G.years_adj_05, G.fires) == (3, 2, 2, 5000)
    assert G.retained == pytest.approx((0.05 * 1000 + 0.01 * 3000 + 0.0) / (0.10 * 1000 + 0.02 * 3000 - 0.01 * 1000))
    full = L.pool_cells(A, V)
    assert not L.cleared(full).iloc[0] and not L.held_all(full).iloc[0]
    assert L.cleared(full, 0.5).iloc[0] and L.cleared(full, 0.0).iloc[0]        # 2 of 3 years: not all, at least half, at least one
    none = full.assign(years_adj_05=0)
    assert not L.cleared(none, 0.0).iloc[0]                                    # no year at all is not "at least one"


def test_rendering_twice_gives_the_same_document_and_one_row_per_cell():
    names = [name for _, name in L.TICK_EVENTS]
    rows, vrows = [], []
    for k, name in enumerate(names):
        for h in L.HORIZONS:
            for y in (2020, 2021):
                r = year_rows(y, 0.03 + 0.001 * k)
                r.update({"pattern": name, "horizon": h})
                rows.append(r)
                v = vwap_rows(y, 0.03, 0.02)
                v.update({"pattern": name, "horizon": h})
                vrows.append(v)
    G = L.pool_cells(pd.DataFrame(rows), pd.DataFrame(vrows))
    shares = pd.DataFrame({"year": [2020, 2021] * len(names), "event": np.repeat(names, 2), "share": 0.01, "fires": 5})
    null = np.array([1.0, 2.0, 3.0])
    a = L.render(G, [2020, 2021], "2021-12", 3, null, 9.0, shares)
    assert a == L.render(G, [2020, 2021], "2021-12", 3, null, 9.0, shares)
    A = pd.DataFrame(rows)
    b = L.render(G, [2020, 2021], "2021-12", 3, null, 9.0, shares, year_rows=A)           # with the per-year ranges and the new sentences present
    assert b == L.render(G, [2020, 2021], "2021-12", 3, null, 9.0, shares, year_rows=A)
    assert "Per year at 15 minutes, the oriented deviation runs from" in b and "Per year at 15 minutes" not in a
    assert "Every event was scored in every year." in b
    assert b.count("Every event was scored in every year.") == 1
    table = [ln for ln in b.splitlines() if ln.startswith("| ") and not ln.startswith("| family")]
    assert len(table) == len(names) * len(L.HORIZONS)
    table = [ln for ln in a.splitlines() if ln.startswith("| ") and not ln.startswith("| family")]
    assert len(table) == len(names) * len(L.HORIZONS)
    assert "Of 66 cells (11 events at 6 horizons), 66 hold their sign in every year." in a
    assert "in every scored year by 66 cells, in at least half of the scored years by 66 and in at least one year by 66; 66 cells" in a
    assert "Null: the largest |z|" in a


def test_vwap_retention_is_shown_only_where_the_interval_excludes_zero():
    rows, vrows = [], []
    for name, diff in (("large-trade burst", 0.001), ("trade-count climax", 0.05)):
        for y in (2020, 2021):
            r = year_rows(y, diff, se=0.01)
            r.update({"pattern": name, "horizon": 5})
            rows.append(r)
            v = vwap_rows(y, diff, diff / 2)
            v.update({"pattern": name, "horizon": 5})
            vrows.append(v)
    G = L.pool_cells(pd.DataFrame(rows), pd.DataFrame(vrows))
    shares = pd.DataFrame({"year": [2020, 2021] * 2, "event": np.repeat(["trade-count climax", "large-trade burst"], 2), "share": 0.01, "fires": 5})
    a = L.render(G, [2020, 2021], "2021-12", 3, np.array([1.0]), 9.0, shares)
    burst = next(ln for ln in a.splitlines() if "| large-trade burst |" in ln)
    climax = next(ln for ln in a.splitlines() if "| trade-count climax |" in ln)
    assert burst.rstrip().endswith("| - |")
    assert climax.rstrip().endswith("| 50% |")


def test_effect_sentences_orient_events_with_a_side_so_that_a_reversal_is_positive():
    rows = []
    for ev, dev in (("trade-count climax at a new 1h high", -0.06), ("trade-count climax at a new 1h low", 0.08)):
        for h in (5, 10, 15, 30):
            rows.append({"event": ev, "horizon": h, "deviation": dev, "lo": dev - 0.01, "hi": dev + 0.01, "years": 3, "years_held": 3})
    G = pd.DataFrame(rows)
    s = L.effect_sentences(G, scale=0.09)
    first = next(x for x in s if x.startswith("A reversal from a price extreme"))
    assert "from +6.0 to +8.0 points (reversal positive)" in first and "8 of 8 cells" in first and first.endswith("cells holding their sign in every year: 8.")
    assert s[-1].startswith("For scale") and "9.0 points" in s[-1]


# ---------------- derivatives coverage ----------------

def touch_futures(cache, funding, metrics_days, perp_months=(), perp_days=()):
    cache.mkdir(parents=True, exist_ok=True)
    for m in funding:
        (cache / f"BTCUSDT-funding-{m}.csv").touch()
    for d in metrics_days:
        (cache / f"BTCUSDT-metrics-{d}.csv").touch()
    for m in perp_months:
        (cache / f"BTCUSDT-perp-1m-{m}.csv").touch()
    for d in perp_days:
        (cache / f"BTCUSDT-perp-1m-{d}.csv").touch()


def test_a_year_needs_all_three_series_for_every_day_before_its_successor_can_be_scored(tmp_path):
    days = [str(d.date()) for d in pd.date_range("2024-01-01", "2025-01-10")]
    months = [f"2024-{m:02d}" for m in range(1, 13)] + ["2025-01"]
    touch_futures(tmp_path, months, days, perp_months=months)
    cov, covered = L.futures_days(tmp_path)
    assert L.full_years(covered) == [2024]
    text = L.render_derivatives(tmp_path)
    assert "the events can be scored in 2025" in text
    assert "| funding rate (monthly files) | 2024-01 | 2025-01 | 13 |" in text
    assert all(e in text for e in L.DERIV_EVENTS)


def test_one_missing_series_day_removes_the_year_and_with_no_full_year_nothing_is_scored(tmp_path):
    days = [str(d.date()) for d in pd.date_range("2024-01-01", "2024-12-31") if str(d.date()) != "2024-06-15"]
    months = [f"2024-{m:02d}" for m in range(1, 13)]
    touch_futures(tmp_path, months, days, perp_months=months)
    assert L.full_years(L.futures_days(tmp_path)[1]) == []
    text = L.render_derivatives(tmp_path)
    assert "no calendar year in full, so no event has a previous year" in text
    empty = tmp_path / "none"
    assert "no calendar year in full" in L.render_derivatives(empty)               # a missing directory is an empty coverage, not an error


def test_the_cache_key_has_no_dot_that_would_truncate_a_file_name():
    assert "." not in L.code_key()
    assert "." not in L.deriv_code_key() and L.deriv_code_key() != L.code_key()


# ---------------- derivatives scoring ----------------

def test_the_derivatives_events_are_grouped_into_families_in_table_order():
    fams = [f for f, _ in L.DERIV_EVENT_FAMILIES]
    assert [fams.count(f) for f in ("funding", "open interest", "liquidation signature")] == [2, 4, 2]
    assert fams == sorted(fams, key=["funding", "open interest", "liquidation signature"].index)
    assert L.DERIV_EVENTS == [name for _, name in L.DERIV_EVENT_FAMILIES]


def month_files(cache, month, skip_day=None):
    p = pd.Period(month, "M")
    days = [str(d.date()) for d in pd.date_range(p.start_time, p.end_time.normalize()) if str(d.date()) != skip_day]
    touch_futures(cache, [month], days, perp_months=[month])


def test_require_futures_names_a_missing_metrics_day_and_passes_when_everything_is_there(tmp_path, monkeypatch):
    monkeypatch.setattr(L.derivatives, "CACHE", tmp_path)
    month_files(tmp_path, "2024-02")
    L.require_futures(["2024-02"])
    (tmp_path / "BTCUSDT-metrics-2024-02-10.csv").unlink()
    with pytest.raises(FileNotFoundError, match="2024-02-10"):
        L.require_futures(["2024-02"])


def test_a_missing_futures_file_is_an_error_and_never_a_download(tmp_path, monkeypatch):
    monkeypatch.setattr(L.derivatives, "CACHE", tmp_path)
    month_files(tmp_path, "2024-02", skip_day="2024-02-10")

    def no_download(*a, **k):
        raise AssertionError("download attempted")

    monkeypatch.setattr(L.derivatives, "_fetch", no_download)
    t = np.arange(1706745600, 1706745600 + 60 * 120, 60)                 # 2024-02-01, two hours
    s = types.SimpleNamespace(t=t, c=np.full(len(t), 100.0))
    monkeypatch.setattr(L, "year_frame", lambda year, end: (s, pd.DataFrame({"i": [0], "t": [t[0]]})))
    with pytest.raises(FileNotFoundError, match="2024-02-10"):
        L.deriv_year_arrays(2024, "2024-02")


def test_the_reference_cutoffs_come_from_the_previous_year_and_not_its_december_before():
    t_dec = 1701388800 + 60 * np.arange(100)                           # 2023-12-01
    t_in = 1704067200 + 60 * np.arange(101)                            # 2024-01-01
    s = types.SimpleNamespace(t=np.concatenate([t_dec, t_in]))
    arrs = {k: np.concatenate([np.full(100, 1000.0), np.linspace(-5, 5, 101)]) for k in ("funding_bp", "doi15", "doi60", "pvol_ratio5", "ret15")}
    asked = []

    def fake(year, end):
        asked.append((year, end))
        return s, None, arrs

    original = L.deriv_year_arrays
    L.deriv_year_arrays = fake
    try:
        cuts = L.deriv_reference_cutoffs(2025)
    finally:
        L.deriv_year_arrays = original
    assert asked == [(2024, "2024-12")]
    assert cuts["funding_bp"] == pytest.approx((-4.0, 4.0))
    assert all(v == pytest.approx((-4.0, 4.0)) for v in cuts.values())


def test_scorable_years_need_a_fully_covered_previous_year_and_stay_in_the_range(tmp_path):
    months = [str(p) for p in pd.period_range("2023-01", "2025-06", freq="M")]
    days = [str(d.date()) for d in pd.date_range("2023-01-01", "2025-06-30")]
    touch_futures(tmp_path, months, days, perp_months=months)
    assert L.scorable_years(tmp_path, 2018, "2025-06") == [2024, 2025]
    assert L.scorable_years(tmp_path, 2025, "2025-06") == [2025]
    assert L.scorable_years(tmp_path, 2018, "2023-12") == []


def scored_cells(events, years=(2020, 2021)):
    rows, vrows = [], []
    for k, name in enumerate(events):
        for h in L.HORIZONS:
            for y in years:
                r = year_rows(y, 0.03 + 0.001 * k)
                r.update({"pattern": name, "horizon": h})
                rows.append(r)
                v = vwap_rows(y, 0.03, 0.02)
                v.update({"pattern": name, "horizon": h})
                vrows.append(v)
    return L.pool_cells(pd.DataFrame(rows), pd.DataFrame(vrows))


def test_the_derivatives_document_has_the_coverage_then_one_row_per_cell(tmp_path):
    months = [f"2024-{m:02d}" for m in range(1, 13)] + ["2025-01"]
    days = [str(d.date()) for d in pd.date_range("2024-01-01", "2025-01-10")]
    touch_futures(tmp_path, months, days, perp_months=months)
    names = L.DERIV_EVENTS
    G = scored_cells(names)
    shares = pd.DataFrame({"year": [2020, 2021] * len(names), "event": np.repeat(names, 2), "share": 0.01, "fires": 5})
    args = (tmp_path, G, [2020, 2021], "2021-12", 3, np.array([1.0, 2.0, 3.0]), 9.0, shares)
    a = L.render_derivatives(*args)
    assert a == L.render_derivatives(*args)
    lines = a.splitlines()
    head = next(k for k, ln in enumerate(lines) if ln.startswith("| family"))
    assert any(ln.startswith("| series | first stamp") for k, ln in enumerate(lines) if k < head)
    table = [ln for ln in lines[head + 1:] if ln.startswith("| ") and not ln.startswith("|---")]
    assert len(table) == len(names) * len(L.HORIZONS) == 48
    assert "| event |" not in lines
    assert "Of 48 cells (8 events at 6 horizons)" in a
    funding = next(x for x in lines if x.startswith("Funding at an extreme"))
    assert "(reversal positive)" in funding
    assert "fires on" in a and L.DERIV_SHARE_EVENTS[0] in a
    assert "over the years in which it was scored" in a and "the share is the share of minutes the event fires on over the years in which it was scored" in a
    assert any(x.startswith("Open interest up over 15 or 60 minutes, top decile") for x in lines)
    assert any(x.startswith("Open interest down over 15 or 60 minutes, bottom decile") for x in lines)
    assert not any(x.startswith("Open interest moves") for x in lines)
    assert "| event |" in L.render_derivatives(tmp_path).splitlines()                 # coverage only: the stand-alone list stays


def test_render_with_the_tick_arguments_given_explicitly_is_the_default():
    names = [name for _, name in L.TICK_EVENTS]
    G = scored_cells(names)
    shares = pd.DataFrame({"year": [2020, 2021] * len(names), "event": np.repeat(names, 2), "share": 0.01, "fires": 5})
    null = np.array([1.0, 2.0, 3.0])
    default = L.render(G, [2020, 2021], "2021-12", 3, null, 9.0, shares, 0.09)
    explicit = L.render(G, [2020, 2021], "2021-12", 3, null, 9.0, shares, 0.09, events=L.TICK_EVENTS, effects=L.TICK_EFFECTS, orient=L.TICK_ORIENT,
                        share_events=L.TICK_SHARE_EVENTS, intro=L.tick_intro([2020, 2021], "2021-12", 3, null))
    assert default == explicit
    assert default.startswith("Tick-level events for the price-action library, 2020 to 2021-12,")
    # The contract changed after the outside review of 2026-10-05: the share is the aggregate over the scored years, and the intro and header say so.
    assert "the share of minutes it fires on over the years in which it was scored (an event with fewer than" in default
    assert "| share (scored years) |" in default


def test_a_negative_deviation_on_the_top_funding_decile_is_a_positive_reversal():
    rows = [{"event": L.DERIV_EVENTS[0], "horizon": h, "deviation": -0.05, "lo": -0.06, "hi": -0.04, "years": 3, "years_held": 3} for h in (5, 10, 15, 30)]
    s = L.effect_sentences(pd.DataFrame(rows), L.DERIV_EFFECTS, L.DERIV_ORIENT)
    first = next(x for x in s if x.startswith("Funding at an extreme"))
    assert "from +5.0 to +5.0 points (reversal positive)" in first


# ---------------- reporting after the outside review of 2026-10-05 ----------------

def share_table(events, years):
    return pd.DataFrame({"year": list(years) * len(events), "event": np.repeat(events, len(years)), "share": 0.01, "fires": 5})


def test_share_is_the_aggregate_over_the_scored_years_and_not_the_mean_of_the_yearly_shares():
    A = pd.DataFrame([year_rows(2020, 0.0, fires=1000, share=0.10), year_rows(2021, 0.0, fires=3000, share=0.30), year_rows(2022, 0.0, fires=1000, share=0.10)])
    V = pd.DataFrame([vwap_rows(2020, 0.0, 0.0), vwap_rows(2021, 0.0, 0.0, fires=3000), vwap_rows(2022, 0.0, 0.0)])
    G = L.pool_cells(A, V).iloc[0]
    # every year is 10,000 minutes (fires / share), so the aggregate is 5000 / 30000; the mean of the three shares would be 0.1667
    assert G.share == pytest.approx(5000 / 30000)
    # these three years happen to have equal minutes, so the mean agrees; unequal minutes tell the two apart:
    # 1000 firings at 0.10 is 10,000 minutes and 3000 firings at 0.15 is 20,000, so 4000 / 30000 = 0.1333, where the mean of the shares is 0.125
    A2 = pd.DataFrame([year_rows(2020, 0.0, fires=1000, share=0.10), year_rows(2021, 0.0, fires=3000, share=0.15)])
    V2 = pd.DataFrame([vwap_rows(2020, 0.0, 0.0), vwap_rows(2021, 0.0, 0.0, fires=3000)])
    G2 = L.pool_cells(A2, V2).iloc[0]
    assert G2.share == pytest.approx(4000 / 30000)
    assert G2.share != pytest.approx(A2.share.mean())


def test_the_table_header_says_the_share_is_over_the_scored_years():
    G = scored_cells(["trade-count climax"])
    a = L.render(G, [2020, 2021], "2021-12", 3, np.array([1.0]), 9.0, share_table(["trade-count climax", "large-trade burst"], [2020, 2021]))
    assert "| fires | share (scored years) | up-rate |" in a


def test_an_event_scored_in_fewer_than_all_years_gets_a_sentence_with_the_counts():
    names = [name for _, name in L.TICK_EVENTS]
    partial = names[-1]
    G = pd.concat([scored_cells(names[:-1], years=(2020, 2021, 2022)), scored_cells([partial], years=(2020, 2021))], ignore_index=True)
    s = L.sentences(G, np.array([1.0]), 9.0, share_table(list(L.TICK_SHARE_EVENTS), [2020, 2021, 2022]), [2020, 2021, 2022])
    expected = f"'{partial}' was scored in 2 of 3 years (fewer than {L.MIN_FIRES} firings in the others)."
    assert s.count(expected) == 1
    assert sum(" years (fewer than " in x for x in s) == 1
    assert "Every event was scored in every year." not in s
    full = L.sentences(scored_cells(names), np.array([1.0]), 9.0, share_table(list(L.TICK_SHARE_EVENTS), [2020, 2021]), [2020, 2021])
    assert "Every event was scored in every year." in full and not any(" years (fewer than " in x for x in full)


def strong_cells(retained_by_event):
    """Cells that hold their sign in every year and clear the null in every year, with the given VWAP retention at the shortest horizon."""
    G = scored_cells(list(retained_by_event))
    first = min(L.HORIZONS)
    for ev, r in retained_by_event.items():
        G.loc[(G.event == ev) & (G.horizon == first), "retained"] = r
    return G


def test_strong_one_minute_cells_that_keep_under_half_under_the_vwap_label_are_listed():
    low, high = "large-trade burst", "trade-count climax"
    G = strong_cells({low: 0.2, high: 0.9})
    s = L.sentences(G, np.array([1.0]), 9.0, share_table(list(L.TICK_SHARE_EVENTS), [2020, 2021]), [2020, 2021])
    line = next(x for x in s if x.startswith("Of the ") and "VWAP label" in x)
    assert f"Of the {len(G)} cells that hold their sign in every year and clear the null in at least half of the years, 1 are at the {min(L.HORIZONS)}-minute horizon" in line
    assert line.endswith(f"keep less than half of their deviation under the VWAP label: {low} (retained 20%).")
    assert high not in line
    nan = strong_cells({low: float("nan")})
    line = next(x for x in L.sentences(nan, np.array([1.0]), 9.0, share_table(list(L.TICK_SHARE_EVENTS), [2020, 2021]), [2020, 2021]) if "VWAP label:" in x)
    assert f"{low} (retained not measured)" in line                                  # an unmeasured retention counts as failing
    ok = strong_cells({low: 0.9})
    line = next(x for x in L.sentences(ok, np.array([1.0]), 9.0, share_table(list(L.TICK_SHARE_EVENTS), [2020, 2021]), [2020, 2021]) if "VWAP label:" in x)
    assert line.endswith("VWAP label: none.")


def test_the_vwap_sentence_is_absent_when_no_cell_is_strong():
    G = strong_cells({"large-trade burst": 0.2}).assign(years_adj_05=0)
    s = L.sentences(G, np.array([1.0]), 9.0, share_table(list(L.TICK_SHARE_EVENTS), [2020, 2021]), [2020, 2021])
    assert not any("VWAP label:" in x for x in s)


def test_the_effect_sentence_gives_the_oriented_per_year_range_at_15_minutes():
    ev = "trade-count climax at a new 1h high"                                           # orient -1: a fall is the reversal
    G = pd.DataFrame([{"event": ev, "horizon": h, "deviation": -0.01, "lo": -0.02, "hi": 0.0, "years": 2, "years_held": 2} for h in (5, 10, 15, 30)])
    A = pd.DataFrame([{"year": 2020, "pattern": ev, "horizon": 15, "diff": 0.02}, {"year": 2021, "pattern": ev, "horizon": 15, "diff": -0.01},
                      {"year": 2020, "pattern": ev, "horizon": 5, "diff": 0.50},            # another horizon: not in the range
                      {"year": 2020, "pattern": "large-trade burst", "horizon": 15, "diff": 0.50}])   # another event: not in this group
    first = next(x for x in L.effect_sentences(G, A=A) if x.startswith("A reversal from a price extreme"))
    assert first.endswith(" Per year at 15 minutes, the oriented deviation runs from -2.0 to +1.0 points over 2 year-cells, 1 of them positive.")
    assert "Per year" not in next(x for x in L.effect_sentences(G) if x.startswith("A reversal from a price extreme"))


def test_open_interest_up_and_down_are_separate_groups_with_a_range_of_one_sign_each():
    d = L.DERIV_EVENTS
    rows = [{"event": e, "horizon": h, "deviation": dev, "lo": dev - 0.001, "hi": dev + 0.001, "years": 3, "years_held": 3}
            for events, dev in (([d[2], d[4]], -0.003), ([d[3], d[5]], 0.015)) for e in events for h in (5, 10, 15, 30)]
    s = L.effect_sentences(pd.DataFrame(rows), L.DERIV_EFFECTS, L.DERIV_ORIENT)
    up = next(x for x in s if x.startswith("Open interest up over 15 or 60 minutes, top decile"))
    down = next(x for x in s if x.startswith("Open interest down over 15 or 60 minutes, bottom decile"))
    assert "runs from -0.3 to -0.3 points (up positive)" in up
    assert "runs from +1.5 to +1.5 points (up positive)" in down
    assert not any(x.startswith("Open interest moves") for x in s)
    assert sorted(e for _, evs in L.DERIV_EFFECTS[2:] for e in evs) == sorted(d[2:6])        # the four open-interest events, each in one group
