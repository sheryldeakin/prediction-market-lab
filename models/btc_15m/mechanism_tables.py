"""Tables for the mechanism study (docs/horizons.md, "The mechanism"): aggregation of the
event frames built by mechanism.py, the pre-specified decision rule, and the runner.

Statistics. Every contrast is the event rows minus their matched control rows, with a
day-clustered standard error (stats.cluster_diff_pvalue on y = a + b * event), computed year by
year and pooled across years with the DerSimonian-Laird random-effects model of horizons_shrink
(95% interval = pooled mean +- 1.96 standard errors). A slice-year with fewer than
MIN_EVENTS_YEAR events is not scored. Null: with six events and a matched control for each,
the comparison is narrow, so no search-wide adjustment is used; the label contrasts in the
embargo table also carry a per-slice null, a day-level sign flip on the matched pairs
(stats.day_sign_test, 2000 draws, one-sided, event above control), pooled over all years.

    python -m models.btc_15m.mechanism_tables --start 2018 --end 2026-08
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m import mechanism as M
from models.btc_15m.horizons_shrink import random_effects
from models.btc_15m.stats import block_bootstrap_ci, cluster_diff_pvalue, day_sign_test

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
CACHE = Path("data/mechanism")            # the working copy's own cache, never LAB_DATA_ROOT
H15 = 15
LAG30 = [s for s, _ in M.LAGS].index(1800)
LAG60S = [s for s, _ in M.LAGS].index(60)

# the decision rule (docs/horizons.md states it in words; tests/test_mechanism.py checks the two agree)
PATH_COMPLETE_SHARE = 0.8        # A2: the first 60 seconds reach at least four fifths of the 30-minute deviation
HORIZONS_NEEDED = 2              # a criterion that is scored at three horizons is met when it holds at two
FLOW_MEASURES = [("ev_absimb", "absolute imbalance"), ("ev_nratio", "trade count against the day's average"), ("ev_big", "large-trade share")]
TERCILE_MEASURES = [("terc_imb", "absolute imbalance"), ("terc_big", "large-trade share")]


# ---------------- pooling ----------------

def contrast(d: pd.DataFrame, col: str) -> tuple[int, float, float]:
    """(events, event-minus-control difference, day-clustered se) of one column."""
    v = d[col].values.astype(float)
    ok = ~np.isnan(v)
    d, v = d[ok], v[ok]
    ev = d.is_event.values
    b, se, _ = cluster_diff_pvalue(ev, v, d.t.values)
    return int(ev.sum()), b, se


def pool_years(rows, min_events: int | None = None) -> dict | None:
    """Random-effects pool of (year, events, difference, se) rows; None when no year qualifies."""
    min_events = M.MIN_EVENTS_YEAR if min_events is None else min_events
    keep =[(y, n, d, s) for y, n, d, s in rows if n >= min_events and np.isfinite(s) and s > 0]
    if not keep:
        return None
    d = np.array([k[2] for k in keep], float)
    se = np.array([k[3] for k in keep], float)
    r = random_effects(d, se)
    return {"mu": float(r["mu"]), "se": float(r["se_mu"]), "lo": float(r["mu"] - 1.96 * r["se_mu"]), "hi": float(r["mu"] + 1.96 * r["se_mu"]),
            "tau": float(r["tau"]), "years": len(keep), "held": int((np.sign(d) == np.sign(r["mu"])).sum()), "events": int(sum(k[1] for k in keep))}


def cell(Fy: dict, sl: str, col: str, extra=None) -> dict | None:
    rows = []
    for y, f in Fy.items():
        d = f[f[f"m_{sl}"]]
        if extra is not None:
            d = d[extra(d).values]
        rows.append((y, *contrast(d, col)))
    return pool_years(rows)


def diff_cell(Fy: dict, sl: str, col: str, ea, eb) -> dict | None:
    """Pooled (contrast in subset a) minus (contrast in subset b), the two subsets independent."""
    rows = []
    for y, f in Fy.items():
        d = f[f[f"m_{sl}"]]
        na, da, sa = contrast(d[ea(d).values], col)
        nb, db, sb = contrast(d[eb(d).values], col)
        rows.append((y, min(na, nb), da - db, float(np.hypot(sa, sb))))
    return pool_years(rows)


def raw_means(F: pd.DataFrame, sl: str, col: str) -> tuple[float, float]:
    d = F[F[f"m_{sl}"]]
    return float(d[d.is_event][col].mean()), float(d[~d.is_event][col].mean())


def paired(F: pd.DataFrame, sl: str, col: str) -> pd.DataFrame:
    d = F[F[f"m_{sl}"]]
    e = d[d.is_event][["year", "pair", "t", col]].rename(columns={col: "e"})
    c = d[~d.is_event][["year", "pair", col]].rename(columns={col: "c"})
    m = e.merge(c, on=["year", "pair"])
    return m[m.e.notna() & m.c.notna()]


def sign_flip_p(F: pd.DataFrame, sl: str, col: str) -> float:
    m = paired(F, sl, col)
    if len(m) < 10:
        return float("nan")
    return day_sign_test(m.e.values, m.c.values, m.t.values.astype(np.int64))["p"]


def pairs_higher(F: pd.DataFrame, sl: str, col: str) -> tuple[float, float, float]:
    m = paired(F, sl, col)
    hits = (m.e.values > m.c.values) + 0.5 * (m.e.values == m.c.values)
    return block_bootstrap_ci(hits, m.t.values.astype(np.int64), n_boot=1000)


# ---------------- formatting ----------------

def pts(c: dict | None, p: float | None = None) -> str:
    if c is None:
        return "n/a"
    s = f"{c['mu']*100:+.1f} [{c['lo']*100:+.1f}, {c['hi']*100:+.1f}]"
    if p is not None and np.isfinite(p):
        s += f", p {'<0.001' if p < 0.001 else f'{p:.3f}'}"
    return s


def bps(c: dict | None) -> str:
    return "n/a" if c is None else f"{c['mu']:+.2f} [{c['lo']:+.2f}, {c['hi']:+.2f}]"


def ratio(emb: dict | None, ref: dict | None) -> float:
    return float("nan") if emb is None or ref is None or not ref["mu"] > 0 else emb["mu"] / ref["mu"]


def retention_class(emb: dict | None, ref: dict | None) -> str:
    """Where the embargoed deviation sits against half of the last-print deviation: 'under half' when its
    whole interval is below half, 'over half' when its whole interval is above half, else 'unresolved'."""
    if emb is None or ref is None:
        return "n/a"
    if not ref["mu"] > 0:
        return "no reversal"
    half = ref["mu"] / 2
    if emb["hi"] < half:
        return "under half"
    if emb["lo"] > half:
        return "over half"
    return "unresolved"


# ---------------- tables ----------------

def embargo_table(F: pd.DataFrame, Fy: dict) -> tuple[list[dict], dict]:
    rows, cells = [], {}
    for sl in M.SLICES:
        for h in M.EVAL_H:
            c = {"lp": cell(Fy, sl, f"lp_{h}")}
            for g in M.GAPS:
                c[f"vw{g}"] = cell(Fy, sl, f"vw{g}_{h}")
            p_lp, p_g1 = sign_flip_p(F, sl, f"lp_{h}"), sign_flip_p(F, sl, f"vw1_{h}")
            cells[(sl, h)] = c
            rows.append({"slice": sl, "h": h, "events": c["lp"]["events"] if c["lp"] else 0, "lp": c["lp"], "vw0": c["vw0"], "vw1": c["vw1"], "vw2": c["vw2"],
                         "p_lp": p_lp, "p_vw1": p_g1, "ret1": ratio(c["vw1"], c["lp"]), "ret2": ratio(c["vw2"], c["lp"]),
                         "class1": retention_class(c["vw1"], c["lp"]), "class2": retention_class(c["vw2"], c["lp"])})
    return rows, cells


def halves_table(Fy: dict) -> tuple[list[dict], dict]:
    rows, cells = [], {}
    for h in M.EVAL_H:
        near = {"lp": diff_free(Fy, "lp", h, False), "vw1": diff_free(Fy, "vw1", h, False)}
        far = {"lp": diff_free(Fy, "lp", h, True), "vw1": diff_free(Fy, "vw1", h, True)}
        cells[h] = (near, far)
        rows.append({"h": h, "near": near, "far": far})
    return rows, cells


def diff_free(Fy: dict, kind: str, h: int, far: bool) -> dict | None:
    return cell(Fy, "union", f"{kind}_{h}", extra=lambda d: d.far if far else ~d.far)


def path_table(F: pd.DataFrame, Fy: dict) -> list[dict]:
    rows = []
    price = [cell(Fy, "union", f"path_{k}") for k in range(len(M.LAGS))]
    ref = price[LAG30]
    for k, (s, name) in enumerate(M.LAGS):
        fl = cell(Fy, "union", f"flow_{k}")
        ev, ct = raw_means(F, "union", f"flow_{k}")
        lo, hi = M.EDGES[k], M.EDGES[k + 1]
        rows.append({"lag": name, "k": k, "price": price[k], "share": (price[k]["mu"] / ref["mu"]) if price[k] and ref and ref["mu"] > 0 else float("nan"),
                     "bin": f"{_name(lo)} to {_name(hi)}", "flow": fl, "flow_event": ev, "flow_control": ct})
    return rows


def _name(s: int) -> str:
    if s == 0:
        return "0"
    return f"{s} s" if s < 120 else f"{s // 60} min"


def flow_table(F: pd.DataFrame, Fy: dict) -> list[dict]:
    rows = []
    measures = [("ev_imb", "imbalance in the direction of the move (share of volume)")] + [(c, n) for c, n in FLOW_MEASURES]
    for sl in M.SLICES:
        for col, name in measures:
            ev, ct = raw_means(F, sl, col)
            m, lo, hi = pairs_higher(F, sl, col)
            rows.append({"slice": sl, "col": col, "name": name, "event": ev, "control": ct, "excess": cell(Fy, sl, col), "higher": m, "higher_lo": lo, "higher_hi": hi})
    return rows


def scale_table(F: pd.DataFrame, Fy: dict) -> tuple[list[dict], dict]:
    rows, top_bottom = [], {}
    for tcol, tname in TERCILE_MEASURES:
        for k, kname in enumerate(["lowest third", "middle third", "highest third"]):
            sel = lambda d, k=k, tcol=tcol: d[tcol] == k
            d = F[F.m_union & F.is_event & (F[tcol] == k)]
            rows.append({"measure": tname, "third": kname, "events": int(len(d)), "move": float(d.ret5_abs.mean()),
                         **{f"lp{h}": cell(Fy, "union", f"lp_{h}", sel) for h in M.EVAL_H}, "path": cell(Fy, "union", f"path_{LAG30}", sel)})
        hi_, lo_ = (lambda d, tcol=tcol: d[tcol] == 2), (lambda d, tcol=tcol: d[tcol] == 0)
        tb = {f"lp{h}": diff_cell(Fy, "union", f"lp_{h}", hi_, lo_) for h in M.EVAL_H}
        tb["path"] = diff_cell(Fy, "union", f"path_{LAG30}", hi_, lo_)
        top_bottom[tcol] = tb
        rows.append({"measure": tname, "third": "highest minus lowest", "events": None, "move": None, **tb})
    return rows, top_bottom


# ---------------- the rule ----------------

def apply_rule(a1: list[str], a2_share: float, a3: list[tuple], b_embargo: list[str], b1_lo: dict, b3_lo: dict) -> dict:
    """The pre-specified decision rule.
    a1: retention class of the g=1 VWAP label at each horizon. a2_share: share of the 30-minute price
    deviation reached after 60 seconds. a3: per horizon (near mu, near lo, near hi, far mu), last-print label.
    b_embargo: same classes as a1. b1_lo: lower interval bound of the event-minus-control excess for each of
    the three flow measures. b3_lo: lower bound of the highest-minus-lowest third difference of the
    15-minute last-print label for each of the two flow measures.
    A is supported when A1 and A2 hold; B when the embargoed labels keep most, B1 and B3 hold; neither or both
    is 'unidentified with this data'. A3 corroborates A and does not enter the verdict."""
    A1 = sum(c == "under half" for c in a1) >= HORIZONS_NEEDED
    A2 = bool(np.isfinite(a2_share) and a2_share >= PATH_COMPLETE_SHARE)
    A3 = sum(bool(n_mu < 0.5 * f_mu and n_lo <= 0 <= n_hi) for n_mu, n_lo, n_hi, f_mu in a3 if np.isfinite(n_mu) and np.isfinite(f_mu) and f_mu > 0) >= HORIZONS_NEEDED
    BE = sum(c == "over half" for c in b_embargo) >= HORIZONS_NEEDED
    B1 = bool(len(b1_lo) > 0 and all(v > 0 for v in b1_lo.values()))
    B3 = bool(len(b3_lo) > 0 and all(v > 0 for v in b3_lo.values()))
    a_sup = A1 and A2
    b_sup = BE and B1 and B3
    if a_sup and not b_sup:
        verdict = "A supported: bid-ask bounce or last-trade noise"
    elif b_sup and not a_sup:
        verdict = "B supported: transient price impact"
    else:
        verdict = "unidentified with this data"
    return {"A1": A1, "A2": A2, "A3": A3, "B_embargo": BE, "B1": B1, "B3": B3, "A_supported": a_sup, "B_supported": b_sup, "verdict": verdict}


# ---------------- rendering ----------------

def yesno(x: bool) -> str:
    return "yes" if x else "no"


def render_embargo(rows, halves, years, end) -> str:
    out = [f"Embargoed labels for events of any of the six kinds and for each kind alone, {years[0]} to {end}. Each event is the first firing of its kind in any {M.BLOCK_MIN} minutes; each has one matched control minute (same year, same hour of day, same previous-year volatility decile, none of the six firing in the {M.BLOCK_MIN} minutes up to and including it). All labels are signed so that a reversal is positive: the share of events whose label points back against the move, minus the same share for the matched controls, in points, with a 95% interval (day-clustered errors, years pooled by random effects). 'Last print' is the library's label (close of the horizon's last minute against the open of the decision minute); the VWAP labels compare the 60-second VWAP of minute g after the decision minute with the VWAP of minute g+h-1, so g=0 is the VWAP label of the cells section and g=1 and g=2 enter one and two minutes later. 'Retained' is the embargoed deviation as a share of the last-print deviation. The p after a last-print or g=1 interval is a per-slice null: a day-level sign flip on the matched pairs (event against its control), 2000 draws, one-sided, all years pooled; no search-wide adjustment is used because the comparison is six events. Years held: years in which the last-print deviation had the pooled sign, out of the years with at least {M.MIN_EVENTS_YEAR} events.", "",
           "| event | horizon (min) | events | last print | VWAP, g=0 | VWAP, g=1 | VWAP, g=2 | retained, g=1 | retained, g=2 | years held |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lp = r["lp"]
        out.append(f"| {M.NAMES[r['slice']]} | {r['h']} | {r['events']:,} | {pts(lp, r['p_lp'])} | {pts(r['vw0'])} | {pts(r['vw1'], r['p_vw1'])} | {pts(r['vw2'])} | "
                   f"{_pct(r['ret1'])} ({r['class1']}) | {_pct(r['ret2'])} ({r['class2']}) | {lp['held'] if lp else 0}/{lp['years'] if lp else 0} |")
    out += ["", f"Is the reversal confined to events whose last print was far from the minute's VWAP? Events of any of the six kinds split in each year at the median of |close minus VWAP| of the event minute, in basis points (the median of that year's events); each control takes the half of the event it is matched to. Same deviations as above, points with 95% intervals.", "",
            "| half of events by distance from VWAP | horizon (min) | events | last print | VWAP, g=1 |", "|---|---|---|---|---|"]
    for r in halves:
        for name, key in (("near the VWAP", "near"), ("far from the VWAP", "far")):
            c = r[key]
            out.append(f"| {name} | {r['h']} | {c['lp']['events'] if c['lp'] else 0:,} | {pts(c['lp'])} | {pts(c['vw1'])} |")
    return "\n".join(out) + "\n"


def _pct(x: float) -> str:
    return "n/a" if not np.isfinite(x) else f"{x*100:.0f}%"


def render_path(rows, years, end) -> str:
    out = [f"The path after the event minute and the flow beside it, events of any of the six kinds, {years[0]} to {end}, events minus matched controls. Price: the VWAP of the trailing window of min(lag, {M.MAX_WINDOW}) seconds ending at the lag after the event minute, against the event minute's close, in basis points, positive in the reversal direction; mean excess over the controls with a 95% interval (day-clustered errors, years pooled by random effects). Share: the excess at that lag as a share of the excess at 30 minutes. Flow: signed aggressor volume over volume in the bin that ends at the lag, positive when aggressors trade in the direction of the move (selling after a drop, buying after a rise), in percent, for the events, for the controls, and the excess with its interval. Years held: years in which the price excess had the pooled sign.", "",
           "| lag after the event minute | price excess (bp) | share of 30-minute excess | years held | flow bin | flow, events (%) | flow, controls (%) | flow excess (points) |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        p = r["price"]
        out.append(f"| {r['lag']} | {bps(p)} | {_pct(r['share'])} | {p['held'] if p else 0}/{p['years'] if p else 0} | {r['bin']} | {r['flow_event']*100:+.1f} | {r['flow_control']*100:+.1f} | {pts(r['flow'])} |")
    return "\n".join(out) + "\n"


def render_flow(rows, years, end) -> str:
    out = [f"Flow in the event minute against matched controls, {years[0]} to {end}. The event minute is the minute that closes at the decision time; all four measures come from the per-second trade table. Imbalance is signed aggressor volume over volume, positive when aggressors trade in the direction of the move; trade count is the minute's count over the mean per-minute count of the previous 24 hours; a trade is large when its notional is at or above the previous UTC day's 99th percentile. 'Excess' is the event mean minus the control mean (imbalance and share in points of a share, count as a ratio), 95% interval, years pooled by random effects. 'Events higher' is the share of matched pairs in which the event exceeds its control (ties count half), with a day-block 95% interval.", "",
           "| event | measure | events | controls | excess | events higher |", "|---|---|---|---|---|---|"]
    for r in rows:
        scale = 100 if r["col"] != "ev_nratio" else 1
        ex = r["excess"]
        exs = "n/a" if ex is None else f"{ex['mu']*scale:+.2f} [{ex['lo']*scale:+.2f}, {ex['hi']*scale:+.2f}]"
        fmt = (lambda x: f"{x*100:.1f}%") if r["col"] != "ev_nratio" else (lambda x: f"{x:.2f}x")
        out.append(f"| {M.NAMES[r['slice']]} | {r['name']} | {fmt(r['event'])} | {fmt(r['control'])} | {exs} | {r['higher']*100:.1f}% [{r['higher_lo']*100:.1f}, {r['higher_hi']*100:.1f}] |")
    return "\n".join(out) + "\n"


def render_scale(rows, years, end) -> str:
    out = [f"Does the recovery grow with the event's own flow? Events of any of the six kinds, {years[0]} to {end}, split in each year into thirds of the event minute's absolute imbalance and of its large-trade share (cutoffs from that year's events, so each year contributes equal thirds; a descriptive split, not a rule a trader could apply in advance). Last-print deviation at 5, 15 and 30 minutes (points, reversal positive, events minus matched controls, 95% interval) and the 30-minute price excess in basis points (path table). 'Mean move' is the mean absolute 5-minute move into the event, in basis points, so the reader can see whether a larger flow is just a larger move. The last row of each block is the highest third minus the lowest, with the two thirds treated as independent samples.", "",
           "| measure | third | events | mean move (bp) | last print, 5 min | last print, 15 min | last print, 30 min | price excess at 30 min (bp) |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        ev = "" if r["events"] is None else f"{r['events']:,}"
        mv = "" if r["move"] is None else f"{r['move']:.1f}"
        out.append(f"| {r['measure']} | {r['third']} | {ev} | {mv} | {pts(r['lp5'])} | {pts(r['lp15'])} | {pts(r['lp30'])} | {bps(r['path'])} |")
    return "\n".join(out) + "\n"


def render_verdict(crit: list[dict], res: dict, years, end) -> str:
    out = [f"The pre-specified rule applied to the tables above, {years[0]} to {end}. A criterion scored at three horizons is met when it holds at {HORIZONS_NEEDED} of them. A is supported when A1 and A2 are met; B when A1 read the other way, B1 and B3 are met; if neither or both, the section says it cannot tell. A3 corroborates A and B2 is reported; neither enters the verdict.", "",
           "| criterion | what is measured | value | met |", "|---|---|---|---|"]
    for c in crit:
        out.append(f"| {c['id']} | {c['what']} | {c['value']} | {'reported' if c['met'] is None else yesno(c['met'])} |")
    out += ["", f"Verdict by the rule: {res['verdict']}."]
    return "\n".join(out) + "\n"


# ---------------- run ----------------

def code_key() -> str:
    h = hashlib.sha1()
    for f in ("mechanism.py",):
        h.update((Path(__file__).parent / f).read_bytes())
    return h.hexdigest()[:10]


def git(*args) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip()


def require_files(first: str, last: str):
    from models.btc_15m import data, ticks
    missing = []
    for p in pd.period_range(first, last, freq="M"):
        m = str(p)
        for f in (data.CACHE / f"BTCUSDT-1m-{m}.csv", ticks.tick_path(m)):
            if not f.exists():
                missing.append(str(f))
    if missing:
        raise FileNotFoundError(f"missing raw data (nothing is downloaded here): {missing[:4]}{' ...' if len(missing) > 4 else ''}")


def load_year(year: int, end: str, rows_from: str | None):
    from models.btc_15m.data import load
    from models.btc_15m.features import Series, features_all
    from models.btc_15m.ticks import load_seconds
    if rows_from:
        first = str(pd.Period(rows_from, "M") - 1)
    else:
        first = f"{year - 1}-12"
    last = str(min(pd.Period(f"{year + 1}-01", "M"), pd.Period(end, "M")))
    require_files(first, last)
    series = Series(load(first, last))
    D = features_all(series)
    yr = pd.to_datetime(D.t, unit="s").dt.year
    keep = (yr == year).values
    if rows_from:
        keep &= (D.t.values >= int(pd.Timestamp(rows_from).timestamp()))
    D = D[keep].reset_index(drop=True)
    cum = M.SecCum(load_seconds(first, last))
    return series, D, cum


def main():
    from threadpoolctl import threadpool_limits
    import psutil
    threadpool_limits(2)
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2018)
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--rows-from", default=None, help="smoke test: score only decision minutes from this month, one year")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--refresh", action="store_true", help="rebuild the cached event frames")
    a = ap.parse_args()
    if a.rows_from:
        M.MIN_EVENTS_YEAR = 5       # a two-month smoke test has few events; it checks the plumbing, not a result
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    years = [int(a.rows_from[:4])] if a.rows_from else list(range(a.start, int(a.end[:4]) + 1))
    key = code_key()
    frames, stats, edges = [], [], None
    for year in years:
        tag = f"{year}-{a.end}-{a.rows_from or 'all'}-{key}"
        fp, sp = CACHE / f"events-{tag}.parquet", CACHE / f"events-{tag}.json"
        if fp.exists() and sp.exists() and not a.refresh:
            f, st = pd.read_parquet(fp), json.loads(sp.read_text())
        else:
            series, D, cum = load_year(year, a.end, a.rows_from)
            if edges is None:           # first year: its own first quarter, the repo's convention
                q1 = D[pd.to_datetime(D.t, unit="s").dt.month <= 3] if not a.rows_from else D
                edges = np.quantile(q1.vol60.values, np.linspace(0.1, 0.9, 9))
            f, st = M.build_year(series, D, cum, edges, np.random.default_rng(year), year)
            st["edges_used"] = [float(x) for x in edges]
            st["next_edges"] = [float(x) for x in np.quantile(D.vol60.values, np.linspace(0.1, 0.9, 9))]
            f.to_parquet(fp, index=False)
            sp.write_text(json.dumps(st))
            del series, D, cum
        edges = np.array(st["next_edges"])
        frames.append(f)
        stats.append(st)
        print(f"{year}: {st['unique_events']} events, {st['unmatched']} unmatched, {st['ambiguous']} ambiguous; union {st['events']['union']}", flush=True)
    F = pd.concat([f for f in frames if len(f)], ignore_index=True)
    Fy = {y: g for y, g in F.groupby("year")}
    yrs = sorted(Fy)

    emb_rows, emb_cells = embargo_table(F, Fy)
    half_rows, half_cells = halves_table(Fy)
    path_rows = path_table(F, Fy)
    flow_rows = flow_table(F, Fy)
    scale_rows, top_bottom = scale_table(F, Fy)

    a1 = [retention_class(emb_cells[("union", h)]["vw1"], emb_cells[("union", h)]["lp"]) for h in M.EVAL_H]
    a2 = path_rows[LAG60S]["share"]
    a3 = []
    for h in M.EVAL_H:
        near, far = half_cells[h]
        nl, fl = near["lp"], far["lp"]
        a3.append((nl["mu"], nl["lo"], nl["hi"], fl["mu"]) if nl and fl else (float("nan"),) * 4)
    union_flow = {r["col"]: r for r in flow_rows if r["slice"] == "union"}
    b1 = {c: (union_flow[c]["excess"]["lo"] if union_flow[c]["excess"] else float("nan")) for c, _ in FLOW_MEASURES}
    b3 = {tcol: (top_bottom[tcol]["lp15"]["lo"] if top_bottom[tcol]["lp15"] else float("nan")) for tcol, _ in TERCILE_MEASURES}
    res = apply_rule(a1, a2, a3, a1, b1, b3)

    names_h = lambda L: "; ".join(f"{h} min: {c}" for h, c in zip(M.EVAL_H, L))
    crit = [
        {"id": "A1", "what": "VWAP label entered one minute later keeps under half of the last-print deviation (class by interval)", "value": names_h(a1), "met": res["A1"]},
        {"id": "A2", "what": f"the first 60 seconds reach at least {PATH_COMPLETE_SHARE*100:.0f}% of the 30-minute price excess", "value": _pct(a2), "met": res["A2"]},
        {"id": "A3 (corroboration)", "what": "near-VWAP half keeps under half of the far half's last-print deviation, interval includes zero", "value": "; ".join(f"{h} min: near {_f(x[0])}, far {_f(x[3])}" for h, x in zip(M.EVAL_H, a3)), "met": res["A3"]},
        {"id": "A1, other side", "what": "VWAP label entered one minute later keeps over half of the last-print deviation (class by interval)", "value": names_h(a1), "met": res["B_embargo"]},
        {"id": "B1", "what": "the event minute's flow exceeds the controls' on all three measures (lower bound of the excess above zero, shown in points of a share, count as a ratio)", "value": "; ".join(f"{n}: lower bound {_g(b1[c], c)}" for c, n in FLOW_MEASURES), "met": res["B1"]},
        {"id": "B2 (reported, not in the rule)", "what": "price recovers while flow in the direction of the move continues or fades", "value": "see the path table", "met": None},
        {"id": "B3", "what": "highest third minus lowest third of the 15-minute last-print deviation is above zero for both flow measures", "value": "; ".join(f"{n}: lower bound {_f(b3[c])}" for c, n in TERCILE_MEASURES), "met": res["B3"]},
    ]
    (out / "mechanism_embargo.md").write_text(render_embargo(emb_rows, half_rows, yrs, a.end), encoding="utf-8")
    (out / "mechanism_path.md").write_text(render_path(path_rows, yrs, a.end), encoding="utf-8")
    (out / "mechanism_flow.md").write_text(render_flow(flow_rows, yrs, a.end), encoding="utf-8")
    (out / "mechanism_scale.md").write_text(render_scale(scale_rows, yrs, a.end), encoding="utf-8")
    (out / "mechanism_verdict.md").write_text(render_verdict(crit, res, yrs, a.end), encoding="utf-8")
    flat = lambda c: {} if c is None else {k: v for k, v in c.items()}
    csv_rows = []
    for r in emb_rows:
        for lab in ("lp", "vw0", "vw1", "vw2"):
            csv_rows.append({"table": "embargo", "slice": r["slice"], "h": r["h"], "label": lab, **flat(r[lab])})
    for r in path_rows:
        csv_rows.append({"table": "path", "slice": "union", "label": f"price_{r['lag']}", **flat(r["price"])})
        csv_rows.append({"table": "path", "slice": "union", "label": f"flow_{r['lag']}", **flat(r["flow"])})
    for r in flow_rows:
        csv_rows.append({"table": "flow", "slice": r["slice"], "label": r["col"], **flat(r["excess"])})
    pd.DataFrame(csv_rows).to_csv(out / "mechanism_embargo.csv", index=False)
    pd.DataFrame([{"measure": r["measure"], "third": r["third"], "events": r["events"], **{k: (r[k]["mu"] if r[k] else None) for k in ("lp5", "lp15", "lp30", "path")}} for r in scale_rows]).to_csv(out / "mechanism_scale.csv", index=False)
    pd.DataFrame([{"slice": r["slice"], "measure": r["col"], "event_mean": r["event"], "control_mean": r["control"], "excess": r["excess"]["mu"] if r["excess"] else None,
                   "excess_lo": r["excess"]["lo"] if r["excess"] else None, "excess_hi": r["excess"]["hi"] if r["excess"] else None, "events_higher": r["higher"]} for r in flow_rows]).to_csv(out / "mechanism_flow.csv", index=False)
    pd.DataFrame([{"lag": r["lag"], "price_excess_bp": r["price"]["mu"] if r["price"] else None, "lo": r["price"]["lo"] if r["price"] else None, "hi": r["price"]["hi"] if r["price"] else None,
                   "share_of_30min": r["share"], "flow_event": r["flow_event"], "flow_control": r["flow_control"], "flow_excess": r["flow"]["mu"] if r["flow"] else None} for r in path_rows]).to_csv(out / "mechanism_path.csv", index=False)
    dirty = bool(git("status", "--porcelain", "--untracked-files=no"))
    (out / "mechanism.json").write_text(json.dumps({
        "ran_at": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "commit": git("rev-parse", "HEAD"), "dirty": dirty,
        "years": yrs, "end": a.end, "wall_seconds": round(time.time() - t0), "peak_working_set_mb": round(getattr(psutil.Process().memory_info(), "peak_wset", psutil.Process().memory_info().rss) / 2**20),
        "per_year": stats, "criteria": crit,
        "rule": {k: (bool(v) if k != "verdict" else v) for k, v in res.items()}}, indent=2), encoding="utf-8")
    print("verdict:", res["verdict"])
    print(f"wrote mechanism tables to {out} in {time.time()-t0:.0f}s")


def _f(x: float, d: int = 1) -> str:
    return "n/a" if x is None or not np.isfinite(x) else f"{x*100:+.{d}f}"


def _g(x: float, col: str) -> str:
    """A lower bound in the unit its table uses: points for shares, a ratio for the trade count."""
    if x is None or not np.isfinite(x):
        return "n/a"
    return f"{x:+.2f}" if col == "ev_nratio" else f"{x*100:+.2f}"


if __name__ == "__main__":
    main()
