"""Hour of day and the calendar as conditioners of the two window rules, and of the strongest
any-minute cells, across nine years.

The question: does any hour of the day, weekday, session, month or event-time slot change the
accuracy of (i) the previous-window reversal at the open or (ii) the lead-sign rule at minute 3
in a way that holds year after year? Hourly accuracies read off a short record are noise-sized
(a month of data is about 130 windows per hour), so the study asks it over 2018 to the last
full month.

Rules (windows on the quarter-hour grid, label = the window closes at or above its open)
  reversal at the open    call the opposite of the previous window's direction (win1 >= 0 is
                          up, so the call is down), decided at minute 0
  lead sign at minute 3   call the sign of the move from the window's open to the close of
                          minute 2, decided at minute 3 (a tie counts as up, like the label)

Cells (every minute a decision time, 15-minute horizon, call = the reversal the cell implies)
  3-sd drop / rise (5-minute move beyond 3 standard deviations), 4-hour low / high
  (rangepos <= 0.02 / >= 0.98), RSI14 below 25 / above 75

Slices, five families, all in UTC and assigned from the decision time (the window's open for
the rules, the decision minute for the cells)
  hour         the 24 clock hours
  weekday      Monday to Sunday
  session      Asia 00-08, Europe 08-13, overlap 13-17, US 17-21, late 21-24
  month        the twelve months of the year
  event slot   the funding hours (00, 08, 16), the funding settlement window (the 15 minutes
               from 00:00, 08:00, 16:00), the US equity open window (13:30), the close window
               (20:00), the first hour of the week (Monday 00-01), the weekend

Statistic     per year and slice, accuracy in the slice minus the year's accuracy over all
              decisions, with a day-clustered sandwich error (the same regression as
              stats.cluster_diff_pvalue, scaled by the share outside the slice)
Null          per year, labels rotated within each calendar month, NULL_RUNS times; the largest
              |z| across the slices of a family gives every slice in that family a search-wide
              adjusted p (single-step max-T, as horizons.py). The pooled statistic gets its own
              null: in each run the nine yearly estimates are pooled exactly as the real ones
              are, and the largest pooled |z| in the family is kept
Pooling       DerSimonian-Laird random effects (horizons_shrink.random_effects)
Held          years in which the deviation had the pooled sign, out of the years in which the
              slice had at least MIN_N decisions inside and outside it

    python -m models.btc_15m.calendar_study --start 2018 --end 2026-08
"""
from __future__ import annotations

import argparse
import time
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.events2 import base_events
from models.btc_15m.features import WINDOW, Series
from models.btc_15m.horizons import labels, year_frame
from models.btc_15m.horizons_shrink import random_effects
from models.btc_15m.log import current_rows, read_log
from models.btc_15m.search_null import rotate_within_groups
from models.btc_15m.stats import block_bootstrap_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
NULL_RUNS = 500
MIN_N = 100              # decisions inside and outside a slice for a slice-year to be scored
MIN_YEARS = 3            # scored years a slice needs to be pooled
HOLD_YEARS = 8           # "holds year after year": the pooled sign in at least this many years
ALPHA = 0.05
RULES = ("reversal at the open", "lead sign at minute 3")
FAMILIES = ("hour", "weekday", "session", "month", "event slot")
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
SESSIONS = (("Asia 00-08", 0, 8), ("Europe 08-13", 8, 13), ("overlap 13-17", 13, 17), ("US 17-21", 17, 21), ("late 21-24", 21, 24))
FUNDING_HOURS = (0, 8, 16)
CELLS = ("3-sd drop (5-min move < -3 sd)", "3-sd rise (5-min move > +3 sd)", "4-hour low (rangepos <= 0.02)",
         "4-hour high (rangepos >= 0.98)", "RSI14 below 25", "RSI14 above 75")
CELL_HORIZON = 15


# ---------------- slice assignment ----------------

def slice_masks(t: np.ndarray) -> dict[str, dict[str, np.ndarray]]:
    """Boolean masks, family by family, for decision times t (epoch seconds, UTC). Hours,
    weekdays, sessions and months each partition the times; the event slots overlap."""
    t = np.asarray(t, dtype=np.int64)
    hour = (t // 3600) % 24
    quarter = ((t // 60) % 1440) // 15 * 15                       # minute of the day at the start of the quarter hour
    wday = (t // 86400 + 3) % 7                                   # Monday 0 ... Sunday 6 (1970-01-01 was a Thursday)
    month = t.astype("datetime64[s]").astype("datetime64[M]").astype(np.int64) % 12      # January 0
    out: dict[str, dict[str, np.ndarray]] = {f: {} for f in FAMILIES}
    for h in range(24):
        out["hour"][f"{h:02d}:00"] = hour == h
    for k, name in enumerate(WEEKDAYS):
        out["weekday"][name] = wday == k
    for name, a, b in SESSIONS:
        out["session"][name] = (hour >= a) & (hour < b)
    for k, name in enumerate(MONTHS):
        out["month"][name] = month == k
    slots = out["event slot"]
    slots["funding hours (00, 08, 16)"] = np.isin(hour, FUNDING_HOURS)
    slots["funding settlement window (00:00, 08:00, 16:00 +15 min)"] = np.isin(quarter, [60 * h for h in FUNDING_HOURS])
    slots["US equity open window (13:30 +15 min)"] = quarter == 13 * 60 + 30
    slots["US equity close window (20:00 +15 min)"] = quarter == 20 * 60
    slots["first hour of the week (Mon 00-01)"] = (wday == 0) & (hour == 0)
    slots["weekend (Sat, Sun)"] = wday >= 5
    return out


def slice_matrix(t: np.ndarray) -> tuple[np.ndarray, list[str], np.ndarray]:
    """All slices as one boolean matrix (rows = times), the slice names, and each column's family index."""
    masks = slice_masks(t)
    cols, names, fam = [], [], []
    for k, f in enumerate(FAMILIES):
        for name, m in masks[f].items():
            cols.append(m); names.append(name); fam.append(k)
    return np.column_stack(cols), names, np.array(fam)


def day_starts(t: np.ndarray) -> np.ndarray:
    """First row of each UTC day in time-sorted t."""
    day = np.asarray(t, dtype=np.int64) // 86400
    return np.flatnonzero(np.r_[True, day[1:] != day[:-1]])


# ---------------- statistic ----------------

def slice_stats(hit: np.ndarray, M: np.ndarray, starts: np.ndarray, min_n: int = MIN_N):
    """Deviation of the mean hit rate inside each slice from the mean over all rows, with a
    day-clustered standard error. Columns of M are slices. It is the regression hit = a + b * slice
    of stats.cluster_diff_pvalue (b is inside minus outside) scaled by the share outside, because
    inside-minus-overall = (1 - share) * b. Rows must be sorted by time; starts = day_starts(t).
    Returns (dev, se, n_inside), NaN where either side has fewer than min_n rows."""
    n = len(hit)
    m = M.astype(float)
    n1 = m.sum(axis=0)
    n0 = n - n1
    ok = (n1 >= min_n) & (n0 >= min_n)
    n1s, n0s = np.where(ok, n1, 1.0), np.where(ok, n0, 1.0)
    sum1 = hit @ m
    mean1, mean0 = sum1 / n1s, (hit.sum() - sum1) / n0s
    b = mean1 - mean0
    e = hit[:, None] - mean0 - b * m
    s0 = np.add.reduceat(e, starts, axis=0)
    s1 = np.add.reduceat(e * m, starts, axis=0)
    S00, S01, S11 = (s0 * s0).sum(axis=0), (s0 * s1).sum(axis=0), (s1 * s1).sum(axis=0)
    det = n * n1s - n1s ** 2
    var_b = (n1s ** 2 * S00 - 2 * n1s * n * S01 + n ** 2 * S11) / det ** 2
    outside = 1 - n1s / n
    dev = np.where(ok, outside * b, np.nan)
    se = np.where(ok, outside * np.sqrt(np.maximum(var_b, 0.0)), np.nan)
    return dev, se, n1


def family_max(absz: np.ndarray, fam: np.ndarray) -> np.ndarray:
    """Largest |z| within each family for every run: absz is (runs, slices), fam each slice's
    family index; returns (runs, families). A slice's adjusted p is read against its own family's column."""
    out = np.zeros((absz.shape[0], len(FAMILIES)))
    for f in range(len(FAMILIES)):
        cols = np.flatnonzero(fam == f)
        if len(cols):
            out[:, f] = np.nan_to_num(absz[:, cols], nan=0.0, posinf=0.0).max(axis=1)
    return out


def adjusted_p(absz: float, null_max: np.ndarray) -> float:
    """Share of null runs whose family maximum reaches this |z| (single-step max-T), with the
    observed value counted once so the smallest possible p is 1 / (runs + 1)."""
    return float((1 + (null_max >= absz).sum()) / (len(null_max) + 1))


def pool_years(d: np.ndarray, se: np.ndarray):
    """Random-effects pool of one slice's yearly deviations (NaN = year not scored); None when fewer than MIN_YEARS."""
    ok = np.isfinite(d) & np.isfinite(se) & (se > 0)
    if ok.sum() < MIN_YEARS:
        return None
    return random_effects(d[ok], se[ok])


# ---------------- rows: windows and cells ----------------

@dataclass
class Pool:
    """Every labelled decision of a year: the 0/1 labels and the month each belongs to (labels are rotated within months)."""
    y: np.ndarray
    groups: np.ndarray


@dataclass
class Block:
    """One rule or cell: the rows of its pool it decides on, and the direction it calls on each."""
    name: str
    pool: Pool
    sel: np.ndarray
    call_up: np.ndarray
    t: np.ndarray
    prepared: dict = field(default_factory=dict)

    def prepare(self):
        if not self.prepared:
            M, names, fam = slice_matrix(self.t)
            self.prepared = {"M": M, "names": names, "fam": fam, "starts": day_starts(self.t)}
        return self.prepared

    def hits(self, y: np.ndarray) -> np.ndarray:
        return (self.call_up == (y[self.sel] == 1)).astype(float)


def month_codes(t: np.ndarray) -> np.ndarray:
    return t.astype("datetime64[s]").astype("datetime64[M]").astype(np.int64)


def rule_rows(s: Series, D: pd.DataFrame):
    """The quarter-hour windows of a year whose own fifteen candles are present, with the label and the
    two rules' calls. Returns (rows into D, t, y, reversal_call_up, lead_call_up)."""
    n = len(s.c)
    rows = np.flatnonzero(D.t.values % 900 == 0)
    i = D.i.values[rows]
    keep = i + WINDOW <= n
    rows, i = rows[keep], i[keep]
    bad = np.concatenate([[0], np.cumsum(~s.ok)])
    keep = (bad[i + WINDOW] - bad[i]) == 0
    rows, i = rows[keep], i[keep]
    y = (s.c[i + WINDOW - 1] >= s.o[i]).astype(int)
    reversal_up = D.win1.values[rows] < 0                       # the previous window closed down: call up
    lead_up = s.c[i + 2] >= s.o[i]                              # the close of minute 2 is the lead seen at minute 3
    return rows, D.t.values[rows], y, reversal_up, lead_up


def cell_masks(D: pd.DataFrame) -> dict[str, tuple[np.ndarray, bool]]:
    """The six cells' firing masks on the minute-0 feature frame and the direction each calls."""
    b = base_events(D)
    return {CELLS[0]: (b["5-min move < -3 sd"], True), CELLS[1]: (b["5-min move > +3 sd"], False),
            CELLS[2]: (D.rangepos.values <= 0.02, True), CELLS[3]: (D.rangepos.values >= 0.98, False),
            CELLS[4]: (b["RSI14 < 25"], True), CELLS[5]: (b["RSI14 > 75"], False)}


def year_pools(year: int, end: str) -> list[PoolBlocks] | None:
    yf = year_frame(year, end)
    if yf is None:
        return None
    s, D = yf
    rows, t, y, rev_up, lead_up = rule_rows(s, D)
    wp = Pool(y, month_codes(t))
    sel = np.arange(len(y))
    rules = [Block(RULES[0], wp, sel, rev_up, t), Block(RULES[1], wp, sel, lead_up, t)]
    y15 = labels(s, D.i.values)[CELL_HORIZON]
    valid = ~np.isnan(y15)
    tt = D.t.values[valid]
    cp = Pool(y15[valid].astype(int), month_codes(tt))
    cells = []
    for name, (mask, up) in cell_masks(D).items():
        idx = np.flatnonzero(mask[valid])
        cells.append(Block(name, cp, idx, np.full(len(idx), up), tt[idx]))
    return [PoolBlocks(wp, rules), PoolBlocks(cp, cells)]


@dataclass
class PoolBlocks:
    pool: Pool
    blocks: list[Block]


# ---------------- one year: real statistics and the rotated-label null ----------------

def score_pool(pb: PoolBlocks, rng, runs: int) -> dict[str, dict]:
    """For each block of the pool: the real per-slice deviation, standard error, inside count and overall
    accuracy; and the same statistics on `runs` rotations of the labels within months (shared by the blocks)."""
    out = {}
    for b in pb.blocks:
        P = b.prepare()
        hit = b.hits(pb.pool.y)
        dev, se, n1 = slice_stats(hit, P["M"], P["starts"])
        out[b.name] = {"dev": dev, "se": se, "n1": n1, "acc": float(hit.mean()), "n": len(hit),
                       "null_dev": np.full((runs, len(dev)), np.nan), "null_se": np.full((runs, len(dev)), np.nan)}
    for r in range(runs):
        yr = rotate_within_groups(pb.pool.y, pb.pool.groups, rng)
        for b in pb.blocks:
            P = b.prepare()
            d, e, _ = slice_stats(b.hits(yr), P["M"], P["starts"])
            out[b.name]["null_dev"][r], out[b.name]["null_se"][r] = d, e
    return out


# ---------------- all years: pooling, adjusted p, held ----------------

def summarise(name: str, years: list[int], res: dict[int, dict], names: list[str], fam: np.ndarray, hold_years: int = HOLD_YEARS) -> pd.DataFrame:
    """One row per slice for a block: pooled deviation and error, tau, years held, adjusted p."""
    dev = np.array([res[y]["dev"] for y in years]); se = np.array([res[y]["se"] for y in years])
    n1 = np.array([res[y]["n1"] for y in years])
    nd = np.stack([res[y]["null_dev"] for y in years]); ns = np.stack([res[y]["null_se"] for y in years])      # (years, runs, slices)
    Y, R, S = nd.shape
    scored = np.isfinite(dev) & np.isfinite(se) & (se > 0)
    real = [pool_years(dev[:, s], se[:, s]) for s in range(S)]
    zn = np.full((R, S), np.nan)                                 # pooled |z| in each null run, same pooling as the real estimate
    for s in range(S):
        if real[s] is None:
            continue
        for r in range(R):
            q = pool_years(nd[:, r, s], ns[:, r, s])
            if q is not None:
                zn[r, s] = abs(q["mu"] / q["se_mu"])
    pooled_null_max = family_max(zn, fam)                       # (runs, families)
    with np.errstate(invalid="ignore", divide="ignore"):
        yearly_absz = np.abs(nd / ns)                            # (years, runs, slices)
    by_year = [family_max(yearly_absz[y], fam) for y in range(Y)]
    year_null = [np.concatenate([by_year[y][:, f] for y in range(Y)]) for f in range(len(FAMILIES))]
    rows = []
    for s in range(S):
        f = int(fam[s])
        base = {"block": name, "family": FAMILIES[f], "slice": names[s]}
        if real[s] is None:
            rows.append({**base, "years": int(scored[:, s].sum()), "scored": False})
            continue
        q = real[s]
        mu, se_mu = float(q["mu"]), float(q["se_mu"])
        z = mu / se_mu
        use = scored[:, s]
        held = int((np.sign(dev[use, s]) == np.sign(mu)).sum())
        yz = np.abs(dev[use, s] / se[use, s])
        yp = np.array([adjusted_p(v, year_null[f]) for v in yz])
        rows.append({**base, "scored": True, "years": int(use.sum()), "per_year": float(n1[use, s].mean()), "pooled": mu, "pooled_se": se_mu,
                     "tau": float(q["tau"]), "z": z, "p_adj": adjusted_p(abs(z), pooled_null_max[:, f]),
                     "years_held": held, "years_p05": int((yp <= ALPHA).sum()), "min_year_p": float(yp.min()),
                     "half_width": float(1.96 * np.median(se[use, s])),
                     "z_crit": float(np.quantile(pooled_null_max[:, f], 1 - ALPHA))})
    T = pd.DataFrame(rows)
    T["clears"] = T.scored & (T.p_adj <= ALPHA)
    T["holds"] = T.clears & (T.years_held >= hold_years)
    T["detectable"] = T.z_crit * T.pooled_se
    return T


# ---------------- tables and sentences ----------------

def pts(x: float, signed: bool = True) -> str:
    return f"{x*100:+.1f}" if signed else f"{x*100:.1f}"


def cell_text(r) -> str:
    if not r.scored:
        return "n/a"
    return f"{pts(r.pooled)} ({pts(r.pooled_se, False)}) {int(r.years_held)}/{int(r.years)}, p {r.p_adj:.3f}"


def write_rules(path: Path, acc: pd.DataFrame, T: pd.DataFrame, years: list[int], runs: int):
    with open(path, "w") as f:
        f.write(f"Hour of day and the calendar against the two window rules, {years[0]} to {years[-1]}, all times UTC. A slice's deviation is its accuracy minus the year's accuracy over all windows, in points; pooled over the years by random effects (standard error in brackets), then 'years held' is the number of scored years whose deviation had the pooled sign. The adjusted p compares the slice's pooled |z| with the largest pooled |z| among the slices of its own family on {runs} runs with the labels rotated within each month in every year. A slice-year is scored when at least {MIN_N} windows fall inside and outside it.\n\n")
        f.write("The rules' accuracy over all windows, by year (day-block 95% intervals).\n\n| year | windows | " + " | ".join(RULES) + " |\n|---|---|---|---|\n")
        for y in years:
            a = acc[acc.year == y]
            f.write(f"| {y} | {int(a.n.iloc[0]):,} | " + " | ".join(f"{a[a.rule == r].mean_.iloc[0]*100:.2f}% [{a[a.rule == r].lo.iloc[0]*100:.2f}, {a[a.rule == r].hi.iloc[0]*100:.2f}]" for r in RULES) + " |\n")
        f.write("\nBy family: how many slices there are, the typical size of a slice-year, the 95% half-width of a yearly deviation (median over slices and years), the smallest pooled deviation that would clear the family's 5% adjusted line (median over slices), and how many slices clear it and hold the sign in at least " + f"{HOLD_YEARS} years.\n\n")
        f.write("| rule | family | slices | windows per slice-year (median) | yearly 95% half-width (points) | smallest clearing deviation (points) | clear the null | clear and hold |\n|---|---|---|---|---|---|---|---|\n")
        for r in RULES:
            for fam in FAMILIES:
                g = T[(T.block == r) & (T.family == fam) & T.scored]
                f.write(f"| {r} | {fam} | {len(g)} | {g.per_year.median():,.0f} | {g.half_width.median()*100:.1f} | {g.detectable.median()*100:.1f} | {int(g.clears.sum())} | {int(g.holds.sum())} |\n")
        f.write("\nEvery slice: pooled deviation in points (standard error), years held out of years scored, adjusted p.\n\n")
        f.write("| family | slice | " + " | ".join(RULES) + " |\n|---|---|---|---|\n")
        a, b = (T[T.block == r].reset_index(drop=True) for r in RULES)
        for k in range(len(a)):
            f.write(f"| {a.family[k]} | {a['slice'][k]} | {cell_text(a.iloc[k])} | {cell_text(b.iloc[k])} |\n")


def write_cells(path: Path, base: pd.DataFrame, T: pd.DataFrame, years: list[int], runs: int):
    with open(path, "w") as f:
        f.write(f"The same slices for the six strongest any-minute cells at the {CELL_HORIZON}-minute horizon, {years[0]} to {years[-1]}, all times UTC: every minute is a decision time, the call is the reversal the cell implies (up after a drop, a low or RSI14 below 25; down after the mirror), and a slice is the cell's firings inside it. Deviation, pooling, years held and the family-wise adjusted p are as in calendar_rules.md ({runs} rotated-label runs per year; a slice-year is scored when at least {MIN_N} firings fall inside and outside the slice).\n\n")
        f.write("The cells over all firings: firings per year (mean) and the accuracy of the call, firing-weighted over the years.\n\n| cell | firings per year | accuracy |\n|---|---|---|\n")
        for _, r in base.iterrows():
            f.write(f"| {r.cell} | {r.per_year:,.0f} | {r.accuracy*100:.1f}% |\n")
        f.write("\nBy cell and family: slices scored, how many clear the family's 5% adjusted line and how many of those hold the sign in at least " + f"{HOLD_YEARS} years, the smallest pooled deviation that would clear the line (median over slices), and the slice with the largest pooled |z|.\n\n")
        f.write("| cell | family | slices scored | clear the null | clear and hold | smallest clearing deviation (points) | largest |z| slice | its deviation (points), years held, adjusted p |\n|---|---|---|---|---|---|---|---|\n")
        for c in CELLS:
            for fam in FAMILIES:
                g = T[(T.block == c) & (T.family == fam) & T.scored]
                if g.empty:
                    f.write(f"| {c} | {fam} | 0 | 0 | 0 | n/a | n/a | n/a |\n")
                    continue
                best = g.loc[g.z.abs().idxmax()]
                f.write(f"| {c} | {fam} | {len(g)} | {int(g.clears.sum())} | {int(g.holds.sum())} | {g.detectable.median()*100:.1f} | {best['slice']} | {cell_text(best)} |\n")


def holdout_per_hour(path: Path) -> int | None:
    """Windows per clock hour in the forward log's minute-0 rows (the model version in current use), or None without a log."""
    if not path.exists():
        return None
    L = current_rows(read_log(path))
    L = L[L.minute == 0]
    if L.empty:
        return None
    per_hour = pd.to_datetime(L.time_utc).dt.hour.value_counts()
    return int(per_hour.median())


def expected_range(n_slices: int, sd: float, draws: int = 20000, seed: int = 0) -> float:
    """Mean gap between the best and worst of n_slices independent normal readings with standard deviation sd."""
    x = np.random.default_rng(seed).normal(0, sd, (draws, n_slices))
    return float((x.max(axis=1) - x.min(axis=1)).mean())


def name_list(g: pd.DataFrame, with_block: bool = False) -> str:
    items = [f"{(r.block + ': ') if with_block else ''}{r.family} {r.slice} ({pts(r.pooled)} points, {int(r.years_held)} of {int(r.years)} years, adjusted p {r.p_adj:.3f})" for r in g.itertuples()]
    return "; ".join(items)


def write_sentences(path: Path, R: pd.DataFrame, C: pd.DataFrame, holdout: int | None, runs: int):
    lines = []
    n_slices = int(R[R.block == RULES[0]].scored.sum())
    for r in RULES:
        g = R[(R.block == r) & R.scored]
        clear, hold = g[g.clears], g[g.holds]
        lines.append(f"- **{r}.** Slices clearing their family's 5% adjusted line on the pooled years: {len(clear)} of {len(g)} (in {len(FAMILIES)} families); of those, holding the pooled sign in at least {HOLD_YEARS} years: {len(hold)}" + (f" ({name_list(hold)})." if len(hold) else "."))
        flip = clear[~clear.holds]
        if len(flip):
            lines.append(f"  - Clears the null but not held: {name_list(flip)}.")
        lines.append(f"  - Largest pooled |z| among all {len(g)}: {g.z.abs().max():.2f} ({g.loc[g.z.abs().idxmax()]['family']} {g.loc[g.z.abs().idxmax()]['slice']}); the 5% line is {g.z_crit.min():.2f} to {g.z_crit.max():.2f} depending on the family.")
    for r in RULES:
        g = R[(R.block == r) & R.scored]
        parts = []
        for fam in FAMILIES:
            h = g[g.family == fam]
            parts.append(f"{fam} {h.detectable.median()*100:.1f} (yearly half-width {h.half_width.median()*100:.1f})")
        lines.append(f"- **Detectable deviation, {r}.** A slice's pooled deviation has to reach about this many points to clear its family's 5% line (median over the family's slices; the median 95% half-width of a single year's deviation in brackets): " + "; ".join(parts) + ".")
    gc = C[C.scored]
    clear, hold = gc[gc.clears], gc[gc.holds]
    lines.append(f"- **The six cells.** Cell-and-slice pairs clearing their family's 5% adjusted line on the pooled years: {len(clear)} of {len(gc)}; of those, holding the pooled sign in at least {HOLD_YEARS} years: {len(hold)}" + (f" ({name_list(hold, True)})." if len(hold) else "."))
    flip = clear[~clear.holds]
    if len(flip):
        lines.append(f"  - Clears the null but not held: {name_list(flip, True)}.")
    parts = []
    for fam in FAMILIES:
        h = gc[gc.family == fam]
        parts.append(f"{fam} {h.detectable.median()*100:.1f} (yearly half-width {h.half_width.median()*100:.1f})")
    lines.append("- **Detectable deviation, the cells.** Median over cells and slices, in points: " + "; ".join(parts) + ".")
    exp_false = len(FAMILIES) * ALPHA
    lines.append(f"- **How many clears chance alone would give.** Each rule is tested in {len(FAMILIES)} families at {ALPHA:.0%}, so up to {exp_false:.2f} families per rule would show a clear slice on labels that carry no information; the six cells are {len(CELLS) * len(FAMILIES)} cell-and-family pairs, up to {len(CELLS) * len(FAMILIES) * ALPHA:.1f} such clears.")
    if holdout:
        sd = (0.25 / holdout) ** 0.5
        lines.append(f"- **The forward log's hour table.** With {holdout} windows in each clock hour, one hour's accuracy has a standard error of {sd*100:.1f} points even if nothing depends on the hour, so the 24 hours would differ between the best and the worst by {expected_range(24, sd)*100:.0f} points on average with no hour effect at all.")
    path.write_text("\n".join(lines) + "\n")


# ---------------- run ----------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2018)
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--null-runs", type=int, default=NULL_RUNS)
    a = ap.parse_args()
    t0 = time.time()
    rng = np.random.default_rng(0)
    years = list(range(a.start, int(a.end[:4]) + 1))
    res: dict[str, dict[int, dict]] = {}
    names = fam = None
    acc_rows, per_year_rows = [], []
    for year in years:
        pbs = year_pools(year, a.end)
        if pbs is None:
            continue
        for pb in pbs:
            scored = score_pool(pb, rng, a.null_runs)
            for b in pb.blocks:
                res.setdefault(b.name, {})[year] = scored[b.name]
                P = b.prepare()
                names, fam = P["names"], P["fam"]
                if b.name in RULES:
                    m, lo, hi = block_bootstrap_ci(b.hits(pb.pool.y), b.t)
                    acc_rows.append({"year": year, "rule": b.name, "n": len(b.t), "mean_": m, "lo": lo, "hi": hi})
                for k, nm in enumerate(names):
                    r = scored[b.name]
                    per_year_rows.append({"block": b.name, "year": year, "family": FAMILIES[int(fam[k])], "slice": nm, "inside": float(r["n1"][k]),
                                          "deviation": r["dev"][k], "se": r["se"][k]})
        print(f"{year}: done, {time.time() - t0:.0f} s", flush=True)
    yrs = sorted({y for v in res.values() for y in v})
    T = pd.concat([summarise(b, [y for y in yrs if y in res[b]], res[b], names, fam) for b in list(RULES) + list(CELLS)], ignore_index=True)
    R, C = T[T.block.isin(RULES)], T[T.block.isin(CELLS)]
    base = []
    for c in CELLS:
        ys = sorted(res[c])
        n = np.array([res[c][y]["n"] for y in ys]); acc = np.array([res[c][y]["acc"] for y in ys])
        base.append({"cell": c, "per_year": n.mean(), "accuracy": float((acc * n).sum() / n.sum())})
    A = pd.DataFrame(acc_rows)
    cols = ["block", "family", "slice", "years", "per_year", "pooled", "pooled_se", "tau", "z", "p_adj", "years_held", "years_p05", "min_year_p", "half_width", "z_crit", "detectable", "clears", "holds"]
    R[cols].to_csv(OUT / "calendar_rules.csv", index=False)
    C[cols].to_csv(OUT / "calendar_cells.csv", index=False)
    pd.DataFrame(per_year_rows).to_csv(OUT / "calendar_years.csv", index=False)
    write_rules(OUT / "calendar_rules.md", A, R, yrs, a.null_runs)
    write_cells(OUT / "calendar_cells.md", pd.DataFrame(base), C, yrs, a.null_runs)
    write_sentences(OUT / "calendar_sentences.md", R, C, holdout_per_hour(OUT / "predictions.csv"), a.null_runs)
    print(f"wrote calendar tables in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
