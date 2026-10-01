"""Download and reduce Binance aggTrades month by month, oldest first, so each month's
first day can use the previous month's large-trade cutoff. Skips months already reduced.

    python scripts/fetch_ticks_history.py --start 2017-08 --end 2025-09
"""
import argparse
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models.btc_15m.ticks import reduce_month, tick_path  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--start", default="2017-08")
ap.add_argument("--end", default="2025-09")
a = ap.parse_args()
for p in pd.period_range(a.start, a.end, freq="M"):
    m = str(p)
    if tick_path(m).exists():
        print(m, "already reduced", flush=True)
        continue
    t0 = time.time()
    for attempt in range(3):
        try:
            out = reduce_month(m)
            break
        except Exception as e:                       # network hiccups: wait and retry
            print(m, "retry after", repr(e)[:80], flush=True)
            time.sleep(60 * (attempt + 1))
    else:
        print(m, "FAILED", flush=True)
        continue
    print(m, out, f"{time.time() - t0:.0f}s", flush=True)
