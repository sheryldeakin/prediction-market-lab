"""How fast are the cells fading, and when would a straight line reach zero?

The eras table says the strongest cells have roughly halved since 2018-19. This turns that
into a forecast with a record. For each of the strongest cells (held every year, both
libraries), the yearly deviations from horizons_cells.csv and price_action_cells.csv are
fitted with a straight line in the year, weighted by the inverse squared standard error:

  held-out record   for each test year Y from FIRST_TEST, the line fitted on years before Y
                    forecasts Y; the error is compared with the naive forecast "same as last
                    year" and with "the mean of all earlier years"
  forecast          the line fitted on all years gives a slope (points per year), a forecast
                    for FORECAST_YEAR with a 95% prediction interval, and the year at which
                    the line reaches zero (the cell's expiry if the trend continued)

A straight line is the simplest honest trend; it is not a claim that the fading is linear.
The record column says whether it forecasts better than doing nothing.

    python -m models.btc_15m.cells_decay_forecast
"""
from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
TOP = 16
FIRST_TEST = 2022
FORECAST_YEAR = 2027


def weighted_line(x: np.ndarray, y: np.ndarray, se: np.ndarray) -> tuple[float, float, np.ndarray]:
    """Weighted least squares y = a + b x with weights 1/se^2. Returns (a, b, covariance of (a, b))."""
    w = 1.0 / np.maximum(se, 1e-9) ** 2
    X = np.column_stack([np.ones_like(x, dtype=float), x.astype(float)])
    XtW = X.T * w
    cov = np.linalg.inv(XtW @ X)
    beta = cov @ XtW @ y
    resid = y - X @ beta
    dof = max(len(x) - 2, 1)
    scale = max((w * resid ** 2).sum() / dof, 1.0)       # inflate the covariance when the points scatter more than their errors say
    return float(beta[0]), float(beta[1]), cov * scale


def predict(a: float, b: float, cov: np.ndarray, x: float, dof: int) -> tuple[float, float, float]:
    """Point forecast and 95% prediction interval (parameter uncertainty only) at x."""
    v = np.array([1.0, x])
    mean = a + b * x
    se = float(np.sqrt(v @ cov @ v))
    tcrit = stats.t.ppf(0.975, max(dof, 1))
    return mean, mean - tcrit * se, mean + tcrit * se


def record(years: np.ndarray, dev: np.ndarray, se: np.ndarray, first_test: int = FIRST_TEST) -> dict:
    """Mean absolute forecast error of the line, 'same as last year' and 'mean so far' over the test years."""
    err_line, err_last, err_mean = [], [], []
    for Y in years[years >= first_test]:
        tr = years < Y
        if tr.sum() < 3:
            continue
        a, b, _ = weighted_line(years[tr], dev[tr], se[tr])
        actual = dev[years == Y][0]
        err_line.append(abs(a + b * Y - actual))
        err_last.append(abs(dev[tr][-1] - actual))
        err_mean.append(abs(dev[tr].mean() - actual))
    n = len(err_line)
    return {"tests": n, "mae_line": float(np.mean(err_line)) if n else np.nan, "mae_last": float(np.mean(err_last)) if n else np.nan,
            "mae_mean": float(np.mean(err_mean)) if n else np.nan}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=TOP)
    a = ap.parse_args()
    H = pd.read_csv(OUT / "horizons_cells.csv"); H["library"] = "lib"
    P = pd.read_csv(OUT / "price_action_cells.csv"); P["library"] = "pa"
    cells = pd.concat([H, P], ignore_index=True)
    # strongest cells held every year, one horizon per pattern (its largest pooled deviation)
    keys = ["library", "pattern", "horizon"]
    cells["w_diff"] = cells["diff"] * cells.fires
    S = cells.groupby(keys).agg(years=("year", "size"), wsum=("w_diff", "sum"), fires_all=("fires", "sum")).reset_index()
    S["pooled"] = S.wsum / S.fires_all
    cells = cells.merge(S[keys + ["pooled"]], on=keys)
    cells["same"] = np.sign(cells["diff"]) == np.sign(cells.pooled)
    S = S.merge(cells.groupby(keys)["same"].sum().reset_index(name="held"), on=keys)
    n_years = cells.year.nunique()
    S = S[(S.years == n_years) & (S.held == n_years)].sort_values("pooled", key=np.abs, ascending=False)
    S = S.drop_duplicates(["library", "pattern"]).head(a.top)
    rows = []
    for r in S.itertuples():
        d = cells[(cells.library == r.library) & (cells.pattern == r.pattern) & (cells.horizon == r.horizon)].sort_values("year")
        years, dev, se = d.year.values.astype(float), d["diff"].values, d.se.values
        sign = np.sign(r.pooled)
        a_, b_, cov = weighted_line(years, dev, se)
        mean, lo, hi = predict(a_, b_, cov, FORECAST_YEAR, len(years) - 2)
        zero_year = -a_ / b_ if b_ * sign < 0 else np.inf          # only a trend toward zero has an expiry
        rec = record(years, dev, se)
        rows.append({"library": r.library, "pattern": r.pattern, "horizon": int(r.horizon), "first": dev[0], "last": dev[-1],
                     "slope": b_, "forecast": mean, "forecast_lo": lo, "forecast_hi": hi, "zero_year": zero_year, **rec})
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "cells_decay_forecast.csv", index=False)
    with open(OUT / "cells_decay_forecast.md", "w") as f:
        f.write(f"Fading as a forecast: the {len(R)} strongest cells held in every year (both libraries, one horizon per event), their yearly deviation fitted with a straight line in the year (weights 1/se^2). Slope in points per year; the {FORECAST_YEAR} forecast with a 95% interval from the fitted line's uncertainty; the year the line reaches zero if the trend continued ('none' when the trend points away from zero). Record: mean absolute error, in points, of forecasting each year from {FIRST_TEST} with the line fitted on earlier years, against 'same as last year' and 'mean of earlier years'.\n\n")
        f.write(f"| library | pattern | horizon (min) | {int(cells.year.min())} | {int(cells.year.max())} | slope (points/year) | {FORECAST_YEAR} forecast [95%] | line reaches zero | record: line | same as last year | mean so far |\n|---|---|---|---|---|---|---|---|---|---|---|\n")
        for r in R.itertuples():
            zero = "none" if not np.isfinite(r.zero_year) else f"{r.zero_year:.0f}"
            f.write(f"| {r.library} | {r.pattern} | {r.horizon} | {r.first*100:+.1f} | {r.last*100:+.1f} | {r.slope*100:+.2f} | {r.forecast*100:+.1f} [{r.forecast_lo*100:+.1f}, {r.forecast_hi*100:+.1f}] | {zero} | {r.mae_line*100:.1f} | {r.mae_last*100:.1f} | {r.mae_mean*100:.1f} |\n")
        fin = R[np.isfinite(R.zero_year)]
        f.write(f"\nAcross the {len(R)} cells: the line beats 'same as last year' in {int((R.mae_line < R.mae_last).sum())} and 'mean so far' in {int((R.mae_line < R.mae_mean).sum())}; {len(fin)} trend toward zero, reaching it between {fin.zero_year.min():.0f} and {fin.zero_year.max():.0f} (median {fin.zero_year.median():.0f}); the {FORECAST_YEAR} forecasts are {R.forecast.abs().min()*100:.1f} to {R.forecast.abs().max()*100:.1f} points in size against {R['last'].abs().min()*100:.1f} to {R['last'].abs().max()*100:.1f} in {int(cells.year.max())}.\n")
    print("wrote cells_decay_forecast.md")


if __name__ == "__main__":
    main()
