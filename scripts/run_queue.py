"""Run experiment commands one after another, admitting each only when the machine has
room for it. Two profiles:

  quiet   (default) for when the owner is working: at most --max-jobs of our own jobs,
          and a job starts only after three samples five seconds apart all show idle CPU
          of at least 25%, at least 8 GB of free memory, GPU busy under 50% and at least
          8 GB of free GPU memory. Jobs run at below-normal priority and are told to keep
          the GPU under half (LAB_GPU_FRACTION=0.25, LAB_GPU_TARGET=50).
  full    for overnight or an idle machine: admission only requires our own job count;
          normal priority; jobs may use the whole GPU.

Our own jobs are python processes whose command line has a "models." module; the
browser, the remote desktop and other programs are not counted, but their load still
shows in the idle-CPU and memory checks in quiet mode. Logs CPU, memory and GPU every
30 seconds while a job runs.

    python scripts/run_queue.py "python -m models.btc_15m.rules" "python -m models.btc_15m.diagnostics"
    python scripts/run_queue.py --profile full "python -m models.btc_15m.sequence2"
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "logs"
QUIET = {"min_idle_cpu": 25.0, "min_free_gb": 8.0, "max_gpu_util": 50.0, "min_free_gpu_gb": 8.0}


def gpu() -> tuple[float, float, float]:
    """(utilisation %, used GiB, total GiB); zeros when there is no GPU."""
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=5).stdout.strip().split(",")
        return float(out[0]), float(out[1]) / 1024, float(out[2]) / 1024
    except Exception:
        return 0.0, 0.0, 0.0


def own_jobs() -> list[str]:
    """Our running experiment processes (one entry per job; the launcher's child is skipped)."""
    found = {}
    for p in psutil.process_iter(["name", "cmdline", "ppid"]):
        try:
            cmd = p.info["cmdline"] or []
            if p.info["name"] and p.info["name"].lower().startswith("python") and any(c.startswith("models.") for c in cmd) \
                    and not any("run_queue" in c for c in cmd):
                found[p.pid] = (p.info["ppid"], " ".join(c for c in cmd if c.startswith("models.")))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return [name for pid, (ppid, name) in found.items() if ppid not in found]


def room(profile: str, max_jobs: int) -> tuple[bool, str]:
    jobs = own_jobs()
    cpu = psutil.cpu_percent(interval=5)
    free_gb = psutil.virtual_memory().available / 1e9
    util, used, total = gpu()
    state = f"{len(jobs)} own job(s) {jobs}, idle cpu {100-cpu:.0f}%, free mem {free_gb:.1f} GB, gpu {util:.0f}% busy, {total-used:.1f} GB free"
    if len(jobs) >= max_jobs:
        return False, state
    if profile == "full":
        return True, state
    q = QUIET
    ok = (100 - cpu) >= q["min_idle_cpu"] and free_gb >= q["min_free_gb"] and util <= q["max_gpu_util"] and (total - used) >= q["min_free_gpu_gb"]
    return ok, state


def wait_for_room(profile: str, max_jobs: int, log, samples: int = 3):
    quiet = 0
    while quiet < samples:
        ok, state = room(profile, max_jobs)
        if ok:
            quiet += 1
        else:
            quiet = 0
            log(f"  waiting: {state}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=["quiet", "full"], default="quiet")
    ap.add_argument("--max-jobs", type=int, default=2)
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
    env = dict(os.environ)
    if a.profile == "quiet":
        env.update({"LAB_GPU_FRACTION": "0.25", "LAB_GPU_TARGET": "50"})
    for cmd in a.commands:
        parts = shlex.split(cmd)
        if parts[0] == "python":
            parts[0] = py
        name = next((p for p in parts if p.startswith("models.") or p.endswith(".py")), parts[-1]).split(".")[-1].replace(".py", "")
        wait_for_room(a.profile, a.max_jobs, log)
        log(f"start [{a.profile}] {cmd}")
        out = open(LOGS / f"{name}.log", "w")
        flags = subprocess.BELOW_NORMAL_PRIORITY_CLASS if (a.profile == "quiet" and sys.platform == "win32") else 0
        proc = subprocess.Popen(parts, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, env=env, creationflags=flags)
        t0 = time.time()
        while proc.poll() is None:
            time.sleep(30)
            util, used, total = gpu()
            log(f"  {name}: cpu {psutil.cpu_percent(interval=1):.0f}%, mem {psutil.virtual_memory().percent:.0f}%, gpu {util:.0f}% {used:.1f} GB, {int(time.time()-t0)}s")
        log(f"done {cmd} (exit {proc.returncode}, {int(time.time()-t0)}s)")
    qlog.close()


if __name__ == "__main__":
    main()
