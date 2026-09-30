"""Run experiment commands one at a time, starting each only when the CPU has been
below a threshold for a few samples. Logs CPU and GPU use while each job runs.

    python scripts/run_queue.py --max-cpu 60 -- "python -m models.btc_15m.multi_asset" "python -m models.btc_15m.drift"

Each command's output goes to logs/<module>.log. The queue itself logs to logs/queue.log.
"""
from __future__ import annotations

import argparse
import datetime as dt
import shlex
import subprocess
import sys
import time
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "logs"


def gpu_util() -> str:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=5).stdout.strip()
        u, m = out.split(",")
        return f"gpu {u.strip()}% {int(m):,} MiB"
    except Exception:
        return "gpu n/a"


def wait_for_cpu(max_cpu: float, samples: int = 3, interval: float = 5.0, log=print):
    quiet = 0
    while quiet < samples:
        c = psutil.cpu_percent(interval=interval)
        if c < max_cpu:
            quiet += 1
        else:
            quiet = 0
            log(f"  waiting: cpu {c:.0f}% > {max_cpu:.0f}%")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-cpu", type=float, default=60.0)
    ap.add_argument("commands", nargs="+")
    a = ap.parse_args()
    LOGS.mkdir(exist_ok=True)
    qlog = open(LOGS / "queue.log", "a")

    def log(msg):
        line = f"{dt.datetime.now():%H:%M:%S} {msg}"
        print(line, flush=True)
        qlog.write(line + "\n")
        qlog.flush()

    py = str(ROOT / ".venv" / "Scripts" / "python.exe")
    for cmd in a.commands:
        parts = shlex.split(cmd)
        if parts[0] == "python":
            parts[0] = py
        name = next((p for p in parts if p.startswith("models.") or p.endswith(".py")), parts[-1]).split(".")[-1].replace(".py", "")
        wait_for_cpu(a.max_cpu, log=log)
        log(f"start {cmd}")
        out = open(LOGS / f"{name}.log", "w")
        proc = subprocess.Popen(parts, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT)
        t0 = time.time()
        while proc.poll() is None:
            time.sleep(30)
            log(f"  {name}: cpu {psutil.cpu_percent(interval=1):.0f}%, {gpu_util()}, {int(time.time()-t0)}s")
        log(f"done {cmd} (exit {proc.returncode}, {int(time.time()-t0)}s)")
    qlog.close()


if __name__ == "__main__":
    main()
