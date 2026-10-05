"""Download the public Binance USDT-margined futures history for one symbol into data/binance_futures.

Three series, the same files models/btc_15m/derivatives.py reads: monthly funding-rate files, monthly
1-minute perpetual klines, and daily open-interest and positioning metrics. A file that the archive does
not have (the series start at different dates) returns 404 and is skipped and counted, so the run can
start before any series begins. Files already on disk are not fetched again. Nothing is deleted.

    python scripts/fetch_futures_history.py --start 2019-09 --end 2025-09

Progress goes to stdout, one line per month, with a summary at the end.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from models.btc_15m.derivatives import BASE, CACHE, _fetch  # noqa: E402


def month_days(month: str) -> list[str]:
    p = pd.Period(month, freq="M")
    return [str(d) for d in pd.date_range(p.to_timestamp(), (p + 1).to_timestamp() - pd.Timedelta(days=1)).date]


def fetch_month(month: str, symbol: str) -> dict[str, int]:
    got = {"funding": 0, "klines": 0, "metrics": 0, "missing": 0}
    for key, url, out in (
        ("funding", f"{BASE}/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{month}.zip", CACHE / f"{symbol}-funding-{month}.csv"),
        ("klines", f"{BASE}/monthly/klines/{symbol}/1m/{symbol}-1m-{month}.zip", CACHE / f"{symbol}-perp-1m-{month}.csv"),
    ):
        if _fetch(url, out) is None:
            got["missing"] += 1
        else:
            got[key] += 1
    for d in month_days(month):
        out = CACHE / f"{symbol}-metrics-{d}.csv"
        if _fetch(f"{BASE}/daily/metrics/{symbol}/{symbol}-metrics-{d}.zip", out) is None:
            got["missing"] += 1
        else:
            got["metrics"] += 1
    return got


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--start", required=True, help="first month, YYYY-MM")
    ap.add_argument("--end", required=True, help="last month, YYYY-MM")
    ap.add_argument("--symbol", default="BTCUSDT")
    a = ap.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    months = [str(p) for p in pd.period_range(a.start, a.end, freq="M")]
    totals = {"funding": 0, "klines": 0, "metrics": 0, "missing": 0}
    t0 = time.time()
    for m in months:
        got = fetch_month(m, a.symbol)
        for k, v in got.items():
            totals[k] += v
        print(f"{m}: funding {got['funding']} klines {got['klines']} metrics {got['metrics']} missing {got['missing']} ({time.time() - t0:.0f}s)", flush=True)
    print(f"done: {len(months)} months, funding {totals['funding']} klines {totals['klines']} metrics {totals['metrics']} missing {totals['missing']}, {time.time() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
