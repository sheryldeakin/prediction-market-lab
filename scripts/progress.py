"""Print the study checklist with what has finished, from the queue logs.

    python scripts/progress.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from run_queue import own_jobs  # noqa: E402

# (label, module name as it appears in the queue logs, result file)
PLAN = [
    ("Conditional direction tables, 2018 to 2026", "horizons", "horizons.md"),
    ("Eras and selection spans", "horizons_spans", "horizons_spans.md"),
    ("The cells under VWAP labels", "horizons_vwap", "horizons_vwap.md"),
    ("Regimes: dating, HMM states, fingerprints", "regimes", "regimes.md"),
    ("Each cell as a meta-analysis", "horizons_shrink", "horizons_shrink.md"),
    ("Direction with magnitude", "horizons_barrier", "horizons_barrier.md"),
    ("HMM predictors (round one)", "hmm_models", "hmm_models.md"),
    ("Price-action library, pass 1 (67 events)", "price_action", "price_action.md"),
    ("Price-action library, pass 2 (79 events, with rejections and acceptances)", "price_action#2", "price_action.md"),
    ("Within-window table: next-5-minute call against the close call, per pattern and minute", "within_window", "within_window.md"),
    ("HMM round two: states as features, model per state, richer states", "hmm_models2", "hmm_models2.md"),
    ("Full ETH, SOL, DOGE candle histories", "data_history_coins", None),
    ("Full futures history from 2019", "data_history_futures", None),
    ("Full Coinbase and Bitstamp histories", "data_history_venues", None),
    ("Live view on the tracking page (product)", "tracking_page", None),
]


def main():
    text = "\n".join(p.read_text(errors="ignore") for p in sorted((ROOT / "logs").glob("queue_*.log")))
    running = own_jobs()
    seen_running = set()
    for label, module, result in PLAN:
        base, _, nth = module.partition("#")
        done_lines = re.findall(rf"\d\d:\d\d:\d\d done .*models\.btc_15m\.{base}(?: |$)", text, flags=re.M)
        n_needed = int(nth) if nth else 1
        ran_directly = not nth and result is not None and (ROOT / "results" / "btc_15m" / result).exists() and not done_lines
        is_running = any(base in j for j in running) and base not in seen_running and len(done_lines) == n_needed - 1
        if len(done_lines) >= n_needed or ran_directly:
            mark = "[x]"
        elif is_running:
            mark = "[~] running"
            seen_running.add(base)
        else:
            mark = "[ ]"
        print(f"{mark} {label}" + (f"  -> results/btc_15m/{result}" if mark == "[x]" else ""))


if __name__ == "__main__":
    main()
