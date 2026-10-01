"""Does the boundary reversal replicate on other venues and other coins?

  venues     one-minute BTC-USD candles from Coinbase and Bitstamp (free public APIs, no
             key; Kraken's public API returns only the last 720 candles, so it is not
             used). Each venue's own 15-minute windows, labelled by its own prints. If
             the reversal comes from Binance's boundary print noise it should be weaker
             or absent elsewhere; if it is a property of Bitcoin around the quarter hour
             it should replicate. These candles carry no taker-side volume, so the forest
             uses price features only, and so does a Binance price-only forest on the
             same windows for comparison.
  coins      transfer in time order: for each test month, a forest trained on BTC's
             earlier months (Binance) scores ETH and SOL that month; compared with each
             coin's own-history forest and its prev-window baseline.

Candles are cached to data/venues/{venue}-BTCUSD-1m-{YYYY-MM}.parquet.

    python -m models.btc_15m.venues --start 2025-10 --end 2026-08
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from models.btc_15m.data import load
from models.btc_15m.evaluate import ALL, add_baseline_columns, make_model, walk_forward
from models.btc_15m.features import PRICE_FEATURES, Series, dataset
from models.btc_15m.stats import block_bootstrap_ci, paired_difference_ci

warnings.filterwarnings("ignore")
OUT = Path("results/btc_15m")
CACHE = Path("data/venues")
MAX_FILL = 3          # minutes without a candle that are filled with the last close (no trades); longer gaps are outages


def _get(url: str, tries: int = 5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "prediction-market-lab/1.0"})
            return json.loads(urllib.request.urlopen(req, timeout=30).read())
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 ** i)


def fetch_coinbase(a: int, b: int) -> pd.DataFrame:
    rows = []
    t = a
    while t < b:
        e = min(t + 300 * 60, b)
        iso = lambda x: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(x))
        data = _get(f"https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=60&start={iso(t)}&end={iso(e - 60)}")
        rows += [{"t": int(r[0]), "low": r[1], "high": r[2], "open": r[3], "close": r[4], "volume": r[5]} for r in data]
        t = e
        time.sleep(0.15)
    return pd.DataFrame(rows)


def fetch_bitstamp(a: int, b: int) -> pd.DataFrame:
    rows = []
    t = a
    while t < b:
        data = _get(f"https://www.bitstamp.net/api/v2/ohlc/btcusd/?step=60&limit=1000&start={t}")
        got = [{"t": int(r["timestamp"]), **{k: float(r[k]) for k in ("open", "high", "low", "close", "volume")}} for r in data["data"]["ohlc"]]
        got = [r for r in got if a <= r["t"] < b]
        if not got:
            break
        rows += got
        t = max(r["t"] for r in got) + 60
        time.sleep(0.15)
    return pd.DataFrame(rows)


FETCH = {"coinbase": fetch_coinbase, "bitstamp": fetch_bitstamp}


def to_grid(df: pd.DataFrame, a: int, b: int) -> pd.DataFrame:
    """Candles on a full minute grid in the layout Series expects. Missing minutes up to
    MAX_FILL long take the last close with zero volume (no trades); longer gaps are
    marked not ok. No taker-side data: taker_buy is half the volume, trades is 1."""
    grid = pd.DataFrame({"t": np.arange(a, b, 60)})
    d = grid.merge(df.drop_duplicates("t"), on="t", how="left")
    have = d.close.notna()
    run = (~have).groupby(have.cumsum()).cumsum()
    d["close"] = d.close.ffill()
    for c in ("open", "high", "low"):
        d[c] = d[c].fillna(d.close)
    d["volume"] = d.volume.fillna(0.0)
    d["ok"] = (run <= MAX_FILL) & d.close.notna()
    d["trades"] = 1.0
    d["taker_buy"] = d.volume / 2
    return d


def load_venue(venue: str, start: str, end: str) -> pd.DataFrame:
    CACHE.mkdir(parents=True, exist_ok=True)
    parts = []
    for p in pd.period_range(start, end, freq="M"):
        f = CACHE / f"{venue}-BTCUSD-1m-{p}.parquet"
        a = int(p.start_time.timestamp()); b = int((p + 1).start_time.timestamp())
        if not f.exists():
            raw = FETCH[venue](a, b)
            to_grid(raw, a, b).to_parquet(f, index=False)
            print(f"fetched {venue} {p}: {len(raw)} candles", flush=True)
        parts.append(pd.read_parquet(f))
    return pd.concat(parts, ignore_index=True)


def venue_rows(name: str, s: Series, binance: pd.DataFrame | None) -> list:
    D = add_baseline_columns(dataset(s, 0), 0)
    if binance is not None:
        D = D[D.t.isin(binance.t)].reset_index(drop=True)          # the same windows on both venues
    out = []
    preds = {}
    for model, cols, kind in (("prev-window", ["prev_up"], "bitrate"), ("forest, price features", PRICE_FEATURES, "forest")):
        pred, y, _, t = walk_forward(D, cols, kind)
        preds[model] = (pred, y, t)
    hb = ((preds["prev-window"][0] > 0.5) == preds["prev-window"][1]).astype(float)
    for model, (pred, y, t) in preds.items():
        h = ((pred > 0.5) == y).astype(float)
        m, lo, hi = block_bootstrap_ci(h, t)
        vs = "" if model == "prev-window" else "{:+.2f} [{:+.2f}, {:+.2f}]".format(*[x * 100 for x in paired_difference_ci(h, hb, t)])
        out.append([name, model, len(y), f"{y.mean()*100:.1f}%", f"{m*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", vs])
    return out, D


def transfer_rows(start: str, end: str) -> list:
    btc = add_baseline_columns(dataset(Series(load(start, end, "BTCUSDT")), 0), 0)
    rows = []
    for sym in ("ETHUSDT", "SOLUSDT"):
        D = add_baseline_columns(dataset(Series(load(start, end, sym)), 0), 0)
        month = pd.to_datetime(D.t, unit="s").dt.to_period("M")
        bmonth = pd.to_datetime(btc.t, unit="s").dt.to_period("M")
        pred = np.full(len(D), np.nan)
        for m in sorted(month.unique())[3:]:
            model = make_model("forest").fit(btc.loc[(bmonth < m).values, ALL], btc.y[(bmonth < m).values])
            te = (month == m).values
            pred[te] = model.predict_proba(D.loc[te, ALL])[:, 1]
        keep = ~np.isnan(pred)
        po, yo, _, to = walk_forward(D, ALL, "forest")
        pb, _, _, _ = walk_forward(D, ["prev_up"], "bitrate")
        assert np.array_equal(to, D.t.values[keep])
        y = D.y.values[keep]
        hb = ((pb > 0.5) == y).astype(float)
        for name, p in (("prev-window (own)", pb), ("forest, own history", po), ("forest trained on BTC", pred[keep])):
            h = ((p > 0.5) == y).astype(float)
            m_, lo, hi = block_bootstrap_ci(h, to)
            vs = "" if name.startswith("prev") else "{:+.2f} [{:+.2f}, {:+.2f}]".format(*[x * 100 for x in paired_difference_ci(h, hb, to)])
            rows.append([sym[:-4], name, len(y), f"{m_*100:.2f}% [{lo*100:.2f}, {hi*100:.2f}]", vs])
            print("transfer", rows[-1], flush=True)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10")
    ap.add_argument("--end", default="2026-08")
    a = ap.parse_args()
    binance_rows, B = venue_rows("Binance BTC-USDT", Series(load(a.start, a.end)), None)
    rows = list(binance_rows)
    for venue in ("coinbase", "bitstamp"):
        v_rows, _ = venue_rows(f"{venue.title()} BTC-USD", Series(load_venue(venue, a.start, a.end)), B)
        rows += v_rows
        for r in v_rows:
            print("venue", r, flush=True)
    trows = transfer_rows(a.start, a.end)
    with open(OUT / "venues.md", "w") as f:
        f.write(f"The boundary reversal on other venues, {a.start} to {a.end}, minute 0, walk-forward by month. Each venue's windows are labelled by its own candles; Coinbase and Bitstamp are restricted to windows Binance also has. Coinbase and Bitstamp candles carry no taker-side volume, so the forest uses price features only. Last column: minus prev-window on the same windows, day-block 95% interval.\n\n")
        f.write("| venue | model | windows | share up | accuracy [95% CI] | minus prev-window |\n|---|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
        f.write("\nTransfer in time order: a forest trained on Bitcoin's earlier months (Binance, price + flow features) scores ETH and SOL each test month, against each coin's own-history forest and its prev-window baseline. Last column: minus prev-window on the same windows.\n\n")
        f.write("| coin | model | windows | accuracy [95% CI] | minus prev-window |\n|---|---|---|---|---|\n")
        for r in trows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")
    print("wrote venues.md")


if __name__ == "__main__":
    main()
