"""Overnight runner. Reads queue/night.txt (one experiment command per line, '#' for
comments), runs each through run_queue.py with the full profile, and removes a line
once its job has finished. Meant for a scheduler at a quiet hour with pythonw.exe;
output goes to logs/night.txt.

    .venv\\Scripts\\pythonw.exe scripts\\run_night_queue.py
"""
import datetime as dt
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
(ROOT / "logs").mkdir(exist_ok=True)
(ROOT / "queue").mkdir(exist_ok=True)
QUEUE = ROOT / "queue" / "night.txt"
log = open(ROOT / "logs" / "night.txt", "a")
sys.stdout = sys.stderr = log
print(f"\n=== {dt.datetime.now():%Y-%m-%d %H:%M} ===")
lines = [l.strip() for l in QUEUE.read_text().splitlines()] if QUEUE.exists() else []
todo = [l for l in lines if l and not l.startswith("#")]
if not todo:
    print("nothing queued")
for cmd in todo:
    print(f"running: {cmd}", flush=True)
    r = subprocess.run([str(ROOT / ".venv" / "Scripts" / "python.exe"), str(ROOT / "scripts" / "run_queue.py"), "--profile", "full", "--max-jobs", "1", cmd],
                       cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    print(f"exit {r.returncode}", flush=True)
    remaining = [l for l in QUEUE.read_text().splitlines() if l.strip() != cmd]
    QUEUE.write_text("\n".join(remaining) + ("\n" if remaining else ""))
print("done", flush=True)
log.close()
