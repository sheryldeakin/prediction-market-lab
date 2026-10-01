"""The price-action library: trader vernacular turned into events defined before the fact.

"Momentum failed at X", "rejected at resistance", "swept the lows", "reclaimed VWAP": each
is written here as a boolean per minute i that reads only candles up to i-1, and scored
with the horizons machinery (every minute, horizons 1 to 30, year by year, rotated-label
null). Families and their definitions (p is the last close, levels come from candles that
closed before the ones that test them):

  levels      failed breakout: within the last M minutes a close went above the N-minute
              high as it stood M minutes earlier, and the last close is back below it
              (N = 60, 240, 1440; M = 15); mirror for lows
              wick rejection: the last minute's high crossed the N-minute high of the
              candles before it, its close did not; mirror
              liquidity sweep: the last minute's low took out the 60-minute low and its
              close came back above it; mirror
              retest from above: the 240-minute high was crossed upward in the last hour
              and the price is now within 5 bp above that level; mirror
              previous day's high and low: approach (within 10 bp, not crossed) and break
              (closed beyond within the last 5 minutes); the daily open crossed in the
              last 5 minutes
              range breakout: the previous hour's range (excluding the last 5 minutes) was
              under 15 bp and the last close is outside it
              repeated rejection: the 4h high touched within 2 bp by two or more separate
              minutes in the last 30 with no close above it; mirror. Rejecting the ups:
              three or more up-minutes in the last 15 each undone by the next minute;
              mirror. Lower highs: three successive 10-minute highs declining; mirror.
              VWAP reclaim: the session VWAP (from the UTC day's open) crossed upward in
              the last 5 minutes after at least 30 minutes below it; mirror
  round       the next $1000 level above is within 10 bp and the last 5 minutes rose
  numbers     (approach from below); the mirror from above; a $1000 level crossed upward
              in the last 3 minutes; mirror. The same at $100 levels, which matter when
              the price was in the thousands.
  time        the 10 minutes before and after funding settlement (00:00, 08:00, 16:00
              UTC); the US equity open (13:30 UTC, 10 minutes after) and close (20:00
              UTC); the London open (07:00 UTC); the last 5 and first 5 minutes of each
              hour, each 4-hour block and each UTC day; Saturday and Sunday; the first
              hour of the week
  volume and  volume climax: the last minute's volume is the hour's largest and its high
  flow        or low is a new 60-minute extreme; absorption: taker selling dominated the
              last 5 minutes (share under 35%) and the price did not fall; mirror;
              delta divergence: a new 240-minute high in the last minute with net taker
              selling over the last 60 minutes; mirror; imbalance: taker share in the
              last minute above 70% or below 30%
  candles     bullish and bearish engulfing (the last body covers the previous body in
              the opposite direction); pin bar at an extreme (a wick at least twice the
              body, the body in the opposite third, at a new 60-minute high or low);
              inside bar; doji at a new 60-minute extreme (body under a tenth of the range)
  volatility  squeeze: the last hour's range is under 40% of the median hourly range of
              the previous day

    python -m models.btc_15m.price_action --start 2018 --end 2026-08
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.features import Series
from models.btc_15m.horizons import HORIZONS, MIN_FIRES, score_year, year_frame

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
NULL_RUNS = 30


def _roll_max_before(x: np.ndarray, w: int, lag: int = 1) -> np.ndarray:
    """out[i] = max(x[i-lag-w+1 .. i-lag]): the w values ending lag minutes before i."""
    r = pd.Series(x).rolling(w).max().values
    out = np.full(len(x), np.nan)
    out[lag:] = r[:-lag]
    return out


def _roll_min_before(x: np.ndarray, w: int, lag: int = 1) -> np.ndarray:
    r = pd.Series(x).rolling(w).min().values
    out = np.full(len(x), np.nan)
    out[lag:] = r[:-lag]
    return out


def _lagged(x: np.ndarray, k: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    out[k:] = x[:-k]
    return out


def _bp(a, b):
    return (a / b - 1) * 1e4


def minute_events(s: Series) -> dict[str, tuple[str, np.ndarray]]:
    """{name: (family, boolean per minute i)}; every array reads candles up to i-1 only."""
    c, o, h, l, v, t = s.c, s.o, s.h, s.l, s.v, s.t
    n = len(c)
    i = np.arange(n)
    p = _lagged(c, 1)                                       # last close
    h1, l1, o1, c1, v1 = _lagged(h, 1), _lagged(l, 1), _lagged(o, 1), _lagged(c, 1), _lagged(v, 1)
    h2, l2, o2, c2 = _lagged(h, 2), _lagged(l, 2), _lagged(o, 2), _lagged(c, 2)
    ret5 = _bp(p, _lagged(c, 6))
    E = {}

    def add(name, family, mask):
        E[name] = (family, np.nan_to_num(mask.astype(float), nan=0.0).astype(bool))

    # ---- levels ----
    M = 15
    for N, lab in ((60, "1h"), (240, "4h"), (1440, "daily")):
        hiN = _roll_max_before(h, N, lag=M + 1)             # the N-minute high as it stood M minutes ago
        loN = _roll_min_before(l, N, lag=M + 1)
        max_close_recent = _roll_max_before(c, M, lag=1)    # closes in the last M minutes
        min_close_recent = _roll_min_before(c, M, lag=1)
        add(f"failed breakout above the {lab} high", "levels", (max_close_recent > hiN) & (p < hiN))
        add(f"failed breakdown below the {lab} low", "levels", (min_close_recent < loN) & (p > loN))
        hi_b = _roll_max_before(h, N, lag=2)                # level from candles before the last one
        lo_b = _roll_min_before(l, N, lag=2)
        add(f"wick rejection at the {lab} high", "levels", (h1 >= hi_b) & (c1 < hi_b))
        add(f"wick rejection at the {lab} low", "levels", (l1 <= lo_b) & (c1 > lo_b))
    lo60_b, hi60_b = _roll_min_before(l, 60, lag=2), _roll_max_before(h, 60, lag=2)
    add("liquidity sweep of the 1h low (took it out, closed back above)", "levels", (l1 < lo60_b) & (c1 > lo60_b))
    add("liquidity sweep of the 1h high (took it out, closed back below)", "levels", (h1 > hi60_b) & (c1 < hi60_b))
    hi240_hour_ago = _roll_max_before(h, 240, lag=61)
    crossed_up_last_hour = _roll_max_before(c, 60, lag=1) > hi240_hour_ago
    add("retest from above of a 4h high broken in the last hour", "levels", crossed_up_last_hour & (p >= hi240_hour_ago) & (_bp(p, hi240_hour_ago) <= 5))
    lo240_hour_ago = _roll_min_before(l, 240, lag=61)
    crossed_dn_last_hour = _roll_min_before(c, 60, lag=1) < lo240_hour_ago
    add("retest from below of a 4h low broken in the last hour", "levels", crossed_dn_last_hour & (p <= lo240_hour_ago) & (_bp(lo240_hour_ago, p) <= 5))
    # repeated rejection: the 4h high (from candles before the last 30 minutes) touched within 2 bp by
    # at least two separate minutes in the last 30, with no close above it
    hi240_30 = _roll_max_before(h, 240, lag=31)
    lo240_30 = _roll_min_before(l, 240, lag=31)
    touches_hi = np.zeros(n); touches_lo = np.zeros(n); closed_above = np.zeros(n); closed_below = np.zeros(n)
    for k in range(1, 31):
        hk, lk, ck = _lagged(h, k), _lagged(l, k), _lagged(c, k)
        touches_hi += (np.abs(_bp(hk, hi240_30)) <= 2).astype(float)
        touches_lo += (np.abs(_bp(lk, lo240_30)) <= 2).astype(float)
        closed_above += (ck > hi240_30).astype(float)
        closed_below += (ck < lo240_30).astype(float)
    add("repeated rejection at the 4h high (2+ touches in 30 minutes, no close above)", "levels", (touches_hi >= 2) & (closed_above == 0))
    add("repeated rejection at the 4h low (2+ touches in 30 minutes, no close below)", "levels", (touches_lo >= 2) & (closed_below == 0))
    # rejecting the ups: up-minutes undone by the next minute, at least three in the last 15
    undone_up = np.zeros(n); undone_dn = np.zeros(n)
    for k in range(1, 15):
        ok_, ck, ck_next = _lagged(o, k + 1), _lagged(c, k + 1), _lagged(c, k)
        undone_up += ((ck > ok_) & (ck_next < ok_)).astype(float)
        undone_dn += ((ck < ok_) & (ck_next > ok_)).astype(float)
    add("rejecting the ups (3+ up-minutes undone by the next minute in the last 15)", "levels", undone_up >= 3)
    add("rejecting the downs (3+ down-minutes undone by the next minute in the last 15)", "levels", undone_dn >= 3)
    # lower highs: three successive 10-minute block highs, each below the previous; mirror
    b1 = _roll_max_before(h, 10, lag=1); b2 = _roll_max_before(h, 10, lag=11); b3 = _roll_max_before(h, 10, lag=21)
    add("lower highs (three successive 10-minute highs declining)", "levels", (b1 < b2) & (b2 < b3))
    m1 = _roll_min_before(l, 10, lag=1); m2 = _roll_min_before(l, 10, lag=11); m3 = _roll_min_before(l, 10, lag=21)
    add("higher lows (three successive 10-minute lows rising)", "levels", (m1 > m2) & (m2 > m3))
    # previous UTC day's high, low, and today's open
    day = t // 86400
    df = pd.DataFrame({"day": day, "h": h, "l": l, "o": o, "i": i})
    dh = df.groupby("day").h.max(); dl = df.groupby("day").l.min(); do = df.groupby("day").o.first()
    pdh = pd.Series(day).map(dh.shift(1)).values; pdl = pd.Series(day).map(dl.shift(1)).values; dopen = pd.Series(day).map(do).values
    add("approaching the previous day's high from below (within 10 bp)", "levels", (p < pdh) & (_bp(pdh, p) <= 10))
    add("approaching the previous day's low from above (within 10 bp)", "levels", (p > pdl) & (_bp(p, pdl) <= 10))
    c6 = _lagged(c, 6)
    add("broke above the previous day's high in the last 5 minutes", "levels", (c6 <= pdh) & (p > pdh))
    add("broke below the previous day's low in the last 5 minutes", "levels", (c6 >= pdl) & (p < pdl))
    add("crossed above the daily open in the last 5 minutes", "levels", (c6 <= dopen) & (p > dopen))
    add("crossed below the daily open in the last 5 minutes", "levels", (c6 >= dopen) & (p < dopen))
    hr_hi, hr_lo = _roll_max_before(h, 55, lag=6), _roll_min_before(l, 55, lag=6)
    narrow = _bp(hr_hi, hr_lo) < 15
    add("range breakout upward (prior hour under 15 bp)", "levels", narrow & (p > hr_hi))
    add("range breakdown downward (prior hour under 15 bp)", "levels", narrow & (p < hr_lo))
    # session VWAP from the day's open, from candle data (typical price times volume)
    tp = (h + l + c) / 3
    cum_pv = pd.Series(tp * v).groupby(day).cumsum().values
    cum_v = pd.Series(v).groupby(day).cumsum().values
    vwap = np.where(cum_v > 0, cum_pv / np.maximum(cum_v, 1e-9), np.nan)
    above = (c > vwap).astype(float)
    above1 = _lagged(above, 1)
    below_30 = _roll_max_before(above, 30, lag=6) == 0      # below the VWAP for all of minutes i-35 .. i-6
    above_30 = _roll_min_before(above, 30, lag=6) == 1
    add("reclaimed the session VWAP in the last 5 minutes after 30+ minutes below", "levels", below_30 & (above1 == 1))
    add("lost the session VWAP in the last 5 minutes after 30+ minutes above", "levels", above_30 & (above1 == 0))

    # ---- round numbers ----
    for step, lab in ((1000, "$1,000"), (100, "$100")):
        above_lvl = np.ceil(p / step) * step
        below_lvl = np.floor(p / step) * step
        dist_up = _bp(above_lvl, p); dist_dn = _bp(p, below_lvl)
        add(f"approaching a {lab} level from below (within 10 bp, rising)", "round numbers", (dist_up > 0) & (dist_up <= 10) & (ret5 > 0))
        add(f"approaching a {lab} level from above (within 10 bp, falling)", "round numbers", (dist_dn > 0) & (dist_dn <= 10) & (ret5 < 0))
        c4 = _lagged(c, 4)
        add(f"crossed a {lab} level upward in the last 3 minutes", "round numbers", np.floor(p / step) > np.floor(c4 / step))
        add(f"crossed a {lab} level downward in the last 3 minutes", "round numbers", np.floor(p / step) < np.floor(c4 / step))

    # ---- time ----
    sec = t % 86400
    mins = sec // 60
    hour = mins // 60
    mod_h = mins % 60
    for hh in (0, 8, 16):
        add(f"10 minutes before funding settlement ({hh:02d}:00 UTC)", "time", (hour == (hh - 1) % 24) & (mod_h >= 50))
        add(f"10 minutes after funding settlement ({hh:02d}:00 UTC)", "time", (hour == hh) & (mod_h < 10))
    add("10 minutes after the US equity open (13:30 UTC)", "time", (hour == 13) & (mod_h >= 30) & (mod_h < 40))
    add("10 minutes after the US equity close (20:00 UTC)", "time", (hour == 20) & (mod_h < 10))
    add("10 minutes after the London open (07:00 UTC)", "time", (hour == 7) & (mod_h < 10))
    add("last 5 minutes of the hour", "time", mod_h >= 55)
    add("first 5 minutes of the hour", "time", mod_h < 5)
    add("last 5 minutes of a 4-hour block", "time", (hour % 4 == 3) & (mod_h >= 55))
    add("first 5 minutes of a 4-hour block", "time", (hour % 4 == 0) & (mod_h < 5))
    add("last 5 minutes of the UTC day", "time", (hour == 23) & (mod_h >= 55))
    add("first 5 minutes of the UTC day", "time", (hour == 0) & (mod_h < 5))
    wd = (t // 86400 + 3) % 7
    add("Saturday or Sunday", "time", wd >= 5)
    add("first hour of the week (Monday 00:00 to 01:00 UTC)", "time", (wd == 0) & (hour == 0))

    # ---- volume and flow ----
    signed = 2 * s._raw[1] - v
    share1 = np.where(v1 > 0, _lagged(s._raw[1], 1) / np.maximum(v1, 1e-9), 0.5)
    vmax60 = _roll_max_before(v, 60, lag=1)
    add("volume climax at a new 1h high (hour's largest volume)", "volume and flow", (v1 >= vmax60) & (h1 >= _roll_max_before(h, 60, lag=2)))
    add("volume climax at a new 1h low (hour's largest volume)", "volume and flow", (v1 >= vmax60) & (l1 <= _roll_min_before(l, 60, lag=2)))
    sv5 = pd.Series(signed).rolling(5).sum().values; v5 = pd.Series(v).rolling(5).sum().values
    flow5 = np.full(n, np.nan); flow5[1:] = (sv5 / np.maximum(v5, 1e-9))[:-1]
    add("absorption: heavy taker selling in the last 5 minutes, price did not fall", "volume and flow", (flow5 < -0.3) & (ret5 >= 0))
    add("absorption: heavy taker buying in the last 5 minutes, price did not rise", "volume and flow", (flow5 > 0.3) & (ret5 <= 0))
    sv60 = pd.Series(signed).rolling(60).sum().values; flow60 = np.full(n, np.nan); flow60[1:] = sv60[:-1]
    add("delta divergence: new 4h high with net taker selling over the hour", "volume and flow", (h1 >= _roll_max_before(h, 240, lag=2)) & (flow60 < 0))
    add("delta divergence: new 4h low with net taker buying over the hour", "volume and flow", (l1 <= _roll_min_before(l, 240, lag=2)) & (flow60 > 0))
    add("taker buying above 70% of the last minute", "volume and flow", share1 > 0.7)
    add("taker selling above 70% of the last minute", "volume and flow", share1 < 0.3)

    # ---- candles ----
    body1, body2 = c1 - o1, c2 - o2
    rng1 = h1 - l1
    add("bullish engulfing", "candles", (body2 < 0) & (body1 > 0) & (o1 <= c2) & (c1 >= o2))
    add("bearish engulfing", "candles", (body2 > 0) & (body1 < 0) & (o1 >= c2) & (c1 <= o2))
    upper_wick = h1 - np.maximum(o1, c1); lower_wick = np.minimum(o1, c1) - l1
    new_hi60 = h1 >= _roll_max_before(h, 60, lag=2); new_lo60 = l1 <= _roll_min_before(l, 60, lag=2)
    add("pin bar at a new 1h high (long upper wick)", "candles", new_hi60 & (upper_wick >= 2 * np.abs(body1)) & (np.maximum(o1, c1) <= l1 + rng1 / 3 + 1e-9) & (rng1 > 0))
    add("pin bar at a new 1h low (long lower wick)", "candles", new_lo60 & (lower_wick >= 2 * np.abs(body1)) & (np.minimum(o1, c1) >= h1 - rng1 / 3 - 1e-9) & (rng1 > 0))
    add("inside bar (last minute inside the previous one)", "candles", (h1 <= h2) & (l1 >= l2))
    add("doji at a new 1h high", "candles", new_hi60 & (np.abs(body1) < 0.1 * rng1) & (rng1 > 0))
    add("doji at a new 1h low", "candles", new_lo60 & (np.abs(body1) < 0.1 * rng1) & (rng1 > 0))

    # ---- volatility ----
    hr_range = _bp(_roll_max_before(h, 60, lag=1), _roll_min_before(l, 60, lag=1))
    med_day = pd.Series(hr_range).rolling(1440).median().values
    med_day = _lagged(med_day, 1)
    add("squeeze: last hour's range under 40% of the previous day's median hourly range", "volatility", hr_range < 0.4 * med_day)
    return E


def masks_for(D: pd.DataFrame, E: dict) -> dict[str, np.ndarray]:
    idx = D.i.values
    return {name: arr[idx] for name, (fam, arr) in E.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2018)
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--null-runs", type=int, default=NULL_RUNS)
    a = ap.parse_args()
    rng = np.random.default_rng(0)
    years = list(range(a.start, int(a.end[:4]) + 1))
    frames, nulls, families = [], [], {}
    for year in years:
        yf = year_frame(year, a.end)
        if yf is None:
            continue
        s, D = yf
        E = minute_events(s)
        families.update({k: fam for k, (fam, _) in E.items()})
        R, mz = score_year(s, D, None, rng, a.null_runs, masks_in=masks_for(D, E))
        R.insert(0, "year", year)
        frames.append(R); nulls.append(mz)
        print(f"{year}: {R.pattern.nunique()} events scored, max |z| {R.z.abs().max():.2f}, null median {np.median(mz):.2f}", flush=True)
    A = pd.concat(frames, ignore_index=True)
    null_all = np.concatenate(nulls)
    A["p_adj"] = [(1 + (null_all >= abs(z)).sum()) / (len(null_all) + 1) for z in A.z]
    A["family"] = A.pattern.map(families)
    A.to_csv(OUT / "price_action_cells.csv", index=False)
    g = []
    for (pat, h), grp in A.groupby(["pattern", "horizon"]):
        sign = np.sign(grp["diff"].sum())
        fires = int(grp.fires.sum())
        g.append({"family": families[pat], "pattern": pat, "horizon": h, "years": len(grp), "years_held": int((np.sign(grp["diff"]) == sign).sum()), "fires": fires,
                  "share": float(grp.share.mean()), "up_rate": float((grp.up_rate * grp.fires).sum() / fires), "deviation": float(((grp.up_rate - grp.base) * grp.fires).sum() / fires),
                  "min_p_adj": float(grp.p_adj.min()), "all_years_adj_05": bool((grp.p_adj <= 0.05).all())})
    G = pd.DataFrame(g).sort_values("deviation", key=np.abs, ascending=False)
    G.to_csv(OUT / "price_action_summary.csv", index=False)
    held = G[(G.years_held == G.years) & (G.years >= 5)]
    with open(OUT / "price_action.md", "w") as f:
        f.write(f"The price-action library, {years[0]} to {a.end}, every minute as a decision time: trader vernacular written as events that read only earlier candles (definitions in models/btc_15m/price_action.py), scored like the conditional tables in horizons.md. Pooled up-rate of the next h minutes when the event holds, deviation from the unconditional rate in points, share of minutes it fires on, years in which the sign matched the pooled sign out of years with at least {MIN_FIRES} firings, and the smallest search-wide adjusted p across years ({a.null_runs} rotated-label runs per year). Top 40 cells by absolute deviation that held in every year.\n\n")
        f.write("| family | event | horizon (min) | up-rate | deviation (points) | fires on | years held | min adjusted p |\n|---|---|---|---|---|---|---|---|\n")
        for r in held.head(40).itertuples():
            f.write(f"| {r.family} | {r.pattern} | {r.horizon} | {r.up_rate*100:.1f}% | {r.deviation*100:+.1f} | {r.share*100:.2f}% | {r.years_held}/{r.years} | {r.min_p_adj:.4f} |\n")
        f.write("\nBy family: events defined, cells (event by horizon) that held their sign in every year, and the largest absolute deviation among them.\n\n| family | events | cells tested | held every year | largest deviation among those (points) |\n|---|---|---|---|---|\n")
        for fam, grp in G.groupby("family"):
            hh = grp[(grp.years_held == grp.years) & (grp.years >= 5)]
            f.write(f"| {fam} | {grp.pattern.nunique()} | {len(grp)} | {len(hh)} | {hh.deviation.abs().max()*100 if len(hh) else float('nan'):.1f} |\n")
        f.write("\nEvery event at the 15-minute horizon, held or not, so that the null results are visible too.\n\n| family | event | up-rate | deviation (points) | fires on | years held | min adjusted p |\n|---|---|---|---|---|---|---|\n")
        for r in G[G.horizon == 15].sort_values(["family", "deviation"], key=lambda x: x if x.name == "family" else -x.abs()).itertuples():
            f.write(f"| {r.family} | {r.pattern} | {r.up_rate*100:.1f}% | {r.deviation*100:+.1f} | {r.share*100:.2f}% | {r.years_held}/{r.years} | {r.min_p_adj:.4f} |\n")
        f.write(f"\nNull: the largest |z| across all events and horizons on rotated labels has median {np.median(null_all):.2f} and 95th percentile {np.quantile(null_all, 0.95):.2f}; the real search's largest |z| is {A.z.abs().max():.2f}.\n")
    print("wrote price_action.md")


if __name__ == "__main__":
    main()
