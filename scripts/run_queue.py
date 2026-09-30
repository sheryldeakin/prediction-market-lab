"""Run experiment commands, starting the next one only when fewer than --max-jobs of
this repo's own jobs are running and the machine is not saturated. The gate counts our
own python processes (command line contains "models."), so a browser or a remote
desktop session in the background does not block the queue. Logs CPU and GPU use
while each job runs.

    python scripts/run_queue.py "python -m models.btc_15m.multi_asset" "python -m models.btc_15m.drift"

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


def own_jobs() -> list[str]:
    """Our running experiment processes (one entry per job; the launcher's child is skipped)."""
    found = {}
    for p in psutil.process_iter(["name", "cmdline", "ppid"]):
        try:
            if p.info["name"] and p.info["name"].lower().startswith("python") and any("models." in c for c in (p.info["cmdline"] or [])):
                found[p.pid] = (p.info["ppid"], " ".join(c for c in p.info["cmdline"] if c.startswith("models.")))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return [name for pid, (ppid, name) in found.items() if ppid not in found]


def wait_for_slot(max_jobs: int, max_cpu: float, samples: int = 3, interval: float = 5.0, log=print):
    quiet = 0
    while quiet < samples:
        c = psutil.cpu_percent(interval=interval)
        jobs = own_jobs()
        if len(jobs) < max_jobs and c < max_cpu:
            quiet += 1
        else:
            quiet = 0
            log(f"  waiting: {len(jobs)} own job(s) running {jobs}, cpu {c:.0f}% (limits {max_jobs}, {max_cpu:.0f}%)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-jobs", type=int, default=2, help="our own concurrent jobs; each is capped at ~2 of 8 cores")
    ap.add_argument("--max-cpu", type=float, default=90.0, help="absolute guard on total machine load")
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
        wait_for_slot(a.max_jobs, a.max_cpu, log=log)
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
