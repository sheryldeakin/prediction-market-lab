"""A profile of the conditional cells: which events fire together, how the effect decays
with the horizon, and how it scales with the volatility of the last hour.

Three tables over the same nine years, every minute as a decision time, both libraries
(the horizons event set of horizons.candidates and the price-action library):

  clusters     two overlap measures on the firing minutes of every pair of events, pooled
               over years: the overlap coefficient (shared minutes over the rarer event's
               minutes, which is 1 when one event is nested in the other) and Jaccard (shared
               over either). Average-linkage clusters cut at OVERLAP_CUT on the overlap
               coefficient are the main table: a rare event that fires inside a broad one is
               a costume of it. For each cluster: its members, the share of minutes on which
               any member fires, the union's deviation at 5 and 30 minutes with years held,
               and how many members point the other way at 30 minutes. The cluster count
               under both measures at several cuts is reported so the cut is not load-bearing.
  decay        for one cell per cluster among the strongest (held every year at 30 minutes),
               the deviation at every horizon 1 to HMAX, pooled over years with a day-clustered
               standard error, years held at each horizon, and the peak horizon.
  volatility   for the strongest cells of both libraries (one per Jaccard cluster, so an event
               listed under two names appears once), the deviation within each tercile of vol60
               (trailing-hour volatility; tercile cutoffs from the previous year) at 5 and 30
               minutes, against that tercile's own base rate, with intervals and years held.
               The tercile is known at the time, so a live view can show it.

Deviations are the up-rate when the event fires minus the up-rate when it does not, in
points; a year counts as held when its sign matches the pooled sign and the event fired at
least MIN_FIRES times.

    python -m models.btc_15m.cells_profile --start 2018 --end 2026-08
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.features import Series
from models.btc_15m.horizons import MIN_FIRES, candidates, year_frame
from models.btc_15m.price_action import masks_for, minute_events
from models.btc_15m.rules import vol_cutoffs
from models.btc_15m.stats import cluster_diff_pvalue

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
HMAX = 60
H_REF = 30                                      # the horizon that ranks cells and names the clusters' deviation
DECAY_ROWS = tuple(range(1, 31)) + (35, 40, 45, 50, 55, 60)
OVERLAP_CUT = 0.5
CUTS = {"overlap coefficient": (0.5, 0.7, 0.9), "Jaccard": (0.2, 0.3, 0.5)}
JACCARD_DEDUP = 0.3                             # events this close are one event for the volatility table
MAX_LISTED = 6
DECAY_CELLS = 8
VOL_CELLS_PER_HORIZON = 12
VOL_HORIZONS = (5, 30)
CHUNK = 1 << 17


def labels_upto(s: Series, idx: np.ndarray, hmax: int = HMAX) -> np.ndarray:
    """(n, hmax) int8: the label for horizons 1..hmax (column h-1), -1 where the horizon runs past the data."""
    n = len(s.c)
    Y = np.full((len(idx), hmax), -1, np.int8)
    for h in range(1, hmax + 1):
        end = idx + h - 1
        ok = end < n
        Y[ok, h - 1] = (s.c[end[ok]] >= s.o[idx[ok]]).astype(np.int8)
    return Y


def event_masks(s: Series, D: pd.DataFrame, cutoffs) -> dict[str, np.ndarray]:
    """Both libraries, prefixed by library, as boolean masks over D's rows."""
    C = candidates(D, cutoffs)
    E = masks_for(D, minute_events(s))
    return {**{f"lib: {k}": np.asarray(v, bool) for k, v in C.items()}, **{f"pa: {k}": np.asarray(v, bool) for k, v in E.items()}}


def terciles(vol: np.ndarray, cut: tuple[float, float]) -> np.ndarray:
    """0, 1, 2 for the low, mid and high tercile of vol60 under the given cutoffs; -1 where vol is missing."""
    out = np.full(len(vol), -1, np.int8)
    ok = ~np.isnan(vol)
    out[ok] = 0
    out[ok & (vol > cut[0])] = 1
    out[ok & (vol > cut[1])] = 2
    return out


def jaccard_matrix(co: np.ndarray) -> np.ndarray:
    """Jaccard overlap from a co-firing count matrix whose diagonal holds each event's firings."""
    f = np.diag(co).astype(float)
    union = f[:, None] + f[None, :] - co
    with np.errstate(divide="ignore", invalid="ignore"):
        J = np.where(union > 0, co / union, 0.0)
    np.fill_diagonal(J, 1.0)
    return J


def overlap_matrix(co: np.ndarray) -> np.ndarray:
    """Overlap coefficient: shared firings over the rarer event's firings (1 when one event is nested in the other)."""
    f = np.diag(co).astype(float)
    smaller = np.minimum(f[:, None], f[None, :])
    with np.errstate(divide="ignore", invalid="ignore"):
        O = np.where(smaller > 0, co / smaller, 0.0)
    np.fill_diagonal(O, 1.0)
    return O


def clusters_at(J: np.ndarray, cut: float) -> np.ndarray:
    """Average-linkage clusters of the events, merged while the linkage Jaccard is at least `cut`. Labels start at 1."""
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import squareform
    if len(J) == 1:
        return np.array([1])
    Dm = 1.0 - J
    Dm = (Dm + Dm.T) / 2
    np.fill_diagonal(Dm, 0.0)
    Z = linkage(squareform(Dm, checks=False), method="average")
    return fcluster(Z, t=1.0 - cut, criterion="distance")


def pooled(per_year: list[tuple[int, float, float]]) -> tuple[float, float, int, int]:
    """Firing-weighted pooled deviation, its standard error (years independent), years held, years."""
    per_year = [(f, d, se) for f, d, se in per_year if f >= MIN_FIRES and np.isfinite(se)]
    if not per_year:
        return float("nan"), float("nan"), 0, 0
    f = np.array([p[0] for p in per_year], float); d = np.array([p[1] for p in per_year]); se = np.array([p[2] for p in per_year])
    w = f / f.sum()
    dev = float((w * d).sum())
    return dev, float(np.sqrt(((w * se) ** 2).sum())), int((np.sign(d) == np.sign(dev)).sum()), len(per_year)


def unpack(Xp: np.ndarray, j: int, n: int) -> np.ndarray:
    return np.unpackbits(Xp[j], count=n).astype(bool)


def year_stats(mask: np.ndarray, Y: np.ndarray, t: np.ndarray, h: int, sel: np.ndarray | None = None) -> tuple[int, float, float]:
    """(fires, deviation, se) of one event at horizon h in one year, optionally within a selection of minutes."""
    y = Y[:, h - 1]
    ok = y >= 0
    if sel is not None:
        ok &= sel
    if (mask & ok).sum() < 2:
        return int((mask & ok).sum()), 0.0, float("inf")
    b, se, _ = cluster_diff_pvalue(mask[ok], y[ok], t[ok])
    return int((mask & ok).sum()), b, se


def fmt(dev: float, se: float, held: int, years: int) -> str:
    if not np.isfinite(dev):
        return ""
    return f"{dev*100:+.1f} [{(dev-1.96*se)*100:+.1f}, {(dev+1.96*se)*100:+.1f}] {held}/{years}"


def listed(names_: list[str], limit: int = MAX_LISTED) -> str:
    return "; ".join(names_[:limit]) + (f"; and {len(names_) - limit} more" if len(names_) > limit else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2018)
    ap.add_argument("--end", default="2026-08")
    a = ap.parse_args()
    years_all = list(range(a.start, int(a.end[:4]) + 1))

    names = None
    co = None
    data = {}                                       # year -> packed masks, labels, times, terciles
    dev_year = {}                                   # year -> (events x HMAX) deviation, fires
    cutoffs, vcut = None, None
    for year in years_all:
        yf = year_frame(year, a.end)
        if yf is None:
            continue
        s, D = yf
        if cutoffs is None:
            first_q = D[pd.to_datetime(D.t, unit="s").dt.month <= 3]
            cutoffs = vol_cutoffs(first_q)
            vcut = tuple(np.nanquantile(first_q.vol60.values, [1 / 3, 2 / 3]))
        M = event_masks(s, D, cutoffs)
        if names is None:
            names = sorted(M)
            co = np.zeros((len(names), len(names)))
        n = len(D)
        X = np.column_stack([M.get(k, np.zeros(n, bool)) for k in names]).astype(np.uint8)
        Y = labels_upto(s, D.i.values)
        Yup = (Y == 1).astype(np.float32); Yok = (Y >= 0).astype(np.float32)
        ups = np.zeros((len(names), HMAX)); fires_h = np.zeros((len(names), HMAX))
        for lo in range(0, n, CHUNK):
            Xf = X[lo:lo + CHUNK].astype(np.float32)
            co += Xf.T @ Xf
            ups += Xf.T @ Yup[lo:lo + CHUNK]
            fires_h += Xf.T @ Yok[lo:lo + CHUNK]
        base = Yup.sum(axis=0) / np.maximum(Yok.sum(axis=0), 1)
        with np.errstate(divide="ignore", invalid="ignore"):
            dev = np.where(fires_h > 0, ups / fires_h - base, np.nan)
        dev_year[year] = (dev, fires_h)
        data[year] = {"Xp": np.packbits(X.T, axis=1), "n": n, "Y": Y, "t": D.t.values, "terc": terciles(D.vol60.values, vcut)}
        cutoffs = vol_cutoffs(D)
        vcut = tuple(np.nanquantile(D.vol60.values, [1 / 3, 2 / 3]))
        print(f"{year}: {n:,} minutes, {len(names)} events", flush=True)
    years = sorted(data)
    m = len(names)

    # pooled deviation per (event, horizon), without intervals, for ranking
    F = np.stack([dev_year[y][1] for y in years]); Dv = np.stack([dev_year[y][0] for y in years])
    enough = F >= MIN_FIRES
    W = np.where(enough, F, 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        pooled_dev = np.nansum(np.where(enough, Dv, 0.0) * W, axis=0) / W.sum(axis=0)
    held = (enough & (np.sign(np.nan_to_num(Dv)) == np.sign(pooled_dev)[None])).sum(axis=0)
    years_with = enough.sum(axis=0)
    all_held = (held == years_with) & (years_with == len(years))

    # clusters
    J, O = jaccard_matrix(co), overlap_matrix(co)
    fires_total = np.diag(co)
    active = fires_total >= MIN_FIRES * len(years)
    labels_by = {}
    for measure, Mx in (("overlap coefficient", O), ("Jaccard", J)):
        for cut in CUTS[measure]:
            lab = np.zeros(m, int)
            lab[active] = clusters_at(Mx[np.ix_(active, active)], cut)
            labels_by[(measure, cut)] = lab
    lab = labels_by[("overlap coefficient", OVERLAP_CUT)]
    jlab = labels_by[("Jaccard", JACCARD_DEDUP)]
    h30 = H_REF - 1
    cluster_rows, member_rows = [], []
    for c in sorted(set(lab[active])):
        members = np.where(lab == c)[0]
        lead = members[np.argmax(fires_total[members])]
        union_stats = {}
        for h in (5, H_REF):
            per = []
            for y in years:
                d = data[y]
                u = np.zeros(d["n"], bool)
                for j in members:
                    u |= unpack(d["Xp"], j, d["n"])
                per.append(year_stats(u, d["Y"], d["t"], h))
            union_stats[h] = pooled(per)
        share = sum(np.unpackbits(np.bitwise_or.reduce(data[y]["Xp"][members], axis=0), count=data[y]["n"]).sum() for y in years) / sum(data[y]["n"] for y in years)
        opposite = int((np.sign(np.nan_to_num(pooled_dev[members, h30])) == -np.sign(union_stats[H_REF][0])).sum())
        cluster_rows.append({"cluster": int(c), "name": names[lead], "members": len(members), "share": share,
                             "dev5": union_stats[5][0], "se5": union_stats[5][1], "held5": union_stats[5][2], "years5": union_stats[5][3],
                             "dev30": union_stats[H_REF][0], "se30": union_stats[H_REF][1], "held30": union_stats[H_REF][2], "years30": union_stats[H_REF][3],
                             "opposite30": opposite, "member_names": "; ".join(names[j] for j in members)})
        for j in members:
            member_rows.append({"event": names[j], "cluster": int(c), "cluster_name": names[lead], "fires": int(fires_total[j]), "dev30": pooled_dev[j, h30], "held30": int(held[j, h30]), "years30": int(years_with[j, h30])})
    CR = pd.DataFrame(cluster_rows).sort_values("dev30", key=np.abs, ascending=False)
    pd.DataFrame(member_rows).to_csv(OUT / "cells_clusters.csv", index=False)
    strong = active & all_held[:, h30]
    strong_clusters = {k: len(set(v[strong])) for k, v in labels_by.items()}
    all_clusters = {k: len(set(v[active])) for k, v in labels_by.items()}

    # decay: one cell per cluster among the strongest at 30 minutes
    order = np.argsort(-np.abs(np.nan_to_num(pooled_dev[:, h30])))
    chosen, seen = [], set()
    for j in order:
        if not (strong[j] and lab[j] not in seen):
            continue
        seen.add(lab[j]); chosen.append(j)
        if len(chosen) == DECAY_CELLS:
            break
    decay = {}
    for j in chosen:
        for h in range(1, HMAX + 1):
            per = [year_stats(unpack(data[y]["Xp"], j, data[y]["n"]), data[y]["Y"], data[y]["t"], h) for y in years]
            decay[(j, h)] = pooled(per)
        print(f"decay: {names[j]}", flush=True)
    DR = pd.DataFrame([{"event": names[j], "horizon": h, "deviation": v[0], "se": v[1], "years_held": v[2], "years": v[3]} for (j, h), v in decay.items()])
    DR.to_csv(OUT / "cells_decay.csv", index=False)

    # volatility terciles for the strongest cells at 5 and 30 minutes, one per Jaccard cluster
    vol_rows = []
    for h in VOL_HORIZONS:
        col = h - 1
        order = np.argsort(-np.abs(np.nan_to_num(pooled_dev[:, col])))
        picked, seen = [], set()
        for j in order:
            if active[j] and all_held[j, col] and jlab[j] not in seen:
                seen.add(jlab[j]); picked.append(j)
            if len(picked) == VOL_CELLS_PER_HORIZON:
                break
        for j in picked:
            row = {"event": names[j], "horizon": h}
            for name, sel_fn in (("all", lambda d: None), ("low", lambda d: d["terc"] == 0), ("mid", lambda d: d["terc"] == 1), ("high", lambda d: d["terc"] == 2)):
                per = []
                for y in years:
                    d = data[y]
                    per.append(year_stats(unpack(d["Xp"], j, d["n"]), d["Y"], d["t"], h, sel_fn(d)))
                dev, se, hd, yr = pooled(per)
                row.update({f"dev_{name}": dev, f"se_{name}": se, f"held_{name}": hd, f"years_{name}": yr, f"fires_{name}": int(sum(p[0] for p in per))})
            vol_rows.append(row)
        print(f"volatility: horizon {h}", flush=True)
    VR = pd.DataFrame(vol_rows)
    VR.to_csv(OUT / "cells_volatility.csv", index=False)

    span = f"{years[0]} to {a.end}"
    with open(OUT / "cells_clusters.md", "w") as f:
        CR["all30"] = (CR.held30 == CR.years30) & (CR.years30 == len(years))
        shown = CR[CR.all30].sort_values("dev30", key=np.abs, ascending=False)
        f.write(f"Co-firing clusters of the {int(active.sum())} events of both libraries that fire at least {MIN_FIRES * len(years):,} times over {span} ('lib' is the horizons event set, 'pa' the price-action library). Overlap coefficient of firing minutes pooled over years (shared minutes over the rarer event's minutes, so an event nested inside a broader one scores 1), average linkage, cut at {OVERLAP_CUT}. Each cluster is named by its most frequent member; 'union' is the up-rate deviation when any member fires, points, 95% interval from day-clustered errors, years held out of years with enough firings; 'opposite' counts members whose own 30-minute deviation has the other sign. The {len(shown)} clusters (of {len(CR)}) whose union deviation at 30 minutes held in every year, by absolute deviation; every event's cluster is in cells_clusters.csv.\n\n")
        f.write("| cluster (most frequent member) | members | minutes any member fires | union deviation at 5 min | union deviation at 30 min | opposite | other members |\n|---|---|---|---|---|---|---|\n")
        for r in shown.itertuples():
            others = [x for x in r.member_names.split("; ") if x != r.name]
            f.write(f"| {r.name} | {r.members} | {r.share*100:.2f}% | {fmt(r.dev5, r.se5, r.held5, r.years5)} | {fmt(r.dev30, r.se30, r.held30, r.years30)} | {r.opposite30} | {listed(others)} |\n")
        f.write(f"\nHow many clusters under each measure and cut: all {int(active.sum())} active events, and the {int(strong.sum())} events whose 30-minute cell held its sign in every year.\n\n| measure | cut | clusters, all active events | clusters, events held every year at 30 min |\n|---|---|---|---|\n")
        for (measure, cut), n_all in all_clusters.items():
            f.write(f"| {measure} | {cut} | {n_all} | {strong_clusters[(measure, cut)]} |\n")

    with open(OUT / "cells_decay.md", "w") as f:
        f.write(f"The effect by horizon, {span}: for one cell per cluster among the strongest events held every year at {H_REF} minutes, the pooled deviation at horizons 1 to {HMAX} minutes (points, firing-weighted over years; the number after +/- is half the 95% interval from day-clustered errors pooled as if years were independent; in brackets, years held at that horizon). Every minute to 30, then every five. Below, where each peaks.\n\n")
        cols = [names[j] for j in chosen]
        f.write("| horizon (min) | " + " | ".join(cols) + " |\n|---|" + "---|" * len(cols) + "\n")
        for h in DECAY_ROWS:
            cells = []
            for j in chosen:
                dev, se, hd, yr = decay[(j, h)]
                cells.append(f"{dev*100:+.1f} +/-{1.96*se*100:.1f} ({hd}/{yr})" if np.isfinite(dev) else "")
            f.write(f"| {h} | " + " | ".join(cells) + " |\n")
        f.write(f"\n| event | deviation at 1 min | at 5 min | at 15 min | at 30 min | at {HMAX} min | peak horizon (min) | deviation at peak | horizons of {HMAX} held every year |\n|---|---|---|---|---|---|---|---|---|\n")
        for j in chosen:
            devs = np.array([decay[(j, h)][0] for h in range(1, HMAX + 1)])
            peak = int(np.nanargmax(np.abs(devs))) + 1
            every = sum(1 for h in range(1, HMAX + 1) if decay[(j, h)][2] == decay[(j, h)][3] == len(years))
            f.write(f"| {names[j]} | {devs[0]*100:+.1f} | {devs[4]*100:+.1f} | {devs[14]*100:+.1f} | {devs[29]*100:+.1f} | {devs[-1]*100:+.1f} | {peak} | {devs[peak-1]*100:+.1f} | {every}/{HMAX} |\n")

    with open(OUT / "cells_volatility.md", "w") as f:
        f.write(f"The strongest cells by tercile of the trailing-hour volatility (vol60; tercile cutoffs from the previous year, so known at the time), {span}: the {VOL_CELLS_PER_HORIZON} largest pooled deviations held every year at each of {', '.join(str(h) for h in VOL_HORIZONS)} minutes, one per group of near-identical events (Jaccard {JACCARD_DEDUP}). Because the cutoffs come from the previous year, a calm year after a wild one puts most of its minutes in the low tercile, which is why some terciles have few years with enough firings. Deviation of the up-rate from the tercile's own unconditional rate, points, 95% interval, years held; firings in brackets.\n\n")
        f.write("| event | horizon (min) | all minutes | low-volatility third | middle third | high-volatility third |\n|---|---|---|---|---|---|\n")
        for r in VR.itertuples():
            cells = [f"{fmt(getattr(r, f'dev_{k}'), getattr(r, f'se_{k}'), getattr(r, f'held_{k}'), getattr(r, f'years_{k}'))} [{getattr(r, f'fires_{k}'):,}]" for k in ("all", "low", "mid", "high")]
            f.write(f"| {r.event} | {r.horizon} | " + " | ".join(cells) + " |\n")
        ratio = VR.dev_high.abs() / VR.dev_low.abs()
        f.write(f"\nAcross the {len(VR)} cells, the high-volatility deviation is {ratio.median():.1f} times the low-volatility one (median; range {ratio.min():.1f} to {ratio.max():.1f}); the sign agrees between the two terciles in {int((np.sign(VR.dev_high) == np.sign(VR.dev_low)).sum())} of {len(VR)}.\n")
    print("wrote cells_clusters.md, cells_decay.md, cells_volatility.md")


if __name__ == "__main__":
    main()
