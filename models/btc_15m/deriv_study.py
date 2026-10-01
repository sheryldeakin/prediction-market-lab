"""Do inputs from the perpetual-futures market help?

  ablation   walk-forward by month, forest and XGBoost, price + flow + indicators with
             and without the twelve derivative features (basis, funding, perp flow,
             open interest, positioning); accuracy difference with day-block intervals
  events     the spike events of study 16 split by what open interest did over the same
             minutes: a spike with open interest falling (positions being closed or
             liquidated) versus rising (positions being opened)
  forward    both models trained through the cutoff month and scored on the forward
             period (September 2026 onward), never seen by the search
  importance permutation importance of each derivative feature on the held-out months

    python -m models.btc_15m.deriv_study --start 2025-10 --end 2026-08 --forward-through 2026-09-29
"""
from __future__ import annotations

import argparse
import datetime as dt
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss, roc_auc_score

from models.btc_15m.data import load, load_days
from models.btc_15m.derivatives import DERIV_FEATURES, build
from models.btc_15m.diagnostics import permutation_importance
from models.btc_15m.evaluate import make_model, walk_forward
from models.btc_15m.features import FLOW_FEATURES, PRICE_FEATURES, Series, dataset
from models.btc_15m.indicators import INDICATOR_FEATURES
from models.btc_15m.stats import block_bootstrap_ci, paired_difference_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
BASE = PRICE_FEATURES + FLOW_FEATURES + INDICATOR_FEATURES
ALL = BASE + DERIV_FEATURES


def attach(s: Series, months, days):
    s.extra = build(s.t.astype(np.int64), s.c, months, days)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    ap.add_argument("--forward-through", default=str(dt.datetime.utcnow().date() - dt.timedelta(days=1)))
    ap.add_argument("--minutes", default="0,3")
    a = ap.parse_args()
    months = [str(p) for p in pd.period_range(a.start, a.end, freq="M")]
    s = attach(Series(load(a.start, a.end)), months, [])
    first = (pd.Period(a.end, freq="M") + 1).to_timestamp().date()
    last = dt.date.fromisoformat(a.forward_through)
    days = [str(first + dt.timedelta(days=i)) for i in range((last - first).days + 1)]
    fs = attach(Series(load_days([a.end], days)), [a.end], days)
    start_t = int(pd.Timestamp(first).timestamp())

    abl_rows, ev_rows, fwd_rows, imp_rows = [], [], [], []
    for k in [int(x) for x in a.minutes.split(",")]:
        D = dataset(s, k)
        F = dataset(fs, k, cache=False)
        F = F[F.t >= start_t].reset_index(drop=True)
        y, t = D.y.values, D.t.values
        # ---- ablation ----
        for kind in ("forest", "xgb"):
            pb, yb, _, tb = walk_forward(D, BASE, kind)
            pa, ya, _, ta = walk_forward(D, ALL, kind)
            hb, ha = ((pb > 0.5) == yb).astype(float), ((pa > 0.5) == ya).astype(float)
            d, lo, hi = paired_difference_ci(ha, hb, tb)
            for name, p, h in (("without derivatives", pb, hb), ("with derivatives", pa, ha)):
                m, mlo, mhi = block_bootstrap_ci(h, tb)
                abl_rows.append([k, kind, name, len(yb), f"{m*100:.2f}% [{mlo*100:.2f}, {mhi*100:.2f}]", f"{roc_auc_score(yb, p):.3f}", f"{log_loss(yb, np.clip(p, 1e-6, 1-1e-6)):.4f}",
                                 f"{d*100:+.2f} [{lo*100:+.2f}, {hi*100:+.2f}]" if name.startswith("with") else "reference"])
                print(abl_rows[-1], flush=True)
        # ---- forward ----
        for kind in ("forest", "xgb"):
            for name, cols in (("without derivatives", BASE), ("with derivatives", ALL)):
                model = make_model(kind).fit(D[cols], y)
                p = model.predict_proba(F[cols])[:, 1]
                h = ((p > 0.5) == F.y.values).astype(float)
                m, lo, hi = block_bootstrap_ci(h, F.t.values)
                fwd_rows.append([k, kind, name, len(F), f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]"])
                print(fwd_rows[-1], flush=True)
        # ---- events split by open interest ----
        if k == 0:
            v = D.vol60.values + 1e-9
            base_rate = y.mean()
            spikes = {"5-min move > +2 sd": D.ret5.values > 2 * v * np.sqrt(5), "5-min move < -2 sd": D.ret5.values < -2 * v * np.sqrt(5),
                      "15-min move > +2 sd": D.ret15.values > 2 * v * np.sqrt(15), "15-min move < -2 sd": D.ret15.values < -2 * v * np.sqrt(15),
                      "price at 4h high": D.rangepos.values >= 0.98, "price at 4h low": D.rangepos.values <= 0.02}
            for name, m in spikes.items():
                for cond, mm in (("open interest fell (doi15 < -0.1%)", m & (D.doi15.values < -0.1)), ("open interest flat", m & (D.doi15.values.__abs__() <= 0.1)), ("open interest rose (doi15 > +0.1%)", m & (D.doi15.values > 0.1))):
                    if mm.sum() < 50:
                        ev_rows.append([name, cond, int(mm.sum()), "", ""]); continue
                    mu, lo, hi = block_bootstrap_ci(y[mm].astype(float), t[mm])
                    ev_rows.append([name, cond, int(mm.sum()), f"{mu*100:.1f}% [{lo*100:.1f}, {hi*100:.1f}]", f"{(mu-base_rate)*100:+.1f}"])
                    print(ev_rows[-1], flush=True)
        # ---- importance of the derivative features on held-out months ----
        month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
        agg = {c: [] for c in DERIV_FEATURES}
        for mth in sorted(month.unique())[3:]:
            tr, te = (month < mth).values, (month == mth).values
            model = make_model("xgb").fit(D.loc[tr, ALL], y[tr])
            pi = permutation_importance(model, D[te], y[te], ALL)
            for c in DERIV_FEATURES:
                agg[c].append(pi[c])
        for c in DERIV_FEATURES:
            imp_rows.append([k, c, f"{np.mean(agg[c])*100:+.2f}", f"{np.min(agg[c])*100:+.2f} to {np.max(agg[c])*100:+.2f}"])

    with open(OUT / "derivatives.md", "w") as f:
        f.write("Perpetual-futures inputs (basis, its change, perp taker flow, perp volume ratio, funding rate, open-interest change over 15 and 60 minutes, top-trader and all-account long/short ratios, taker buy/sell ratio) added to price + flow + indicators. Walk-forward by month; last column is accuracy with minus without, on the same windows, day-block 95% interval.\n\n")
        f.write("| minute | model | features | n | accuracy [95% CI] | AUC | log loss | with minus without |\n|---|---|---|---|---|---|---|---|\n")
        for r in abl_rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        f.write(f"\nForward check: models trained on {a.start} to {a.end}, scored on {first} to {last}.\n\n| minute | model | features | n | accuracy [95% CI] |\n|---|---|---|---|---|\n")
        for r in fwd_rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        f.write("\nSpike events split by what open interest did over the same 15 minutes (minute 0). Falling open interest during a move means positions were closed or liquidated; rising means positions were opened.\n\n| event | open interest | fires | up-rate [95% CI] | vs base |\n|---|---|---|---|---|\n")
        for r in ev_rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        f.write("\nPermutation importance of each derivative feature on the held-out months (accuracy drop in points when shuffled; mean over months and range).\n\n| minute | feature | mean | range |\n|---|---|---|---|\n")
        for r in imp_rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print("wrote derivatives.md")


if __name__ == "__main__":
    main()
